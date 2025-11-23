from PySide6.QtWidgets import QVBoxLayout, QGridLayout, QWidget
from PySide6.QtCore import Qt
from app.ui import styles
from app.ui.components.create_project_button import CreateProjectButton
from app.ui.components.project_button import ProjectButton
from app.ui.components.title import Title
from app.ui.components.menu_button import MenuButton

class ProjectSelect(QWidget):
    def __init__(self, go_to_editor,go_to_editor_with_project_name, vids):
        super().__init__()
        
        self.setStyleSheet(styles.WINDOW_STYLE)

        layoutCreate = QVBoxLayout(self)
        layoutCreate.setSpacing(30)
        layoutCreate.setContentsMargins(50, 50, 50, 50)

        layoutCreate.addWidget(Title("Luminare"))

        layoutCreate.addWidget(CreateProjectButton("Éditeur", go_to_editor))

        layoutProject = QGridLayout()
        layoutProject.setVerticalSpacing(15)
        cols = 5
        for i, text in enumerate(vids):
            row = i // cols
            col = i % cols
            load_func = lambda checked, name=text: go_to_editor_with_project_name(name)
            layoutProject.addWidget(ProjectButton(text, load_func), row, col, alignment=Qt.AlignmentFlag.AlignTop)

        layoutCreate.addLayout(layoutProject)

        layoutCreate.addStretch(1)