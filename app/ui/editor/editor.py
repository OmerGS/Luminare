from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

class Editor(QWidget):
    def __init__(self, go_to_menu):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Bienvenue dans l'éditeur"))
        btn = QPushButton("Retour au menu")
        btn.clicked.connect(go_to_menu)
        layout.addWidget(btn)