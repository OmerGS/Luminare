# ui/editor/inspector.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QDoubleSpinBox, QCheckBox, QSizePolicy, QGroupBox
)
from typing import Optional

class Inspector(QWidget):
    # ---- Signaux "Titres"
    addTitleRequested = Signal(str)        # texte du champ -> ajouter un titre
    removeLastTitleRequested = Signal()    # supprimer le dernier titre
    setTitleStartRequested = Signal()      # "Début = curseur"
    setTitleEndRequested = Signal()        # "Fin = curseur"
    titleTextChanged = Signal(str)         # champ texte modifié (maj dernier titre)

    # ---- Signaux "Filtres"
    filtersChanged = Signal(float, float, float, bool)  # b, c, s, vignette

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(220)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self._selected_overlay = None

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(8)

        # ---------- Bloc Titres ----------
        gb_titles = QGroupBox("Titres")
        v = QVBoxLayout(gb_titles)

        self.edt_title = QLineEdit()
        v.addWidget(self.edt_title)

        row_btn1 = QHBoxLayout()
        self.btn_add_title = QPushButton("Ajouter un titre")
        self.btn_del_last  = QPushButton("Supprimer dernier")
        row_btn1.addWidget(self.btn_add_title)
        row_btn1.addWidget(self.btn_del_last)
        v.addLayout(row_btn1)

        row_btn2 = QHBoxLayout()
        self.btn_start = QPushButton("Début = curseur")
        self.btn_end   = QPushButton("Fin = curseur")
        row_btn2.addWidget(self.btn_start)
        row_btn2.addWidget(self.btn_end)
        v.addLayout(row_btn2)

        root.addWidget(gb_titles)

        # ---------- Bloc Filtres ----------
        gb_filters = QGroupBox("Couleur (export)")
        fv = QVBoxLayout(gb_filters)

        def mk_spin(label_text, default):
            row = QHBoxLayout()
            row.addWidget(QLabel(label_text))
            sp = QDoubleSpinBox()
            sp.setRange(-10_000.0, 10_000.0)
            sp.setDecimals(2)
            sp.setSingleStep(0.05)
            sp.setValue(default)
            sp.setAlignment(Qt.AlignRight)
            row.addWidget(sp)
            fv.addLayout(row)
            return sp

        self.sp_brightness = mk_spin("Brightness", 0.00)
        self.sp_contrast   = mk_spin("Contrast",   1.00)
        self.sp_saturation = mk_spin("Saturation", 1.00)

        self.cb_vignette = QCheckBox("Vignette")
        fv.addWidget(self.cb_vignette)

        root.addWidget(gb_filters)
        root.addStretch(1)

        # ---------- Connexions ----------
        # Titres
        self.btn_add_title.clicked.connect(lambda: self.addTitleRequested.emit(self.edt_title.text()))
        self.btn_del_last.clicked.connect(self.removeLastTitleRequested.emit)
        self.btn_start.clicked.connect(self.setTitleStartRequested.emit)
        self.btn_end.clicked.connect(self.setTitleEndRequested.emit)
        self.edt_title.textEdited.connect(self.titleTextChanged.emit)

        # Filtres (toutes modifs émettent)
        def emit_filters():
            self.filtersChanged.emit(
                float(self.sp_brightness.value()),
                float(self.sp_contrast.value()),
                float(self.sp_saturation.value()),
                bool(self.cb_vignette.isChecked()),
            )
        self.sp_brightness.valueChanged.connect(lambda *_: emit_filters())
        self.sp_contrast.valueChanged.connect(lambda *_: emit_filters())
        self.sp_saturation.valueChanged.connect(lambda *_: emit_filters())
        self.cb_vignette.toggled.connect(lambda *_: emit_filters())
    
    def set_selected_overlay(self, overlay: Optional[object]):
        """
        Met à jour le champ texte quand un overlay (titre) est sélectionné sur la vidéo.
        """
        self._selected_overlay = overlay
        # éviter d’émettre titleTextChanged pendant qu’on remplit le champ
        self.edt_title.blockSignals(True)
        self.edt_title.setText(getattr(overlay, "text", "") if overlay else "")
        self.edt_title.blockSignals(False)
