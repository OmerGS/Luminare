from PySide6.QtWidgets import QWidget, QVBoxLayout, QSlider
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

        settingsLayout.addWidget(VolumeSlider(orientation=Qt.Horizontal, interval=1))
