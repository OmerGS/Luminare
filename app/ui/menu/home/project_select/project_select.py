from PySide6.QtWidgets import QVBoxLayout, QGridLayout, QWidget
from app.ui import styles
from app.ui.components.create_project_button import CreateProjectButton
from app.ui.components.project_button import ProjectButton
from app.ui.components.title import Title
from app.ui.components.menu_button import MenuButton

class ProjectSelect(QWidget):
    def __init__(self, go_to_editor, vids):
        super().__init__()
        
        self.setStyleSheet(styles.WINDOW_STYLE)

        layoutCreate = QVBoxLayout(self)
        layoutCreate.setSpacing(30)
        layoutCreate.setContentsMargins(50, 50, 50, 50)

                # Titre (utilisation du composant Title)
        layoutCreate.addWidget(Title("🎬 Luminare"))

        # Boutons (utilisation du composant MenuButton)
        layoutCreate.addWidget(CreateProjectButton("🖊️ Éditeur", go_to_editor), stretch=7 )

        layoutCreate.addStretch()

        layoutProject = QGridLayout(self)
        cols = 5
        for i, text in enumerate(vids):
            row = i // cols
            col = i % cols
            layoutProject.addWidget(ProjectButton(text, go_to_editor), row, col)

        layoutCreate.addLayout(layoutProject)