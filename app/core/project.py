from dataclasses import dataclass, field

@dataclass
class Clip:
    path: str
    start: float = 0.0   # position sur la timeline (s)
    inpoint: float = 0.0
    outpoint: float = 0.0

@dataclass
class Project:
    fps: int = 30
    width: int = 1920
    height: int = 1080
    clips: list[Clip] = field(default_factory=list)
