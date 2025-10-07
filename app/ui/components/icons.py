from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QStyle


def get_icon(category_name: str, widget) -> QIcon:
    """Retourne une icône native du style Qt, selon la catégorie."""
    style = widget.style()

    icons = {
        "Vidéo": style.standardIcon(QStyle.SP_MediaPlay),
        "Audio": style.standardIcon(QStyle.SP_MediaVolume),
        "Images": style.standardIcon(QStyle.SP_FileIcon),
        "Texte": style.standardIcon(QStyle.SP_DialogOpenButton),
        "Effets": style.standardIcon(QStyle.SP_ComputerIcon),
    }

    # Icône par défaut
    return icons.get(category_name, style.standardIcon(QStyle.SP_FileDialogNewFolder))
