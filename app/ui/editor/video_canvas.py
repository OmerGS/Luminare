from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QPainter, QPixmap, QImage, QFont, QColor, QPen, QBrush
from PySide6.QtWidgets import QWidget, QSizePolicy
from core.project import Project

class VideoCanvas(QWidget):
    overlaySelected = Signal(object)  # émet le TextOverlay sélectionné (ou None)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        self._frame: QImage | None = None
        self._project: Project | None = None
        self._playhead_ms: int = 0

        self._selected_overlay = None
        self._dragging = False
        self._drag_offset = (0, 0)  # offset souris dans le rect du texte
        self._last_overlay_boxes: list[tuple[object, QRect]] = []
        self._last_target_rect: QRect | None = None  # rect de la vidéo (letterbox)

    # --- API ---
    def set_frame(self, img: QImage):
        self._frame = img if (img is not None and not img.isNull()) else None
        self.update()

    def set_project(self, proj: Project | None):
        self._project = proj
        self.update()

    def set_playhead_ms(self, ms: int):
        self._playhead_ms = max(0, int(ms))
        self.update()

    # --- rendu ---
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        r = self.rect()
        p.fillRect(r, Qt.black)

        self._last_overlay_boxes.clear()
        self._last_target_rect = None

        if self._frame:
            pix = QPixmap.fromImage(self._frame)
            target = self._fit_rect_keep_aspect(pix.width(), pix.height(), r)
            self._last_target_rect = target
            p.drawPixmap(target, pix)
            self._paint_overlay(p, target)

        p.end()

    def _fit_rect_keep_aspect(self, w, h, bounds: QRect) -> QRect:
        if w <= 0 or h <= 0:
            return bounds
        scale = min(bounds.width()/w, bounds.height()/h)
        nw, nh = int(w*scale), int(h*scale)
        x = bounds.x() + (bounds.width()-nw)//2
        y = bounds.y() + (bounds.height()-nh)//2
        return QRect(x, y, nw, nh)

    def _paint_overlay(self, p: QPainter, target: QRect):
        """Dessine les titres et enregistre leurs zones cliquables."""
        if not self._project or not getattr(self._project, "text_overlays", None):
            return

        t_sec = self._playhead_ms / 1000.0
        W, H = target.width(), target.height()

        for ov in self._project.text_overlays:
            # migration douce : si x/y ne sont pas numériques, on fallback
            if not isinstance(getattr(ov, "x", 0.0), (float, int)) or not isinstance(getattr(ov, "y", 0.0), (float, int)):
                ov.x = 0.5
                ov.y = 0.1

            if not (ov.start <= t_sec <= ov.end):
                continue

            font = QFont()
            pt = max(10, int(ov.fontsize * (H / 1080.0)))
            font.setPointSize(pt)
            p.setFont(font)

            text = ov.text or ""
            metrics = p.fontMetrics()
            tw = metrics.horizontalAdvance(text)
            th = metrics.height()

            x = target.x() + int(float(ov.x) * W)
            y = target.y() + int(float(ov.y) * H)

            rect_text = QRect(x, y - th, tw, th)
            self._last_overlay_boxes.append((ov, rect_text))

            # box optionnelle
            if getattr(ov, "box", False):
                col = QColor("black"); col.setAlphaF(0.5)
                p.fillRect(rect_text.adjusted(-4, -4, 4, 4), col)

            # texte
            p.setPen(QPen(QColor(getattr(ov, "fontcolor", "white"))))
            p.drawText(rect_text.bottomLeft(), text)

            # highlight si sélectionné
            if ov is self._selected_overlay:
                pen = QPen(QColor("cyan")); pen.setWidth(2)
                p.setPen(pen); p.setBrush(Qt.NoBrush)
                p.drawRect(rect_text.adjusted(-6, -6, 6, 6))

    # --- interaction ---
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            pt = e.position().toPoint()
            for ov, rect in self._last_overlay_boxes:
                if rect.contains(pt):
                    self._selected_overlay = ov
                    self.overlaySelected.emit(ov)
                    self._dragging = True
                    self._drag_offset = (pt.x() - rect.x(), pt.y() - rect.y())
                    self.update()
                    return
            # clic à côté -> désélection
            self._selected_overlay = None
            self.overlaySelected.emit(None)
            self.update()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._dragging and self._selected_overlay and self._last_target_rect:
            target = self._last_target_rect
            W, H = target.width(), target.height()
            px = int(e.position().x() - self._drag_offset[0])
            py = int(e.position().y() - self._drag_offset[1])

            # clamp dans le target
            px = max(target.x(), min(px, target.right()))
            py = max(target.y(), min(py, target.bottom()))

            # conversion en coordonnées normalisées
            new_x = (px - target.x()) / float(W)
            new_y = (py - target.y()) / float(H)
            self._selected_overlay.x = max(0.0, min(new_x, 1.0))
            self._selected_overlay.y = max(0.0, min(new_y, 1.0))
            self.update()
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(e)
