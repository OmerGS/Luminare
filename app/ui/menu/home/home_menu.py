# app/ui/menu/home/home_menu.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from app.ui import styles
from app.ui.components.title import Title
from app.ui.components.menu_button import MenuButton
from app.ui.components.project_button import ProjectButton
from app.ui.components.leave_button import LeaveButton
from app.ui.components.create_project_button import CreateProjectButton
from app.ui.menu.home.project_select.project_select import ProjectSelect

class MainMenu(QWidget):
    def __init__(self, go_to_editor, go_to_settings, go_to_home, vids):
        super().__init__()

        self.setStyleSheet(styles.WINDOW_STYLE)

        mainLayout = QHBoxLayout(self)

        layoutMenu = QVBoxLayout(self)
        layoutMenu.addWidget(MenuButton("Home", go_to_home))
        layoutMenu.addWidget(MenuButton("Settings", go_to_settings))
        layoutMenu.addWidget(LeaveButton("Leave", self.close_app))

        layoutOther = QVBoxLayout(self)
        project_select = ProjectSelect(go_to_editor, vids)

        layoutOther.addWidget(project_select)

        mainLayout.addLayout(layoutMenu, stretch=1)
        mainLayout.addLayout(layoutOther, stretch=8)

        

    def close_app(self):
        from PySide6.QtWidgets import QApplication
        QApplication.quit()
