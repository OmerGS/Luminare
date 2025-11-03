from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QMessageBox, QSizePolicy, QSplitter

from ui.editor.video_canvas import VideoCanvas
from ui.editor.player_controls import PlayerControls
from ui.editor.timeline_graphics import TimelineView
from ui.editor.timeline import TimelineScroll       # timeline images / titres
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
        self.timeline_scroll = TimelineScroll(self)  # timeline images + titres

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
        tl_layout.addWidget(self.timeline_view, stretch=3)     # Timeline vidéo
        tl_layout.addWidget(self.timeline_scroll, stretch=1)   # Timeline images/titres

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
        self.timeline_view.seekRequested.connect(self.media.seek_ms)
        self.media.positionChanged.connect(self.timeline_view.set_playhead_ms)
        self.controls.zoomChanged.connect(self.timeline_view.set_zoom)

        # --- Timeline images/titres : DnD d’images ---
        self.timeline_scroll.timeline.imageDropped.connect(self.on_timeline_drop_image)

        # --- DnD vidéo depuis assets vers timeline vidéo ---
        self.timeline_view.clipDropRequested.connect(self._add_video_clip_at_seconds)

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
        self.inspector.addTitleRequested.connect(lambda: (self.store.add_text_overlay(), self._refresh_overlay()))
        self.inspector.removeTitleRequested.connect(lambda: (self.store.remove_last_text_overlay(), self._refresh_overlay()))
        self.inspector.titleTextChanged.connect(lambda txt: (self.store.update_last_overlay_text(txt), self._refresh_overlay()))
        self.inspector.filtersChanged.connect(self._on_filters_changed)
        self.inspector.setTitleStartRequested.connect(self._apply_title_start_from_playhead)
        self.inspector.setTitleEndRequested.connect(self._apply_title_end_from_playhead)
        self.canvas.overlaySelected.connect(self.inspector.set_selected_overlay)

        # --- Store → UI ---
        self.store.overlayChanged.connect(self._refresh_overlay)
        self.store.clipsChanged.connect(self._on_clips_changed)

        # --- Initialisation ---
        self._refresh_overlay()
        self._on_clips_changed()

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
        self.media.play()

        def _once_set_clip(d_ms: int):
            try:
                self.media.durationChanged.disconnect(_once_set_clip)
            except Exception:
                pass
            dur_s = max(0.1, d_ms / 1000.0)
            self.store.add_video_clip(path, in_s=0.0, out_s=0.0, duration=dur_s)
            self._on_clips_changed()

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
        self._refresh_overlay()

    def _apply_title_end_from_playhead(self):
        ms = self.media.position_ms()
        self.store.set_last_overlay_end(ms / 1000.0)
        self._refresh_overlay()

    def _refresh_overlay(self):
        """Rafraîchit les titres et images sur la timeline dédiée"""
        from pathlib import Path as _P
        proj = self.store.project()
        self.canvas.set_project(proj)

        # timeline images/titres (TimelineScroll)
        self.timeline_scroll.timeline.set_overlays([
            {"start": ov.start, "end": ov.end, "label": (ov.text or "Titre")}
            for ov in proj.text_overlays
        ])
        self.timeline_scroll.timeline.set_images([
            {"start": o.start, "end": o.end, "label": f"img:{_P(o.path).stem}"}
            for o in proj.image_overlays
        ])

    # ---------- Clips / Timeline ----------
    def _on_clips_changed(self):
        clips = self.store.project().clips
        items = clips_to_timeline_items(clips)
        self.timeline_view.set_clips(items)
        total_ms = total_sequence_duration_ms(clips)
        if total_ms > 0:
            self.timeline_view.set_total_duration(total_ms)

    def _add_video_clip_at_seconds(self, path: str, start_s: float):
        self.store.add_video_clip(path, in_s=0.0, out_s=0.0, duration=0.0)
        self._on_clips_changed()
        if hasattr(self.timeline_view, "ensure_visible_time"):
            self.timeline_view.ensure_visible_time(start_s)

    def _add_video_at_playhead(self, path: str):
        start_s = self.media.position_ms() / 1000.0
        self._add_video_clip_at_seconds(path, start_s)

    # ---------- Images ----------
    def _add_image_at_playhead(self, path: str):
        start_s = self.media.position_ms() / 1000.0
        self.on_timeline_drop_image(path, start_s)

    def on_timeline_drop_image(self, path: str, start_s: float):
        self.store.add_image_overlay(path, start_s, duration=3.0)
        self._refresh_overlay()
        self.canvas.set_project(self.store.project())
        self.media.seek_ms(int(start_s * 1000))
