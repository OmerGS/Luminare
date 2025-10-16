# app/ui/editor/timeline_graphics.py
from __future__ import annotations
from typing import List, Dict

from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsLineItem
)

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
        p.drawLine(r.left(), r.bottom()-1, r.right(), r.bottom()-1)

        # graduations
        p.setPen(QColor(60, 60, 60))
        font = p.font()
        font.setPointSize(8)
        p.setFont(font)

        secs = int(max(1, self._w / self._px))
        for s in range(secs + 1):
            x = s * self._px
            # grande graduation chaque 1s
            p.drawLine(x, r.bottom()-1, x, r.bottom()-8)
            # sous-graduations (quart de seconde)
            step = max(1, self._px // 4)
            for k in range(1, 4):
                xx = x + k * step
                if xx >= r.right():
                    break
                p.drawLine(xx, r.bottom()-1, xx, r.bottom()-5)
            if s % 5 == 0:
                p.drawText(x + 3, r.top() + 10, f"{s}s")


class ClipItem(QObject, QGraphicsRectItem):
    """
    Bloc clip déplaçable horizontalement.
    Émet moved(new_start_s) lorsque sa position change.
    """
    moved = Signal(float)

    def __init__(self, model: Dict, px_per_sec: int, scene_width: float, lane_y: float):
        QObject.__init__(self)
        QGraphicsRectItem.__init__(self)
        self.setZValue(10)
        self.model = model
        self._px = px_per_sec
        self._scene_w = scene_width
        self._snap_s = 0.1  # snap 100ms
        self._lane_y = lane_y

        w = max(2.0, float(model["duration"]) * self._px)
        x = float(model["start"]) * self._px
        self.setRect(0, 0, w, 36.0)
        self.setPos(QPointF(x, self._lane_y))

        # style
        color = QColor(model.get("color", "#7fb3ff"))
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor(40, 40, 40), 1))

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def update_metrics(self, px_per_sec: int, scene_width: float):
        self._px = max(10, int(px_per_sec))
        self._scene_w = float(scene_width)
        w = max(2.0, float(self.model["duration"]) * self._px)
        x = float(self.model["start"]) * self._px
        self.setRect(0, 0, w, 36.0)
        self.setPos(QPointF(x, self._lane_y))

    def itemChange(self, change, value):
        # restreindre au déplacement horizontal + snap
        if change == QGraphicsItem.ItemPositionChange:
            new_pos: QPointF = value.toPointF()
            new_pos.setY(self._lane_y)

            # clamp largeur scène
            max_x = max(0.0, self._scene_w - self.rect().width())
            new_x = max(0.0, min(new_pos.x(), max_x))

            # snap
            s = new_x / float(self._px)
            if self._snap_s > 0:
                s = round(s / self._snap_s) * self._snap_s
            new_pos.setX(s * self._px)
            return new_pos

        if change == QGraphicsItem.ItemPositionHasChanged:
            # mettre à jour le modèle et émettre
            start_s = max(0.0, self.pos().x() / float(self._px))
            self.model["start"] = start_s
            self.moved.emit(start_s)

        return super().itemChange(change, value)
# --------------------------
#  Vue/Scene
# --------------------------

