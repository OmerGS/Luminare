# app/ui/video_view.py
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QSizePolicy

class VideoView(QVideoWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def attach(self, media_controller):
        # connecte la sortie vidéo du contrôleur à ce widget
        media_controller.set_video_output(self)
