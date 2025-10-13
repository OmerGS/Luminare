from enum import Enum

class ImportTypes(Enum):
    """
    Définit les types de ressources pouvant être importées dans le projet.
    """    
    VISUEL = "VISUEL"
    AUDIO = "AUDIO"
    TEXT = "TEXTE"