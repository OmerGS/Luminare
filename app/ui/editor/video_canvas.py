from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QPainter, QPixmap, QImage, QFont, QColor, QPen
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

        # --- Sélection & drag (textes) ---
        self._selected_overlay = None
        self._dragging_text = False
        self._drag_offset = (0, 0)  # offset souris dans le rect du texte
        self._last_overlay_boxes: list[tuple[object, QRect]] = []

        # --- Sélection & drag (images) ---
        self._selected_image_overlay = None
        self._dragging_image = False
        self._drag_offset_img = (0, 0)  # offset souris dans le rect de l'image
        self._last_image_boxes: list[tuple[object, QRect]] = []

        # --- Letterbox rect ---
        self._last_target_rect: QRect | None = None

        # --- cache images ---
        self._image_cache: dict[str, QPixmap] = {}

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

        # reset des hitboxes
        self._last_overlay_boxes.clear()
        self._last_image_boxes.clear()
        self._last_target_rect = None

        # calcule le rect "target" (zone d'affichage vidéo)
        if self._frame:
            pix = QPixmap.fromImage(self._frame)
            target = self._fit_rect_keep_aspect(pix.width(), pix.height(), r)
            self._last_target_rect = target
            p.drawPixmap(target, pix)
        else:
            target = r
            self._last_target_rect = target

        # 1) IMAGES (sous les textes, au-dessus de la vidéo)
        self._paint_image_overlays(p, target)

        # 2) TEXTES
        self._paint_text_overlays(p, target)

        p.end()

    def _fit_rect_keep_aspect(self, w, h, bounds: QRect) -> QRect:
        if w <= 0 or h <= 0:
            return bounds
        scale = min(bounds.width()/w, bounds.height()/h)
        nw, nh = int(w*scale), int(h*scale)
        x = bounds.x() + (bounds.width()-nw)//2
        y = bounds.y() + (bounds.height()-nh)//2
        return QRect(x, y, nw, nh)

    # ---------- IMAGES : affichage + hitbox ----------
    def _paint_image_overlays(self, p: QPainter, target: QRect):
        if not self._project or not getattr(self._project, "image_overlays", None):
            return

        t_sec = self._playhead_ms / 1000.0
        W, H = target.width(), target.height()

        for ov in self._project.image_overlays:
            # actif dans le temps ?
            if not (ov.start <= t_sec < ov.end):
                continue

            path = getattr(ov, "path", None)
            if not path:
                continue

            # charge depuis cache
            pix = self._image_cache.get(path)
            if pix is None:
                tmp = QPixmap(path)
                if tmp.isNull():
                    continue
                pix = tmp
                self._image_cache[path] = pix

            # valeurs par défaut (centré, échelle 1.0)
            if not hasattr(ov, "x"): ov.x = 0.5
            if not hasattr(ov, "y"): ov.y = 0.5
            if not hasattr(ov, "scale"): ov.scale = 1.0

            # taille de base "contain" dans target
            base = self._fit_rect_keep_aspect(pix.width(), pix.height(), target)
            bw, bh = base.width(), base.height()

            # applique l'échelle
            sw = max(1, int(bw * float(ov.scale)))
            sh = max(1, int(bh * float(ov.scale)))

            # position : ov.x/ov.y sont des coords normalisées (0..1) au CENTRE de l'image
            cx = target.x() + int(float(ov.x) * W)
            cy = target.y() + int(float(ov.y) * H)
            rx = cx - sw // 2
            ry = cy - sh // 2

            rect_img = QRect(rx, ry, sw, sh)

            # dessine
            p.drawPixmap(rect_img, pix)

            # si sélectionné, petit cadre
            if ov is self._selected_image_overlay:
                pen = QPen(QColor("yellow"))
                pen.setWidth(2)
                p.setPen(pen); p.setBrush(Qt.NoBrush)
                p.drawRect(rect_img)

            # mémorise la hitbox pour la souris
            self._last_image_boxes.append((ov, rect_img))

    # ---------- TEXTES : affichage + hitbox ----------
    def _paint_text_overlays(self, p: QPainter, target: QRect):
        if not self._project or not getattr(self._project, "text_overlays", None):
            return

        t_sec = self._playhead_ms / 1000.0
        W, H = target.width(), target.height()

        for ov in self._project.text_overlays:
            # defaults pour migration
            if not isinstance(getattr(ov, "x", 0.0), (float, int)):
                ov.x = 0.5
            if not isinstance(getattr(ov, "y", 0.0), (float, int)):
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

            # 1) test d'abord les IMAGES (au-dessus : z-order “interactif”)
            for ov, rect in reversed(self._last_image_boxes):
                if rect.contains(pt):
                    self._selected_image_overlay = ov
                    self._dragging_image = True
                    self._drag_offset_img = (pt.x() - rect.x(), pt.y() - rect.y())
                    # désélectionne le texte si besoin
                    self._selected_overlay = None
                    self.overlaySelected.emit(None)
                    self.update()
                    return

            # 2) sinon, TEST LES TEXTES
            for ov, rect in reversed(self._last_overlay_boxes):
                if rect.contains(pt):
                    self._selected_overlay = ov
                    self.overlaySelected.emit(ov)
                    self._dragging_text = True
                    self._drag_offset = (pt.x() - rect.x(), pt.y() - rect.y())
                    # désélectionne l'image
                    self._selected_image_overlay = None
                    self.update()
                    return

            # clic à côté -> tout désélectionner
            self._selected_overlay = None
            self._selected_image_overlay = None
            self.overlaySelected.emit(None)
            self.update()

        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        # drag d'IMAGE
        if self._dragging_image and self._selected_image_overlay and self._last_target_rect:
            ov = self._selected_image_overlay
            target = self._last_target_rect
            W, H = target.width(), target.height()

            # retrouve la taille actuelle de l'image pour centrer pendant le drag
            # reconstitue le rect comme dans _paint_image_overlays (sans dessiner)
            # taille base
            path = getattr(ov, "path", None)
            pix = self._image_cache.get(path)
            if pix is None and path:
                tmp = QPixmap(path)
                if not tmp.isNull():
                    pix = tmp
                    self._image_cache[path] = pix
            if pix:
                base = self._fit_rect_keep_aspect(pix.width(), pix.height(), target)
                bw, bh = base.width(), base.height()
            else:
                bw, bh = target.width(), target.height()

            scale = float(getattr(ov, "scale", 1.0))
            sw = max(1, int(bw * scale))
            sh = max(1, int(bh * scale))

            px = int(e.position().x() - self._drag_offset_img[0])
            py = int(e.position().y() - self._drag_offset_img[1])

            # centre à partir du coin haut-gauche calculé
            cx = px + sw // 2
            cy = py + sh // 2

            # clamp centre dans la zone vidéo
            cx = max(target.x(), min(cx, target.right()))
            cy = max(target.y(), min(cy, target.bottom()))

            # convertit en coords normalisées
            new_x = (cx - target.x()) / float(W)
            new_y = (cy - target.y()) / float(H)
            ov.x = max(0.0, min(new_x, 1.0))
            ov.y = max(0.0, min(new_y, 1.0))
            self.update()

        # drag de TEXTE
        if self._dragging_text and self._selected_overlay and self._last_target_rect:
            target = self._last_target_rect
            W, H = target.width(), target.height()
            px = int(e.position().x() - self._drag_offset[0])
            py = int(e.position().y() - self._drag_offset[1])

            px = max(target.x(), min(px, target.right()))
            py = max(target.y(), min(py, target.bottom()))

            new_x = (px - target.x()) / float(W)
            new_y = (py - target.y()) / float(H)
            self._selected_overlay.x = max(0.0, min(new_x, 1.0))
            self._selected_overlay.y = max(0.0, min(new_y, 1.0))
            self.update()

        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._dragging_text = False
            self._dragging_image = False
        super().mouseReleaseEvent(e)

    # --- zoom sur l’image sélectionnée (Ctrl + molette) ---
    def wheelEvent(self, e):
        if self._selected_image_overlay is None:
            return super().wheelEvent(e)

        if not (e.modifiers() & Qt.ControlModifier):
            # molette normale = comportement par défaut (scroll)
            return super().wheelEvent(e)

        # Ctrl + molette => zoom image sélectionnée
        delta = e.angleDelta().y()
        ov = self._selected_image_overlay
        cur = float(getattr(ov, "scale", 1.0))
        # facteur de zoom doux
        factor = 1.0 + (0.1 if delta > 0 else -0.1)
        new_scale = max(0.1, min(cur * factor, 5.0))
        ov.scale = new_scale
        self.update()
        e.accept()
