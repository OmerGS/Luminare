from PySide6.QtWidgets import QWidget, QVBoxLayout, QSlider, QHBoxLayout, QLabel
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

        volumeLayout = QHBoxLayout()

        pathLayout = QVBoxLayout()

        volumeLabel = QLabel("Volume")
        volumeLabel.setStyleSheet("color: white; font-size: 16px; margin-right: 10px;")

        self.volume_slider = VolumeSlider(orientation=Qt.Horizontal, interval=100)

        exportLabel = QLabel("export path")
        exportLabel.setStyleSheet("color: white; font-size: 16px; margin-right: 10px;")

        saveLabel = QLabel("save path")
        saveLabel.setStyleSheet("color: white; font-size: 16px; margin-right: 10px;")

        self.change_export = ChangeExportFolderButton(exportPath, openFileSearch)
        self.change_save = ChangeSaveFolderButton(savePath, openFileSearch)

        volumeLayout.addWidget(volumeLabel)
        volumeLayout.addWidget(self.volume_slider, stretch=1)

        pathLayout.addWidget(exportLabel)
        pathLayout.addWidget(self.change_export)
        pathLayout.addWidget(saveLabel)
        pathLayout.addWidget(self.change_save)

        settingsLayout.addLayout(pathLayout)
        settingsLayout.addLayout(volumeLayout)

        settingsLayout.addStretch()
