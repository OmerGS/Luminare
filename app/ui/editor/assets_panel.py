from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QTabWidget, QLabel, QSizePolicy, QStyle, QApplication
)
import os
from core.store import Store   
# NOTE: Je suppose que MediaListWidget est bien importé de ui.components.media_list 
# et supporte les méthodes add_media_item() et current_path().
from ui.components.media_list import MIME_MEDIA_ASSET, MediaListWidget 


class AssetsPanel(QWidget):
    """Panneau : import, aperçu, ajout ou chargement de médias."""
    addImageRequested = Signal(str)
    # NOUVEAU: Signal pour demander l'ajout d'une vidéo à la timeline
    addVideoRequested = Signal(str) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.store = Store() # Initialisation du Store

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        def _get_icon(standard_icon):
            return QApplication.style().standardIcon(standard_icon)

        # --- Onglets basés sur MediaListWidget ---
        # Tous les onglets ont besoin du mime_type pour le Drag & Drop vers la timeline
        # MIME_MEDIA_ASSET est utilisé pour indiquer que c'est un asset de base
        self.tab_audio  = MediaListWidget(store=self.store, mime_type_for_drag=MIME_MEDIA_ASSET)
        self.tab_images = MediaListWidget(store=self.store, mime_type_for_drag=MIME_MEDIA_ASSET)
        self.tab_text   = MediaListWidget(store=self.store, mime_type_for_drag=MIME_MEDIA_ASSET)
        self.tab_video  = MediaListWidget(store=self.store, mime_type_for_drag=MIME_MEDIA_ASSET)

        # Ajout des onglets avec icônes
        self.tabs.addTab(self.tab_video, _get_icon(QStyle.SP_MediaPlay), "Vidéo")
        self.tabs.addTab(self.tab_audio, _get_icon(QStyle.SP_MediaVolume), "Audio")
        self.tabs.addTab(self.tab_images, _get_icon(QStyle.SP_FileIcon), "Images")
        self.tabs.addTab(self.tab_text, _get_icon(QStyle.SP_FileDialogContentsView), "Texte")

        # --- Bouton d’import ---
        btn_row1 = QHBoxLayout()
        self.btn_import = QPushButton(_get_icon(QStyle.SP_DialogOpenButton), " Importer…")
        btn_row1.addWidget(self.btn_import)
        root.addLayout(btn_row1)

        # --- Aperçu (Preview) ---
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(80)
        self.preview.setStyleSheet("QLabel { background: #eee; border: 1px solid #ccc; }")
        root.addWidget(self.preview, 0)

        # --- Bouton d'ajout à la timeline ---
        btn_row2 = QHBoxLayout()
        # Le même bouton servira pour l'ajout d'images ET de vidéos
        self.btn_add = QPushButton(_get_icon(QStyle.SP_MediaSeekForward), " Ajouter à la timeline")
        btn_row2.addWidget(self.btn_add)
        root.addLayout(btn_row2)
        

        # --- Connexions ---
        self.btn_import.clicked.connect(self._handle_import_click)
        self.btn_add.clicked.connect(self._emit_selected_to_timeline)
        
        # Mise à jour de l'aperçu et de la visibilité lorsque l'élément sélectionné ou l'onglet change
        self.tabs.currentChanged.connect(self._update_add_button_visibility)
        self.tabs.currentChanged.connect(self._update_preview) 
        self.tab_images.currentItemChanged.connect(self._update_preview)
        self.tab_video.currentItemChanged.connect(self._update_preview)
        # La logique de _update_add_button_visibility contient la logique de preview pour l'image
        self._update_add_button_visibility(self.tabs.currentIndex())


    # ------------------------
    # Logique d'Importation
    # ------------------------

    def _handle_import_click(self):
        """Déclenche la méthode d'importation appropriée selon l'onglet actif."""
        current_tab = self.tabs.currentWidget()
        
        if current_tab is self.tab_video:
            self._import_video()
        elif current_tab is self.tab_images:
            self._import_images()
        elif current_tab is self.tab_audio:
            self._import_audio()

    def _import_video(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Choisir des vidéos", "",
            "Vidéos (*.mp4 *.mov *.mkv *.avi);;Tous les fichiers (*.*)"
        )
        for f in files:
            # Utilise add_media_item() de MediaListWidget
            self.tab_video.add_media_item(f) 
        if files:
            self.tabs.setCurrentWidget(self.tab_video)

    def _import_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Choisir des images", "",
            "Images (*.png *.jpg *.jpeg *.webp *.gif);;Tous les fichiers (*.*)"
        )
        for f in files:
            # Utilise add_media_item() de MediaListWidget
            self.tab_images.add_media_item(f)
        if files:
            self.tabs.setCurrentWidget(self.tab_images)

    def _import_audio(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Choisir des fichiers audio", "",
            "Audio (*.mp3 *.wav *.ogg);;Tous les fichiers (*.*)"
        )
        for f in files:
            # Utilise add_media_item() de MediaListWidget
            self.tab_audio.add_media_item(f)
        if files:
            self.tabs.setCurrentWidget(self.tab_audio)


    # ------------------------
    # Logique d'Aperçu et d'Ajout
    # ------------------------

    def _update_add_button_visibility(self, index):
        """Met à jour la visibilité du bouton 'Ajouter à la timeline'."""
        current_widget = self.tabs.widget(index)

        # On permet l'ajout à la timeline pour les images et les vidéos
        is_addable = current_widget in (self.tab_images, self.tab_video)
        
        self.btn_add.setVisible(is_addable)
        
        # On affiche la preview uniquement si c'est un onglet d'asset supportant l'aperçu
        is_previewable = current_widget is self.tab_images
        self.preview.setVisible(is_previewable)


    def _emit_selected_to_timeline(self):
        """Émet le chemin de l'asset sélectionné pour l'ajout à la timeline."""
        current_tab = self.tabs.currentWidget()
        path = current_tab.current_path() if hasattr(current_tab, 'current_path') else None
        
        if not path:
            return

        # Logique fusionnée : envoie soit une image, soit une vidéo
        if current_tab is self.tab_images:
            self.addImageRequested.emit(path)
        elif current_tab is self.tab_video:
            self.addVideoRequested.emit(path)

    
    def _update_preview(self, *_):
        """Affiche la miniature de l'image ou efface l'aperçu."""
        current_tab = self.tabs.currentWidget()
        
        # On n'affiche la preview que pour les images
        if current_tab is not self.tab_images:
            self.preview.clear()
            return
            
        path = current_tab.current_path() if hasattr(current_tab, 'current_path') else None

        if path and os.path.exists(path):
            # Vérification simple du suffixe pour les images (similaire à la seconde version)
            if os.path.splitext(path)[1].lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
                self.preview.setPixmap(QPixmap(path).scaledToHeight(76, Qt.SmoothTransformation))
                return

        # Si pas d'image ou si la path n'est pas un fichier image, on efface
        self.preview.setText("")