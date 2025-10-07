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
        self._selected_type = None      # "text" / "image"
        self._img_cache = {}            # path -> QPixmap
        self._resize_handle = None      # "se" etc.


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
        self._resize_handle_rect = None  # reset du handle à chaque frame

        if self._frame:
            pix = QPixmap.fromImage(self._frame)
            target = self._fit_rect_keep_aspect(pix.width(), pix.height(), r)
            self._last_target_rect = target
            p.drawPixmap(target, pix)

            # Dessiner indépendamment (pas de return global)
            self._paint_text_overlays(p, target)
            self._paint_image_overlays(p, target)

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
        """
        Dessine d'abord les images, puis les titres,
        et enregistre des zones cliquables homogènes (obj, rect, kind).
        """
        if not self._project:
            return

        t_sec = self._playhead_ms / 1000.0
        W, H = target.width(), target.height()

        # --- 1) IMAGES ---
        for img in getattr(self._project, "image_overlays", []) or []:
            if not (img.start <= t_sec <= img.end):
                continue
            self._draw_image_overlay(p, target, img)  # cette méthode ajoute déjà (obj, rect, "image")

        # --- 2) TITRES ---
        for to in getattr(self._project, "text_overlays", []) or []:
            if not (to.start <= t_sec <= to.end):
                continue

            # normalise x/y si besoin (coordonnées 0..1)
            if not isinstance(getattr(to, "x", 0.5), (int, float)):
                to.x = 0.5
            if not isinstance(getattr(to, "y", 0.1), (int, float)):
                to.y = 0.1

            font = QFont()
            pt = max(10, int(to.fontsize * (H / 1080.0)))
            font.setPointSize(pt)
            p.setFont(font)

            text = to.text or ""
            fm = p.fontMetrics()
            tw = fm.horizontalAdvance(text)
            th = fm.height()

            x = target.x() + int(float(to.x) * W)
            y = target.y() + int(float(to.y) * H)
            rect_text = QRect(x, y - th, tw, th)

            # zone cliquable homogène: (obj, rect, "text")
            self._last_overlay_boxes.append((to, rect_text, "text"))

            # box optionnelle
            if getattr(to, "box", False):
                col = QColor("black"); col.setAlphaF(0.5)
                p.fillRect(rect_text.adjusted(-4, -4, 4, 4), col)

            # texte
            p.setPen(QPen(QColor(getattr(to, "fontcolor", "white"))))
            p.drawText(rect_text.bottomLeft(), text)

            # highlight sélection
            if to is self._selected_overlay:
                pen = QPen(QColor("cyan")); pen.setWidth(2)
                p.setPen(pen); p.setBrush(Qt.NoBrush)
                p.drawRect(rect_text.adjusted(-6, -6, 6, 6))


    def _paint_text_overlays(self, p: QPainter, target: QRect):
        if not self._project:
            return
        overlays = getattr(self._project, "text_overlays", [])
        if not overlays:
            return

        t_sec = self._playhead_ms / 1000.0
        W, H = target.width(), target.height()

        for ov in overlays:
            if not (ov.start <= t_sec <= ov.end):
                continue

            # Sécurise x/y normalisés
            if not isinstance(getattr(ov, "x", 0.5), (int, float)):
                ov.x = 0.5
            if not isinstance(getattr(ov, "y", 0.1), (int, float)):
                ov.y = 0.1

            font = QFont()
            pt = max(10, int(ov.fontsize * (H / 1080.0)))
            font.setPointSize(pt)
            p.setFont(font)

            text = ov.text or ""
            fm = p.fontMetrics()
            tw = fm.horizontalAdvance(text)
            th = fm.height()

            x = target.x() + int(float(ov.x) * W)
            y = target.y() + int(float(ov.y) * H)

            rect_text = QRect(x, y - th, tw, th)
            # always triplet: (object, rect, kind)
            self._last_overlay_boxes.append((ov, rect_text, "text"))

            if getattr(ov, "box", False):
                col = QColor("black"); col.setAlphaF(0.5)
                p.fillRect(rect_text.adjusted(-4, -4, 4, 4), col)

            p.setPen(QPen(QColor(getattr(ov, "fontcolor", "white"))))
            p.drawText(rect_text.bottomLeft(), text)

            if ov is self._selected_overlay:
                pen = QPen(QColor("cyan")); pen.setWidth(2)
                p.setPen(pen); p.setBrush(Qt.NoBrush)
                p.drawRect(rect_text.adjusted(-6, -6, 6, 6))


    def _paint_image_overlays(self, p: QPainter, target: QRect):
        if not self._project:
            return
        items = getattr(self._project, "image_overlays", [])
        if not items:
            return

        t_sec = self._playhead_ms / 1000.0
        W, H = target.width(), target.height()

        for ov in items:
            if not (ov.start <= t_sec <= ov.end):
                continue

            pix = self._img_cache.get(ov.path)
            if pix is None:
                pix = QPixmap(ov.path)
                self._img_cache[ov.path] = pix
            if pix.isNull():
                continue

            # coords/taille normalisées (0..1)
            x = target.x() + int(float(getattr(ov, "x", 0.5)) * W)
            y = target.y() + int(float(getattr(ov, "y", 0.5)) * H)
            w = int(float(getattr(ov, "w", 0.25)) * W)
            h = int(float(getattr(ov, "h", 0.25)) * H)
            rect = QRect(x, y, w, h)

            p.drawPixmap(rect, pix)
            self._last_overlay_boxes.append((ov, rect, "image"))

            if ov is self._selected_overlay:
                pen = QPen(QColor("cyan")); pen.setWidth(2)
                p.setPen(pen); p.setBrush(Qt.NoBrush)
                p.drawRect(rect)
                handle = QRect(rect.right() - 8, rect.bottom() - 8, 8, 8)
                p.fillRect(handle, QColor("cyan"))
                self._resize_handle_rect = handle


    def _draw_image_overlay(self, p, target, ov):
        # cache du pixmap
        pix = self._img_cache.get(ov.path)
        if pix is None:
            pix = QPixmap(ov.path)
            self._img_cache[ov.path] = pix

        W, H = target.width(), target.height()
        w = int(ov.w * W); h = int(ov.h * H)
        x = target.x() + int(ov.x * W); y = target.y() + int(ov.y * H)
        rect = QRect(x, y, w, h)
        if not pix.isNull():
            p.drawPixmap(rect, pix)
        self._last_overlay_boxes.append((ov, rect, "image"))

        # handles (si sélectionnée)
        if ov is self._selected_overlay:
            p.setPen(QPen(QColor("cyan"), 2)); p.setBrush(Qt.NoBrush); p.drawRect(rect)
            handle = QRect(rect.right()-8, rect.bottom()-8, 8, 8)  # coin bas-droit
            p.fillRect(handle, QColor("cyan"))
            # stocker pour hit-test resize
            self._resize_handle_rect = handle


    # --- interaction ---
    def mousePressEvent(self, e):
        pt = e.position().toPoint()
        # priorité au handle de resize
        if getattr(self, "_resize_handle_rect", None) and self._resize_handle_rect.contains(pt):
            self._dragging = True; self._resizing = True; return

        for entry in reversed(self._last_overlay_boxes):
            # reversed = on prend l’item dessiné au-dessus si chevauchement
            ov, rect, kind = entry
            if rect.contains(pt):
                self._selected_overlay = ov
                self._selected_type = kind
                self.overlaySelected.emit(ov)
                self._dragging = True; self._resizing = False
                self._drag_offset = (pt.x()-rect.x(), pt.y()-rect.y())
                self.update(); return

        self._selected_overlay = None; self._selected_type = None
        self.overlaySelected.emit(None); self.update()

    def mouseMoveEvent(self, e):
        if self._dragging and self._selected_overlay and self._last_target_rect:
            target = self._last_target_rect
            W, H = target.width(), target.height()

            if getattr(self, "_resizing", False):
                # redimension depuis coin bas-droit
                px = max(target.x(), min(int(e.position().x()), target.right()))
                py = max(target.y(), min(int(e.position().y()), target.bottom()))
                new_w = (px - (target.x() + int(self._selected_overlay.x * W))) / float(W)
                new_h = (py - (target.y() + int(self._selected_overlay.y * H))) / float(H)
                self._selected_overlay.w = max(0.02, min(new_w, 1.0))
                self._selected_overlay.h = max(0.02, min(new_h, 1.0))
            else:
                px = int(e.position().x() - self._drag_offset[0])
                py = int(e.position().y() - self._drag_offset[1])
                px = max(target.x(), min(px, target.right()))
                py = max(target.y(), min(py, target.bottom()))
                self._selected_overlay.x = (px - target.x()) / float(W)
                self._selected_overlay.y = (py - target.y()) / float(H)

            self.update()

    def mouseReleaseEvent(self, e):
        self._dragging = False; self._resizing = False
        super().mouseReleaseEvent(e)
