# app/ui/menu/home/home_menu.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from app.ui import styles
from app.ui.components.title import Title
from app.ui.components.menu_button import MenuButton
from app.ui.components.project_button import ProjectButton
from app.ui.components.leave_button import LeaveButton

class MainMenu(QWidget):
    def __init__(self, go_to_editor, go_to_settings, go_to_home, vids):
        super().__init__()

        self.setStyleSheet(styles.WINDOW_STYLE)

        mainLayout = QHBoxLayout(self)

        layoutMenu = QVBoxLayout(self)
        layoutMenu.addWidget(MenuButton("Home", go_to_home))
        layoutMenu.addWidget(MenuButton("Settings", go_to_settings))
        layoutMenu.addWidget(LeaveButton("Leave", self.close_app))

        layoutCreate = QVBoxLayout(self)
        layoutCreate.setSpacing(30)
        layoutCreate.setContentsMargins(50, 50, 50, 50)

        mainLayout.addLayout(layoutMenu, stretch=1)
        mainLayout.addLayout(layoutCreate, stretch=8)
        
        # Titre (utilisation du composant Title)
        layoutCreate.addWidget(Title("🎬 Luminare"))

        # Boutons (utilisation du composant MenuButton)
        layoutCreate.addWidget(MenuButton("🖊️ Éditeur", go_to_editor), stretch=7 )

        layoutCreate.addStretch()

        layoutProject = QGridLayout(self)
        cols = 5
        for i, text in enumerate(vids):
            row = i // cols
            col = i % cols
            layoutProject.addWidget(ProjectButton(text, go_to_editor), row, col)

        layoutCreate.addLayout(layoutProject)

        

    def close_app(self):
        from PySide6.QtWidgets import QApplication
        QApplication.quit()
