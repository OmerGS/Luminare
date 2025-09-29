# app/ui/timeline.py
from PySide6.QtCore import Qt, Signal, QSize, QRect
from PySide6.QtGui import QPainter, QPen, QBrush
from PySide6.QtWidgets import QWidget, QScrollArea
import numpy as np

class TimelineWidget(QWidget):
    seekRequested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration_ms = 0
        self._position_ms = 0
        self._px_per_sec = 80
        self._drag = False
        self._wave_env = None         # np.ndarray shape [N] float32 (0..1)
        self._wave_sps = 0            # samples par seconde pour l’enveloppe
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

    def set_waveform(self, env: np.ndarray, samples_per_second: int):
        self._wave_env = env.astype(np.float32) if env is not None else None
        self._wave_sps = int(samples_per_second or 0)
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

    # paint
    def paintEvent(self, _):
        p = QPainter(self); r = self.rect()
        p.fillRect(r, QBrush(self.palette().base()))
        alt = QBrush(self.palette().alternateBase())
        for i in range(0, r.width(), self._px_per_sec):
            if (i // self._px_per_sec) % 2 == 0:
                p.fillRect(i, 0, self._px_per_sec, r.height(), alt)

        # règle
        p.setPen(QPen(self.palette().mid().color(), 1)); p.drawLine(0, 30, r.right(), 30)
        p.setPen(self.palette().text().color())
        for s in range(int(self._duration_ms/1000)+1):
            x = self._s_to_x(s)
            p.drawLine(x, 30, x, 18)
            step = max(1, self._px_per_sec // 4)
            for k in range(1, 4): p.drawLine(x + k*step, 30, x + k*step, 24)
            if s % 5 == 0: p.drawText(x + 3, 14, f"{s}s")

        # zone contenu
        content_top = 40; content_h = r.height() - content_top - 10
        p.setPen(QPen(self.palette().mid().color(), 1, Qt.DashLine))
        p.drawRect(0, content_top, r.width()-1, content_h)

        # ------- WAVeform (aire) -------
        if self._wave_env is not None and self._wave_env.size and self._wave_sps > 0 and self._duration_ms > 0:
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(self.palette().midlight()))
            # mapping: 1 échantillon d'enveloppe = (1 / _wave_sps) seconde
            sec_per_sample = 1.0 / float(self._wave_sps)
            px_per_sample = self._px_per_sec * sec_per_sample
            y_base = content_top + content_h // 2
            amp = (content_h // 2) - 2

            # Dessin en colonnes (rapide) : 1 rect par sample visible
            # On borne à la zone visible (optimisation simple)
            from_x = 0
            to_x   = r.width()
            first_i = max(0, int(from_x / px_per_sample) - 1)
            last_i  = min(self._wave_env.size, int(to_x / px_per_sample) + 2)

            for i in range(first_i, last_i):
                x = int(i * px_per_sample)
                v = float(self._wave_env[i])  # 0..1
                h = int(v * amp)
                if h <= 0: 
                    continue
                p.drawRect(QRect(x, y_base - h, max(1, int(px_per_sample)), h*2))

        # playhead
        x_ph = self._ms_to_x(self._position_ms)
        p.setPen(QPen(Qt.red, 2)); p.drawLine(x_ph, 0, x_ph, r.height())

    # interaction
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = True
            ms = self._x_to_ms(int(e.position().x()))
            self._position_ms = ms; self.seekRequested.emit(ms); self.update()
            e.accept()
        else: super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag and (e.buttons() & Qt.LeftButton):
            ms = self._x_to_ms(int(e.position().x()))
            self._position_ms = ms; self.seekRequested.emit(ms); self.update()
            e.accept()
        else: super().mouseMoveEvent(e)

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
