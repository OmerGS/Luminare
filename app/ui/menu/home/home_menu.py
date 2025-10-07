# app/ui/menu/home/home_menu.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from app.ui import styles
from app.ui.components.title import Title
from app.ui.components.menu_button import MenuButton
from app.ui.components.project_button import ProjectButton

class MainMenu(QWidget):
    def __init__(self, go_to_editor, go_to_settings, go_to_home):
        super().__init__()

        self.setStyleSheet(styles.WINDOW_STYLE)

        mainLayout = QHBoxLayout(self)

        layoutMenu = QVBoxLayout(self)
        layoutMenu.addWidget(MenuButton("Home", go_to_home))
        layoutMenu.addWidget(MenuButton("Settings", go_to_settings))
        

        layoutCreate = QVBoxLayout(self)
        layoutCreate.setSpacing(30)
        layoutCreate.setContentsMargins(50, 50, 50, 50)

        mainLayout.addLayout(layoutMenu, stretch=1)
        mainLayout.addLayout(layoutCreate, stretch=8)
        
        # Titre (utilisation du composant Title)
        layoutCreate.addWidget(Title("🎬 Luminare"))

        # Boutons (utilisation du composant MenuButton)
        layoutCreate.addWidget(MenuButton("🖊️ Éditeur", go_to_editor), stretch=7 )
        layoutCreate.addWidget(MenuButton("❌ Quitter", self.close_app))

        layoutCreate.addStretch()

        layoutProject = QGridLayout(self)
        layoutProject.addWidget(ProjectButton("Projet1", go_to_editor), 0, 0)
        layoutProject.addWidget(ProjectButton("Projet2", go_to_editor), 0,1)
        layoutProject.addWidget(ProjectButton("Projet3", go_to_editor), 1,0)
        layoutProject.addWidget(ProjectButton("Projet4", go_to_editor), 1,1)

        layoutCreate.addLayout(layoutProject)

        

    def close_app(self):
        from PySide6.QtWidgets import QApplication
        QApplication.quit()