class TimelineView(QGraphicsView):
    """
    Timeline graphique :
      - ruler (graduations)
      - clips déplaçables (ordre temporel visuel)
      - playhead
    """
    seekRequested = Signal(int)          # ms
    clipMoved = Signal(int, float)       # index, new_start_s

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHints(self.renderHints() | QPainter.Antialiasing)
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._px_per_sec = 80
        self._height = 160.0
        self._total_ms = 0
        self._models: List[Dict] = []
        self._items: List[ClipItem] = []

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # géométrie scène
        self._rebuild_scene_rect()

        # ruler
        self._ruler = RulerItem(self._px_per_sec, self._scene_width())
        self._scene.addItem(self._ruler)

        # playhead (ligne rouge)
        self._playhead = QGraphicsLineItem()
        self._playhead.setPen(QPen(QColor("red"), 2))
        self._playhead.setZValue(100)
        self._scene.addItem(self._playhead)
        self._update_playhead_x(0)

        # fond des lanes
        self._lane_bg = QGraphicsRectItem(0, 32, self._scene_width(), self._height - 40)
        self._lane_bg.setBrush(QBrush(QColor(250, 250, 250)))
        self._lane_bg.setPen(QPen(QColor(220, 220, 220), 1, Qt.DashLine))
        self._lane_bg.setZValue(-5)
        self._scene.addItem(self._lane_bg)

    # ---- helpers géométrie ----
    def _scene_width(self) -> float:
        secs = max(1.0, self._total_ms / 1000.0)
        return max(1200.0, secs * self._px_per_sec)

    def _rebuild_scene_rect(self):
        self._scene.setSceneRect(QRectF(0, 0, self._scene_width(), self._height))
        self.setMinimumHeight(int(self._height) + 40)

    # ---- API publique ----
    def set_total_duration(self, total_ms: int):
        self._total_ms = max(0, int(total_ms))
        self._rebuild_scene_rect()
        self._ruler.set_width(self._scene_width())
        self._lane_bg.setRect(0, 32, self._scene_width(), self._height - 40)
        # repositionner les items selon la nouvelle largeur (au cas où)
        for it in self._items:
            it.update_metrics(self._px_per_sec, self._scene_width())

    def set_zoom(self, px_per_sec: int):
        self._px_per_sec = max(10, int(px_per_sec))
        self._ruler.set_px_per_sec(self._px_per_sec)
        self.set_total_duration(self._total_ms)  # met à jour largeur scène
        # remettre les clips à la bonne taille/pos
        for it in self._items:
            it.update_metrics(self._px_per_sec, self._scene_width())
        # playhead x
        self._update_playhead_x(self._current_ms if hasattr(self, "_current_ms") else 0)

    def set_playhead_ms(self, ms: int):
        self._current_ms = max(0, int(ms))
        self._update_playhead_x(self._current_ms)

    def _update_playhead_x(self, ms: int):
        x = (ms / 1000.0) * self._px_per_sec
        self._playhead.setLine(x, 0, x, self._height)

    def set_clips(self, items: List[Dict]):
        """
        items: [{start:sec, duration:sec, label:str, color:"#RRGGBB"}, ...]
        """
        # purge anciens items clips
        for it in self._items:
            self._scene.removeItem(it)
        self._items.clear()
        self._models = list(items)

        lane_y = 50.0
        for idx, vm in enumerate(self._models):
            it = ClipItem(vm, self._px_per_sec, self._scene_width(), lane_y)
            self._scene.addItem(it)
            # Naïf : on empile verticalement si plusieurs (optionnel)
            lane_y += 42.0

            # texte du clip (optionnel : simple)
            label = vm.get("label", "")
            if label:
                text_color = QColor(20, 20, 20)
                pen = QPen(text_color)
                text_item = self._scene.addText(label)
                text_item.setDefaultTextColor(text_color)
                text_item.setPos(it.pos().x() + 6, it.pos().y() + 8)
                text_item.setZValue(20)
                # on « accroche » le label visuellement : on recalcule à chaque move
                def _sync_label(new_start_s: float, t_item=text_item, item_ref=it):
                    t_item.setPos(item_ref.pos().x() + 6, item_ref.pos().y() + 8)
                it.moved.connect(_sync_label)

            # propager mouvement vers le monde extérieur
            def _emit_moved(new_start_s: float, index=idx):
                self.clipMoved.emit(index, new_start_s)
            it.moved.connect(_emit_moved)

            self._items.append(it)

    # ---- interactions ----
    def mousePressEvent(self, e):
        pos_scene = self.mapToScene(e.pos())
        # si on clique sur le fond (pas un clip), on cherche
        if not self.itemAt(e.pos()):
            ms = int(max(0.0, pos_scene.x() / self._px_per_sec) * 1000.0)
            self.seekRequested.emit(ms)
            self._update_playhead_x(ms)
        super().mousePressEvent(e)
