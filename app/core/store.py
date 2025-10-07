# core/store.py
from typing import Optional
from PySide6.QtCore import QObject, Signal
from .project import Project, Clip, TextOverlay, Filters, ImageOverlay 

class Store(QObject):
    changed = Signal()              # state global changé
    overlayChanged = Signal()       # overlays changés (pour l’UI overlay live)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project = Project()

    def project(self) -> Project:
        return self._project

    # --- Mutations ---
    def set_clip(self, path: str, duration_s: float):
        self._project.clips = [Clip(path=path, trim=(0.0, max(1.0, duration_s)))]
        self.changed.emit()

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
        self.overlayChanged.emit()
        return ov
    
    def remove_last_image_overlay(self):
        if self._project.image_overlays:
            self._project.image_overlays.pop()
            self.overlayChanged.emit()

    def project(self): return self._project