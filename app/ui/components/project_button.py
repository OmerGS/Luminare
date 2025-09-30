from PySide6.QtWidgets import QPushButton
from app.ui import styles

class ProjectButton(QPushButton):
    def __init__(self, text: str, on_click=None):
        super().__init__(text)
        self.setStyleSheet(styles.BUTTON_STYLE)
        if on_click:
            self.clicked.connect(on_click)