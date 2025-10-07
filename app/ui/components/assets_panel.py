# app/ui/components/assets_panel.py
from PySide6.QtCore import Qt, QMimeData, QByteArray, Signal
from PySide6.QtGui import QIcon, QPixmap, QDrag
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QFileDialog, QAbstractItemView
)
import json
import os

# Mime type utilisé pour le DnD vers la timeline
MIME_IMAGE_ASSET = "application/x-luminare-asset-image"


class AssetsPanel(QWidget):
    """
    Panneau de médias (images):
      - Importer des images (miniatures)
      - Drag & drop vers la timeline (mime custom)
      - Bouton "Ajouter à la timeline (au curseur)" -> signal addImageRequested(path)
    """
    addImageRequested = Signal(str)  # émet le path de l'image sélectionnée

    def __init__(self, parent=None):
        super().__init__(parent)

        self.list = QListWidget()
        self.list.setViewMode(QListWidget.IconMode)
        self.list.setIconSize(QPixmap(96, 96).size())
        self.list.setResizeMode(QListWidget.Adjust)
        self.list.setDragEnabled(True)
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)

        btn_import = QPushButton("Importer des images…")
        btn_import.clicked.connect(self._import_images)

        btn_add = QPushButton("Ajouter à la timeline (au curseur)")
        btn_add.clicked.connect(self._emit_selected)   # <= méthode définie plus bas

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        layout.addWidget(btn_import)
        layout.addWidget(self.list, 1)
        layout.addWidget(btn_add)

    # --- Actions ---
    def _import_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Choisir des images", "",
            "Images (*.png *.jpg *.jpeg *.webp *.gif)"
        )
        for f in files:
            it = QListWidgetItem(os.path.basename(f))
            it.setIcon(QIcon(f))
            it.setData(Qt.UserRole, f)
            self.list.addItem(it)

    def _emit_selected(self):
        """Émet le signal addImageRequested pour l’item sélectionné."""
        it = self.list.currentItem()
        if it:
            path = it.data(Qt.UserRole)
            if path:
                self.addImageRequested.emit(path)

    # --- Drag depuis la liste (pour DnD vers la timeline) ---
    def mouseMoveEvent(self, e):
        item = self.list.itemAt(e.pos())
        if item and (e.buttons() & Qt.LeftButton):
            path = item.data(Qt.UserRole)
            if path:
                md = QMimeData()
                md.setData(
                    MIME_IMAGE_ASSET,
                    QByteArray(json.dumps({"path": path}).encode("utf-8"))
                )
                drag = QDrag(self)
                drag.setMimeData(md)
                drag.setPixmap(item.icon().pixmap(96, 96))
                drag.exec(Qt.CopyAction)
        super().mouseMoveEvent(e)
