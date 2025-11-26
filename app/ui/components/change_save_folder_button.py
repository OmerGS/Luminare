from PySide6.QtWidgets import QPushButton
from app.ui import styles

class ChangeSaveFolderButton(QPushButton):
    def __init__(self, text: str, on_click=None):
        super().__init__(text)
        self.setStyleSheet(styles.CHANGE_FOLDER_BUTTON)
        if on_click:
            self.clicked.connect(on_click)