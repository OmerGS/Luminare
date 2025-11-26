from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QIcon


class ImportButton(QPushButton):
    """Bouton d'import avec icône."""

    def __init__(self, text="Importer", parent=None):
        super().__init__(text, parent)
        self.setIcon(QIcon.fromTheme("document-open"))
