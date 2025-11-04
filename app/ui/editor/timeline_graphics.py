from __future__ import annotations
from typing import List, Dict
import json

from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QCursor
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsLineItem
)

from ui.components.assets_panel import MIME_IMAGE_ASSET, MIME_VIDEO_ASSET


# --------------------------
#  Ruler (règle temporelle)
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

        p.setPen(QColor(60, 60, 60))
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
#  Clip vidéo redimensionnable
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

        # état du drag
        self._dragging_handle = None
        self._drag_start_x = 0.0
        self._orig_rect = None
        self._orig_x = 0.0
        self._orig_in_s = float(self.model.get("in_s", 0.0))
        self._orig_start = float(self.model.get("start", 0.0))

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
        self._orig_x = float(self.x())
        # snapshot des valeurs de modèle pour éviter l'accumulation
        self._orig_in_s = float(self.model.get("in_s", 0.0))
        self._orig_start = float(self.model.get("start", 0.0))

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._dragging_handle:
            return super().mouseMoveEvent(event)

        delta_x = float(event.scenePos().x() - self._drag_start_x)
        min_w_px = 10.0  # largeur mini visuelle

        if self._dragging_handle == "left":
            # largeur et x basés sur les originaux (pas cumulatif)
            new_w = float(self._orig_rect.width() - delta_x)
            if new_w < min_w_px:
                delta_x = self._orig_rect.width() - min_w_px
                new_w = min_w_px

            new_x = self._orig_x + delta_x
            if new_x < 0.0:
                delta_x -= new_x
                new_x = 0.0
                new_w = float(self._orig_rect.width() - delta_x)

            self.setRect(0, 0, new_w, 36.0)
            self.setX(new_x)

            # mise à jour logique à partir des originaux
            delta_s = delta_x / float(self._px)
            self.model["in_s"] = max(0.0, self._orig_in_s + delta_s)
            self.model["start"] = max(0.0, self._orig_start + delta_s)
            self.model["duration"] = max(0.1, new_w / self._px)

        elif self._dragging_handle == "right":
            new_w = float(self._orig_rect.width() + delta_x)
            if new_w < min_w_px:
                new_w = min_w_px
            max_w = max(min_w_px, self._scene_w - self._orig_x)
            if new_w > max_w:
                new_w = max_w

            self.setRect(0, 0, new_w, 36.0)
            self.model["duration"] = max(0.1, new_w / self._px)

        self._update_handles()
        self.resized.emit(self.model.get("start", 0.0), self.model.get("in_s", 0.0), self.model.get("duration", 0.0))

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
#  Timeline à 3 pistes
# --------------------------

