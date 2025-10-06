# core/media_controller.py
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink
from PySide6.QtGui import QImage

class MediaController(QObject):
    durationChanged = Signal(int)
    positionChanged = Signal(int)
    errorOccurred = Signal(str)
    frameImageAvailable = Signal(QImage)   # ← frame vidéo (image) pour le canvas

    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._player.setAudioOutput(self._audio)
        self._current_url = None

        # vidéo
        self._sink = QVideoSink(self)
        self._player.setVideoOutput(self._sink)
        self._sink.videoFrameChanged.connect(self._on_frame)

        self._player.durationChanged.connect(lambda d: self.durationChanged.emit(int(d or 0)))
        self._player.positionChanged.connect(lambda p: self.positionChanged.emit(int(p or 0)))
        self._player.errorOccurred.connect(lambda e, t="": self.errorOccurred.emit(f"{e}: {t}" if e else ""))

    # ---- video frames -> image
    def _on_frame(self, frame):
        if not frame.isValid():
            return
        img = frame.toImage()  # QImage
        if not img.isNull():
            self.frameImageAvailable.emit(img)

    # ---- control
    def load(self, url: QUrl):
        self._current_url = url
        self._player.setSource(url)

    def play(self): self._player.play()
    def pause(self): self._player.pause()
    def stop(self): self._player.stop()
    def seek_ms(self, ms: int): self._player.setPosition(max(0, int(ms)))
    def set_volume(self, v: float): self._audio.setVolume(max(0.0, min(1.0, float(v))))

    # info
    def duration_ms(self) -> int: return int(self._player.duration() or 0)
    def position_ms(self) -> int: return int(self._player.position() or 0)
    def current_path(self) -> str:
        try:
            return self._current_url.toLocalFile() if self._current_url else ""
        except Exception:
            return ""
