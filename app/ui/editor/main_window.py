# app/ui/main_window.py
from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QFrame, QSizePolicy, QSplitter

from ui.editor.video_canvas import VideoCanvas
from ui.editor.player_controls import PlayerControls
from ui.editor.timeline import TimelineScroll
from ui.editor.inspector import Inspector
from core.media_controller import MediaController
from core.store import Store
from engine.exporter import Exporter
from ui.editor.assets_panel import AssetsPanel


# app/ui/main_window.py (extrait: classe EditorWindow)
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
        #self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.controls = PlayerControls()
        self.controls.set_media(self.media)

        self.timeline_scroll = TimelineScroll(self)
        self.timeline = self.timeline_scroll.timeline
        self.timeline.imageDropped.connect(self.on_timeline_drop_image)

        self.inspector = Inspector(self)
        #self.inspector.setMinimumWidth(260)
        #self.inspector.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.assets = AssetsPanel(self)

        #self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #self.assets.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #self.inspector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # --- Layout racine (UN SEUL) ---
        #main_layout = QVBoxLayout(self)
        #main_layout.setContentsMargins(6, 6, 6, 6)
       # #main_layout.setSpacing(6)

        #top_layout = QHBoxLayout()
        #top_layout.setContentsMargins(0, 0, 0, 0)
        #top_layout.setSpacing(6)

        # Colonne gauche : Import + Assets
        #left_col = QVBoxLayout()
        #left_col.setContentsMargins(0, 0, 0, 0)
        #left_col.setSpacing(6)
        #left_col.addWidget(self.assets, stretch=1)

        # Colonne centre : Vidéo + Controls
        #center_col = QVBoxLayout()
        #center_col.setContentsMargins(0, 0, 0, 0)
        #center_col.setSpacing(6)
        #center_col.addWidget(self.canvas, stretch=3)
        #center_col.addLayout(self.controls)

        # Colonne droite : Inspector
        #right_col = QVBoxLayout()
        #right_col.setContentsMargins(0, 0, 0, 0)
        #right_col.setSpacing(6)
        #right_col.addWidget(self.inspector, stretch=1)

        #top_layout.addLayout(left_col, 1)
        #top_layout.addLayout(center_col, 3)
        #top_layout.addLayout(right_col, 1)


        #main_layout.addLayout(top_layout, 5)
        #main_layout.addWidget(self.timeline_scroll, 1)

        # Colonne Gauche (Assets) : doit pouvoir se rétrécir mais rester lisible.
        self.assets.setMinimumWidth(150) # AJOUTÉ : Taille minimale pour Assets

        # Colonne Centre (Canvas + Controls) : doit avoir une taille minimale pour la vidéo.
        self.canvas.setMinimumSize(300, 200) # AJOUTÉ : Taille minimale pour la zone vidéo

        # Colonne Droite (Inspector) : a déjà 100 de minimum dans votre code ci-dessous.

        # Timeline : Assure une hauteur minimale pour la timeline.
        # Note : Votre classe TimelineScroll/TimelineWidget doit gérer son MinimumHeight correctement.
        if hasattr(self.timeline, 'setMinimumHeight'):
             self.timeline.setMinimumHeight(100) 

        self.center_container = QWidget()
        center_col_layout = QVBoxLayout(self.center_container)
        center_col_layout.setContentsMargins(0, 0, 0, 0)
        center_col_layout.setSpacing(6)

        center_col_layout.addWidget(self.canvas, stretch=3) 
        center_col_layout.addWidget(self.controls) 

        top_splitter = QSplitter(Qt.Orientation.Horizontal)


        top_splitter.addWidget(self.assets)          # Colonne gauche
        top_splitter.addWidget(self.center_container) # Colonne centre (Canvas + Controls)
        top_splitter.addWidget(self.inspector)

        top_splitter.setSizes([200, 600, 200])

        self.inspector.setMinimumWidth(100)

        main_splitter = QSplitter(Qt.Orientation.Vertical)
        
        main_splitter.addWidget(top_splitter)          # La zone supérieure complète
        main_splitter.addWidget(self.timeline_scroll)  # La Timeline

        main_splitter.setSizes([500, 100])
        
        # --- 4. Layout racine (UN SEUL) ---
        # Le layout principal contient désormais uniquement le splitter principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)
        main_layout.addWidget(main_splitter)

        # --- Wiring vidéo & timeline ---
        self.media.frameImageAvailable.connect(self.canvas.set_frame)
        self.media.positionChanged.connect(self.canvas.set_playhead_ms)
        self.canvas.set_project(self.store.project())

        self.assets.addImageRequested.connect(self._add_image_at_playhead)

        self.timeline.seekRequested.connect(self.media.seek_ms)
        self.media.durationChanged.connect(self.timeline.set_duration)
        self.media.positionChanged.connect(self.timeline.set_position)
        self.media.errorOccurred.connect(self._on_media_error)
        self.media.durationChanged.connect(self.controls.set_duration)
        self.media.positionChanged.connect(self.controls.set_position)

        # Actions
        self.controls.openRequested.connect(self._open_file)
        self.controls.exportRequested.connect(self._export)
        self.controls.zoomChanged.connect(self.timeline.set_zoom)
        self.controls.seekRelativeRequested.connect(self.media.seek_relative_ms)


        # Inspector ↔ Store
        self.inspector.addTitleRequested.connect(lambda: (self.store.add_text_overlay(), self._refresh_overlay()))
        self.inspector.removeTitleRequested.connect(lambda: (self.store.remove_last_text_overlay(), self._refresh_overlay()))
        self.inspector.titleTextChanged.connect(lambda txt: (self.store.update_last_overlay_text(txt), self._refresh_overlay()))
        self.inspector.filtersChanged.connect(self._on_filters_changed)
        self.inspector.setTitleStartRequested.connect(self._apply_title_start_from_playhead)
        self.inspector.setTitleEndRequested.connect(self._apply_title_end_from_playhead)
        self.canvas.overlaySelected.connect(self.inspector.set_selected_overlay)

        # Store → UI
        self.store.overlayChanged.connect(self._refresh_overlay)
        self._refresh_overlay()


    # ----- actions & helpers identiques à ta version -----
    def _open_file(self):
        start_dir = str(Path.cwd() / "assets")
        f, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir une vidéo", start_dir,
            "Vidéos (*.mp4 *.mov *.mkv *.avi);;Tous les fichiers (*.*)"
        )
        if not f:
            return
        self.media.load(QUrl.fromLocalFile(f))
        self.media.play()
        self.store.set_clip(f, duration_s=5.0)

    def _export(self):
        proj = self.store.project()
        src = proj.clips[0].path if proj.clips else (str(Path("assets") / "Fluid_Sim_Hue_Test.mp4"))
        try:
            out_path = self.exporter.export_from_project(proj, fallback_src=src)
            QMessageBox.information(self, "Export", f"Fichier exporté : {out_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export échoué", str(e))

    def _on_media_error(self, text: str):
        if text:
            QMessageBox.warning(self, "Avertissement média", text)

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

    def on_timeline_drop_image(self, path: str, start_s: float):
        ov = self.store.add_image_overlay(path, start_s, duration=3.0)
        from pathlib import Path as _P
        self.timeline.set_images([
            {"start": o.start, "end": o.end, "label": f"img:{_P(o.path).stem}"}
            for o in self.store.project().image_overlays
        ])
        self.canvas.set_project(self.store.project())
        self.media.seek_ms(int(start_s * 1000))

    def _add_image_at_playhead(self, path: str):
        start_s = self.media.position_ms() / 1000.0
        self.on_timeline_drop_image(path, start_s)

    def _refresh_overlay(self):
        self.canvas.set_project(self.store.project())
        from pathlib import Path as _P
        self.timeline.set_overlays([
            {"start": ov.start, "end": ov.end, "label": (ov.text or "Titre")}
            for ov in self.store.project().text_overlays
        ])

        if hasattr(self.timeline, "set_images"):
            self.timeline.set_images([
                {"start": o.start, "end": o.end, "label": f"img:{_P(o.path).stem}"}
                for o in self.store.project().image_overlays
            ])

