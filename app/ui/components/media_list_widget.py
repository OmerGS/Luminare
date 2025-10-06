# app/ui/editor/components/media_list_widget.py
import os
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QSize


class MediaListWidget(QListWidget):
    """Liste de médias avec aperçu (image / icône)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setDragEnabled(True)
        self.setIconSize(QSize(64, 64))  # ✅ Taille fixe 64x64

    def add_media_item(self, file_path: str):
        """Ajoute un média avec une miniature ou une icône par défaut."""
        ext = os.path.splitext(file_path)[1].lower()

        # Choix de l'icône
        if ext in [".png", ".jpg", ".jpeg", ".gif"]:
            pixmap = QPixmap(file_path).scaled(64, 64)
            icon = QIcon(pixmap)
        elif ext in [".mp4", ".avi", ".mov", ".mkv"]:
            icon = QIcon.fromTheme("video-x-generic") or QIcon("assets/icons/video.png")
        elif ext in [".mp3", ".wav", ".ogg"]:
            icon = QIcon.fromTheme("audio-x-generic") or QIcon("assets/icons/audio.png")
        elif ext in [".txt"]:
            icon = QIcon.fromTheme("text-x-generic") or QIcon("assets/icons/text.png")
        else:
            icon = QIcon.fromTheme("unknown") or QIcon("assets/icons/file.png")

        # Item avec icône
        item = QListWidgetItem(icon, os.path.basename(file_path))
        item.setData(256, file_path)  # stocker chemin complet
        self.addItem(item)
