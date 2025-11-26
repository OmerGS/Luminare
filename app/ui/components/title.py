from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel
from app.ui import styles

class Title(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.setStyleSheet(styles.TITLE_STYLE)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
