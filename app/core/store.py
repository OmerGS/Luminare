# app/core/store.py
from typing import Optional
from PySide6.QtCore import QObject, Signal
from core.project import Project, TextOverlay, Filters, ImageOverlay, VideoClip

class Store(QObject):
    changed = Signal()
    overlayChanged = Signal()
    clipsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project = Project()

    def project(self) -> Project:
        return self._project

    # --- CLIPS -------------------------------------------------
    def set_clip(self, path: str, duration_s: float):
        """Remplace l’unique clip par un VideoClip 'nouveau modèle'."""
        dur = max(0.1, float(duration_s))
        self._project.clips = [VideoClip(path=path, in_s=0.0, out_s=dur, duration_s=dur)]
        self.clipsChanged.emit()
        self.changed.emit()

    def add_video_clip(self, path: str, in_s: float = 0.0, out_s: float = 0.0, duration: float = 0.0):
        dur = duration if duration > 0 else max(0.0, out_s - in_s)
        clip = VideoClip(path=path, in_s=in_s, out_s=(in_s + dur), duration_s=dur)
        self._project.clips.append(clip)
        self.clipsChanged.emit()
        self.changed.emit()
        return clip

    def remove_clip_at(self, idx: int):
        if 0 <= idx < len(self._project.clips):
            del self._project.clips[idx]
            self.clipsChanged.emit()
            self.changed.emit()

    def split_clip_at(self, idx: int, local_s: float):
        if not (0 <= idx < len(self._project.clips)):
            return None
        c = self._project.clips[idx]
        start = float(getattr(c, "in_s", 0.0))
        end   = float(getattr(c, "out_s", start))
        if end <= start:
            return None
        split_s = max(start, min(start + float(local_s), end))
        if split_s <= start or split_s >= end:
            return None

        left  = VideoClip(path=c.path, in_s=start, out_s=split_s, duration_s=(split_s - start))
        right = VideoClip(path=c.path, in_s=split_s, out_s=end,   duration_s=(end - split_s))
        self._project.clips[idx] = left
        self._project.clips.insert(idx + 1, right)
        self.clipsChanged.emit()
        self.changed.emit()
        return idx, idx + 1

    def move_clip(self, old_idx: int, new_idx: int):
        if 0 <= old_idx < len(self._project.clips):
            clip = self._project.clips.pop(old_idx)
            new_idx = max(0, min(new_idx, len(self._project.clips)))
            self._project.clips.insert(new_idx, clip)
            self.clipsChanged.emit()
            self.changed.emit()

    # --- Overlays & filtres (inchangé) ------------------------
    def add_text_overlay(self, ov: Optional[TextOverlay] = None):
        self._project.text_overlays.append(ov or TextOverlay())
        self.overlayChanged.emit(); self.changed.emit()

    def remove_last_text_overlay(self):
        if self._project.text_overlays:
            self._project.text_overlays.pop()
            self.overlayChanged.emit(); self.changed.emit()

    def update_last_overlay_text(self, text: str):
        if not self._project.text_overlays: return
        self._project.text_overlays[-1].text = text
        self.overlayChanged.emit(); self.changed.emit()

    def set_last_overlay_start(self, start_sec: float):
        if not self._project.text_overlays: return
        ov = self._project.text_overlays[-1]
        ov.start = max(0.0, float(start_sec))
        if ov.end < ov.start: ov.end = ov.start
        self.overlayChanged.emit(); self.changed.emit()

    def set_last_overlay_end(self, end_sec: float):
        if not self._project.text_overlays: return
        ov = self._project.text_overlays[-1]
        ov.end = max(0.0, float(end_sec))
        if ov.end < ov.start: ov.start = ov.end
        self.overlayChanged.emit(); self.changed.emit()

    def set_filters(self, brightness=None, contrast=None, saturation=None, vignette=None):
        f = self._project.filters
        if brightness is not None: f.brightness = float(brightness)
        if contrast is not None:   f.contrast = float(contrast)
        if saturation is not None: f.saturation = float(saturation)
        if vignette is not None:   f.vignette = bool(vignette)
        self.changed.emit()

    def add_image_overlay(self, path:str, start:float, duration:float=3.0):
        ov = ImageOverlay(path=path, start=start, end=start+duration)
        self._project.image_overlays.append(ov)
        self.overlayChanged.emit(); self.changed.emit()
        return ov

    def remove_last_image_overlay(self):
        if self._project.image_overlays:
            self._project.image_overlays.pop()
            self.overlayChanged.emit(); self.changed.emit()
