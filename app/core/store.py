# core/store.py
from typing import Optional
from PySide6.QtCore import QObject, Signal, QTimer
from core.project import Project, Clip, TextOverlay, Filters

class Store(QObject):
    changed = Signal()              # state global changé
    overlayChanged = Signal()       # overlays changés (pour l’UI overlay live)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project = Project(name="Nouveau projet")

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

    def start_auto_save(self, interval_ms: int = 30000):
        """Démarre une sauvegarde automatique toutes les interval_ms millisecondes."""
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._auto_save_timer.start(interval_ms)

    def _auto_save(self):
        from core.save_system.save_api import ProjectAPI
        try:
            ProjectAPI.save(self._project, "auto_save.lmprj")
            print("Auto-save effectué")
        except Exception as e:
            print("Auto-save échoué :", e)

    def load_project(self, filename: str) -> None:
        """
        Charge un projet à partir d'un fichier et écrase le projet actuel.
        Émet les signaux de changement appropriés.
        """
        from core.save_system.save_api import ProjectAPI        
        try:
            new_project = ProjectAPI.load(filename)
            
            self._project = new_project
            
            self.overlayChanged.emit()
            self.changed.emit()
            print(f"Projet chargé avec succès : {filename}")

        except FileNotFoundError:
            print(f"Erreur de chargement : Le fichier '{filename}' n'existe pas.")
        except Exception as e:
            print(f"Erreur de chargement du projet : {e}")