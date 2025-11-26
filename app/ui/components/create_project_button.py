from PySide6.QtWidgets import QPushButton
from app.ui import styles

class CreateProjectButton(QPushButton):
    def __init__(self, text: str, on_click=None):
        super().__init__(text)
        self.setStyleSheet(styles.CREATE_PROJECT_BUTTON_STYLE)
        if on_click:
            self.clicked.connect(on_click)