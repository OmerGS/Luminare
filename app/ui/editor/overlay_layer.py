from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import QWidget
from core.project import Project

class OverlayLayer(QWidget):
    """
    Calque au-dessus de la vidéo. Affiche les TextOverlay actifs en fonction
    du playhead courant.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project: Project | None = None
        self._playhead_ms: int = 0
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def set_project(self, project: Project):
        self._project = project
        self.update()

    def set_playhead_ms(self, ms: int):
        self._playhead_ms = max(0, int(ms))
        self.update()

    def paintEvent(self, _):
        if not self._project: return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        t_sec = self._playhead_ms / 1000.0
        for ov in self._project.text_overlays:
            if not (ov.start <= t_sec <= ov.end):
                continue

            font = QFont()
            font.setPointSize(int(ov.fontsize * 0.8))
            p.setFont(font)

            text = ov.text
            metrics = p.fontMetrics()
            tw = metrics.horizontalAdvance(text)
            th = metrics.height()

            W = self.width(); H = self.height()
            x = (W - tw)//2 if "(w-text_w)/2" in ov.x else 20
            y = int(H*0.1) if "h*0.1" in ov.y else 40

            if ov.box:
                p.setPen(Qt.NoPen)
                col = QColor("black")
                # parse alpha style "black@0.5"
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

            p.setPen(QPen(QColor(ov.fontcolor)))
            p.drawText(x, y, text)
