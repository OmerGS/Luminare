import os
import json
from PySide6.QtCore import Qt, QSize, QMimeData, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QDrag
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView

MIME_MEDIA_ASSET = "application/x-luminare-asset-media" 

class MediaListWidget(QListWidget):

    FILE_PATH_ROLE = Qt.UserRole + 1 

    def __init__(self, mime_type_for_drag: str | None = MIME_MEDIA_ASSET, parent=None):
        super().__init__(parent)
        self.mime_type_for_drag = mime_type_for_drag
        
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(QSize(96, 96)) 
        self.setResizeMode(QListWidget.Adjust)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionMode(QListWidget.SingleSelection)

    def add_media_item(self, file_path: str):
        """Ajoute un média avec une miniature ou une icône par défaut."""
        ext = os.path.splitext(file_path)[1].lower()

        icon = None
        if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
            pixmap = QPixmap(file_path).scaled(
                self.iconSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            icon = QIcon(pixmap)
        elif ext in [".mp4", ".avi", ".mov", ".mkv"]:
            # Placeholder for video icon
            icon = QIcon.fromTheme("video-x-generic") or QIcon("assets/icons/video.png")
        elif ext in [".mp3", ".wav", ".ogg"]:
            # Placeholder for audio icon
            icon = QIcon.fromTheme("audio-x-generic") or QIcon("assets/icons/audio.png")
        elif ext in [".txt"]:
            # Placeholder for text icon
            icon = QIcon.fromTheme("text-x-generic") or QIcon("assets/icons/text.png")
        else:
            # Default file icon
            icon = QIcon.fromTheme("unknown") or QIcon("assets/icons/file.png")

        item = QListWidgetItem(icon, os.path.basename(file_path))
        item.setData(self.FILE_PATH_ROLE, file_path)  
        self.addItem(item)

    def current_path(self) -> str | None:
        it = self.currentItem()
        return it.data(self.FILE_PATH_ROLE) if it else None

    def mouseMoveEvent(self, e):

        item = self.itemAt(e.pos())
        if item and (e.buttons() & Qt.LeftButton) and self.mime_type_for_drag:
            path = item.data(self.FILE_PATH_ROLE)
            if path:
                md = QMimeData()
                payload = {"path": path}
                data = QByteArray(json.dumps(payload).encode("utf-8"))
                md.setData(self.mime_type_for_drag, data)
                drag = QDrag(self)
                drag.setMimeData(md)
                drag.setPixmap(item.icon().pixmap(self.iconSize())) 
                drag.exec(Qt.CopyAction)
        
        super().mouseMoveEvent(e)