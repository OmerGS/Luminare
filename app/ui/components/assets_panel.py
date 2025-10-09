# app/ui/components/assets_panel.py
from PySide6.QtCore import Qt, QMimeData, QByteArray, Signal
from PySide6.QtGui import QIcon, QPixmap, QDrag
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QTabWidget, QAbstractItemView, QLabel, QSizePolicy
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


class AssetsPanel(QWidget):
    """Panneau unique : onglets + import + bouton 'ajouter au curseur'."""
    addImageRequested = Signal(str)  # (path) → MainWindow._add_image_at_playhead

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        # Onglets
        self.tab_audio  = _MediaList(None)                               # pas de DnD (pour plus tard)
        self.tab_images = _MediaList(MIME_IMAGE_ASSET)                   # DnD vers timeline OK
        self.tab_text   = _MediaList(None)

        self.tabs.addTab(self.tab_audio,  "🎵 Audio")
        self.tabs.addTab(self.tab_images, "🖼️ Images")
        self.tabs.addTab(self.tab_text,   "📝 Texte")

        # Barre d’actions sous la liste
        btn_row1 = QHBoxLayout()
        self.btn_import = QPushButton("Importer des images…")
        btn_row1.addWidget(self.btn_import)
        root.addLayout(btn_row1)

        # Aperçu simple sous le bouton (optionnel)
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(80)
        self.preview.setStyleSheet("QLabel { background: #eee; border: 1px solid #ccc; }")
        root.addWidget(self.preview, 0)

        btn_row2 = QHBoxLayout()
        self.btn_add = QPushButton("Ajouter à la timeline (au curseur)")
        btn_row2.addWidget(self.btn_add)
        root.addLayout(btn_row2)

        # Connexions
        self.btn_import.clicked.connect(self._import_images)
        self.btn_add.clicked.connect(self._emit_selected)
        self.tab_images.currentItemChanged.connect(self._update_preview)

    # --- actions ---
    def _import_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Choisir des images", "",
            "Images (*.png *.jpg *.jpeg *.webp *.gif)"
        )
        for f in files:
            self.tab_images.add_path(f)
        # focus onglet Images si on vient d’ajouter des images
        if files:
            self.tabs.setCurrentWidget(self.tab_images)

    def _emit_selected(self):
        # On ne gère pour l’instant que l’onglet Images (comme demandé)
        if self.tabs.currentWidget() is self.tab_images:
            path = self.tab_images.current_path()
            if path:
                self.addImageRequested.emit(path)

    def _update_preview(self):
        path = self.tab_images.current_path()
        if path and os.path.exists(path):
            self.preview.setPixmap(QPixmap(path).scaledToHeight(76, Qt.SmoothTransformation))
        else:
            self.preview.setText("")
