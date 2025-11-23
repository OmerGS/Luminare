# core/sequence_player.py
from __future__ import annotations
from typing import List, Tuple, Optional
from PySide6.QtCore import QObject, Signal, QUrl

from core.store import Store
from core.project import Clip, Project
from core.utils_timeline import total_sequence_duration_ms

class SequencePlayer(QObject):
    """Lit une séquence de clips comme s'il s'agissait d'une seule vidéo."""
    frameImageAvailable = Signal(object)  # QImage
    positionChanged = Signal(int)         # ms (global)
    durationChanged = Signal(int)         # ms (total)
    errorOccurred = Signal(str)

    def __init__(self, media_controller, store: Store, parent=None):
        super().__init__(parent)
        self._media = media_controller   # core.media_controller.MediaController
        self._store = store
        self._clips: List[Clip] = []
        self._boundaries_ms: List[Tuple[int, int]] = []  # [(start_ms, end_ms) global pour chaque clip]
        self._total_ms = 0
        self._current_clip_index: int = -1
        self._loading = False  # évite les boucles d'événements pendant les seek/load

        # Re-propage les signaux vidéo (frame)
        self._media.frameImageAvailable.connect(self.frameImageAvailable.emit)
        self._media.errorOccurred.connect(self.errorOccurred.emit)
        # Recalcule position globale à partir de la position locale du media courant
        self._media.positionChanged.connect(self._on_local_position_changed)

        # Suivre les changements du Store
        self._store.clipsChanged.connect(self._rebuild_map)
        self._rebuild_map()

    # ----- API publique (compatible PlayerControls) -----
    def play(self): self._media.play()
    def pause(self): self._media.pause()
    def stop(self):
        self._media.stop()
        self.seek_ms(0)

    def seek_ms(self, global_ms: int):
        """Seek temps global (0..total). Charge le bon fichier et seek localement."""
        if not self._clips:
            self.positionChanged.emit(0)
            return
        g = max(0, min(int(global_ms), int(self._total_ms)))
        idx, local_ms = self._locate(g)
        self._switch_if_needed(idx, local_ms)
        self.positionChanged.emit(g)

    def set_volume(self, v: float): self._media.set_volume(v)
    def position_ms(self) -> int:
        """Retourne une estimation du temps global courant."""
        g = 0
        if 0 <= self._current_clip_index < len(self._boundaries_ms):
            start, end = self._boundaries_ms[self._current_clip_index]
            g = start + self._media.position_ms()
            if g > end: g = end
        return int(g)

    # ----- internes -----
    def _rebuild_map(self):
        proj: Project = self._store.project()
        self._clips = list(proj.clips)
        self._boundaries_ms.clear()

        acc = 0
        for c in self._clips:
            dur_s = max(0.0, float(getattr(c, "duration_s", 0.0)) or (float(c.out_s) - float(c.in_s)))
            dur_ms = int(dur_s * 1000)
            self._boundaries_ms.append((acc, acc + dur_ms))
            acc += dur_ms

        self._total_ms = acc
        self.durationChanged.emit(int(self._total_ms))

        # Sécurité : si plus de clip, reset
        if not self._clips:
            self._current_clip_index = -1
            self.positionChanged.emit(0)

    def _locate(self, global_ms: int) -> Tuple[int, int]:
        """Retourne (index_clip, local_ms)."""
        g = int(global_ms)
        for i, (s, e) in enumerate(self._boundaries_ms):
            if s <= g < e or (g == e and i == len(self._boundaries_ms) - 1):
                return i, g - s
        # hors bornes -> fin
        return max(0, len(self._clips) - 1), 0

    def _switch_if_needed(self, idx: int, local_ms: int):
        """Charge un nouveau média si on change de clip; sinon seek localement."""
        if idx < 0 or idx >= len(self._clips):
            return
        clip = self._clips[idx]
        # temps local réel = offset d'entrée + local_ms
        in_ms = int(float(getattr(clip, "in_s", 0.0)) * 1000.0)
        target_ms = in_ms + int(local_ms)

        if idx != self._current_clip_index:
            self._current_clip_index = idx
            self._loading = True
            # charger la source
            self._media.load(QUrl.fromLocalFile(clip.path))
            # appliquer le seek local après le load
            self._media.seek_ms(target_ms)
            self._loading = False
        else:
            # même source -> seek local
            self._media.seek_ms(target_ms)

    def _on_local_position_changed(self, local_abs_ms: int):
        """Convertit la position locale courante en temps global, enchaîne si fin de clip."""
        if self._loading or self._current_clip_index < 0:
            return
        # bornes globales du clip courant
        start_g, end_g = self._boundaries_ms[self._current_clip_index]
        clip = self._clips[self._current_clip_index]
        in_ms = int(float(getattr(clip, "in_s", 0.0)) * 1000.0)
        # local absolu dans la source -> local relatif dans le segment
        local_rel_ms = max(0, local_abs_ms - in_ms)
        g = start_g + local_rel_ms
        self.positionChanged.emit(int(min(g, self._total_ms)))

        # Enchaînement automatique à la fin du clip
        if g >= end_g - 2:  # petite marge
            next_idx = self._current_clip_index + 1
            if next_idx < len(self._clips):
                self._switch_if_needed(next_idx, 0)
            else:
                # fin de séquence
                self._media.pause()
