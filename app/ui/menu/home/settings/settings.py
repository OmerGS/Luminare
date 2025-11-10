from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from app.ui import styles
from app.ui.components.change_export_folder_button import ChangeExportFolderButton
from app.ui.components.change_save_folder_button import ChangeSaveFolderButton
from app.ui.components.volume_slider import VolumeSlider

class SettingsMenu(QWidget):
    def __init__(self, exportPath, savePath, openFileSearch):
        super().__init__()
        
        self.setStyleSheet(styles.WINDOW_STYLE)

        settingsLayout = QVBoxLayout(self)

        volumeLayout = QVBoxLayout()

        pathLayout = QVBoxLayout()

        volumeLabel = QLabel("Volume")

        self.volume_slider = VolumeSlider(orientation=Qt.Horizontal, interval=100)
        self.volume_slider.setMinimumWidth(750)

        exportLabel = QLabel("export path")

        saveLabel = QLabel("save path")

        self.change_export = ChangeExportFolderButton(exportPath, openFileSearch)
        self.change_save = ChangeSaveFolderButton(savePath, openFileSearch)

        volumeLayout.addWidget(volumeLabel)
        volumeLayout.addWidget(self.volume_slider,stretch=10, alignment=Qt.AlignmentFlag.AlignLeft)

        pathLayout.addWidget(exportLabel)
        pathLayout.addWidget(self.change_export,)
        pathLayout.addWidget(saveLabel)
        pathLayout.addWidget(self.change_save)

        settingsLayout.addLayout(pathLayout, stretch=1)
        settingsLayout.addLayout(volumeLayout, stretch=1)

        settingsLayout.addStretch()
