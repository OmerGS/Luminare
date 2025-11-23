from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QPushButton, QLabel, QSlider, QStyle, QWidget, QVBoxLayout, QHBoxLayout, QApplication, QSizePolicy
)
from typing import Optional # Ajout de l'import pour Optional

# Constantes pour l'état du lecteur
class PlaybackState:
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2

class PlayerControls(QWidget):
    openRequested = Signal()
    exportRequested = Signal()
    zoomChanged = Signal(int)
    splitRequested = Signal()
    markInRequested = Signal()
    markOutRequested = Signal()
    deleteSelectionCloseRequested = Signal()
    deleteSelectionGapRequested = Signal()
    # Signal pour le seek relatif (ajouté si utilisé plus tard)
    seekRelativeRequested = Signal(int) 
 
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # --- 1. Initialisation des composants ---

        # Boutons de contrôle
        self.btn_play_pause = QPushButton(self._icon(QStyle.SP_MediaPlay), "") 
        self.btn_stop   = QPushButton(self._icon(QStyle.SP_MediaStop), "")
        self.btn_split  = QPushButton("✂ Couper") 
        
        # Boutons de navigation rapide
        self.btn_backward = QPushButton(self._icon(QStyle.SP_MediaSeekBackward), "")
        self.btn_forward  = QPushButton(self._icon(QStyle.SP_MediaSeekForward), "")

        # Boutons d'action
        self.btn_export = QPushButton("Exporter (MVP)")
        self.btn_del_close = QPushButton("Suppr (refermer)")
        
        # Sliders et labels de temps
        self.pos_slider = QSlider(Qt.Horizontal); self.pos_slider.setRange(0, 0)
        self.lbl_time = QLabel("00:00 / 00:00"); 
        self.lbl_time.setMinimumWidth(120); 
        self.lbl_time.setAlignment(Qt.AlignCenter)

        # Volume
        self.vol_lbl = QLabel("Vol"); self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100); self.vol_slider.setValue(80)
        self.vol_slider.setMaximumWidth(150)

        # Zoom
        self.zoom_lbl = QLabel("Zoom"); self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 400); self.zoom_slider.setValue(80)
        self.zoom_slider.setMaximumWidth(150)
        
        # Outils internes
        self.seek_timer = QTimer(self)
        self.seek_timer.setSingleShot(True)
        self.seek_timer.timeout.connect(self._enable_seek_buttons)
        self._media = None
        self._state = PlaybackState.STOPPED

        # Tooltips
        self.btn_split.setToolTip("Couper le clip au niveau de la tête de lecture")
        self.btn_del_close.setToolTip("Supprimer la sélection de la timeline et refermer le trou.")
        
        # --- 2. Création et organisation des Layouts ---
        
        main_vbox = QVBoxLayout(self) # Le layout principal de PlayerControls
        main_vbox.setContentsMargins(4, 4, 4, 4)
        main_vbox.setSpacing(6)

        # A. Première ligne: Lecture et Actions
        h_box_controls = QHBoxLayout()
        
        # Contrôles de lecture
        h_box_controls.addWidget(self.btn_stop)
        h_box_controls.addWidget(self.btn_backward)
        h_box_controls.addWidget(self.btn_play_pause)
        h_box_controls.addWidget(self.btn_forward)
        
        h_box_controls.addSpacing(10)
        
        # Actions de timeline
        h_box_controls.addWidget(self.btn_split)
        h_box_controls.addWidget(self.btn_del_close)
        
        h_box_controls.addStretch(1) # Espace flexible

        # Export (à droite)
        h_box_controls.addWidget(self.btn_export)
        
        # B. Deuxième ligne: Position de lecture (Slider + Temps)
        h_box_timeline = QHBoxLayout()
        h_box_timeline.addWidget(self.pos_slider, 1) # Le slider prend l'espace disponible (stretch factor 1)
        h_box_timeline.addWidget(self.lbl_time)

        # C. Troisième ligne: Zoom et Volume
        h_box_settings = QHBoxLayout()
        
        h_box_settings.addStretch(1) # Alignement à droite

        # Volume
        h_box_settings.addWidget(self.vol_lbl)
        h_box_settings.addWidget(self.vol_slider)
        
        h_box_settings.addSpacing(20)

        # Zoom
        h_box_settings.addWidget(self.zoom_lbl)
        h_box_settings.addWidget(self.zoom_slider)
        
        h_box_settings.addStretch(1) # Le reste de l'espace est flexible

        # Ajout des lignes au layout principal
        main_vbox.addLayout(h_box_controls)
        main_vbox.addLayout(h_box_timeline)
        main_vbox.addLayout(h_box_settings)
        
        # --- 3. Connexions des signaux (maintenues) ---

        # Signaux primaires
        self.btn_export.clicked.connect(self.exportRequested.emit)
        self.btn_split.clicked.connect(self.splitRequested.emit)
        self.btn_del_close.clicked.connect(self.deleteSelectionCloseRequested.emit)
        
        self.zoom_slider.valueChanged.connect(
            lambda v: (self.zoom_lbl.setText(f"Zoom ({v}px/s)"), self.zoomChanged.emit(v))
        )

        # Logique pour le bouton unique Play/Pause
        self.btn_play_pause.clicked.connect(self._toggle_play_pause)
        self.btn_stop.clicked.connect(lambda: self._media and self._media.stop())
        
        # Connexions pour le seeking rapide
        self.btn_backward.clicked.connect(lambda: self._handle_seek(-5000))
        self.btn_forward.clicked.connect(lambda: self._handle_seek(5000))
        
        # Callbacks
        self.pos_slider.sliderMoved.connect(self._on_slider_moved)
        self.vol_slider.valueChanged.connect(self._on_volume_changed)
        
        self.set_state(PlaybackState.STOPPED)
        

    def _icon(self, std):
        """Helper pour obtenir les icônes standards."""
        return QApplication.style().standardIcon(std)
    
    # ... (le reste de vos méthodes sont fonctionnelles et inchangées) ...
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
            
    # La méthode _icon est déjà définie ci-dessus, j'enlève le duplicata.

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

    def _handle_seek(self, ms: int):
        self.btn_forward.setEnabled(False)
        self.btn_backward.setEnabled(False)
        # Utilise le signal mis à jour
        self.seekRelativeRequested.emit(ms) 
        self.seek_timer.start(200) 

    def _enable_seek_buttons(self):
        self.btn_forward.setEnabled(True)
        self.btn_backward.setEnabled(True)