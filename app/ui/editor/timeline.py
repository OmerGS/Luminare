# app/ui/timeline.py
from PySide6.QtCore import Qt, Signal, QSize, QRect
from PySide6.QtGui import QPainter, QPen, QBrush, QFontMetrics, QCursor
from PySide6.QtWidgets import QWidget, QScrollArea, QToolTip

class TimelineWidget(QWidget):
    seekRequested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration_ms = 0
        self._position_ms = 0
        self._px_per_sec = 80
        self._drag = False
        self._overlays = []  # list of (start_sec, end_sec)
        self.setMinimumHeight(160)
        self.setMouseTracking(True)
        self.setAutoFillBackground(True)
        self._update_width()

    # API
    def set_duration(self, ms: int):
        self._duration_ms = max(0, ms)
        self._update_width(); self.update()

    def set_position(self, ms: int):
        self._position_ms = max(0, min(ms, self._duration_ms))
        if not self._drag: self.update()

    def set_zoom(self, px_per_sec: int):
        self._px_per_sec = max(10, min(int(px_per_sec), 400))
        self._update_width(); self.update()

    def set_overlays(self, items):
        """
        items peut être :
          - [(start, end)]                     # rétro-compat
          - [(start, end, label)]             # tuple avec label
          - [{"start":..., "end":..., "label": "..."}]
        """
        norm = []
        for it in items:
            if isinstance(it, dict):
                s = float(it.get("start", 0.0)); e = float(it.get("end", 0.0))
                label = str(it.get("label", "Titre"))
            elif isinstance(it, (list, tuple)):
                if len(it) == 2:
                    s, e = float(it[0]), float(it[1]); label = "Titre"
                else:
                    s, e, label = float(it[0]), float(it[1]), str(it[2])
            else:
                continue
            norm.append({"s": max(0.0, s), "e": max(0.0, e), "label": label})
        self._overlays = norm
        self.update()

    # geometry
    def _update_width(self):
        secs = max(1, int(self._duration_ms / 1000))
        width = max(1000, secs * self._px_per_sec)
        self.setFixedSize(width, 160)

    def sizeHint(self): return self.size()

    # convert
    def _s_to_x(self, s: float) -> int: return int(s * self._px_per_sec)
    def _ms_to_x(self, ms: int) -> int: return self._s_to_x(ms / 1000.0)
    def _x_to_ms(self, x: int) -> int:
        s = max(0.0, x / float(self._px_per_sec)); return int(s * 1000)

    def paintEvent(self, _):
        p = QPainter(self); r = self.rect()
        p.fillRect(r, QBrush(self.palette().base()))
        alt = QBrush(self.palette().alternateBase())
        for i in range(0, r.width(), self._px_per_sec):
            if (i // self._px_per_sec) % 2 == 0:
                p.fillRect(i, 0, self._px_per_sec, r.height(), alt)

        # règle
        p.setPen(QPen(self.palette().mid().color(), 1))
        p.drawLine(0, 30, r.right(), 30)
        p.setPen(self.palette().text().color())
        for s in range(int(self._duration_ms/1000)+1):
            x = self._s_to_x(s)
            p.drawLine(x, 30, x, 18)
            step = max(1, self._px_per_sec // 4)
            for k in range(1, 4):
                p.drawLine(x + k*step, 30, x + k*step, 24)
            if s % 5 == 0:
                p.drawText(x + 3, 14, f"{s}s")

        # zone contenu
        content_top = 40; content_h = r.height() - content_top - 10
        p.setPen(QPen(self.palette().mid().color(), 1, Qt.DashLine))
        p.drawRect(0, content_top, r.width()-1, content_h)

        # --- lane overlays (barres + labels) ---
        if self._overlays:
            lane_h = max(16, content_h // 6)
            lane_y = content_top + 6
            for ov in self._overlays:
                s, e = ov["s"], ov["e"]
                if e < s: s, e = e, s
                x1 = self._s_to_x(s); x2 = self._s_to_x(e)
                w = max(2, x2 - x1)

                # bande
                p.setPen(Qt.NoPen)
                p.setBrush(QBrush(self.palette().midlight()))
                p.drawRect(QRect(x1, lane_y, w, lane_h))

                # label (ellipsisé si trop long)
                label_rect = QRect(x1+4, lane_y, max(0, w-8), lane_h)
                if label_rect.width() > 12:
                    fm = QFontMetrics(p.font())
                    text = fm.elidedText(ov["label"], Qt.ElideRight, label_rect.width())
                    p.setPen(self.palette().text().color())
                    baseline = label_rect.y() + (label_rect.height() + fm.ascent() - fm.descent())//2
                    p.drawText(label_rect.x(), baseline, text)

        # playhead
        x_ph = self._ms_to_x(self._position_ms)
        p.setPen(QPen(Qt.red, 2))
        p.drawLine(x_ph, 0, x_ph, r.height())

    # (ajoute un petit tooltip pratique)
    def mouseMoveEvent(self, e):
        pos_x = int(e.position().x())
        s_at = pos_x / float(self._px_per_sec)

        # position globale de la souris  (Qt6) ; fallback Qt5
        try:
            pos_global = e.globalPosition().toPoint()
        except AttributeError:
            pos_global = e.globalPos()

        for ov in self._overlays:
            s, e_ = min(ov["s"], ov["e"]), max(ov["s"], ov["e"])
            if s <= s_at <= e_:
                QToolTip.showText(
                    pos_global,
                    f"{ov['label']}  [{s:.2f}s → {e_:.2f}s]",
                    self
                )
                break
        else:
            QToolTip.hideText()

        super().mouseMoveEvent(e)



    # interaction
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = True
            ms = self._x_to_ms(int(e.position().x()))
            self._position_ms = ms; self.seekRequested.emit(ms); self.update()
            e.accept()
        else: super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        if self._drag and e.button() == Qt.LeftButton:
            self._drag = False; e.accept()
        else: super().mouseReleaseEvent(e)

    def wheelEvent(self, e):
        if e.modifiers() & Qt.ControlModifier:
            delta = e.angleDelta().y()
            self.set_zoom(self._px_per_sec + (10 if delta > 0 else -10))
            e.accept()
        else: super().wheelEvent(e)

class TimelineScroll(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.timeline = TimelineWidget()
        self.setWidget(self.timeline)
