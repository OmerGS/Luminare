from core.save_system.save_api import ProjectAPI
from core.save_system.serializers import LMPRJChunkedSerializer
import os

def list_lmprj_files():
    """Retourne la liste des fichiers .lmprj dans le dossier de sauvegarde"""
    save_dir = LMPRJChunkedSerializer.get_save_dir()
    if not os.path.exists(save_dir):
        return []
    return [f for f in os.listdir(save_dir) if f.endswith(".lmprj")]

def display_project(proj):
    """Affichage lisible du projet"""
    print("\n=== Contenu du projet ===")
    print(f"Nom du projet   : {proj.name}")
    print(f"Résolution      : {proj.resolution[0]}x{proj.resolution[1]}")
    print(f"FPS             : {proj.fps}")
    print(f"Output          : {proj.output}")
    print(f"Audio normalisé : {proj.audio_normalize}")
    print(f"Nombre de clips : {len(proj.clips)}")
    for i, clip in enumerate(proj.clips, 1):
        print(f"  Clip {i} : {clip['path']} (trim {clip['trim'][0]} - {clip['trim'][1]})")

if __name__ == "__main__":
    # 🔹 Affiche le nombre total de projets et de clips
    print(f"\nNombre total de projets : {ProjectAPI.get_save_count()}")

    # 🔹 Liste les projets disponibles
    files = list_lmprj_files()
    if not files:
        print(f"\nAucun fichier .lmprj trouvé dans {LMPRJChunkedSerializer.get_save_dir()}")
        exit()

    print("\nFichiers disponibles :")
    for idx, filename in enumerate(files, 1):
        print(f"{idx}. {filename}")

    # 🔹 Demande à l’utilisateur lequel charger
    while True:
        try:
            choice = int(input(f"\nChoisis un fichier à charger (1-{len(files)}): "))
            if 1 <= choice <= len(files):
                break
            else:
                print("Numéro invalide, recommence.")
        except ValueError:
            print("Entrée invalide, recommence.")

    selected_file = files[choice - 1]

    loaded_proj = ProjectAPI.load(selected_file)

    display_project(loaded_proj)

    clip_count = ProjectAPI.get_clip_count(selected_file)
    print(f"\n📊 Ce projet contient {clip_count} clip(s).")