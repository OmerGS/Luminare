# app/ui/components/assets_panel.py
from PySide6.QtCore import Qt, QMimeData, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QDrag
from PySide6.QtWidgets import (
    QListWidget, QListWidgetItem, QAbstractItemView,
)
import json, os

MIME_IMAGE_ASSET = "application/x-luminare-asset-image"

class _MediaList(QListWidget):
    """Liste avec miniatures + DnD vers la timeline."""
    def __init__(self, mime_type_for_drag: str | None = None, parent=None):
        super().__init__(parent)
        self.mime_type_for_drag = mime_type_for_drag
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(QPixmap(96, 96).size())
        self.setResizeMode(QListWidget.Adjust)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def add_path(self, path: str):
        it = QListWidgetItem(os.path.basename(path))
        it.setIcon(QIcon(path))
        it.setData(Qt.UserRole, path)
        self.addItem(it)

    def current_path(self) -> str | None:
        it = self.currentItem()
        return it.data(Qt.UserRole) if it else None

    def mouseMoveEvent(self, e):
        # DnD si on est sur une entrée
        item = self.itemAt(e.pos())
        if item and (e.buttons() & Qt.LeftButton) and self.mime_type_for_drag:
            path = item.data(Qt.UserRole)
            if path:
                md = QMimeData()
                payload = {"path": path}
                md.setData(self.mime_type_for_drag, QByteArray(json.dumps(payload).encode("utf-8")))
                drag = QDrag(self)
                drag.setMimeData(md)
                drag.setPixmap(item.icon().pixmap(96, 96))
                drag.exec(Qt.CopyAction)
        super().mouseMoveEvent(e)
