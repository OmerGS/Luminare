# engine/exporter.py
from pathlib import Path
from core.save_system.save_api import ProjectAPI
from core.project import Project

class Exporter:
    def __init__(self):
        try:
            from mvp_editor import main as render_project
            self._render = render_project
        except Exception:
            self._render = None

    def export_quick(self, src_path: str, duration_ms: int) -> str:
        """
        Export rapide depuis un fichier source (temporaire)
        """
        if not self._render:
            raise RuntimeError("mvp_editor introuvable.")
        out = Path("exports") / "output_gui.mp4"
        out.parent.mkdir(parents=True, exist_ok=True)

        seconds = max(1, int((duration_ms or 5000) / 1000))
        seconds = min(5, seconds)

        # On construit un projet temporaire
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

    def _export_project(self, proj: Project, output_path: Path) -> str:
        """
        Convertit un Project en dict et appelle le moteur mvp_editor
        """
        clips = [{"path": c["path"], "trim": c["trim"]} for c in proj.clips]

        # TODO : ajouter tes filtres/text_overlays si besoin
        project_dict = {
            "clips": clips,
            "resolution": proj.resolution,
            "filters": {"brightness": 0.0, "contrast":1.0, "saturation":1.0, "vignette":False},
            "text_overlays": [],
            "output": str(output_path),
            "fps": proj.fps,
            "audio_normalize": proj.audio_normalize
        }

        self._render(project_dict)
        return str(output_path)