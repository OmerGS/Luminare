from typing import List, Dict, Any, Tuple

class Project:
    def __init__(
        self,
        name: str = "Nouveau projet",
        resolution: Tuple[int,int] = (1920,1080),
        fps: float = 30.0,
        output: str = "exports/output.mp4",
        audio_normalize: bool = True
    ):
        self.name: str = name
        self._resolution: Tuple[int,int] = resolution
        self._fps: float = fps
        self.clips: List[Dict[str, Any]] = []
        self.output: str = output
        self.audio_normalize: bool = audio_normalize

    # ---------- Getters / Setters ----------
    @property
    def resolution(self) -> Tuple[int,int]:
        return self._resolution

    @resolution.setter
    def resolution(self, value: Tuple[int,int]):
        if not isinstance(value, (tuple,list)) or len(value) != 2:
            raise ValueError("Resolution doit être un tuple (largeur, hauteur)")
        self._resolution = tuple(value)

    @property
    def fps(self) -> float:
        return self._fps

    @fps.setter
    def fps(self, value: float):
        if not isinstance(value, (int,float)) or value <= 0:
            raise ValueError("FPS doit être un nombre positif")
        self._fps = float(value)

    # ---------- Gestion des clips ----------
    def add_clip(self, clip: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ajouter un clip simple:
        clip: {"path": str, "trim": (start:float, end:float)}
        """
        self.clips.append(clip)
        return clip

    # ---------- Export / Import dict ----------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "clips": self.clips,
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
        proj.clips = data.get("clips", [])
        return proj


# ---------- Petit test ----------
if __name__ == "__main__":
    proj = Project("Projet Test", resolution=(1280,720), fps=24)
    proj.add_clip({"path": "assets/video.mp4", "trim": (0,5)})
    print(proj.to_dict())