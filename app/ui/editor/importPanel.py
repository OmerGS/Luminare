# app/ui/editor/import_panel.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QTabWidget, QHBoxLayout
from app.ui.components.media_list_widget import MediaListWidget
from app.ui.components.import_button import ImportButton


class ImportPanel(QWidget):
    def __init__(self, add_to_timeline_callback=None, parent=None):
        super().__init__(parent)

        self.add_to_timeline_callback = add_to_timeline_callback

        layout = QVBoxLayout(self)

        # Onglets catégories
        self.tabs = QTabWidget()
        self.categories = {
            "📹 Vidéo": ["*.mp4", "*.avi", "*.mov", "*.mkv"],
            "🎵 Audio": ["*.mp3", "*.wav", "*.ogg"],
            "🖼️ Images": ["*.png", "*.jpg", "*.jpeg", "*.gif"],
            "📝 Texte": ["*.txt"],
        }

        self.lists = {}
        for name in self.categories.keys():
            lst = MediaListWidget()
            self.lists[name] = lst
            self.tabs.addTab(lst, name)

        layout.addWidget(self.tabs)

        # Bouton Import
        btn_layout = QHBoxLayout()
        self.btn_import = ImportButton("Importer")
        self.btn_import.clicked.connect(self.import_file)
        btn_layout.addWidget(self.btn_import)
        layout.addLayout(btn_layout)

    def import_file(self):
        """Ouvre un QFileDialog selon la catégorie active et ajoute le média."""
        current_tab = self.tabs.tabText(self.tabs.currentIndex())
        exts = " ".join(self.categories[current_tab])
        name_filter = f"{current_tab} ({exts})"

        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter(name_filter)

        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            for f in files:
                self.lists[current_tab].add_media_item(f)
                if self.add_to_timeline_callback:
                    self.add_to_timeline_callback(f)
