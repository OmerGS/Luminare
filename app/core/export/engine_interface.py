import abc
from pathlib import Path
from core.project import Project
from core.export.export_profile import ExportProfile

class RenderError(Exception):
    """Exception personnalisée pour les échecs de rendu."""
    pass

class IRenderEngine(abc.ABC):
    """
    Interface abstraite (le contrat) pour un moteur de rendu vidéo.
    """
    
    @abc.abstractmethod
    def render(self, 
               project: Project, 
               output_path: Path, 
               profile: ExportProfile) -> None:
        """
        Effectue le rendu d'un objet Project vers un fichier de sortie
        en utilisant un profil d'exportation spécifique.
        """
        pass