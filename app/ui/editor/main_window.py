from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QMessageBox, QSizePolicy, QSplitter

from ui.editor.video_canvas import VideoCanvas
from ui.editor.player_controls import PlayerControls
from ui.editor.timeline_graphics import TimelineView
from ui.editor.inspector import Inspector
from core.media_controller import MediaController
from core.store import Store
from engine.exporter import Exporter
from ui.components.assets_panel import AssetsPanel
from core.utils_timeline import clips_to_timeline_items, total_sequence_duration_ms


class EditorWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Luminare — Lecteur & Timeline")
        self.resize(1280, 720)

        # --- Backends ---
        self.media = MediaController(self)
        self.store = Store(self)
        self.exporter = Exporter()

        # --- Widgets principaux ---
        self.canvas = VideoCanvas()
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.controls = PlayerControls()
        self.controls.set_media(self.media)

        self.timeline_view = TimelineView(self)      # timeline vidéo

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
        center_col_layout.addLayout(self.controls)

        # --- Splitter horizontal principal (Assets | Canvas | Inspector) ---
        top_splitter = QSplitter(Qt.Horizontal, self)
        top_splitter.addWidget(self.assets)
        top_splitter.addWidget(self.center_container)
        top_splitter.addWidget(self.inspector)
        top_splitter.setSizes([220, 820, 240])

        # --- Panel des timelines (empile les 2 timelines) ---
        timelines_panel = QWidget(self)
        tl_layout = QVBoxLayout(timelines_panel)
        tl_layout.setContentsMargins(0, 0, 0, 0)
        tl_layout.setSpacing(2)
        tl_layout.addWidget(self.timeline_view, stretch=1)     # Timeline vidéo

        # --- Splitter vertical (haut/bas) ---
        main_splitter = QSplitter(Qt.Vertical, self)
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(timelines_panel)
        main_splitter.setSizes([520, 240])

        # --- Layout racine ---
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)
        root.addWidget(main_splitter)

        # --- Connexions principales ---
        self.media.frameImageAvailable.connect(self.canvas.set_frame)
        self.media.positionChanged.connect(self.canvas.set_playhead_ms)
        self.canvas.set_project(self.store.project())

        # --- Timeline vidéo ↔ player ---
        self.timeline_view.seekRequested.connect(self._on_smart_seek)
        self.media.positionChanged.connect(self.timeline_view.set_playhead_ms)
        self.controls.zoomChanged.connect(self.timeline_view.set_zoom)

        # --- Timeline images/titres : DnD d’images ---
        self.timeline_view.clipDropRequested.connect(self._on_timeline_drop)


        # --- Assets panel events ---
        if hasattr(self.assets, "addImageRequested"):
            self.assets.addImageRequested.connect(self._add_image_at_playhead)
        if hasattr(self.assets, "addVideoRequested"):
            self.assets.addVideoRequested.connect(self._add_video_at_playhead)
        if hasattr(self.assets, "loadVideoRequested"):  # ✅ nouveau signal du bouton "Charger dans le lecteur"
            self.assets.loadVideoRequested.connect(self._open_video_from_assets)    

        # --- Erreurs et timecodes ---
        self.media.errorOccurred.connect(self._on_media_error)
        self.media.durationChanged.connect(self.controls.set_duration)
        self.media.positionChanged.connect(self.controls.set_position)

        # --- Contrôles ---
        self.controls.openRequested.connect(self._open_file)
        self.controls.exportRequested.connect(self._export)

        # --- Inspector ↔ Store ---
        self.inspector.filtersChanged.connect(self._on_filters_changed)
        self.inspector.setTitleStartRequested.connect(self._apply_title_start_from_playhead)
        self.inspector.setTitleEndRequested.connect(self._apply_title_end_from_playhead)
        self.canvas.overlaySelected.connect(self.inspector.set_selected_overlay)

        # --- Store → UI ---
        self.store.overlayChanged.connect(self._refresh_all_timeline_items)
        self.store.clipsChanged.connect(self._refresh_all_timeline_items)

        # --- Initialisation ---
        self._refresh_all_timeline_items()

    # ---------- Actions ----------
    def _open_file(self):
        start_dir = str(Path.cwd() / "assets")
        f, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir une vidéo", start_dir,
            "Vidéos (*.mp4 *.mov *.mkv *.avi);;Tous les fichiers (*.*)"
        )
        if not f:
            return

        self._open_video_from_assets(f)

    def _open_video_from_assets(self, path: str):
        """Charge une vidéo dans le lecteur + ajoute le clip à la timeline."""
        if not path or not Path(path).exists():
            QMessageBox.warning(self, "Erreur", "Le fichier vidéo n’existe pas.")
            return

        print(f"[INFO] Chargement vidéo : {path}")
        self.media.load(QUrl.fromLocalFile(path))
        self._current_media_path = path
        self.media.play()

        def _once_set_clip(d_ms: int):
            try:
                self.media.durationChanged.disconnect(_once_set_clip)
            except Exception:
                pass
            dur_s = max(0.1, d_ms / 1000.0)
            self.store.add_video_clip(path, in_s=0.0, out_s=0.0, duration=dur_s)

        self.media.durationChanged.connect(_once_set_clip)

    def _export(self):
        proj = self.store.project()
        src = proj.clips[0].path if proj.clips else str(Path("assets") / "Fluid_Sim_Hue_Test.mp4")
        try:
            out_path = self.exporter.export_from_project(proj, fallback_src=src)
            QMessageBox.information(self, "Export", f"Fichier exporté : {out_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export échoué", str(e))

    def _on_media_error(self, text: str):
        if text:
            QMessageBox.warning(self, "Avertissement média", text)

    # ---------- Overlays ----------
    def _on_filters_changed(self, b, c, s, v):
        self.store.set_filters(brightness=b, contrast=c, saturation=s, vignette=v)

    def _apply_title_start_from_playhead(self):
        ms = self.media.position_ms()
        self.store.set_last_overlay_start(ms / 1000.0)

    def _apply_title_end_from_playhead(self):
        ms = self.media.position_ms()
        self.store.set_last_overlay_end(ms / 1000.0)

    def _refresh_all_timeline_items(self):
        """
        Rafraîchit TOUS les items (clips, images, titres) sur la TimelineView.
        """
        project = self.store.project()
        
        # 1. Mettre à jour la timeline graphique
        self.timeline_view.set_project_data(project) 
        
        # 2. Mettre à jour le canvas
        self.canvas.set_project(project)


    def _on_timeline_drop(self, path: str, start_s: float):
        """
        Gère un drop depuis l'AssetsPanel, qu'importe le type.
        """
        # On pourrait faire une détection de type plus robuste
        ext = (path.split(".")[-1] or "").lower()
        if ext in ["mp4", "mov", "mkv", "avi"]:
            # C'est une vidéo
            self.store.add_video_clip_at(path, start_s, duration_s=5.0)
            # self._on_clips_changed() # <- Plus besoin, Store émettra clipsChanged
        elif ext in ["png", "jpg", "jpeg", "webp"]:
            # C'est une image
            self.store.add_image_overlay(path, start_s, duration=3.0)
            # self._refresh_overlay() # <- Plus besoin, Store émettra overlayChanged
            self.media.seek_ms(int(start_s * 1000))


    def _add_video_at_playhead(self, path: str):
        start_s = self.media.position_ms() / 1000.0
        self.store.add_video_clip_at(path, start_s, duration_s=5.0)

    # ---------- Images ----------
    def _add_image_at_playhead(self, path: str):
        start_s = self.media.position_ms() / 1000.0
        self.on_timeline_drop_image(path, start_s)

    def on_timeline_drop_image(self, path: str, start_s: float):
        self.store.add_image_overlay(path, start_s, duration=3.0)
        self.canvas.set_project(self.store.project())
        self.media.seek_ms(int(start_s * 1000))

    def _on_smart_seek(self, global_ms: int):
        """
        Le "chef d'orchestre".
        Trouve le bon clip à la bonne position et dit au MediaController de le charger.
        """
        global_s = global_ms / 1000.0
        
        # 1. Demander au Store quel clip se trouve à cet instant
        #    (C'est la fonction que vous avez ajoutée dans store.py)
        idx, clip, local_s = self.store.clip_at_global_time(global_s)

        if not clip:
            # On a cliqué après la fin, ou la timeline est vide
            self.media.stop() # Ou self.media.pause()
            self._current_media_path = None
            return

        # 2. Convertir le temps local en millisecondes
        local_ms = int(local_s * 1000.0)
        
        # 3. Le clip trouvé est-il déjà chargé ?
        if clip.path == self._current_media_path:
            # OUI : Il suffit de chercher (seek)
            self.media.seek_ms(local_ms)
        else:
            # NON : Il faut charger le nouveau clip ET chercher
            print(f"[DEBUG] Changement de clip : {clip.path}")
            self._current_media_path = clip.path
            self.media.load(QUrl.fromLocalFile(clip.path))
            
            # ATTENTION : QMediaPlayer charge de manière asynchrone.
            # On ne peut pas appeler seek_ms() immédiatement.
            # On doit attendre que le média soit chargé.
            
            def _seek_when_loaded():
                try:
                    # Se désinscrire pour ne pas appeler en boucle
                    self.media.durationChanged.disconnect(_seek_when_loaded)
                except Exception:
                    pass # Déjà déconnecté
                
                print(f"[DEBUG] Média chargé, seek à {local_ms}ms")
                self.media.seek_ms(local_ms)
                
            # Le signal 'durationChanged' est un bon indicateur que le média est prêt
            self.media.durationChanged.connect(_seek_when_loaded)
