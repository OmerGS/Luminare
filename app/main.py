# app/main.py
import sys
from pathlib import Path

# S'assurer que le répertoire racine est dans le sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QMessageBox
from mvp_editor import main as render_project, project  # <-- on importe depuis mvp_editor.py

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Video Editor - MVP")
        layout = QVBoxLayout(self)

        btn = QPushButton("Exporter le projet d'exemple")
        layout.addWidget(btn)

        def do_export():
            try:
                render_project(project)
                QMessageBox.information(self, "OK", "Export terminé ! (voir dossier exports)")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

        btn.clicked.connect(do_export)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow(); w.resize(360, 120); w.show()
    sys.exit(app.exec())
