# app/ui/menu/home/home_menu.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from app.ui import styles
from app.ui.components.title import Title
from app.ui.components.menu_button import MenuButton
from app.ui.components.project_button import ProjectButton

class MainMenu(QWidget):
    def __init__(self, go_to_editor):
        super().__init__()

        self.setStyleSheet(styles.WINDOW_STYLE)

        mainLayout = QHBoxLayout(self)

        layoutCreate = QVBoxLayout(self)
        layoutCreate.setSpacing(30)
        layoutCreate.setContentsMargins(50, 50, 50, 50)

        mainLayout.addLayout(layoutCreate)
        # Titre (utilisation du composant Title)
        layoutCreate.addWidget(Title("🎬 Luminare"))

        # Boutons (utilisation du composant MenuButton)
        layoutCreate.addWidget(MenuButton("▶ Jouer", go_to_editor))
        layoutCreate.addWidget(MenuButton("🖊️ Éditeur", go_to_editor))
        layoutCreate.addWidget(MenuButton("❌ Quitter", self.close_app))

        #layoutCreate.addStretch()

        layoutProject = QHBoxLayout(self)
        layoutProject.addWidget(ProjectButton("Projet1", go_to_editor))
        layoutProject.addWidget(ProjectButton("Projet2", go_to_editor))
        layoutProject.addWidget(ProjectButton("Projet3", go_to_editor))
        layoutProject.addWidget(ProjectButton("Projet4", go_to_editor))

        layoutCreate.addLayout(layoutProject)

        

    def close_app(self):
        from PySide6.QtWidgets import QApplication
        QApplication.quit()
