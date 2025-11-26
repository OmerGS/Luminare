from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any

@dataclass
class ImageOverlay:
    path: str
    x: float = 0.5
    y: float = 0.5
    w: float = 0.25 
    h: float = 0.25 
    start: float = 0.0
    end: float = 3.0
    opacity: float = 1.0

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
    in_s: float = 0.0  
    out_s: float = 0.0 
    duration_s: float = 0.0

    @property
    def effective_duration(self) -> float:
        if self.duration_s > 0:
            return self.duration_s
        if self.out_s > self.in_s:
            return self.out_s - self.in_s
        return 0.0


@dataclass
class Project:
    name: str = "Nouveau projet"
    version: str = "1.0.0"
    clips: List[Clip] = field(default_factory=list)
    text_overlays: List[TextOverlay] = field(default_factory=list)
    filters: Filters = field(default_factory=Filters)
    image_overlays: List[ImageOverlay] = field(default_factory=list)
    resolution: Tuple[int, int] = (1920, 1080)
    fps: float = 30.0
    imported_assets: List[Dict[str, Any]] = field(default_factory=list)
    output: str = "exports/output.mp4"
    audio_normalize: bool = True

    def total_duration_s(self) -> float:
        return sum(max(0.0, c.effective_duration) for c in self.clips)

    def to_dict(self) -> Dict[str, Any]:
        """Exporte le projet en format dictionnaire (utilise toujours le format Clip riche)."""
        return {
            "name": self.name,
            "clips": [
                {
                    "path": c.path,
                    "in_s": c.in_s,
                    "out_s": c.out_s,
                    "duration_s": c.duration_s,
                } for c in self.clips
            ],
            "imported_assets": self.imported_assets,
            "text_overlays": [vars(t) for t in self.text_overlays],
            "filters": vars(self.filters),
            "image_overlays": [vars(o) for o in self.image_overlays],
            "resolution": self.resolution,
            "fps": self.fps,
            "output": self.output,
            "audio_normalize": self.audio_normalize
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Project":
        """Importe un projet, gérant les anciens et nouveaux formats de clip."""
        proj = Project(
            name=data.get("name", "Nouveau projet"),
            resolution=tuple(data.get("resolution", (1920,1080))),
            fps=data.get("fps", 30.0),
            output=data.get("output", "exports/output.mp4"),
            audio_normalize=data.get("audio_normalize", True)
        )
        proj.imported_assets = data.get("imported_assets", [])
        proj.text_overlays = [TextOverlay(**t) for t in data.get("text_overlays", [])]
        
        proj.image_overlays = [ImageOverlay(**o) for o in data.get("image_overlays", [])]

        filt = data.get("filters", {})
        proj.filters = Filters(**filt) if filt else Filters()

        imported_clips = data.get("clips", [])
        proj.clips = []
        for clip_data in imported_clips:
            proj.clips.append(Clip(**clip_data))

        return proj