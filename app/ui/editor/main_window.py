from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QSizePolicy, QSplitter

from ui.editor.video_canvas import VideoCanvas
from ui.editor.player_controls import PlayerControls
from ui.editor.timeline_graphics import TimelineView
from ui.editor.inspector import Inspector

from core.media_controller import MediaController
from core.sequence_player import SequencePlayer
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
        self.media = MediaController(self)        # player 1-fichier
        self.store = Store(self)                  # modèle
        self.seq = SequencePlayer(self.media, self.store, self)  # séquence multi-clips
        self.exporter = Exporter()

        # --- Widgets principaux ---
        self.canvas = VideoCanvas()
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.controls = PlayerControls()
        self.controls.set_media(self.seq)
        self._sel_in_s = None
        self._sel_out_s = None


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
        center_col_layout.addLayout(self.controls)

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

        # --- Bouton Supprimer ---
        self._selected_segment = None  # tuple (index, start_s, duration_s) ou None

        self.timeline_view.segmentSelected.connect(self._on_segment_selected)
        self.timeline_view.segmentCleared.connect(self._on_segment_cleared)

        # Bouton "Suppr (refermer)" -> supprime le segment sélectionné
        if hasattr(self.controls, "deleteSelectionCloseRequested"):
            self.controls.deleteSelectionCloseRequested.connect(self._delete_selected_segment)


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

        # resize d’un clip vidéo (timeline → store)
        self.timeline_view.clipResized.connect(self._on_clip_resized)

    # ---------- Export ----------
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

        video_items = clips_to_timeline_items(proj.clips)  # [{start,duration,label,color}, ...]
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
        """
        Reconstruit la timeline unique (3 pistes : Vidéo / Images / Textes)
        à partir de l'état actuel du Store, puis met à jour la durée totale.
        """
        from pathlib import Path as _P
        proj = self.store.project()

        # PISTE VIDÉO : transforme les clips du projet en items pour la timeline
        video_items = clips_to_timeline_items(proj.clips)  # [{start,duration,label,color}, ...]

        # PISTE IMAGES
        image_items = [
            {
                "start": o.start,
                "duration": max(0.1, (o.end - o.start)),
                "label": f"img:{_P(o.path).stem}",
                "color": "#9be7a5",
            }
            for o in proj.image_overlays
        ]

        # PISTE TEXTES
        text_items = [
            {
                "start": ov.start,
                "duration": max(0.1, (ov.end - ov.start)),
                "label": (ov.text or "Titre"),
                "color": "#d4b5ff",
            }
            for ov in proj.text_overlays
        ]

        # Pousse dans la vue (timeline unique)
        self.timeline_view.set_tracks(video_items, image_items, text_items)

        # Met à jour la durée totale de séquence pour le ruler / zoom / scroll
        total_ms = total_sequence_duration_ms(proj.clips)
        if total_ms > 0:
            self.timeline_view.set_total_duration(total_ms)


    # ---------- Clips / Timeline ----------
    def _on_clips_changed(self):
        self._refresh_overlay()  # on a désormais une seule API pour alimenter les 3 pistes

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
            self._on_clips_changed()

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
            if hasattr(self.store, "clipsChanged"):
                self.store.clipsChanged.emit()
            if hasattr(self.store, "changed"):
                self.store.changed.emit()
            self._refresh_overlay()

    # ---------- Action "✂ Couper au playhead" ----------
    def split_current_clip(self):
        ms = self.seq.position_ms()
        clips = self.store.project().clips
        acc = 0.0
        for i, c in enumerate(clips):
            dur = float(getattr(c, "duration_s", 0.0) or (getattr(c, "out_s", 0.0) - getattr(c, "in_s", 0.0)))
            if acc <= ms/1000.0 <= acc + dur:
                local = ms/1000.0 - acc
                self.store.split_clip_at(i, local)
                self._refresh_overlay()
                return
            acc += dur

    def _on_segment_selected(self, idx: int, start_s: float, duration_s: float):
        self._selected_segment = (int(idx), float(start_s), float(duration_s))

    def _on_segment_cleared(self):
        self._selected_segment = None

    def _delete_selected_segment(self):
        if not self._selected_segment:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Suppression", "Clique d'abord un segment vidéo dans la timeline.")
            return

        idx, start_s, duration_s = self._selected_segment
        a = float(start_s)
        b = float(start_s + duration_s)

        try:
            # refermer le trou
            self.store.delete_segment(a, b, close_gap=True)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Suppression", f"Erreur: {e}")
            return

        # reset sélection UI & refresh
        self._selected_segment = None
        # la timeline se rafraîchit comme d'habitude via clipsChanged -> _refresh_overlay/_on_clips_changed
        if hasattr(self.store, "clipsChanged"):
            self.store.clipsChanged.emit()
