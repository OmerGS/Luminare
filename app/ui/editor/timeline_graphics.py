from __future__ import annotations
from typing import List, Dict
import json
from pathlib import Path

from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainter, QCursor
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsLineItem, QGraphicsTextItem
)
from ui.components.assets_panel import MIME_IMAGE_ASSET, MIME_VIDEO_ASSET


# --------------------------
#  Items : Ruler + ClipItem
# --------------------------

class RulerItem(QGraphicsItem):
    """Règle temporelle en haut de la timeline."""
    def __init__(self, px_per_sec: int, total_w: float, height: float = 28.0, parent=None):
        super().__init__(parent)
        self._px = px_per_sec
        self._w = total_w
        self._h = height
        self.setZValue(-10)

    def set_px_per_sec(self, px: int):
        self._px = max(10, int(px))
        self.prepareGeometryChange()

    def set_width(self, w: float):
        self._w = max(100.0, float(w))
        self.prepareGeometryChange()

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._w, self._h)

    def paint(self, p: QPainter, option, widget=None):
        r = self.boundingRect()
        base = QColor(240, 240, 240)
        p.fillRect(r, base)

        pen_axis = QPen(QColor(180, 180, 180), 1)
        p.setPen(pen_axis)
        p.drawLine(r.left(), r.bottom() - 1, r.right(), r.bottom() - 1)

        # graduations
        p.setPen(QColor(60, 60, 60))
        font = p.font()
        font.setPointSize(8)
        p.setFont(font)

        secs = int(max(1, self._w / self._px))
        for s in range(secs + 1):
            x = s * self._px
            p.drawLine(x, r.bottom() - 1, x, r.bottom() - 8)
            step = max(1, self._px // 4)
            for k in range(1, 4):
                xx = x + k * step
                if xx >= r.right():
                    break
                p.drawLine(xx, r.bottom() - 1, xx, r.bottom() - 5)
            if s % 5 == 0:
                p.drawText(x + 3, r.top() + 10, f"{s}s")


# --------------------------
#  Clip Item amélioré
# --------------------------

class ClipItem(QObject, QGraphicsRectItem):
    """Bloc clip redimensionnable horizontalement (type CapCut)."""
    resized = Signal(float, float, float)  # (start_s, in_s, duration)
    moved = Signal(float)

    def __init__(self, model: Dict, px_per_sec: int, scene_width: float, lane_y: float):
        QObject.__init__(self)
        QGraphicsRectItem.__init__(self)
        self.setZValue(10)

        self.model = model
        self._px = px_per_sec
        self._scene_w = scene_width
        self._lane_y = lane_y
        self._dragging_handle = None
        self._drag_start_x = 0
        self._orig_rect = None

        # taille et position
        w = max(2.0, float(model["duration"]) * self._px)
        x = float(model["start"]) * self._px
        self.setRect(0, 0, w, 36.0)
        self.setPos(QPointF(x, self._lane_y))

        # style
        color = QColor(model.get("color", "#7fb3ff"))
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor(40, 40, 40), 1))
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

        # poignées gauche/droite
        self.handle_left = QGraphicsRectItem(self)
        self.handle_right = QGraphicsRectItem(self)
        for h in (self.handle_left, self.handle_right):
            h.setBrush(QBrush(QColor("#555")))
            h.setPen(Qt.NoPen)
            h.setRect(0, 0, 6, 36)
            h.setZValue(20)
        self._update_handles()

    def _update_handles(self):
        r = self.rect()
        self.handle_left.setPos(0, 0)
        self.handle_right.setPos(r.width() - 6, 0)

    # --- hover pour curseur ---
    def hoverMoveEvent(self, event):
        if self.handle_left.isUnderMouse() or self.handle_right.isUnderMouse():
            self.setCursor(QCursor(Qt.SizeHorCursor))
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))
        super().hoverMoveEvent(event)

    # --- gestion souris ---
    def mousePressEvent(self, event):
        if self.handle_left.isUnderMouse():
            self._dragging_handle = "left"
        elif self.handle_right.isUnderMouse():
            self._dragging_handle = "right"
        else:
            self._dragging_handle = None

        self._drag_start_x = event.scenePos().x()
        self._orig_rect = QRectF(self.rect())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._dragging_handle:
            return super().mouseMoveEvent(event)

        delta_x = event.scenePos().x() - self._drag_start_x
        new_rect = QRectF(self._orig_rect)

        # Redimensionnement gauche
        if self._dragging_handle == "left":
            new_w = new_rect.width() - delta_x
            if new_w >= 10:
                new_rect.setWidth(new_w)
                self.setRect(new_rect)
                self.setX(self.x() + delta_x)
                # mise à jour logique
                delta_s = delta_x / float(self._px)
                self.model["in_s"] = max(0.0, self.model.get("in_s", 0.0) + delta_s)
                self.model["start"] = max(0.0, self.model["start"] + delta_s)
                self.model["duration"] = max(0.1, new_w / self._px)

        # Redimensionnement droite
        elif self._dragging_handle == "right":
            new_w = new_rect.width() + delta_x
            if new_w >= 10:
                new_rect.setWidth(new_w)
                self.setRect(new_rect)
                self.model["duration"] = max(0.1, new_w / self._px)

        self._update_handles()
        self.resized.emit(self.model["start"], self.model.get("in_s", 0.0), self.model["duration"])

    def mouseReleaseEvent(self, event):
        self._dragging_handle = None
        super().mouseReleaseEvent(event)

    def update_metrics(self, px_per_sec: int, scene_width: float):
        """Met à jour la taille du clip si zoom ou resize."""
        self._px = max(10, int(px_per_sec))
        self._scene_w = float(scene_width)
        w = max(2.0, float(self.model["duration"]) * self._px)
        x = float(self.model["start"]) * self._px
        self.setRect(0, 0, w, 36.0)
        self.setPos(QPointF(x, self._lane_y))
        self._update_handles()


