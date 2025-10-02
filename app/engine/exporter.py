from pathlib import Path

class Exporter:
    """
    Pont vers la pipeline d'export.
    Pour l’instant, on réutilise mvp_editor.main(project_dict).
    Tu pourras remplacer cette classe par ta vraie pipeline FFmpeg.
    """
    def __init__(self):
        try:
            from mvp_editor import main as render_project
            self._render = render_project
        except Exception:
            self._render = None

    def export_quick(self, src_path: str, duration_ms: int) -> str:
        if not self._render:
            raise RuntimeError("mvp_editor introuvable (engine/exporter.py).")
        out = Path("exports") / "output_gui.mp4"
        out.parent.mkdir(parents=True, exist_ok=True)

        seconds = max(1, int((duration_ms or 5000) / 1000))
        seconds = min(5, seconds)  # petit export

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
