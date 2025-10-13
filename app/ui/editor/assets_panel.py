# app/ui/components/assets_panel.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QTabWidget, QLabel, QSizePolicy, QStyle, QApplication
)
import os

from ui.components.media_list import MIME_IMAGE_ASSET, _MediaList

class AssetsPanel(QWidget):
    """Panneau unique : onglets + import + bouton 'ajouter au curseur'."""
    addImageRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        # --- Fonctions utilitaires pour les icônes ---
        def _get_icon(standard_icon):
            return QApplication.style().standardIcon(standard_icon)

        # Onglets
        self.tab_audio  = _MediaList(None)
        self.tab_images = _MediaList(MIME_IMAGE_ASSET)
        self.tab_text   = _MediaList(None)

        # =====================================================================
        # MODIFICATION : REMPLACEMENT DES EMOJIS PAR DES ICÔNES QStyle
        # =====================================================================
        
        # Audio (Utilise une icône de haut-parleur/volume)
        icon_audio = _get_icon(QStyle.SP_MediaVolume) # MODIFIÉ
        self.tabs.addTab(self.tab_audio, icon_audio, "Audio")
        
        # Images (Utilise une icône d'image/média)
        icon_images = _get_icon(QStyle.SP_FileIcon) # MODIFIÉ (SP_FileIcon est souvent utilisé pour les fichiers génériques)
        self.tabs.addTab(self.tab_images, icon_images, "Images")
        
        # Texte (Utilise une icône de document/texte)
        icon_text = _get_icon(QStyle.SP_FileDialogDetailedView) # MODIFIÉ (Icône de liste/détail, souvent utilisé pour du contenu textuel ou une liste)
        self.tabs.addTab(self.tab_text, icon_text, "Texte")
        
        # --- Barre d’actions sous la liste (Boutons avec icônes - déjà corrigé) ---
        btn_row1 = QHBoxLayout()
        self.btn_import = QPushButton(_get_icon(QStyle.SP_DialogOpenButton), " Importer…")
        btn_row1.addWidget(self.btn_import)
        root.addLayout(btn_row1)

        # Aperçu simple sous le bouton
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(80)
        self.preview.setStyleSheet("QLabel { background: #eee; border: 1px solid #ccc; }")
        root.addWidget(self.preview, 0)

        btn_row2 = QHBoxLayout()
        self.btn_add = QPushButton(_get_icon(QStyle.SP_MediaSeekForward), " Ajouter à la timeline")
        btn_row2.addWidget(self.btn_add)
        root.addLayout(btn_row2)

        # Connexions
        self.btn_import.clicked.connect(self._import_images)
        self.btn_add.clicked.connect(self._emit_selected)
        self.tab_images.currentItemChanged.connect(self._update_preview)

    # --- actions (inchangées) ---
    def _import_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Choisir des images", "",
            "Images (*.png *.jpg *.jpeg *.webp *.gif)"
        )
        for f in files:
            self.tab_images.add_path(f)
        if files:
            self.tabs.setCurrentWidget(self.tab_images)

    def _emit_selected(self):
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