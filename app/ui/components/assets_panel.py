from PySide6.QtCore import Qt, QMimeData, QByteArray, Signal
from PySide6.QtGui import QIcon, QPixmap, QDrag
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QTabWidget, QAbstractItemView, QLabel, QSizePolicy
)
import json, os
from pathlib import Path

MIME_IMAGE_ASSET = "application/x-luminare-asset-image"
MIME_VIDEO_ASSET = "application/x-luminare/video"


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
        # Icône pour les images / icône par défaut pour les vidéos
        if Path(path).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            it.setIcon(QIcon(path))
        else:
            it.setIcon(QIcon.fromTheme("video-x-generic"))
        it.setData(Qt.UserRole, path)
        self.addItem(it)

    def current_path(self) -> str | None:
        it = self.currentItem()
        return it.data(Qt.UserRole) if it else None

    def mouseMoveEvent(self, e):
        item = self.itemAt(e.pos())
        if item and (e.buttons() & Qt.LeftButton) and self.mime_type_for_drag:
            path = item.data(Qt.UserRole)
            if path:
                md = QMimeData()
                payload = {"path": path}
                md.setData(self.mime_type_for_drag, QByteArray(json.dumps(payload).encode("utf-8")))
                drag = QDrag(self)
                drag.setMimeData(md)
                px = item.icon().pixmap(96, 96)
                if not px.isNull():
                    drag.setPixmap(px)
                drag.exec(Qt.CopyAction)
        super().mouseMoveEvent(e)


class AssetsPanel(QWidget):
    """Panneau : import, aperçu, ajout ou chargement de médias."""
    addImageRequested = Signal(str)
    addVideoRequested = Signal(str)
    loadVideoRequested = Signal(str)  # ← NOUVEAU signal pour charger la vidéo dans le lecteur

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        # --- Onglets ---
        self.tab_video = _MediaList(MIME_VIDEO_ASSET)
        self.tab_audio = _MediaList(None)
        self.tab_images = _MediaList(MIME_IMAGE_ASSET)
        self.tab_text = _MediaList(None)

        self.tabs.addTab(self.tab_video, "▶️ Vidéos")
        self.tabs.addTab(self.tab_audio, "🎵 Audio")
        self.tabs.addTab(self.tab_images, "🖼️ Images")
        self.tabs.addTab(self.tab_text, "📝 Texte")

        # --- Bouton d’import ---
        row_import = QHBoxLayout()
        self.btn_import = QPushButton("Importer des médias…")
        row_import.addWidget(self.btn_import)
        root.addLayout(row_import)

        # --- Aperçu ---
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(80)
        self.preview.setStyleSheet("QLabel { background: #eee; border: 1px solid #ccc; }")
        root.addWidget(self.preview, 0)

        # --- Boutons d’action ---
        row_actions = QHBoxLayout()
        self.btn_add = QPushButton("Ajouter à la timeline (au curseur)")
        self.btn_load_video = QPushButton("Charger dans le lecteur")  # ← NOUVEAU bouton
        row_actions.addWidget(self.btn_add)
        row_actions.addWidget(self.btn_load_video)
        root.addLayout(row_actions)

        # --- Connexions ---
        self.btn_import.clicked.connect(self._import_current_tab)
        self.btn_add.clicked.connect(self._emit_selected)
        self.btn_load_video.clicked.connect(self._emit_load_video)
        self.tab_images.currentItemChanged.connect(self._update_preview)
        self.tab_video.currentItemChanged.connect(self._update_preview)
        self.tabs.currentChanged.connect(self._update_import_button_label)

        self._update_import_button_label()

    # ------------------------
    # Import / Preview / Actions
    # ------------------------
    def _import_current_tab(self):
        current = self.tabs.currentWidget()

        # --- IMAGES ---
        if current is self.tab_images:
            files, _ = QFileDialog.getOpenFileNames(
                self, "Importer des images", str(Path.cwd() / "assets"),
                "Images (*.png *.jpg *.jpeg *.webp *.gif)"
            )
            for f in files:
                self.tab_images.add_path(f)
            if files:
                self.tabs.setCurrentWidget(self.tab_images)
            return

        # --- VIDEOS ---
        if current is self.tab_video:
            files, _ = QFileDialog.getOpenFileNames(
                self, "Importer des vidéos", str(Path.cwd() / "assets"),
                "Vidéos (*.mp4 *.mov *.mkv *.avi)"
            )
            for f in files:
                self.tab_video.add_path(f)
            if files:
                self.tabs.setCurrentWidget(self.tab_video)
            return

    def _emit_selected(self):
        """Ajoute le média courant à la timeline."""
        tab = self.tabs.currentWidget()
        if tab is self.tab_images:
            path = self.tab_images.current_path()
            if path:
                self.addImageRequested.emit(path)
        elif tab is self.tab_video:
            path = self.tab_video.current_path()
            if path:
                self.addVideoRequested.emit(path)

    def _emit_load_video(self):
        """Charge la vidéo courante dans le lecteur."""
        if self.tabs.currentWidget() is not self.tab_video:
            return
        path = self.tab_video.current_path()
        if path:
            self.loadVideoRequested.emit(path)

    def _update_preview(self, *_):
        tab = self.tabs.currentWidget()
        path = None
        if tab is self.tab_images:
            path = self.tab_images.current_path()
        elif tab is self.tab_video:
            path = self.tab_video.current_path()

        if path and os.path.exists(path) and Path(path).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            self.preview.setPixmap(QPixmap(path).scaledToHeight(76, Qt.SmoothTransformation))
        else:
            self.preview.setText(Path(path).name if path else "")

    def _update_import_button_label(self, *_):
        tab = self.tabs.currentWidget()
        if tab is self.tab_images:
            self.btn_import.setText("Importer des images…")
            self.btn_load_video.setVisible(False)
        elif tab is self.tab_video:
            self.btn_import.setText("Importer des vidéos…")
            self.btn_load_video.setVisible(True)  # visible uniquement pour les vidéos
        else:
            self.btn_import.setText("Importer…")
            self.btn_load_video.setVisible(False)
