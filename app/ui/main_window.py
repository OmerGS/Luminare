# app/ui/main_window.py
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QRunnable, Slot, QThreadPool, QObject, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QFrame
)

from app.ui.video_view import VideoView
from app.ui.player_controls import PlayerControls
from app.ui.timeline import TimelineScroll          # <-- assure-toi que le fichier s'appelle timeline.py
from core.media_controller import MediaController
from engine.exporter import Exporter


class MainWindow(QWidget):                           # <-- QWidget est bien importé
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Luminare — Lecteur & Timeline")
        self.resize(1200, 700)

        # back
        self.media = MediaController(self)
        self.exporter = Exporter()

        # UI
        self.video = VideoView()
        self.controls = PlayerControls()
        self.timeline_scroll = TimelineScroll(self)
        self.timeline = self.timeline_scroll.timeline

        # Layout
        root = QVBoxLayout(self)
        root.addWidget(self.video, stretch=5)
        root.addLayout(self.controls)
        sep = QFrame(); sep.setFrameShape(QFrame.HLine); root.addWidget(sep)
        root.addWidget(self.timeline_scroll, stretch=2)

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
            self, "Ouvrir une vidéo", start_dir,
            "Vidéos (*.mp4 *.mov *.mkv *.avi);;Tous les fichiers (*.*)"
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
