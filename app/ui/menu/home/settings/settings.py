from PySide6.QtWidgets import QWidget, QVBoxLayout, QSlider, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from app.ui import styles
from app.ui.components.title import Title
from app.ui.components.menu_button import MenuButton
from app.ui.components.volume_slider import VolumeSlider

class SettingsMenu(QWidget):
    def __init__(self, go_to_menu):
        super().__init__()
        
        self.setStyleSheet(styles.WINDOW_STYLE)

        settingsLayout = QVBoxLayout(self)

        volumeLayout = QHBoxLayout()

        volumeLabel = QLabel("Volume")
        volumeLabel.setStyleSheet("color: white; font-size: 16px; margin-right: 10px;")

        self.volume_slider = VolumeSlider(orientation=Qt.Horizontal, interval=1000)

        volumeLayout.addWidget(volumeLabel)
        volumeLayout.addWidget(self.volume_slider, stretch=1)

        settingsLayout.addLayout(volumeLayout)

        settingsLayout.addStretch()
