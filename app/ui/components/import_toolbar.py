from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QComboBox
from app.ui.components.import_button import ImportButton


class ImportToolbar(QWidget):
    def __init__(self, on_import_clicked=None, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Barre de recherche
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Rechercher un média...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #2c2c2c;
                color: white;
                padding: 6px 10px;
                border-radius: 6px;
                border: 1px solid #555;
            }
            QLineEdit:focus {
                border-color: #0078d7;
            }
        """)
        layout.addWidget(self.search_bar, 3)

        # Menu de tri
        self.sort_menu = QComboBox()
        self.sort_menu.addItems(["Nom (A-Z)", "Nom (Z-A)", "Date", "Taille"])
        self.sort_menu.setStyleSheet("""
            QComboBox {
                background-color: #2c2c2c;
                color: white;
                padding: 5px;
                border-radius: 6px;
                border: 1px solid #555;
            }
        """)
        layout.addWidget(self.sort_menu, 1)

        # Bouton d'import
        self.btn_import = ImportButton("Importer")
        if on_import_clicked:
            self.btn_import.clicked.connect(on_import_clicked)
        layout.addWidget(self.btn_import)
