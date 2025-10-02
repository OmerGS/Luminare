# app/ui/main_window.py
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox,
    QFrame, QGridLayout
)

from app.ui.editor.video_view import VideoView
from app.ui.editor.player_controls import PlayerControls
from app.ui.editor.timeline import TimelineScroll
from app.ui.editor.importPanel import ImportPanel
from core.media_controller import MediaController
from engine.exporter import Exporter


class EditorWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Luminare — Éditeur vidéo")
        self.resize(1400, 800)

        # back
        self.media = MediaController(self)
        self.exporter = Exporter()

        # widgets principaux
        self.import_panel = ImportPanel(self.add_media_to_timeline)  # haut gauche
        self.video = VideoView()                                    # milieu
        self.controls = PlayerControls()
        self.timeline_scroll = TimelineScroll(self)                 # bas
        self.timeline = self.timeline_scroll.timeline

        # placeholder haut droite (vide)
        self.right_placeholder = QFrame()
        self.right_placeholder.setFrameShape(QFrame.StyledPanel)

        # layout éditeur vidéo (vidéo + controls)
        video_layout = QVBoxLayout()
        video_layout.addWidget(self.video, stretch=5)
        video_layout.addLayout(self.controls)
        video_container = QWidget()
        video_container.setLayout(video_layout)

        # Layout principal en grille
        grid = QGridLayout(self)

        # ligne 0 → panneau import (30%) + vidéo (70%) + placeholder (reste)
        grid.addWidget(self.import_panel, 0, 0)
        grid.addWidget(video_container, 0, 1)
        grid.addWidget(self.right_placeholder, 0, 2)

        # ligne 1 → timeline (colspan = 3)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        grid.addWidget(sep, 1, 0, 1, 3)
        grid.addWidget(self.timeline_scroll, 2, 0, 1, 3)

        # proportions
        grid.setColumnStretch(0, 3)   # panneau import = 30%
        grid.setColumnStretch(1, 3)   # vidéo = 50%
        grid.setColumnStretch(2, 3)   # placeholder = 20%
        grid.setRowStretch(0, 5)      # partie haute = 50%
        grid.setRowStretch(2, 5)      # timeline = 50%

        # Wiring UI ↔ back
        self.video.attach(self.media)
        self.controls.attach(self.media)
        self.timeline.seekRequested.connect(self.media.seek_ms)

        # Media ↔ timeline / controls
        self.media.durationChanged.connect(self.timeline.set_duration)
        self.media.positionChanged.connect(self.timeline.set_position)
        self.media.errorOccurred.connect(self._on_media_error)
        self.media.durationChanged.connect(self.controls.set_duration)
        self.media.positionChanged.connect(self.controls.set_position)

        # Actions
        self.controls.openRequested.connect(self._open_file)
        self.controls.exportRequested.connect(self._export)

        # Zoom liaison
        self.controls.zoomChanged.connect(self.timeline.set_zoom)

    # ----- actions -----
    def _open_file(self):
        start_dir = str(Path.cwd() / "assets")
        f, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un média", start_dir,
            "Médias (*.mp4 *.mov *.mkv *.avi *.mp3 *.wav *.png *.jpg *.jpeg *.gif *.txt);;Tous les fichiers (*.*)"
        )
        if not f:
            return
        self.media.load(QUrl.fromLocalFile(f))
        self.media.play()

    def _export(self):
        src = self.media.current_path() or str(Path("assets") / "Fluid_Sim_Hue_Test.mp4")
        try:
            out_path = self.exporter.export_quick(src, self.media.duration_ms())
            QMessageBox.information(self, "Export", f"Fichier exporté : {out_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export échoué", str(e))

    def _on_media_error(self, text: str):
        if text:
            QMessageBox.warning(self, "Avertissement média", text)

    def add_media_to_timeline(self, file_path: str):
        print(f"[INFO] Média ajouté à la timeline : {file_path}")
