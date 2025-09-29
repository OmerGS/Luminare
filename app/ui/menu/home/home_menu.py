# app/ui/menu/home/home_menu.py
from PySide6.QtWidgets import QWidget, QVBoxLayout
from app.ui import styles
from app.ui.components.title import Title
from app.ui.components.menu_button import MenuButton

class MainMenu(QWidget):
    def __init__(self, go_to_editor):
        super().__init__()

        self.setStyleSheet(styles.WINDOW_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(30)
        layout.setContentsMargins(50, 50, 50, 50)

        # Titre (utilisation du composant Title)
        layout.addWidget(Title("🎬 Luminare"))

        # Boutons (utilisation du composant MenuButton)
        layout.addWidget(MenuButton("▶ Jouer", go_to_editor))
        layout.addWidget(MenuButton("🖊️ Éditeur", go_to_editor))
        layout.addWidget(MenuButton("❌ Quitter", self.close_app))

        layout.addStretch()

    def close_app(self):
        from PySide6.QtWidgets import QApplication
        QApplication.quit()
