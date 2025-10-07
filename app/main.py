# app/main.py
import sys
from pathlib import Path

# S'assurer que le répertoire racine est dans le sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QMessageBox, QStackedWidget
from app.ui.menu.home.home_menu import MainMenu
from app.ui.editor.editor import Editor
from mvp_editor import main as render_project, project  # <-- on importe depuis mvp_editor.py

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Luminare")
        self.resize(600, 400)

        # Création du QStackedWidget
        self.stacked = QStackedWidget()

        # Création des pages
        self.main_menu = MainMenu(self.show_editor, self.show_editor, self.show_main_menu, ["video1", "video2","video5","video6","video7","video8","video9","video10"])
        self.editor = Editor(self.show_main_menu)

        # Ajout au QStackedWidget
        self.stacked.addWidget(self.main_menu)  # index 0
        self.stacked.addWidget(self.editor)     # index 1

        # Layout principal
        layout = QVBoxLayout(self)
        layout.addWidget(self.stacked)

    def show_editor(self):
        self.stacked.setCurrentWidget(self.editor)

    def show_main_menu(self):
        self.stacked.setCurrentWidget(self.main_menu)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
