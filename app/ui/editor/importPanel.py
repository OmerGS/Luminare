from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QFileDialog
from app.ui.components.import_toolbar import ImportToolbar
from app.ui.components.media_list_widget import MediaListWidget
from app.ui.components.icons import get_icon


class ImportPanel(QWidget):
    def __init__(self, add_to_timeline_callback=None, parent=None):
        super().__init__(parent)
        self.add_to_timeline_callback = add_to_timeline_callback

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # --- Barre supérieure ---
        self.toolbar = ImportToolbar(on_import_clicked=self.import_file)
        layout.addWidget(self.toolbar)

        # --- Onglets de médias ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444;
                border-radius: 8px;
                background-color: #1f1f1f;
            }
            QTabBar::tab {
                padding: 8px 14px;
                border-radius: 6px;
                margin-right: 4px;
                background-color: #2b2b2b;
                color: white;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: #0078d7;
            }
        """)

        self.categories = {
            "Vidéo": ["*.mp4", "*.avi", "*.mov", "*.mkv"],
            "Audio": ["*.mp3", "*.wav", "*.ogg"],
            "Images": ["*.png", "*.jpg", "*.jpeg", "*.gif"],
            "Texte": ["*.txt"],
            "Effets": ["*.fx", "*.preset", "*.json"],
        }

        self.lists = {}
        for name, exts in self.categories.items():
            lst = MediaListWidget()
            self.lists[name] = lst
            self.tabs.addTab(lst, get_icon(name, self), name)

        layout.addWidget(self.tabs)

    def import_file(self):
        """Ouvre une boîte de dialogue d’import et ajoute les médias dans la liste."""
        current_tab = self.tabs.tabText(self.tabs.currentIndex())
        exts = " ".join(self.categories[current_tab])
        name_filter = f"{current_tab} ({exts})"

        dialog = QFileDialog(self, "Importer des fichiers")
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter(name_filter)

        if dialog.exec():
            files = dialog.selectedFiles()
            for path in files:
                self.lists[current_tab].add_media_item(path)
                if self.add_to_timeline_callback:
                    self.add_to_timeline_callback(path)
