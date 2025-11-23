# app/ui/components/back_button.py
from PySide6.QtWidgets import QPushButton
from app.ui import styles

class BackButton(QPushButton):
    def __init__(self, on_click=None):
        super().__init__("⬅")
        self.setStyleSheet(styles.BUTTON_STYLE)
        if on_click:
            self.clicked.connect(on_click)
