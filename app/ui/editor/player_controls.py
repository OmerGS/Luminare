from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QPushButton, QLabel, QSlider, QStyle, QWidget, QVBoxLayout, QHBoxLayout, QApplication
)

# Constantes pour l'état du lecteur (à définir ou importer)
class PlaybackState:
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2

class PlayerControls(QWidget):
    openRequested = Signal()
    exportRequested = Signal()
    zoomChanged = Signal(int)
    seekRelativeRequested = Signal(int)

    def __init__(self):
        super().__init__()
        
        self.seek_timer = QTimer(self)
        self.seek_timer.setSingleShot(True)
        self.seek_timer.timeout.connect(self._enable_seek_buttons)

        self._state = PlaybackState.STOPPED

        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(4)

        top_hbox = QHBoxLayout() 
        bottom_hbox = QHBoxLayout()
        
        self.btn_open  = QPushButton(self._icon(QStyle.SP_DialogOpenButton), " Ouvrir")
        
        # FUSION PLAY/PAUSE
        self.btn_play_pause = QPushButton(self._icon(QStyle.SP_MediaPlay), "") 
        
        # BOUTONS RAPIDES (seek)
        self.btn_backward = QPushButton(self._icon(QStyle.SP_MediaSeekBackward), "")
        self.btn_forward  = QPushButton(self._icon(QStyle.SP_MediaSeekForward), "")
        self.btn_backward.clicked.connect(lambda: self._handle_seek(-500))
        self.btn_forward.clicked.connect(lambda: self._handle_seek(500))

        self.btn_stop  = QPushButton(self._icon(QStyle.SP_MediaStop), "")
        self.btn_export = QPushButton("Exporter (MVP)")

        # sliders
        self.pos_slider = QSlider(Qt.Horizontal); self.pos_slider.setRange(0,0)
        self.lbl_time = QLabel("00:00 / 00:00"); self.lbl_time.setMinimumWidth(120)
        self.vol_lbl = QLabel("Vol"); self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100); self.vol_slider.setValue(80)

        self.zoom_lbl = QLabel("Zoom"); self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 400); self.zoom_slider.setValue(80)

        top_hbox.addWidget(self.btn_open)

        top_hbox.addWidget(self.btn_backward)
        top_hbox.addWidget(self.btn_play_pause)
        top_hbox.addWidget(self.btn_forward)
        top_hbox.addWidget(self.btn_stop)
        
        top_hbox.addWidget(self.pos_slider, 1)
        top_hbox.addWidget(self.lbl_time)
        top_hbox.addWidget(self.vol_lbl)
        top_hbox.addWidget(self.vol_slider)
        top_hbox.addWidget(self.btn_export)

        # --- Ligne 2 : Zoom ---
        bottom_hbox.addWidget(self.zoom_lbl)
        bottom_hbox.addWidget(self.zoom_slider, 1) 

        # --- Ajout des lignes au layout principal ---
        main_vbox.addLayout(top_hbox)
        main_vbox.addLayout(bottom_hbox)

        # signaux primaires
        self.btn_open.clicked.connect(self.openRequested.emit)
        self.btn_export.clicked.connect(self.exportRequested.emit)
        self.zoom_slider.valueChanged.connect(lambda v: (self.zoom_lbl.setText(f"Zoom ({v}px/s)"),
                                                        self.zoomChanged.emit(v)))

        # callbacks back (attach)
        self._media = None
        self.pos_slider.sliderMoved.connect(self._on_slider_moved)
        self.vol_slider.valueChanged.connect(self._on_volume_changed)
        
        # Logique pour le bouton unique Play/Pause
        self.btn_play_pause.clicked.connect(self._toggle_play_pause)
        
        # Connexions pour le seeking rapide
        self.btn_backward.clicked.connect(lambda: self.seekRelativeRequested.emit(-5000))
        self.btn_forward.clicked.connect(lambda: self.seekRelativeRequested.emit(5000))
        
        self.btn_stop.clicked.connect(lambda: self._media and self._media.stop())
        self.set_state(PlaybackState.STOPPED)
        

    def _icon(self, std):
        return QApplication.style().standardIcon(std)
    
    def _toggle_play_pause(self):
        if not self._media:
            return

        if self._state == PlaybackState.PLAYING:
            self._media.pause()
            self.set_state(PlaybackState.PAUSED)
        else:
            self._media.play()
            self.set_state(PlaybackState.PLAYING)
            
    def set_state(self, state):
        """Met à jour l'icône du bouton Play/Pause."""
        self._state = state
        if state == PlaybackState.PLAYING:
            self.btn_play_pause.setIcon(self._icon(QStyle.SP_MediaPause))
            self.btn_play_pause.setToolTip("Pause")
        elif state == PlaybackState.PAUSED:
            self.btn_play_pause.setIcon(self._icon(QStyle.SP_MediaPlay))
            self.btn_play_pause.setToolTip("Reprendre la lecture")
        elif state == PlaybackState.STOPPED:
            self.btn_play_pause.setIcon(self._icon(QStyle.SP_MediaPlay))
            self.btn_play_pause.setToolTip("Lecture")
            

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
        if self._media: self._media.seek_ms(p)

    def _on_volume_changed(self, v: int):
        if self._media: self._media.set_volume(v / 100)

    def _update_label(self, pos, dur):
        def fmt(ms):
            s = int(ms / 1000); m, s = divmod(s,60); h, m = divmod(m,60)
            return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
        self.lbl_time.setText(f"{fmt(pos)} / {fmt(dur)}")

    def _handle_seek(self, ms: int):
        self.btn_forward.setEnabled(False)
        self.btn_backward.setEnabled(False)
        self.seekRelativeRequested.emit(ms) 
        self.seek_timer.start(200) 


    def _enable_seek_buttons(self):
        self.btn_forward.setEnabled(True)
        self.btn_backward.setEnabled(True)
