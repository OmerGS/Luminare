# app/ui/video_canvas.py
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QPixmap, QImage, QFont, QColor, QPen, QBrush
from PySide6.QtWidgets import QWidget, QSizePolicy
from core.project import Project

class VideoCanvas(QWidget):
    """
    Affiche la frame vidéo courante (QImage) + dessine l'overlay (titres) dans le même paintEvent.
    Ça rend la preview vraiment 'live' et corrige les soucis d'empilement avec QVideoWidget.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._frame: QImage | None = None
        self._project: Project | None = None
        self._playhead_ms: int = 0

    # API
    def set_frame(self, img: QImage):
        # On stocke la dernière frame et on repaint
        self._frame = img.copy() if not img.isNull() else None
        self.update()

    def set_project(self, proj: Project | None):
        self._project = proj
        self.update()

    def set_playhead_ms(self, ms: int):
        self._playhead_ms = max(0, int(ms))
        # redraw overlay même si la frame ne change pas
        self.update()

    # rendering
    def paintEvent(self, _):
        p = QPainter(self)

        try:
            p.setRenderHint(QPainter.SmoothPixmapTransform, True)
            r = self.rect()

            # fond
            p.fillRect(r, Qt.black)  # <-- fix : pas de palette().black()

            # frame (letterbox/contain)
            if self._frame:
                pix = QPixmap.fromImage(self._frame)
                target = self._fit_rect_keep_aspect(pix.width(), pix.height(), r)
                p.drawPixmap(target, pix)

                # overlay titres dans le target (coords locales)
                self._paint_overlay(p, target)
            else:
                # pas de frame pour l'instant
                pass
        finally:
            # en cas d'exception, on ferme proprement le painter
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
        if not self._project or not self._project.text_overlays:
            return
        t_sec = self._playhead_ms / 1000.0

        # système de coordonnées : on mappe w/h 'vidéo' → target
        W, H = target.width(), target.height()

        for ov in self._project.text_overlays:
            if not (ov.start <= t_sec <= ov.end):
                continue

            # taille police relative
            font = QFont()
            # 48 pour 1080p ≈ 4.4% de la hauteur
            pt = max(10, int(ov.fontsize * (H / 1080.0)))
            font.setPointSize(pt)
            p.setFont(font)

            text = ov.text or ""
            metrics = p.fontMetrics()
            tw = metrics.horizontalAdvance(text)
            th = metrics.height()

            # positions 'courantes' supportées
            x = target.x() + (W - tw)//2 if "(w-text_w)/2" in ov.x else target.x() + 20
            y = target.y() + int(H*0.1) if "h*0.1" in ov.y else target.y() + 40

            # box
            if ov.box:
                p.setPen(Qt.NoPen)
                col = QColor("black")
                try:
                    if "@" in ov.boxcolor:
                        alpha = float(ov.boxcolor.split("@")[1])
                        col.setAlphaF(alpha)
                    else:
                        col.setAlphaF(0.5)
                except Exception:
                    col.setAlphaF(0.5)
                p.setBrush(QBrush(col))
                pad = max(4, ov.boxborderw // 2)
                p.drawRect(x - pad, y - th - pad, tw + pad*2, th + pad*2)

            # text
            p.setPen(QPen(QColor(ov.fontcolor)))
            p.drawText(x, y, text)
