from PySide6.QtWidgets import QSlider
from PySide6 import QtWidgets
from app.ui import styles

class VolumeSlider(QSlider):
    def __init__(self, orientation, interval):
        super().__init__(orientation, tickInterval= interval)
        self.setStyleSheet(styles.VOLUME_SLIDER)
        