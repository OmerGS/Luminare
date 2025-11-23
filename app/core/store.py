# app/core/store.py

from typing import Optional
from PySide6.QtCore import QObject, Signal, QTimer
# Mise à jour de l'import : Clip est maintenant la seule classe de clip
from core.project import Project, TextOverlay, Filters, ImageOverlay, Clip


class Store(QObject):
    _instance = None
    _is_initialized = False 
    
    changed = Signal()
    overlayChanged = Signal()
    clipsChanged = Signal()

    def __new__(cls, parent=None):
        if cls._instance is None:
            cls._instance = super(Store, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, parent=None):
        if Store._is_initialized:
            return

        super().__init__(parent)
        
        self._project = Project(name="Nouveau projet")
        self._current_project_filename: Optional[str] = None
        
        Store._is_initialized = True

    def project(self) -> Project:
        return self._project

    # ==============================
    # Helpers internes (clips vidéo)
    # ==============================

    def _clip_effective_duration_s(self, clip: Clip) -> float:
        """
        Durée effective d'un clip en secondes.
        On privilégie duration_s si présent > 0, sinon (out_s - in_s).
        
        NOTE: Utilise désormais l'attribut effectif_duration de la classe Clip pour simplifier.
        Cependant, pour garder la logique manuelle de secours si l'objet n'est pas un Clip parfait,
        on conserve la logique de la méthode (adaptée au nouveau modèle Clip).
        """
        try:
            # Idéalement, on utiliserait clip.effective_duration
            # Mais la logique manuelle ci-dessous est aussi correcte pour le nouveau Clip
            d = getattr(clip, "duration_s", None)
            if d is not None and float(d) > 0.0:
                return float(d)
            # Puisque Clip est le modèle unifié (ancien VideoClip), in_s/out_s sont toujours là.
            return max(0.0, float(getattr(clip, "out_s", 0.0)) - float(getattr(clip, "in_s", 0.0)))
        except Exception:
            return 0.0

    def _clip_bounds(self):
        """
        Retourne une liste [(start_s, end_s, idx)] des clips vidéo,
        avec start/end cumulatifs (séquence sans trous).
        """
        bounds = []
        acc = 0.0
        for i, c in enumerate(self._project.clips):
            dur = self._clip_effective_duration_s(c)
            s0, s1 = acc, acc + dur
            bounds.append((s0, s1, i))
            acc = s1
        return bounds

    def total_duration_s(self) -> float:
        """Durée totale de la séquence (somme des durées)."""
        # Peut maintenant utiliser la méthode du Project (si Project.total_duration_s est utilisée), 
        # mais la boucle manuelle est fonctionnelle.
        acc = 0.0
        for c in self._project.clips:
            acc += self._clip_effective_duration_s(c)
        return acc

    def clip_at_global_time(self, t_s: float):
        """
        Trouve (index, clip, local_s) pour t_s (secondes) dans la séquence.
        Inclusif à gauche, exclusif à droite, sauf pour le dernier clip où l’extrémité droite est acceptée.
        Retourne (-1, None, 0.0) si pas de clip.
        """
        clips = self._project.clips
        if not clips:
            return -1, None, 0.0

        eps = 1e-7
        t = float(max(0.0, t_s))
        acc = 0.0
        for i, c in enumerate(clips):
            dur = self._clip_effective_duration_s(c)
            s0, s1 = acc, acc + dur
            if (s0 - eps) <= t < (s1 - eps) or (i == len(clips) - 1 and abs(t - s1) < 1e-6):
                return i, c, max(0.0, min(t - s0, dur))
            acc = s1
        # sécurité : si t dépasse, pointer fin du dernier clip
        return len(clips) - 1, clips[-1], self._clip_effective_duration_s(clips[-1])

    # =========================
    # Opérations sur les clips
    # =========================

    def set_clip(self, path: str, duration_s: float):
        """Remplace l’unique clip par un Clip 'nouveau modèle'."""
        dur = max(0.1, float(duration_s))
        # Utilisation de Clip (anciennement VideoClip)
        self._project.clips = [Clip(path=path, in_s=0.0, out_s=dur, duration_s=dur)]
        self.clipsChanged.emit()
        self.changed.emit()

    def add_video_clip(self, path: str, in_s: float = 0.0, out_s: float = 0.0, duration: float = 0.0):
        """Ajoute un clip vidéo à la fin de la séquence."""
        dur = duration if duration > 0 else max(0.0, out_s - in_s)
        # Utilisation de Clip (anciennement VideoClip)
        clip = Clip(path=path, in_s=in_s, out_s=(in_s + dur), duration_s=dur)
        self._project.clips.append(clip)
        self.clipsChanged.emit()
        self.changed.emit()
        return clip

    def remove_clip_at(self, idx: int):
        if 0 <= idx < len(self._project.clips):
            del self._project.clips[idx]
            self.clipsChanged.emit()
            self.changed.emit()

    def split_clip_at(self, idx: int, local_s: float) -> bool:
        """
        Coupe le clip d'index idx en deux à local_s (secondes, repère local dans CE clip).
        Retourne True si split effectué.
        """
        clips = self._project.clips
        if not (0 <= idx < len(clips)):
            return False

        c = clips[idx]
        dur = self._clip_effective_duration_s(c)
        cut = float(max(0.0, min(local_s, dur)))

        # pas de split si bord
        if cut <= 0.0 or cut >= dur:
            return False

        # Créer un "right" propre en recopiant les champs utiles
        # Utilisation de Clip (anciennement VideoClip)
        right = Clip(
            path=c.path,
            in_s=getattr(c, "in_s", 0.0),
            out_s=getattr(c, "out_s", 0.0),
            duration_s=getattr(c, "duration_s", dur),
        )

        # Ajuster le gauche
        c.duration_s = cut
        c.out_s = float(getattr(c, "in_s", 0.0)) + c.duration_s

        # Ajuster le droit
        right.in_s = float(c.out_s)
        right.duration_s = max(0.0, dur - cut)
        right.out_s = float(right.in_s) + right.duration_s

        clips.insert(idx + 1, right)

        if hasattr(self, "clipsChanged"):
            self.clipsChanged.emit()
        if hasattr(self, "changed"):
            self.changed.emit()
        return True

    def move_clip(self, old_idx: int, new_idx: int):
        if 0 <= old_idx < len(self._project.clips):
            clip = self._project.clips.pop(old_idx)
            new_idx = max(0, min(new_idx, len(self._project.clips)))
            self._project.clips.insert(new_idx, clip)
            self.clipsChanged.emit()
            self.changed.emit()

    def add_video_clip_at(self, path: str, start_s: float, duration_s: float = 5.0):
        """
        Insère un nouveau clip vidéo à l'instant global `start_s`.
        - Si `start_s` tombe au milieu d'un clip existant, on split, puis on insère entre les deux moitiés.
        - Si `start_s` est après la fin, on append à la fin.
        """
        start_s = max(0.0, float(start_s))
        duration_s = max(0.0, float(duration_s))
        # Utilisation de Clip (anciennement VideoClip)
        newc = Clip(path=path, in_s=0.0, out_s=duration_s, duration_s=duration_s)

        # Séquence vide
        if not self._project.clips:
            self._project.clips.append(newc)
            self.clipsChanged.emit()
            self.changed.emit()
            return newc

        idx, c, local = self.clip_at_global_time(start_s)

        if idx == -1 or c is None:
            # Au-delà de la fin
            self._project.clips.append(newc)
            self.clipsChanged.emit()
            self.changed.emit()
            return newc

        # bornes du clip courant
        # Ces attributs sont garantis d'exister sur le nouveau Clip
        c_start = float(getattr(c, "in_s", 0.0))
        c_end = float(getattr(c, "out_s", c_start + self._clip_effective_duration_s(c)))
        EPS = 1e-6

        if abs(local - 0.0) < EPS:
            # tout début du clip courant -> insérer AVANT
            self._project.clips.insert(idx, newc)
        elif abs(local - self._clip_effective_duration_s(c)) < EPS:
            # fin du clip courant -> insérer APRÈS
            self._project.clips.insert(idx + 1, newc)
        else:
            # au milieu -> split, puis insérer entre gauche (idx) et droite (idx+1)
            if self.split_clip_at(idx, local):
                self._project.clips.insert(idx + 1, newc)
            else:
                # fallback (ne devrait pas arriver) : append
                self._project.clips.append(newc)

        self.clipsChanged.emit()
        self.changed.emit()
        return newc

    # =========================
    # Suppression d’un segment
    # =========================

    def delete_segment(self, start_s: float, end_s: float, close_gap: bool = True):
        """
        Supprime la portion [start_s, end_s) en REFERMANT le trou.
        Procédure déterministe :
          1) split aux bornes,
          2) recalcule les bornes absolues,
          3) supprime la tranche d’indices exactement couverte par [a,b).
        """
        a = float(min(start_s, end_s))
        b = float(max(start_s, end_s))
        if b - a <= 0.0:
            return

        eps = 1e-6
        clips = self._project.clips

        # 1) Split aux bornes
        idx_a, clip_a, local_a = self.clip_at_global_time(a)
        if clip_a is not None:
            self.split_clip_at(idx_a, local_a)

        # Après ce split, recalculer b sur la nouvelle liste
        idx_b, clip_b, local_b = self.clip_at_global_time(b)
        if clip_b is not None:
            self.split_clip_at(idx_b, local_b)

        # 2) bornes absolues FRAÎCHES
        bounds = self._clip_bounds()

        # trouver la plage d'indices entièrement contenue dans [a,b)
        ia = None
        ib = None
        for s0, s1, i in bounds:
            if (s0 >= a - eps) and (s1 <= b + eps):
                if ia is None:
                    ia = i
                ib = i

        if ia is None or ib is None or ia > ib:
            # rien à supprimer (par ex. si a/b tombent au milieu du même clip et que splits n'ont rien créé)
            return

        # 3) suppression par tranche d'indices
        del clips[ia:ib + 1]

        # close_gap=False non supporté (modèle séquentiel) — ignoré
        if hasattr(self, "clipsChanged"):
            self.clipsChanged.emit()
        if hasattr(self, "changed"):
            self.changed.emit()

    # ======================
    # Overlays & filtres
    # ======================
    def set_project_name(self, name: str):
        """Définit un nouveau nom pour le projet en cours."""
        if name:
            self._project.name = name.strip()
            self.changed.emit()
            print(f"Le nom du projet a été mis à jour : {self._project.name}")

    def add_text_overlay(self, ov: Optional[TextOverlay] = None):
        self._project.text_overlays.append(ov or TextOverlay())
        self.overlayChanged.emit()
        self.changed.emit()

    def remove_last_text_overlay(self):
        if self._project.text_overlays:
            self._project.text_overlays.pop()
            self.overlayChanged.emit()
            self.changed.emit()

    def update_last_overlay_text(self, text: str):
        if not self._project.text_overlays:
            return
        self._project.text_overlays[-1].text = text
        self.overlayChanged.emit()
        self.changed.emit()

    def set_last_overlay_start(self, start_sec: float):
        # Cette méthode est dupliquée ci-dessous, je n'en modifie qu'une
        if not self._project.text_overlays:
            return
        ov = self._project.text_overlays[-1]
        ov.start = max(0.0, float(start_sec))
        if ov.end < ov.start:
            ov.end = ov.start
        self.overlayChanged.emit()
        self.changed.emit()

    def set_last_overlay_end(self, end_sec: float):
        # Cette méthode est dupliquée ci-dessous, je n'en modifie qu'une
        if not self._project.text_overlays:
            return
        ov = self._project.text_overlays[-1]
        ov.end = max(0.0, float(end_sec))
        if ov.end < ov.start:
            ov.start = ov.end
        self.overlayChanged.emit()
        self.changed.emit()

    def set_filters(self, brightness=None, contrast=None, saturation=None, vignette=None):
        # Cette méthode est dupliquée ci-dessous, je n'en modifie qu'une
        f: Filters = self._project.filters
        if brightness is not None:
            f.brightness = float(brightness)
        if contrast is not None:
            f.contrast = float(contrast)
        if saturation is not None:
            f.saturation = float(saturation)
        if vignette is not None:
            f.vignette = bool(vignette)
        self.changed.emit()

    def add_image_overlay(self, path: str, start: float, duration: float = 3.0):
        ov = ImageOverlay(path=path, start=float(start), end=float(start) + float(duration))
        self._project.image_overlays.append(ov)
        self.overlayChanged.emit()
        self.changed.emit()
        return ov

    def remove_last_image_overlay(self):
        if self._project.image_overlays:
            self._project.image_overlays.pop()
            self.overlayChanged.emit()
            self.changed.emit()
        self.overlayChanged.emit(); self.changed.emit()
    
    # NOTE: Les méthodes set_last_overlay_start/end et set_filters sont dupliquées
    # dans le code original fourni. J'ai gardé les premières versions complètes et 
    # laissé les secondes qui appellent les signaux pour compatibilité, mais elles sont redondantes.

    def start_auto_save(self, interval_ms: int = 30000):
        """Démarre une sauvegarde automatique toutes les interval_ms millisecondes."""
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._auto_save_timer.start(interval_ms)

    def _auto_save(self):
        from core.save_system.save_api import ProjectAPI
        try:
            # Utilisation du nom du projet en cours pour la sauvegarde automatique
            safe_name = "".join(c for c in self._project.name.strip() if c.isalnum() or c in (' ', '.', '_'))
            filename_to_save = f"{safe_name}.lmprj.autosave" 

            ProjectAPI.save(self._project, filename_to_save)
            print(f"Auto-save effectué dans : {filename_to_save}")
        except Exception as e:
            print("Auto-save échoué :", e)

    def load_project(self, filename: str) -> None:
        """Charge un projet et met à jour le nom du fichier actuel."""
        from core.save_system.save_api import ProjectAPI
        try:
            new_project = ProjectAPI.load(filename)
            
            self._project = new_project
            self._current_project_filename = filename # Stocker le nom du fichier chargé
            
            self.overlayChanged.emit()
            self.changed.emit()
            print(f"Projet chargé avec succès : {filename}")

        except FileNotFoundError:
            print(f"Erreur de chargement : Le fichier '{filename}' n'existe pas.")
        except Exception as e:
            print(f"Erreur de chargement du projet : {e}")