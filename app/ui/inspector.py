# app/ui/inspector.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFormLayout, QDoubleSpinBox, QCheckBox,
    QLabel, QHBoxLayout, QLineEdit
)

class Inspector(QWidget):
    addTitleRequested = Signal()
    removeTitleRequested = Signal()
    filtersChanged = Signal(float, float, float, bool)  # b, c, s, vignette
    titleTextChanged = Signal(str)
    setTitleStartRequested = Signal()  # utilise le playhead courant
    setTitleEndRequested = Signal()    # utilise le playhead courant

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(260)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        # --- Titres ---
        layout.addWidget(QLabel("Titres"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Texte du titre…")
        self.title_edit.textChanged.connect(self.titleTextChanged.emit)
        layout.addWidget(self.title_edit)

        btns = QHBoxLayout()
        btn_add = QPushButton("Ajouter un titre")
        btn_del = QPushButton("Supprimer dernier")
        btns.addWidget(btn_add); btns.addWidget(btn_del)
        layout.addLayout(btns)

        btn_time = QHBoxLayout()
        btn_set_start = QPushButton("Début = curseur")
        btn_set_end   = QPushButton("Fin = curseur")
        btn_time.addWidget(btn_set_start); btn_time.addWidget(btn_set_end)
        layout.addLayout(btn_time)

        btn_add.clicked.connect(self.addTitleRequested.emit)
        btn_del.clicked.connect(self.removeTitleRequested.emit)
        btn_set_start.clicked.connect(self.setTitleStartRequested.emit)
        btn_set_end.clicked.connect(self.setTitleEndRequested.emit)

        # --- Couleur (export) ---
        layout.addSpacing(12)
        layout.addWidget(QLabel("Couleur (export)"))

        form = QFormLayout()
        self.spin_b = QDoubleSpinBox(); self.spin_b.setRange(-1.0, 1.0); self.spin_b.setSingleStep(0.05); self.spin_b.setValue(0.0)
        self.spin_c = QDoubleSpinBox(); self.spin_c.setRange(0.0, 3.0); self.spin_c.setSingleStep(0.05); self.spin_c.setValue(1.0)
        self.spin_s = QDoubleSpinBox(); self.spin_s.setRange(0.0, 3.0); self.spin_s.setSingleStep(0.05); self.spin_s.setValue(1.0)
        self.chk_v  = QCheckBox("Vignette"); self.chk_v.setChecked(False)

        form.addRow("Brightness", self.spin_b)
        form.addRow("Contrast", self.spin_c)
        form.addRow("Saturation", self.spin_s)
        form.addRow("", self.chk_v)
        layout.addLayout(form)

        for w in (self.spin_b, self.spin_c, self.spin_s):
            w.valueChanged.connect(self._emit_filters)
        self.chk_v.toggled.connect(self._emit_filters)

        layout.addStretch(1)

    def _emit_filters(self, *_):
        self.filtersChanged.emit(
            self.spin_b.value(), self.spin_c.value(), self.spin_s.value(), self.chk_v.isChecked()
        )
