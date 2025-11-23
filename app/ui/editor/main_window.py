from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QSizePolicy, QSplitter, QFileDialog, QInputDialog

from ui.editor.video_canvas import VideoCanvas
from ui.editor.player_controls import PlayerControls
from ui.editor.timeline_graphics import TimelineView
from ui.editor.inspector import Inspector

from core.media_controller import MediaController
from core.sequence_player import SequencePlayer
from core.store import Store
from core.utils_timeline import clips_to_timeline_items, total_sequence_duration_ms


from core.export.export_service import ExportService
from core.export.export_profile import DEFAULT_PROFILES
from core.export.engine_interface import RenderError
from ui.editor.assets_panel import AssetsPanel

class EditorWindow(QWidget):
    def __init__(self, store: Store, export_service: ExportService, parent=None):
        super().__init__()
        self.resize(1280, 720)

        
        # back
        self.store = store
        self.exporter = export_service

        self.media = MediaController(self)        # player 1-fichier
        self.seq = SequencePlayer(self.media, self.store, self) 

        # centre vidéo (canvas)
        self.canvas = VideoCanvas()

        self.controls = PlayerControls()
        self.controls.set_media(self.seq)

        self.timeline_view = TimelineView(self)   # Timeline unique à 3 pistes

        self.inspector = Inspector(self)
        self.inspector.setMinimumWidth(220)
        self.inspector.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.assets = AssetsPanel(self)
        self.assets.setMinimumWidth(160)

        # --- Colonne centrale (Canvas + Controls) ---
        self.center_container = QWidget(self)
        center_col_layout = QVBoxLayout(self.center_container)
        center_col_layout.setContentsMargins(0, 0, 0, 0)
        center_col_layout.setSpacing(6)
        center_col_layout.addWidget(self.canvas, stretch=1)
        center_col_layout.addWidget(self.controls)

        # --- Splitter horizontal principal (Assets | Canvas | Inspector) ---
        top_splitter = QSplitter(Qt.Horizontal, self)
        top_splitter.addWidget(self.assets)
        top_splitter.addWidget(self.center_container)
        top_splitter.addWidget(self.inspector)
        top_splitter.setSizes([220, 820, 240])

        # --- Splitter vertical (haut/bas) ---
        main_splitter = QSplitter(Qt.Vertical, self)
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.timeline_view)
        main_splitter.setSizes([520, 240])

        # --- Layout racine ---
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)
        root.addWidget(main_splitter)

        # --- Connexions principales (via le SÉQUENCEUR) ---
        self.seq.frameImageAvailable.connect(self.canvas.set_frame)
        self.seq.positionChanged.connect(self.canvas.set_playhead_ms)
        self.canvas.set_project(self.store.project())

        # --- Timeline ↔ séquenceur ---
        self.timeline_view.seekRequested.connect(self.seq.seek_ms)
        self.seq.positionChanged.connect(self.timeline_view.set_playhead_ms)
        self.controls.zoomChanged.connect(self.timeline_view.set_zoom)

        # --- DnD depuis timeline ---
        self.timeline_view.clipDropRequested.connect(self._add_video_clip_at_seconds)
        self.timeline_view.imageDropRequested.connect(self.on_timeline_drop_image)

        # --- DnD / actions depuis le panneau assets ---
        if hasattr(self.assets, "addImageRequested"):
            self.assets.addImageRequested.connect(self._add_image_at_playhead)
        if hasattr(self.assets, "addVideoRequested"):
            self.assets.addVideoRequested.connect(self._add_video_at_playhead)

        # --- Erreurs et timecodes (via le séquenceur) ---
        self.seq.errorOccurred.connect(self._on_media_error)
        self.seq.durationChanged.connect(self.controls.set_duration)   # durée totale séquence
        self.seq.positionChanged.connect(self.controls.set_position)   # position globale

        # --- Export ---
        self.controls.exportRequested.connect(self._export)

        # --- Bouton ✂ Couper ---
        if hasattr(self.controls, "splitRequested"):
            self.controls.splitRequested.connect(self.split_current_clip)

        # --- Sélection de segment (clic sur timeline) + suppression ---
        self._selected_segment = None  # tuple (index, start_s, duration_s) ou None
        self.timeline_view.segmentSelected.connect(self._on_segment_selected)
        self.timeline_view.segmentCleared.connect(self._on_segment_cleared)
        if hasattr(self.controls, "deleteSelectionCloseRequested"):
            self.controls.deleteSelectionCloseRequested.connect(self._delete_selected_segment)

        # --- Inspector ↔ Store ---
        self.inspector.filtersChanged.connect(self._on_filters_changed)
        self.inspector.setTitleStartRequested.connect(self._apply_title_start_from_playhead)
        self.inspector.setTitleEndRequested.connect(self._apply_title_end_from_playhead)
        self.canvas.overlaySelected.connect(self.inspector.set_selected_overlay)

        # --- Store → UI ---
        # IMPORTANT : un seul point d'entrée pour refresh ET reset de la sélection.
        self.store.overlayChanged.connect(self._on_store_clips_changed)
        self.store.clipsChanged.connect(self._on_store_clips_changed)

        # --- Initialisation ---
        self._on_store_clips_changed()

        # resize d’un clip vidéo (timeline → store)
        self.timeline_view.clipResized.connect(self._on_clip_resized)
        self.store.overlayChanged.connect(self._refresh_overlay)
        self._refresh_overlay()

    # ----- actions -----
    def _open_file(self):
        start_dir = str(Path.cwd() / "assets")
        f, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir une vidéo", start_dir,
            "Vidéos (*.mp4 *.mov *.mkv *.avi);;Tous les fichiers (*.*)"
        )
        if not f: return
        self.media.load(QUrl.fromLocalFile(f))
        self.media.play()
        # provisoire: clip unique avec une durée par défaut (ajustable après)
        self.store.set_clip(f, duration_s=5.0)

    # ---------- Export ----------
    def _export(self):
        proj = self.store.project()
        
        default_name = proj.name.strip() or "output"
        default_path = str(Path.cwd() / "exports" / f"{default_name}.mp4")
        
        out_path_str, _ = QFileDialog.getSaveFileName(
            self, "Exporter la vidéo", default_path, "Vidéos MP4 (*.mp4)"
        )
        
        if not out_path_str:
            return

        out_path = Path(out_path_str)
        
        profile = DEFAULT_PROFILES["h264_medium"]
        
        fallback_src = proj.clips[0].path if proj.clips else (str(Path("assets") / "Fluid_Sim_Hue_Test.mp4"))

        try:
            self.exporter.export_project(
                proj=proj,
                out_path=out_path,
                profile=profile,
                fallback_src=fallback_src
            )
            QMessageBox.information(self, "Exportation terminée", f"Fichier exporté avec succès : \n{out_path}")
            
        except RenderError as e:
            QMessageBox.critical(self, "Échec de l'exportation", f"Une erreur de rendu est survenue:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Échec de l'exportation", f"Une erreur inattendue est survenue:\n{e}")

    def _on_media_error(self, text: str):
        if text:
            QMessageBox.warning(self, "Avertissement média", text)

    # ---------- Overlays ----------
    def _on_filters_changed(self, b, c, s, v):
        self.store.set_filters(brightness=b, contrast=c, saturation=s, vignette=v)

    def _apply_title_start_from_playhead(self):
        ms = self.seq.position_ms()
        self.store.set_last_overlay_start(ms / 1000.0)

    def _apply_title_end_from_playhead(self):
        ms = self.seq.position_ms()
        self.store.set_last_overlay_end(ms / 1000.0)
        self._refresh_overlay()

    def _refresh_overlay(self):
        """Rafraîchit les 3 pistes (vidéo/images/titres) dans la timeline unique."""
        from pathlib import Path as _P
        proj = self.store.project()
        self.canvas.set_project(proj)

        video_items = clips_to_timeline_items(proj.clips)
        image_items = [
            {"start": o.start, "duration": max(0.1, (o.end - o.start)), "label": f"img:{_P(o.path).stem}", "color": "#9be7a5"}
            for o in proj.image_overlays
        ]
        text_items = [
            {"start": ov.start, "duration": max(0.1, (ov.end - ov.start)), "label": (ov.text or "Titre"), "color": "#d4b5ff"}
            for ov in proj.text_overlays
        ]

        self.timeline_view.set_tracks(video_items, image_items, text_items)

        total_ms = total_sequence_duration_ms(proj.clips)
        if total_ms > 0:
            self.timeline_view.set_total_duration(total_ms)

    def on_timeline_drop_image(self, path: str, start_s: float):
        ov = self.store.add_image_overlay(path, start_s, duration=3.0)
        from pathlib import Path as _P
        proj = self.store.project()
        self.canvas.set_project(proj)
        video_items = clips_to_timeline_items(proj.clips)
        image_items = [
            {"start": o.start, "duration": max(0.1, (o.end - o.start)), "label": f"img:{_P(o.path).stem}", "color": "#9be7a5"}
            for o in proj.image_overlays
        ]
        text_items = [
            {"start": ov.start, "duration": max(0.1, (ov.end - ov.start)), "label": (ov.text or "Titre"), "color": "#d4b5ff"}
            for ov in proj.text_overlays
        ]

        self.timeline_view.set_tracks(video_items, image_items, text_items)

        total_ms = total_sequence_duration_ms(proj.clips)
        if total_ms > 0:
            self.timeline_view.set_total_duration(total_ms)

    def _refresh_all_timeline_items(self):
        """(Garde pour compat) : redirige vers _refresh_overlay."""
        self._refresh_overlay()

    def _on_store_clips_changed(self):
        """Unifie refresh & remise à zéro de la sélection après toute modif Store."""
        self._selected_segment = None
        self._refresh_overlay()

    # ---------- Clips / Timeline ----------
    def _probe_duration_and_add(self, path: str, place_s: float):
        """
        Sonde la durée réelle du fichier (via MediaController) et ajoute le clip à la bonne place.
        Évite les 5s fixes.
        """
        tmp = MediaController(self)

        def _on_err(msg: str):
            try:
                tmp.errorOccurred.disconnect(_on_err)
                tmp.durationChanged.disconnect(_on_dur)
            except Exception:
                pass
            QMessageBox.warning(self, "Erreur média", msg)

        def _on_dur(ms: int):
            try:
                tmp.errorOccurred.disconnect(_on_err)
                tmp.durationChanged.disconnect(_on_dur)
            except Exception:
                pass
            dur_s = max(0.1, ms / 1000.0)
            if hasattr(self.store, "add_video_clip_at"):
                self.store.add_video_clip_at(path, place_s, duration_s=dur_s)
            else:
                self.store.add_video_clip(path, in_s=0.0, out_s=dur_s, duration=dur_s)
            # la connexion clipsChanged déclenchera _on_store_clips_changed

        tmp.errorOccurred.connect(_on_err)
        tmp.durationChanged.connect(_on_dur)
        tmp.load(QUrl.fromLocalFile(path))  # charge en silencieux juste pour récupérer la durée

    def _add_video_clip_at_seconds(self, path: str, start_s: float):
        """Ajoute un clip vidéo AU TEMPS demandé avec sa vraie durée."""
        self._probe_duration_and_add(path, start_s)

    def _add_video_at_playhead(self, path: str):
        start_s = self.seq.position_ms() / 1000.0
        self._probe_duration_and_add(path, start_s)

    # ---------- Images ----------
    def _add_image_at_playhead(self, path: str):
        start_s = self.seq.position_ms() / 1000.0
        self.on_timeline_drop_image(path, start_s)

    def on_timeline_drop_image(self, path: str, start_s: float):
        self.store.add_image_overlay(path, start_s, duration=3.0)
        self.canvas.set_project(self.store.project())
        self.seq.seek_ms(int(start_s * 1000))
        # overlayChanged -> _on_store_clips_changed rafraîchira

    # ---------- Timeline resize → Store (vidéo) ----------
    def _on_clip_resized(self, idx: int, start_s: float, in_s: float, duration_s: float):
        proj = self.store.project()
        if 0 <= idx < len(proj.clips):
            c = proj.clips[idx]
            try:
                c.in_s = float(in_s)
                c.duration_s = max(0.1, float(duration_s))
                c.out_s = c.in_s + c.duration_s
            except Exception:
                pass
            # Informe le Store (qui déclenchera le refresh unifié)
            if hasattr(self.store, "clipsChanged"):
                self.store.clipsChanged.emit()
            if hasattr(self.store, "changed"):
                self.store.changed.emit()

    # ---------- Action "✂ Couper" ----------
    def split_current_clip(self):
        """
        Coupe exactement à la dernière position cliquée dans la timeline,
        sinon au niveau du playhead si aucun clic n'a été mémorisé.
        """
        # Immobilise le playhead pendant l'opération
        if hasattr(self.seq, "pause"):
            self.seq.pause()

        # Récupère la dernière position cliquée (timeline) sinon le playhead
        t_click = None
        if hasattr(self.timeline_view, "last_clicked_seconds"):
            t_click = self.timeline_view.last_clicked_seconds()
        t_s = float(t_click) if t_click is not None else (self.seq.position_ms() / 1000.0)

        idx, clip, local = self.store.clip_at_global_time(t_s)
        if idx >= 0 and clip is not None:
            if not self.store.split_clip_at(idx, local):
                # Si exactement sur une frontière, pousse d’un epsilon
                eps = 1e-6
                idx, clip, local = self.store.clip_at_global_time(t_s + eps)
                self.store.split_clip_at(idx, local)

            # Nettoie la dernière position de clic pour éviter tout "fantôme"
            if hasattr(self.timeline_view, "clear_last_click"):
                self.timeline_view.clear_last_click()
            return

        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Couper", "Aucun clip vidéo à cet instant.")


    # ---------- Sélection depuis la timeline ----------
    def _on_segment_selected(self, idx: int, start_s: float, duration_s: float):
        self._selected_segment = (int(idx), float(start_s), float(duration_s))

    def _on_segment_cleared(self):
        self._selected_segment = None

    def _delete_selected_segment(self):
        if not self._selected_segment:
            QMessageBox.information(self, "Suppression", "Clique d'abord un segment vidéo dans la timeline.")
            return

        idx, start_s, duration_s = self._selected_segment
        a = float(start_s)
        b = float(start_s + duration_s)

        try:
            # refermer le trou (le Store émettra clipsChanged → refresh + reset sélection)
            self.store.delete_segment(a, b, close_gap=True)
        except Exception as e:
            QMessageBox.warning(self, "Suppression", f"Erreur: {e}")
            return

    def _prompt_for_project(self):
        """Affiche une boîte de dialogue pour choisir entre nouveau projet ou chargement."""
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("Démarrer votre session")
        msgBox.setText("Que voulez-vous faire ?")
        msgBox.setInformativeText("Un nouveau projet vierge est chargé par défaut.")
        
        new_project_btn = msgBox.addButton("Nouveau Projet", QMessageBox.AcceptRole)
        load_project_btn = msgBox.addButton("Charger un Projet", QMessageBox.ActionRole)
        msgBox.setDefaultButton(new_project_btn)

        msgBox.exec()
        
        clicked_button = msgBox.clickedButton()

        if clicked_button == load_project_btn:
            self._open_load_dialog()
            
        elif clicked_button == new_project_btn:
            new_name, ok = QInputDialog.getText(
                self, 
                "Nommer votre projet", 
                "Entrez le nom du nouveau projet:",
                text=self.store.project().name
            )
            
            if ok and new_name and new_name != self.store.project().name:
                self.store.set_project_name(new_name)
                print(f"Action: Nouveau projet nommé : {new_name}")
            elif ok:
                print("Action: Nouveau projet conservant le nom par défaut.")
            else:
                print("Création du nouveau projet annulée (nom par défaut conservé).")
            
    def _open_load_dialog(self):
        """Ouvre la boîte de dialogue standard pour sélectionner un fichier .lmprj."""
        from core.save_system.serializers import LMPRJChunkedSerializer
        import os
        
        save_dir = LMPRJChunkedSerializer.get_save_dir()
        
        selected_file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Charger un projet Luminare (.lmprj)",
            save_dir,
            "Fichiers Projet Luminare (*.lmprj)"
        )

        if selected_file_path:
            filename_to_load = os.path.basename(selected_file_path)
            self.store.load_project(filename_to_load)
            proj = self.store.project()
            if proj.clips:
                 self.media.load(QUrl.fromLocalFile(proj.clips[0].path))
                 self.media.seek_ms(0)
                 self._refresh_overlay()
        else:
            print("Chargement annulé, conservation du projet actuel.")

    def setup_project_on_entry(self):
        """
        Gère le dialogue de choix Nouveau/Charger. 
        À appeler juste avant de rendre l'éditeur visible.
        """
        self._prompt_for_project() 
        self._refresh_overlay()
        self.setWindowTitle(f"Luminare — {self.store.project().name}")