# --------------------------
#  Vue/Scene principale
# --------------------------

class TimelineView(QGraphicsView):
    """Timeline graphique avec clips redimensionnables."""
    seekRequested = Signal(int)           # ms
    clipMoved = Signal(int, float)        # index, new_start_s
    clipDropRequested = Signal(str, float)

    LANE_DEFINITIONS = [
        {"name": "Vidéo", "y": 50.0, "color": QColor(245, 245, 245)},
        {"name": "Images", "y": 92.0, "color": QColor(240, 245, 240)},
        {"name": "Texte", "y": 134.0, "color": QColor(240, 240, 245)},
    ]
    LANE_HEIGHT = 36.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHints(self.renderHints() | QPainter.Antialiasing)
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setAcceptDrops(True)

        self._px_per_sec = 80
        self._height = 160.0
        self._total_ms = 0
        self._models = []
        self._items = []

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._rebuild_scene_rect()
        self._ruler = RulerItem(self._px_per_sec, self._scene_width())
        self._scene.addItem(self._ruler)

        self._playhead = QGraphicsLineItem()
        self._playhead.setPen(QPen(QColor("red"), 2))
        self._playhead.setZValue(100)
        self._scene.addItem(self._playhead)
        self._update_playhead_x(0)

        self._lane_bgs = []
        for lane_def in self.LANE_DEFINITIONS:
            y = lane_def["y"]
            
            # Le rectangle de fond pour la piste
            bg_rect = QGraphicsRectItem(0, y, self._scene_width(), self.LANE_HEIGHT)
            bg_rect.setBrush(QBrush(lane_def["color"]))
            bg_rect.setPen(QPen(QColor(220, 220, 220), 1, Qt.DashLine))
            bg_rect.setZValue(-5)
            self._scene.addItem(bg_rect)
            self._lane_bgs.append(bg_rect)

    # ---- helpers géométrie ----
    def _scene_width(self) -> float:
        secs = max(1.0, self._total_ms / 1000.0)
        return max(1200.0, secs * self._px_per_sec)

    def _rebuild_scene_rect(self):
        # ✅ On calcule la hauteur totale en fonction des pistes
        total_height = 180.0 # Hauteur par défaut
        if self.LANE_DEFINITIONS:
            last_lane = self.LANE_DEFINITIONS[-1]
            total_height = last_lane["y"] + self.LANE_HEIGHT + 20.0 # y + hauteur + marge
            
        self._scene.setSceneRect(QRectF(0, 0, self._scene_width(), total_height))
        self.setMinimumHeight(int(total_height) + 40) # +40 pour la règle et la scrollbar

    def set_total_duration(self, total_ms: int):
        self._total_ms = max(0, int(total_ms))
        self._rebuild_scene_rect()
        self._ruler.set_width(self._scene_width())
        
        # ✅ On met à jour TOUS les fonds de pistes
        scene_w = self._scene_width()
        for i, lane_def in enumerate(self.LANE_DEFINITIONS):
            if i < len(self._lane_bgs):
                self._lane_bgs[i].setRect(0, lane_def["y"], scene_w, self.LANE_HEIGHT)

        for it in self._items:
            it.update_metrics(self._px_per_sec, self._scene_width())

    def set_zoom(self, px_per_sec: int):
        self._px_per_sec = max(10, int(px_per_sec))
        self._ruler.set_px_per_sec(self._px_per_sec)
        self.set_total_duration(self._total_ms)
        for it in self._items:
            it.update_metrics(self._px_per_sec, self._scene_width())
        self._update_playhead_x(getattr(self, "_current_ms", 0))

    def set_playhead_ms(self, ms: int):
        self._current_ms = max(0, int(ms))
        self._update_playhead_x(self._current_ms)

    def _update_playhead_x(self, ms: int):
        x = (ms / 1000.0) * self._px_per_sec
        self._playhead.setLine(x, 0, x, self.sceneRect().height())

    def set_project_data(self, project):
        # ... (le code pour vider _items et _scene) ...
        for it in self._items:
            self._scene.removeItem(it)
        self._items.clear()
        
        # Piste 1: Clips Vidéo
        lane_y = self.LANE_DEFINITIONS[0]["y"]
        
        # ⬇️ ⬇️ ⬇️ NOUS AVONS BESOIN DE CETTE VARIABLE ⬇️ ⬇️ ⬇️
        global_start_s = 0.0
        
        for clip_model in project.clips:
            # Calcul de la durée (sécurisé)
            duration = getattr(clip_model, 'duration_s', 0.0)
            if duration <= 0.0:
                duration = getattr(clip_model, 'out_s', 0.0) - getattr(clip_model, 'in_s', 0.0)
            duration = max(0.1, duration) # Durée minimale
            
            model_dict = {
                # ❌ AVANT: "start": clip_model.start_s,
                "start": global_start_s, # ✅ APRÈS
                "duration": duration,
                "in_s": getattr(clip_model, 'in_s', 0.0),
                "label": Path(clip_model.path).stem,
                "color": "#7fb3ff" # Couleur pour les vidéos
            }
            it = ClipItem(model_dict, self._px_per_sec, self._scene_width(), lane_y)
            
            # ... (votre code pour ajouter le label au ClipItem) ...
            if model_dict["label"]:
                text_item = QGraphicsTextItem(model_dict["label"], it)
                text_item.setDefaultTextColor(QColor(20, 20, 20))
                text_item.setPos(6, 8)
                text_item.setZValue(20)
            
            self._scene.addItem(it)
            self._items.append(it)
            
            # ⬇️ ⬇️ ⬇️ METTRE À JOUR LE TEMPS GLOBAL ⬇️ ⬇️ ⬇️
            global_start_s += duration

        # Piste 2: Overlays d'images
        lane_y = self.LANE_DEFINITIONS[1]["y"]
        for img_model in project.image_overlays:
            duration = max(0.1, img_model.end - img_model.start)
            model_dict = {
                "start": img_model.start, # ✅ C'est correct, les overlays ont un 'start'
                "duration": duration,
                "label": f"IMG: {Path(img_model.path).stem}",
                "color": "#a9ff7f" # Couleur pour les images
            }
            it = ClipItem(model_dict, self._px_per_sec, self._scene_width(), lane_y)
            # ... (code pour le label) ...
            if model_dict["label"]:
                text_item = QGraphicsTextItem(model_dict["label"], it)
                text_item.setDefaultTextColor(QColor(20, 20, 20))
                text_item.setPos(6, 8)
                text_item.setZValue(20)
                
            self._scene.addItem(it)
            self._items.append(it)

        # Piste 3: Overlays de texte
        lane_y = self.LANE_DEFINITIONS[2]["y"]
        for txt_model in project.text_overlays:
            duration = max(0.1, txt_model.end - txt_model.start)
            model_dict = {
                "start": txt_model.start, # ✅ C'est correct
                "duration": duration,
                "label": txt_model.text or "Titre",
                "color": "#ffaf7f" # Couleur pour les textes
            }
            it = ClipItem(model_dict, self._px_per_sec, self._scene_width(), lane_y)
            # ... (code pour le label) ...
            if model_dict["label"]:
                text_item = QGraphicsTextItem(model_dict["label"], it)
                text_item.setDefaultTextColor(QColor(20, 20, 20))
                text_item.setPos(6, 8)
                text_item.setZValue(20)

            self._scene.addItem(it)
            self._items.append(it)

        total_s = global_start_s
        
        # ... MAIS un overlay peut être plus long, vérifions
        for img_model in project.image_overlays:
            total_s = max(total_s, img_model.end)
        for txt_model in project.text_overlays:
            total_s = max(total_s, txt_model.end)

        # On ajoute une marge de 10s à la fin pour avoir de l'espace
        total_s += 10.0
        
        print(f"[DEBUG] Nouvelle durée totale calculée: {total_s}s")
        # On notifie la timeline de sa nouvelle durée
        self.set_total_duration(int(total_s * 1000))

    # ---- interactions ----
    def mousePressEvent(self, e):
        pos_scene = self.mapToScene(e.pos())
        if not self.itemAt(e.pos()):
            ms = int(max(0.0, pos_scene.x() / self._px_per_sec) * 1000.0)
            self.seekRequested.emit(ms)
            self._update_playhead_x(ms)
        super().mousePressEvent(e)

    # ---- DnD ----
    def _scene_pos_to_seconds(self, ev) -> float:
        try:
            pt_vp = ev.position().toPoint()
        except AttributeError:
            pt_vp = ev.pos()
        x_scene = self.mapToScene(pt_vp).x()
        return max(0.0, x_scene / float(self._px_per_sec))

    def dragEnterEvent(self, e):
        md = e.mimeData()
        if md.hasFormat(MIME_VIDEO_ASSET) or md.hasFormat(MIME_IMAGE_ASSET):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e):
        md = e.mimeData()
        if md.hasFormat(MIME_VIDEO_ASSET):
            data = json.loads(bytes(md.data(MIME_VIDEO_ASSET)).decode("utf-8"))
            path = data.get("path")
            start_s = self._scene_pos_to_seconds(e)
            if path:
                self.clipDropRequested.emit(path, start_s)
            e.acceptProposedAction()
            return

        if md.hasFormat(MIME_IMAGE_ASSET):
            data = json.loads(bytes(md.data(MIME_IMAGE_ASSET)).decode("utf-8"))
            path = data.get("path")
            start_s = self._scene_pos_to_seconds(e)
            if path:
                self.clipDropRequested.emit(path, start_s)
            e.acceptProposedAction()
            return

        e.ignore()
