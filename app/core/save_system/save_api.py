from typing import Callable
import os
from app.types import ImportTypes
from core.save_system.serializers import LMPRJChunkedSerializer
from core import project as Project

class ProjectAPI:
    @staticmethod
    def list_projects() -> list[str]:
        return LMPRJChunkedSerializer.list_projects() if hasattr(LMPRJChunkedSerializer, "list_projects") else [
            f.name for f in os.scandir(LMPRJChunkedSerializer.get_save_dir())
            if f.is_file() and f.name.endswith(".lmprj")
        ]

    @staticmethod
    def load(filename: str) -> Project:
        return LMPRJChunkedSerializer.load(filename)

    @staticmethod
    def save(project: Project, filename: str) -> str:
        return LMPRJChunkedSerializer.save(project, filename)

    @staticmethod
    def update_project(filename: str, callback: Callable[[Project], None]) -> str:
        """
        Charge le projet, applique callback pour modifier seulement certaines parties,
        puis sauvegarde.
        """
        proj = LMPRJChunkedSerializer.load(filename)
        callback(proj)
        return LMPRJChunkedSerializer.save(proj, filename)
    
    @staticmethod
    def get_save_count() -> int:
        """Retourne le nombre de fichiers .lmprj enregistrés dans le dossier de sauvegarde."""
        save_dir = LMPRJChunkedSerializer.get_save_dir()
        if not os.path.exists(save_dir):
            return 0
        files = [f for f in os.listdir(save_dir) if f.endswith(LMPRJChunkedSerializer.EXTENSION)]
        return len(files)
    
    @staticmethod
    def get_clip_count(filename: str) -> int:
        """
        Retourne le nombre de clips dans un projet spécifique (.lmprj).
        """
        proj = LMPRJChunkedSerializer.load(filename)
        return len(proj.clips)
    
    @staticmethod
    def add_import(filename: str, import_path: str, type: ImportTypes) -> str:
        """Ajoute un import au projet spécifié (en modifiant le fichier .lmprj)."""
        
        def update_callback(project):
            new_asset = {
                "path": import_path,
                "type": type.value
            }
            
            if not any(a["path"] == import_path for a in project.imported_assets):
                project.imported_assets.append(new_asset)
                print(f"Asset ajouté au fichier {filename}: {import_path}")
            else:
                print(f"Asset déjà présent dans le fichier {filename}: {import_path}")

        return ProjectAPI.update_project(filename, update_callback)

    @staticmethod
    def remove_import(filename: str, import_path: str) -> str:
        """Retire un import du projet spécifié (en modifiant le fichier .lmprj)."""
        
        def update_callback(project):
            initial_count = len(project.imported_assets)
            
            project.imported_assets = [
                a for a in project.imported_assets if a["path"] != import_path
            ]
            
            if len(project.imported_assets) < initial_count:
                print(f"Asset retiré du fichier {filename}: {import_path}")
            else:
                print(f"Asset non trouvé dans le fichier {filename}: {import_path}")

        return ProjectAPI.update_project(filename, update_callback)
