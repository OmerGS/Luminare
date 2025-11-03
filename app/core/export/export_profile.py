from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class ExportProfile:
    """Définit les paramètres d'encodage pour une exportation."""
    name: str
    description: str
    
    # Paramètres FFmpeg
    vcodec: str = 'libx264'
    preset: str = 'medium'
    crf: int = 18
    pix_fmt: str = 'yuv420p'
    
    acodec: str = 'aac'
    audio_bitrate: str = '192k'
    
    movflags: str = '+faststart'
    
    extra_output_args: Dict[str, Any] = field(default_factory=dict)

    def to_ffmpeg_args(self) -> Dict[str, Any]:
        """Convertit le profil en dictionnaire pour ffmpeg.output()."""
        args = {
            "vcodec": self.vcodec,
            "preset": self.preset,
            "crf": self.crf,
            "pix_fmt": self.pix_fmt,
            "acodec": self.acodec,
            "audio_bitrate": self.audio_bitrate,
            "movflags": self.movflags,
        }
        args.update(self.extra_output_args)
        
        if not self.movflags:
            del args["movflags"]
            
        return args

DEFAULT_PROFILES = {
    "h264_medium": ExportProfile(
        name="H.264 Medium (MP4)",
        description="Bon équilibre qualité/taille. Idéal pour le web."
    ),
    "h264_fast_draft": ExportProfile(
        name="H.264 Brouillon (MP4)",
        description="Rendu très rapide, qualité réduite, pour aperçu.",
        preset="ultrafast",
        crf=26
    ),
}