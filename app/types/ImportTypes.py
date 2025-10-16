from enum import Enum

class ImportTypes(Enum):
    """
    Définit les types de ressources pouvant être importées dans le projet.
    """    
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    TEXT = "TEXTE"
    OTHER = "OTHER"