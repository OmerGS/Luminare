from project.serializers import LMPRJChunkedSerializer
import os

def list_lmprj_files(save_dir):
    """Retourne la liste des fichiers .lmprj dans le dossier de sauvegarde"""
    return [f for f in os.listdir(save_dir) if f.endswith(".lmprj")]

def display_project(proj):
    """Affichage lisible du projet"""
    print("=== Contenu du projet ===")
    print(f"Nom du projet   : {proj.name}")
    print(f"Résolution      : {proj.resolution[0]}x{proj.resolution[1]}")
    print(f"FPS             : {proj.fps}")
    print(f"Output          : {proj.output}")
    print(f"Audio normalisé : {proj.audio_normalize}")
    print(f"Nombre de clips : {len(proj.clips)}")
    for i, clip in enumerate(proj.clips, 1):
        print(f"  Clip {i} : {clip['path']} (trim {clip['trim'][0]} - {clip['trim'][1]})")

if __name__ == "__main__":
    save_dir = LMPRJChunkedSerializer.get_save_dir()
    files = list_lmprj_files(save_dir)

    if not files:
        print(f"Aucun fichier .lmprj trouvé dans {save_dir}")
        exit()

    # Affiche la liste des fichiers avec un numéro
    print("Fichiers disponibles :")
    for idx, filename in enumerate(files, 1):
        print(f"{idx}. {filename}")

    # Demande à l'utilisateur de choisir
    while True:
        try:
            choice = int(input(f"Choisis un fichier à charger (1-{len(files)}): "))
            if 1 <= choice <= len(files):
                break
            else:
                print("Numéro invalide, recommence.")
        except ValueError:
            print("Entrée invalide, recommence.")

    selected_file = files[choice - 1]

    # Charge et affiche le projet
    loaded_proj = LMPRJChunkedSerializer.load(selected_file)
    display_project(loaded_proj)