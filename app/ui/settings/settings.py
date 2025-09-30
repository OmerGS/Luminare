from PySide6.QtWidgets import QWidget, QVBoxLayout
from app.ui import styles
from app.ui.components.title import Title
from app.ui.components.menu_button import MenuButton

class SettingsMenu(QWidget):
    def __init__(self, go_to_menu):
        super().__init__()
        
        self.setStyleSheet(styles.WINDOW_STYLE)