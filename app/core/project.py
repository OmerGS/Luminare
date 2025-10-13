from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any

@dataclass
class TextOverlay:
    text: str = "Titre"
    x: str = "(w-text_w)/2"
    y: str = "h*0.1"
    fontsize: int = 48
    fontcolor: str = "white"
    box: bool = True
    boxcolor: str = "black@0.5"
    boxborderw: int = 10
    start: float = 0.5
    end: float = 4.5
    fontfile: Optional[str] = r"C:\Windows\Fonts\arial.ttf"

@dataclass
class Filters:
    brightness: float = 0.0
    contrast: float = 1.0
    saturation: float = 1.0
    vignette: bool = False

@dataclass
class Clip:
    path: str
    trim: Tuple[float, float] = (0.0, 5.0)

@dataclass
class Project:
    name: str = "Nouveau projet"
    version: str = "1.0.0"
    resolution: Tuple[int, int] = (1920, 1080)
    fps: float = 30.0
    clips: List[Clip] = field(default_factory=list)
    imported_assets: List[Dict[str, Any]] = field(default_factory=list)
    text_overlays: List[TextOverlay] = field(default_factory=list)
    filters: Filters = field(default_factory=Filters)
    output: str = "exports/output.mp4"
    audio_normalize: bool = True

    # ----- dict export/import -----
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "clips": [ {"path": c.path, "trim": c.trim} for c in self.clips ],
            "imported_assets": self.imported_assets,
            "text_overlays": [vars(t) for t in self.text_overlays],
            "filters": vars(self.filters),
            "resolution": self.resolution,
            "fps": self.fps,
            "output": self.output,
            "audio_normalize": self.audio_normalize
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Project":
        proj = Project(
            name=data.get("name", "Nouveau projet"),
            resolution=tuple(data.get("resolution", (1920,1080))),
            fps=data.get("fps", 30.0),
            output=data.get("output", "exports/output.mp4"),
            audio_normalize=data.get("audio_normalize", True)
        )
        proj.imported_assets = data.get("imported_assets", [])
        proj.clips = [Clip(**c) for c in data.get("clips", [])]
        proj.text_overlays = [TextOverlay(**t) for t in data.get("text_overlays", [])]
        filt = data.get("filters", {})
        proj.filters = Filters(**filt) if filt else Filters()
        return proj