# core/project.py
from dataclasses import dataclass, field
from typing import Optional, List, Tuple


@dataclass
class ImageOverlay:
    path: str
    # position et taille normalisées (0..1) dans le cadre vidéo
    x: float = 0.5
    y: float = 0.5
    w: float = 0.25      # largeur relative
    h: float = 0.25      # hauteur relative
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
    fontfile: Optional[str] = r"C:\Windows\Fonts\arial.ttf"  # adapte per-OS

@dataclass
class Filters:
    brightness: float = 0.0       # -1..+1 (on export on clamp à [-1,1])
    contrast: float = 1.0         # 0..3
    saturation: float = 1.0       # 0..3
    vignette: bool = False

@dataclass
class Clip:
    path: str
    trim: Tuple[float, float] = (0.0, 5.0)  # start_sec, duration_sec

@dataclass
class Project:
    resolution: Tuple[int, int] = (1920, 1080)
    fps: int = 30
    clips: List[Clip] = field(default_factory=list)
    text_overlays: List[TextOverlay] = field(default_factory=list)
    filters: Filters = field(default_factory=Filters)
    image_overlays: List[ImageOverlay] = field(default_factory=list)
