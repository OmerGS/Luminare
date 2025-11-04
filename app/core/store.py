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
    
    def add_video_clip_at(self, path: str, start_s: float, duration_s: float = 5.0):
        """
        Insère un nouveau clip vidéo à l'instant global `start_s` dans la séquence.
        - Si `start_s` tombe au milieu d'un clip existant, on le split et on insère le nouveau au milieu.
        - Si `start_s` est après la fin, on append à la fin.
        """
        start_s = max(0.0, float(start_s))
        duration_s = max(0.0, float(duration_s))

        # Cas séquence vide -> on ajoute simplement
        if not self._project.clips:
            newc = VideoClip(path=path, in_s=0.0, out_s=duration_s, duration_s=duration_s)
            self._project.clips.append(newc)
            self.clipsChanged.emit(); self.changed.emit()
            return newc

        idx, c, local = self.clip_at_global_time(start_s)  # (index, clip, temps_local_dans_clip)
        newc = VideoClip(path=path, in_s=0.0, out_s=duration_s, duration_s=duration_s)

        # Si start_s est au-delà de la fin de la séquence (idx == None)
        if idx is None or c is None:
            self._project.clips.append(newc)
            self.clipsChanged.emit(); self.changed.emit()
            return newc

        # bornes du clip courant
        c_start = c.in_s
        c_end   = c.out_s if c.out_s > 0 else (c.in_s + c.duration_s)

        # local = temps local dans la source = c.in_s + (t_global - acc)
        # On veut savoir si on est exactement en bordure ou au milieu
        EPS = 1e-6
        if abs(local - c_start) < EPS:
            # au tout début du clip courant -> on insère AVANT
            self._project.clips.insert(idx, newc)
        elif abs(local - c_end) < EPS:
            # à la fin du clip courant -> on insère APRÈS
            self._project.clips.insert(idx + 1, newc)
        else:
            # au milieu -> on split le clip courant, puis on insère entre les deux
            # split_clip_at attend un temps 'local_s' RELATIF au clip (offset depuis c.in_s)
            rel = local - c_start
            left_idx, right_idx = self.split_clip_at(idx, rel)
            # après split : left à idx, right à idx+1 → on insère newc entre
            self._project.clips.insert(right_idx, newc)

        self.clipsChanged.emit(); self.changed.emit()
        return newc
    
    # --- À coller DANS la classe Store (core/store.py) ---

    def _clip_duration_s(self, clip) -> float:
        """Durée effective d'un clip en secondes."""
        try:
            if getattr(clip, "duration_s", None) not in (None, 0.0):
                return float(clip.duration_s)
            # fallback si le modèle n'a pas duration_s explicitement
            return max(0.0, float(clip.out_s) - float(clip.in_s))
        except Exception:
            return 0.0

    def clip_boundaries(self):
        """
        Retourne les bornes (start_s, end_s) séquentielles de tous les clips
        en supposant un montage linéaire sans trous (accumulation).
        """
        bounds = []
        acc = 0.0
        for c in self.project().clips:
            dur = self._clip_duration_s(c)
            bounds.append((acc, acc + dur))
            acc += dur
        return bounds

    def total_duration_s(self) -> float:
        """Durée totale de la séquence (somme des durées des clips)."""
        acc = 0.0
        for c in self.project().clips:
            acc += self._clip_duration_s(c)
        return acc

    def clip_at_global_time(self, t_s: float):
        """
        Trouve le clip qui recouvre le temps global t_s (en secondes).
        Retourne (index, clip, local_s) où local_s est le temps relatif à CE clip.
        Si t_s est à l'extrême fin, retourne le dernier clip et local_s = sa durée.
        Si aucun clip, retourne (-1, None, 0.0).
        """
        clips = self.project().clips
        if not clips:
            return -1, None, 0.0

        t = max(0.0, float(t_s))
        acc = 0.0
        for i, c in enumerate(clips):
            dur = self._clip_duration_s(c)
            if t < acc + dur or (i == len(clips) - 1 and t <= acc + dur):
                local = max(0.0, min(t - acc, dur))
                return i, c, local
            acc += dur

        # par sécurité (t > total): pointer fin du dernier clip
        return len(clips) - 1, clips[-1], self._clip_duration_s(clips[-1])

