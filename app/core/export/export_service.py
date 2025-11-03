from pathlib import Path
from core.save_system.save_api import ProjectAPI
from core.project import Project
from typing import Optional

from core.export.engine_interface import IRenderEngine, RenderError
from core.export.export_profile import ExportProfile, DEFAULT_PROFILES

class ExportService:
    def __init__(self, engine: IRenderEngine):
        """
        Initialise le service avec un moteur de rendu spécifique (Injection).
        """
        if not isinstance(engine, IRenderEngine):
            raise TypeError("L'objet 'engine' doit implémenter IRenderEngine.")
        self._engine = engine

    def _get_project_or_fallback(self, proj: Project, fallback_src: Optional[str]) -> Project:
        """Crée un projet de fallback si le projet principal est vide."""
        if not proj.clips and fallback_src:
            fallback_proj = Project(
                name=f"{proj.name} (Fallback)",
                resolution=proj.resolution,
                fps=proj.fps
            )
            fallback_proj.add_clip({"path": fallback_src, "trim": (0, 5)})
            return fallback_proj
        
        if not proj.clips:
            raise RenderError("Le projet est vide et aucun 'fallback_src' n'a été fourni.")
            
        return proj

    def export_project(self, 
                         proj: Project, 
                         out_path: Path,
                         profile: Optional[ExportProfile] = None,
                         fallback_src: str = None) -> str:
        """
        Exporte un objet Project en mémoire.
        C'est la méthode principale.
        """
        active_profile = profile or DEFAULT_PROFILES["h264_medium"]
        
        try:
            effective_proj = self._get_project_or_fallback(proj, fallback_src)
            
            print(f"Lancement de l'export vers {out_path} avec profil '{active_profile.name}'...")
            
            self._engine.render(effective_proj, out_path, active_profile)
            
            print(f"Exportation terminée avec succès : {out_path}")
            return str(out_path)

        except RenderError as e:
            print(f"ERREUR D'EXPORTATION : {e}")
            raise
        except Exception as e:
            print(f"ERREUR INATTENDUE (ExportService) : {e}")
            raise RenderError(f"Erreur inattendue dans le service: {e}")


    def export_from_file(self, 
                         filename: str, 
                         out_path: Path,
                         profile: Optional[ExportProfile] = None,
                         fallback_src: str = None) -> str:
        """Charge un .lmprj et l'exporte."""
        
        try:
            proj = ProjectAPI.load(filename)
        except FileNotFoundError:
            if fallback_src:
                proj = Project(name="Export Fallback", resolution=(1920,1080), fps=30)
                proj.add_clip({"path": fallback_src, "trim": (0,5)})
            else:
                raise
        
        return self.export_project(proj, out_path, profile, fallback_src=None)
        
    def export_quick(self, 
                     src_path: str, 
                     duration_ms: int,
                     out_path: Path,
                     profile: Optional[ExportProfile] = None) -> str:
        
        active_profile = profile or DEFAULT_PROFILES["h264_fast_draft"]
        
        seconds = min(5, max(1, int((duration_ms or 5000) / 1000)))
        proj = Project(name="Export Quick", resolution=(1920, 1080), fps=30)
        proj.add_clip({"path": src_path, "trim": (0, seconds)})
        
        return self.export_project(proj, out_path, active_profile, fallback_src=None)