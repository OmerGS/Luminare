from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QPushButton, QLabel, QSlider, QStyle
)

class PlayerControls(QHBoxLayout):
    openRequested = Signal()
    exportRequested = Signal()
    zoomChanged = Signal(int)
    splitRequested = Signal()
    markInRequested = Signal()
    markOutRequested = Signal()
    deleteSelectionCloseRequested = Signal()
    deleteSelectionGapRequested = Signal()
 

    def __init__(self):
        super().__init__()
        # boutons
        self.btn_play   = QPushButton(self._icon(QStyle.SP_MediaPlay), "")
        self.btn_pause  = QPushButton(self._icon(QStyle.SP_MediaPause), "")
        self.btn_stop   = QPushButton(self._icon(QStyle.SP_MediaStop), "")
        self.btn_split  = QPushButton("✂ Couper")  # <-- NEW : bouton ciseaux
        self.btn_export = QPushButton("Exporter (MVP)")

        self.btn_del_close = QPushButton("Suppr (refermer)")

        self.addWidget(self.btn_del_close)

       
        self.btn_del_close.clicked.connect(self.deleteSelectionCloseRequested.emit)
       


        self.btn_split.setToolTip("Couper le clip au niveau de la tête de lecture")

        # sliders
        self.pos_slider = QSlider(Qt.Horizontal); self.pos_slider.setRange(0, 0)
        self.lbl_time = QLabel("00:00 / 00:00"); self.lbl_time.setMinimumWidth(120)
        self.vol_lbl = QLabel("Vol"); self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100); self.vol_slider.setValue(80)

        self.zoom_lbl = QLabel("Zoom"); self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 400); self.zoom_slider.setValue(80)

        # layout
        self.addWidget(self.btn_play)
        self.addWidget(self.btn_pause)
        self.addWidget(self.btn_stop)
        self.addWidget(self.btn_split)           # <-- NEW : placé près des contrôles de lecture
        self.addWidget(self.pos_slider, 1)
        self.addWidget(self.lbl_time)
        self.addWidget(self.vol_lbl)
        self.addWidget(self.vol_slider)
        self.addWidget(self.btn_export)

        # ligne 2 (zoom)
        self.addWidget(self.zoom_lbl)
        self.addWidget(self.zoom_slider, 1)

        # signaux primaires
        self.btn_export.clicked.connect(self.exportRequested.emit)
        self.btn_split.clicked.connect(self.splitRequested.emit)  # <-- NEW
        self.zoom_slider.valueChanged.connect(
            lambda v: (self.zoom_lbl.setText(f"Zoom ({v}px/s)"), self.zoomChanged.emit(v))
        )

        # callbacks back (attach)
        self._media = None
        self.pos_slider.sliderMoved.connect(self._on_slider_moved)
        self.vol_slider.valueChanged.connect(self._on_volume_changed)
        self.btn_play.clicked.connect(lambda: self._media and self._media.play())
        self.btn_pause.clicked.connect(lambda: self._media and self._media.pause())
        self.btn_stop.clicked.connect(lambda: self._media and self._media.stop())

    def _icon(self, std):
        from PySide6.QtWidgets import QStyle, QApplication
        return QApplication.style().standardIcon(std)

    def set_media(self, media):
        self._media = media

    def attach(self, media_controller):
        self._media = media_controller

    def set_duration(self, ms: int):
        self.pos_slider.setRange(0, max(0, ms))
        self._update_label(self.pos_slider.value(), ms)

    def set_position(self, ms: int):
        if not self.pos_slider.isSliderDown():
            self.pos_slider.setValue(ms)
        self._update_label(ms, self.pos_slider.maximum())

    def _on_slider_moved(self, p: int):
        if self._media:
            self._media.seek_ms(p)

    def _on_volume_changed(self, v: int):
        if self._media:
            self._media.set_volume(v / 100)

    def _update_label(self, pos, dur):
        def fmt(ms):
            s = int(ms / 1000); m, s = divmod(s, 60); h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
        self.lbl_time.setText(f"{fmt(pos)} / {fmt(dur)}")
