from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

# Pages simples pour l'exemple
class MainMenu(QWidget):
    def __init__(self, go_to_editor):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Bienvenue dans le menu principal"))
        btn = QPushButton("Aller à l'éditeur")
        btn.clicked.connect(go_to_editor)
        layout.addWidget(btn)