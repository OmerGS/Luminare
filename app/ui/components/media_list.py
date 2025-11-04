import os
import json
from PySide6.QtCore import Qt, QSize, QMimeData, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QDrag
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView

from app.core.save_system.save_api import ProjectAPI
from app.custom_types.ImportTypes import ImportTypes
from core.store import Store

MIME_MEDIA_ASSET = "application/x-luminare-asset-media" 

class MediaListWidget(QListWidget):

    FILE_PATH_ROLE = Qt.UserRole + 1 

    def __init__(self, store: Store, mime_type_for_drag: str | None = MIME_MEDIA_ASSET, parent=None):
        super().__init__(parent)
        self.mime_type_for_drag = mime_type_for_drag
        self.store = store
        
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(QSize(96, 96)) 
        self.setResizeMode(QListWidget.Adjust)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionMode(QListWidget.SingleSelection)

    def add_media_item(self, file_path: str):
        """
        Ajoute un média à la liste UI et enregistre l'import dans le fichier projet.
        """
        import os
        
        ext = os.path.splitext(file_path)[1].lower()
        name = os.path.basename(file_path)
        
        type_asset = ImportTypes.OTHER
        icon = None
        
        if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
            pixmap = QPixmap(file_path).scaled(
                self.iconSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            icon = QIcon(pixmap)
            type_asset = ImportTypes.IMAGE
            
        elif ext in [".mp4", ".avi", ".mov", ".mkv"]:
            icon = QIcon.fromTheme("video-x-generic") or QIcon("assets/icons/video.png")
            type_asset = ImportTypes.VIDEO
            
        elif ext in [".mp3", ".wav", ".ogg"]:
            icon = QIcon.fromTheme("audio-x-generic") or QIcon("assets/icons/audio.png")
            type_asset = ImportTypes.AUDIO
            
        elif ext in [".txt"]:
            icon = QIcon.fromTheme("text-x-generic") or QIcon("assets/icons/text.png")
            type_asset = ImportTypes.TEXT
            
        else:
            icon = QIcon.fromTheme("unknown") or QIcon("assets/icons/file.png")
            type_asset = ImportTypes.OTHER

        item = QListWidgetItem(icon, name)
        item.setData(self.FILE_PATH_ROLE, file_path)
        self.addItem(item)
        
        project_instance = self.store.project() 
        
        project_base_name = project_instance.name.strip()
        safe_name = "".join(c for c in project_base_name if c.isalnum() or c in (' ', '.', '_', '-'))
        
        project_filename = f"{safe_name}.lmprj" 
        
        try:
            ProjectAPI.add_import(
                filename=project_filename,  
                asset_name=name,            
                import_path=file_path,      
                type=type_asset             
            )
        except Exception as e:
            print(f"Erreur lors de l'enregistrement de l'import dans le projet : {e}")       

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