class TimelineView(QGraphicsView):
    """Timeline graphique unique avec 3 pistes : Vidéo / Images / Textes."""
    seekRequested = Signal(int)             # ms
    clipMoved = Signal(int, float)          # index, new_start_s (vidéo)
    clipDropRequested = Signal(str, float)  # path, start_s (vidéo)
    imageDropRequested = Signal(str, float) # path, start_s (images)
    clipResized = Signal(int, float, float, float)  # idx, start_s, in_s, duration (vidéo)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHints(self.renderHints() | QPainter.Antialiasing)
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setAcceptDrops(True)

        self._px_per_sec = 80
        self._height = 230.0   # un peu plus haut : 3 pistes
        self._total_ms = 0

        # modèles par piste
        self._models_video: List[Dict] = []
        self._models_images: List[Dict] = []
        self._models_texts: List[Dict] = []

        # items graphiques
        self._items_video = []
        self._items_images = []
        self._items_texts = []
        self._label_items = []

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._rebuild_scene_rect()
        self._ruler = RulerItem(self._px_per_sec, self._scene_width())
        self._scene.addItem(self._ruler)

        # fonds de pistes
        self._lane_bg_video  = QGraphicsRectItem(0, 32,              self._scene_width(), 40)
        self._lane_bg_images = QGraphicsRectItem(0, 32 + 44,         self._scene_width(), 40)
        self._lane_bg_texts  = QGraphicsRectItem(0, 32 + 44 * 2,     self._scene_width(), 40)
        for bg in (self._lane_bg_video, self._lane_bg_images, self._lane_bg_texts):
            bg.setBrush(QBrush(QColor(250, 250, 250)))
            bg.setPen(QPen(QColor(220, 220, 220), 1, Qt.DashLine))
            bg.setZValue(-5)
            self._scene.addItem(bg)

        self._playhead = QGraphicsLineItem()
        self._playhead.setPen(QPen(QColor("red"), 2))
        self._playhead.setZValue(100)
        self._scene.addItem(self._playhead)
        self._update_playhead_x(0)

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
        # Ajuste la largeur des 3 pistes
        self._lane_bg_video.setRect(0, 32, self._scene_width(), 40)
        self._lane_bg_images.setRect(0, 32 + 44, self._scene_width(), 40)
        self._lane_bg_texts.setRect(0, 32 + 44 * 2, self._scene_width(), 40)
        # resize des items vidéo (images/textes sont de simples rects)
        for it in self._items_video:
            it.update_metrics(self._px_per_sec, self._scene_width())

    def set_zoom(self, px_per_sec: int):
        self._px_per_sec = max(10, int(px_per_sec))
        self._ruler.set_px_per_sec(self._px_per_sec)
        self.set_total_duration(self._total_ms)
        for it in self._items_video:
            it.update_metrics(self._px_per_sec, self._scene_width())
        self._update_playhead_x(getattr(self, "_current_ms", 0))

    def set_playhead_ms(self, ms: int):
        self._current_ms = max(0, int(ms))
        self._update_playhead_x(self._current_ms)

    def _update_playhead_x(self, ms: int):
        x = (ms / 1000.0) * self._px_per_sec
        self._playhead.setLine(x, 0, x, self._height)

    # ---- API 3 pistes ----
    def set_tracks(self, video_items: List[Dict], image_items: List[Dict], text_items: List[Dict]):
        # purge anciens items
        for lst in (self._items_video, self._items_images, self._items_texts, self._label_items):
            for it in lst:
                self._scene.removeItem(it)
            lst.clear()

        self._models_video = list(video_items or [])
        self._models_images = list(image_items or [])
        self._models_texts = list(text_items or [])

        # Y de base pour chaque piste
        y_video = 50.0
        y_images = 50.0 + 44.0
        y_texts = 50.0 + 44.0 * 2

        # --- Piste VIDÉO (items redimensionnables) ---
        for idx, vm in enumerate(self._models_video):
            vm = dict(vm)
            vm.setdefault("color", "#7fb3ff")
            it = ClipItem(vm, self._px_per_sec, self._scene_width(), y_video)
            self._scene.addItem(it)

            # label
            label = vm.get("label", "")
            if label:
                t = self._scene.addText(label)
                t.setDefaultTextColor(QColor(20, 20, 20))
                t.setPos(it.pos().x() + 6, it.pos().y() + 8)
                t.setZValue(20)
                self._label_items.append(t)
                def _sync_label(*_, t_item=t, item_ref=it):
                    if hasattr(t_item, "setPos"):
                        t_item.setPos(item_ref.pos().x() + 6, item_ref.pos().y() + 8)
                it.resized.connect(_sync_label)

            # resize -> remonter vers MainWindow
            def _forward_resize(*_, index=idx, item=it):
                self.clipResized.emit(
                    index,
                    float(item.model.get("start", 0.0)),
                    float(item.model.get("in_s", 0.0)),
                    float(item.model.get("duration", 0.0)),
                )
            it.resized.connect(_forward_resize)

            self._items_video.append(it)

        # --- Piste IMAGES ---
        for vm in self._models_images:
            vm = dict(vm)
            vm.setdefault("color", "#9be7a5")
            it = QGraphicsRectItem()
            w = max(2.0, float(vm["duration"]) * self._px_per_sec)
            x = float(vm["start"]) * self._px_per_sec
            it.setRect(x, y_images, w, 36.0)
            it.setBrush(QBrush(QColor(vm["color"])))
            it.setPen(QPen(QColor(40, 40, 40), 1))
            self._scene.addItem(it)
            self._items_images.append(it)

            label = vm.get("label", "")
            if label:
                t = self._scene.addText(label)
                t.setDefaultTextColor(QColor(20, 20, 20))
                t.setPos(x + 6, y_images + 8)
                t.setZValue(20)
                self._label_items.append(t)

        # --- Piste TEXTES ---
        for vm in self._models_texts:
            vm = dict(vm)
            vm.setdefault("color", "#d4b5ff")
            it = QGraphicsRectItem()
            w = max(2.0, float(vm["duration"]) * self._px_per_sec)
            x = float(vm["start"]) * self._px_per_sec
            it.setRect(x, y_texts, w, 36.0)
            it.setBrush(QBrush(QColor(vm["color"])))
            it.setPen(QPen(QColor(40, 40, 40), 1))
            self._scene.addItem(it)
            self._items_texts.append(it)

            label = vm.get("label", "")
            if label:
                t = self._scene.addText(label)
                t.setDefaultTextColor(QColor(20, 20, 20))
                t.setPos(x + 6, y_texts + 8)
                t.setZValue(20)
                self._label_items.append(t)

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
        start_s = self._scene_pos_to_seconds(e)
        if md.hasFormat(MIME_VIDEO_ASSET):
            data = json.loads(bytes(md.data(MIME_VIDEO_ASSET)).decode("utf-8"))
            path = data.get("path")
            if path:
                self.clipDropRequested.emit(path, start_s)
            e.acceptProposedAction()
            return
        if md.hasFormat(MIME_IMAGE_ASSET):
            data = json.loads(bytes(md.data(MIME_IMAGE_ASSET)).decode("utf-8"))
            path = data.get("path")
            if path:
                self.imageDropRequested.emit(path, start_s)
            e.acceptProposedAction()
            return
        e.ignore()
