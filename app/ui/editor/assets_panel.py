from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QTabWidget, QLabel, QSizePolicy, QStyle, QApplication
)
import os
from core.store import Store   
from ui.components.media_list import MIME_MEDIA_ASSET, MediaListWidget 


class AssetsPanel(QWidget):
    addImageRequested = Signal(str)
    addVideoRequested = Signal(str) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.store = Store()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        def _get_icon(standard_icon):
            return QApplication.style().standardIcon(standard_icon)

        self.tab_audio  = MediaListWidget(store=self.store, mime_type_for_drag=MIME_MEDIA_ASSET)
        self.tab_images = MediaListWidget(store=self.store, mime_type_for_drag=MIME_MEDIA_ASSET)
        self.tab_text   = MediaListWidget(store=self.store, mime_type_for_drag=MIME_MEDIA_ASSET)
        self.tab_video  = MediaListWidget(store=self.store, mime_type_for_drag=MIME_MEDIA_ASSET)

        self.tabs.addTab(self.tab_video, _get_icon(QStyle.SP_MediaPlay), "Vidéo")
        self.tabs.addTab(self.tab_audio, _get_icon(QStyle.SP_MediaVolume), "Audio")
        self.tabs.addTab(self.tab_images, _get_icon(QStyle.SP_FileIcon), "Images")
        self.tabs.addTab(self.tab_text, _get_icon(QStyle.SP_FileDialogContentsView), "Texte")

        btn_row1 = QHBoxLayout()
        self.btn_import = QPushButton(_get_icon(QStyle.SP_DialogOpenButton), " Importer…")
        btn_row1.addWidget(self.btn_import)
        root.addLayout(btn_row1)

        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(80)
        self.preview.setStyleSheet("QLabel { background: #eee; border: 1px solid #ccc; }")
        root.addWidget(self.preview, 0)

        btn_row2 = QHBoxLayout()
        self.btn_add = QPushButton(_get_icon(QStyle.SP_MediaSeekForward), " Ajouter à la timeline")
        btn_row2.addWidget(self.btn_add)
        root.addLayout(btn_row2)
        

        self.btn_import.clicked.connect(self._handle_import_click)
        self.btn_add.clicked.connect(self._emit_selected_to_timeline)
        
        self.tabs.currentChanged.connect(self._update_add_button_visibility)
        self.tabs.currentChanged.connect(self._update_preview) 
        self.tab_images.currentItemChanged.connect(self._update_preview)
        self.tab_video.currentItemChanged.connect(self._update_preview)
        self._update_add_button_visibility(self.tabs.currentIndex())

    def _handle_import_click(self):
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
            self.tab_video.add_media_item(f) 
        if files:
            self.tabs.setCurrentWidget(self.tab_video)

    def _import_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Choisir des images", "",
            "Images (*.png *.jpg *.jpeg *.webp *.gif);;Tous les fichiers (*.*)"
        )
        for f in files:
            self.tab_images.add_media_item(f)
        if files:
            self.tabs.setCurrentWidget(self.tab_images)

    def _import_audio(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Choisir des fichiers audio", "",
            "Audio (*.mp3 *.wav *.ogg);;Tous les fichiers (*.*)"
        )
        for f in files:
            self.tab_audio.add_media_item(f)
        if files:
            self.tabs.setCurrentWidget(self.tab_audio)

    def _update_add_button_visibility(self, index):
        current_widget = self.tabs.widget(index)

        is_addable = current_widget in (self.tab_images, self.tab_video)
        
        self.btn_add.setVisible(is_addable)
        
        is_previewable = current_widget is self.tab_images
        self.preview.setVisible(is_previewable)


    def _emit_selected_to_timeline(self):
        current_tab = self.tabs.currentWidget()
        path = current_tab.current_path() if hasattr(current_tab, 'current_path') else None
        
        if not path:
            return

        if current_tab is self.tab_images:
            self.addImageRequested.emit(path)
        elif current_tab is self.tab_video:
            self.addVideoRequested.emit(path)

    
    def _update_preview(self, *_):
        current_tab = self.tabs.currentWidget()
        
        if current_tab is not self.tab_images:
            self.preview.clear()
            return
            
        path = current_tab.current_path() if hasattr(current_tab, 'current_path') else None

        if path and os.path.exists(path):
            if os.path.splitext(path)[1].lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
                self.preview.setPixmap(QPixmap(path).scaledToHeight(76, Qt.SmoothTransformation))
                return

        self.preview.setText("")