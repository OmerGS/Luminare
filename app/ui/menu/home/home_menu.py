# app/ui/menu/home/home_menu.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedLayout
from PySide6.QtCore import Qt
from app.ui import styles
from app.ui.components.title import Title
from app.ui.components.menu_button import MenuButton
from app.ui.components.project_button import ProjectButton
from app.ui.components.leave_button import LeaveButton
from app.ui.components.create_project_button import CreateProjectButton
from app.ui.menu.home.project_select.project_select import ProjectSelect
from app.ui.menu.home.settings.settings import SettingsMenu
from app.ui.components.volume_slider import VolumeSlider

class MainMenu(QWidget):
    def __init__(self, go_to_editor, go_to_home, vids):
        super().__init__()

        self.setStyleSheet(styles.WINDOW_STYLE)

        mainLayout = QHBoxLayout(self)

        layoutMenu = QVBoxLayout()
        
        
        layoutWidgetButton = QVBoxLayout()

        layoutWidgetButton.addWidget(MenuButton("Home", self.show_project), alignment=Qt.AlignmentFlag.AlignVCenter)
        layoutWidgetButton.addWidget(MenuButton("Settings", self.show_settings), alignment=Qt.AlignmentFlag.AlignTop)

        layoutMenu.addLayout(layoutWidgetButton, )
        layoutMenu.addWidget(LeaveButton("Leave", self.close_app), alignment=Qt.AlignmentFlag.AlignBottom)

        self.layoutOther = QStackedLayout(self)
        self.project_select = ProjectSelect(go_to_editor, vids)
        self.settings = SettingsMenu("testPath", "testPath2", self.show_settings)

        self.layoutOther.addWidget(self.project_select)
        self.layoutOther.addWidget(self.settings)

        self.layoutOther.setCurrentWidget(self.project_select)

        mainLayout.addLayout(layoutMenu, stretch=1)
        mainLayout.addLayout(self.layoutOther, stretch=8)


    def close_app(self):
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    def show_settings(self):
        self.layoutOther.setCurrentWidget(self.settings) 
              

    def show_project(self):
        self.layoutOther.setCurrentWidget(self.project_select)