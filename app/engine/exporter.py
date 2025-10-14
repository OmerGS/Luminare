from pathlib import Path
from core.save_system.save_api import ProjectAPI
from core.project import Project
from typing import Callable, Any, Dict
from mvp_editor import main as render_project

class Exporter:
    def __init__(self):
        try:
            self._render: Callable[[Dict[str, Any]], None] = render_project 
        except Exception:
            self._render = None

    def _create_export_dict(self, proj: Project, out_path: Path) -> dict:
        """Crée le dictionnaire de configuration pour le moteur de rendu."""
        
        clips_export = [{"path": c.path, "trim": c.trim} for c in proj.clips]

        return {
            "clips": clips_export,
            "resolution": proj.resolution,
            "filters": vars(proj.filters),
            "text_overlays": [vars(ov) for ov in proj.text_overlays], 
            "output": str(out_path),
            "fps": proj.fps,
            "audio_normalize": proj.audio_normalize
        }

    def _export_project(self, proj: Project, out_path: Path) -> str:
        """Méthode interne pour effectuer l'exportation et vérifier le moteur."""
        if not self._render:
            raise RuntimeError("mvp_editor introuvable.")
            
        project_dict = self._create_export_dict(proj, out_path)
        
        self._render(project_dict)
        return str(out_path)

    # --- Méthodes Publiques ---

    def export_quick(self, src_path: str, duration_ms: int) -> str:
        """
        Export rapide depuis un fichier source
        """
        if not self._render:
            raise RuntimeError("mvp_editor introuvable.")
        out = Path("exports") / "output_gui.mp4"
        out.parent.mkdir(parents=True, exist_ok=True)

        seconds = max(1, int((duration_ms or 5000) / 1000))
        seconds = min(5, seconds)

        proj = Project(name="Export Quick", resolution=(1920,1080), fps=30)
        proj.add_clip({"path": src_path, "trim": (0, seconds)})

        return self._export_project(proj, out)
        
    def export_from_file(self, filename: str, fallback_src: str = None) -> str:
        """
        Export depuis un fichier .lmprj existant
        """
        if not self._render:
            raise RuntimeError("mvp_editor introuvable.")

        try:
            proj = ProjectAPI.load(filename)
        except FileNotFoundError:
            if fallback_src:
                proj = Project(name="Export Fallback", resolution=(1920,1080), fps=30)
                proj.add_clip({"path": fallback_src, "trim": (0,5)})
            else:
                raise

        out = Path("exports") / "output_gui.mp4"
        out.parent.mkdir(parents=True, exist_ok=True)
        return self._export_project(proj, out)
        
    def export_from_project(self, proj: Project, fallback_src: str) -> str:
        """
        Exportation directe d'un objet Project en mémoire.
        """
        out_path = Path(proj.output) if proj.clips else Path("exports") / "output_gui.mp4"
        if not proj.clips and fallback_src:
            out_path = Path(fallback_src) # Utilise le fallback si le projet est vide
        
        out_path.parent.mkdir(parents=True, exist_ok=True)

        return self._export_project(proj, out_path)