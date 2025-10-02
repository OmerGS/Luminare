# engine/exporter.py
from pathlib import Path
from core.project import Project

class Exporter:
    def __init__(self):
        try:
            from mvp_editor import main as render_project
            self._render = render_project
        except Exception:
            self._render = None

    def export_quick(self, src_path: str, duration_ms: int) -> str:
        if not self._render:
            raise RuntimeError("mvp_editor introuvable.")
        out = Path("exports") / "output_gui.mp4"
        out.parent.mkdir(parents=True, exist_ok=True)
        seconds = max(1, int((duration_ms or 5000) / 1000))
        seconds = min(5, seconds)
        project = {
            "clips": [{"path": src_path, "trim": (0, seconds)}],
            "resolution": (1920, 1080),
            "filters": {"brightness": 0.05, "contrast": 1.10, "saturation": 1.10, "vignette": True},
            "text_overlays": [{
                "text": "Export GUI",
                "x": "(w-text_w)/2", "y": "h*0.1",
                "fontsize": 48, "fontcolor": "white",
                "box": True, "boxcolor": "black@0.5", "boxborderw": 10,
                "start": 0.5, "end": 4.5,
                "fontfile": r"C:\Windows\Fonts\arial.ttf"
            }],
            "output": str(out),
            "fps": 30,
            "audio_normalize": True
        }
        self._render(project)
        return str(out)

    def export_from_project(self, proj: Project, fallback_src: str) -> str:
        if not self._render:
            raise RuntimeError("mvp_editor introuvable.")
        out = Path("exports") / "output_gui.mp4"
        out.parent.mkdir(parents=True, exist_ok=True)

        clips = []
        if proj.clips:
            for c in proj.clips:
                clips.append({"path": c.path, "trim": (c.trim[0], c.trim[1])})
        else:
            clips = [{"path": fallback_src, "trim": (0, 5)}]

        filters = {
            "brightness": max(-1.0, min(1.0, proj.filters.brightness)),
            "contrast":   max(0.0, min(3.0, proj.filters.contrast)),
            "saturation": max(0.0, min(3.0, proj.filters.saturation)),
            "vignette": bool(proj.filters.vignette),
        }

        text_overlays = [ov.__dict__ for ov in proj.text_overlays]

        project_dict = {
            "clips": clips,
            "resolution": proj.resolution,
            "filters": filters,
            "text_overlays": text_overlays,
            "output": str(out),
            "fps": proj.fps,
            "audio_normalize": True
        }
        self._render(project_dict)
        return str(out)
