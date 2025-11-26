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
    """Affichage complet du projet"""
    print("\n=== Contenu du projet ===")
    print(f"Nom du projet      : {proj.name}")
    print(f"Version du projet  : {getattr(proj, 'version', 'inconnue')}")
    print(f"Résolution         : {proj.resolution[0]}x{proj.resolution[1]}")
    print(f"FPS                : {proj.fps}")
    print(f"Output             : {proj.output}")
    print(f"Audio normalisé    : {proj.audio_normalize}")

    print(f"\nRessources importées ({len(proj.imported_assets)}) :")
    if proj.imported_assets:
        for i, asset in enumerate(proj.imported_assets, 1):
            name = asset.get("name", "N/A")
            path = asset.get("path", "N/A")
            asset_type = asset.get("type", "N/A")
            print(f"  Asset {i} ({asset_type}) : {name} | Path: {path}")
    else:
        print("Aucun import trouvée.")

    # Clips
    print(f"\nClips ({len(proj.clips)}) :")
    if proj.clips:
        for i, clip in enumerate(proj.clips, 1):
            print(f"  Clip {i} : {clip.path} (in={clip.in_s}, out={clip.out_s}, duration={clip.duration_s})")
    else:
        print("  Aucun clip trouvé.")

    # Filters
    f = proj.filters
    print(f"\nFiltres : brightness={f.brightness}, contrast={f.contrast}, "
          f"saturation={f.saturation}, vignette={f.vignette}")

    # Text overlays
    print(f"\nText Overlays ({len(proj.text_overlays)}) :")
    if proj.text_overlays:
        for i, ov in enumerate(proj.text_overlays, 1):
            print(f"  Overlay {i}: '{ov.text}' [{ov.start}-{ov.end}s], "
                  f"position=({ov.x},{ov.y}), fontsize={ov.fontsize}, color={ov.fontcolor}")
    else:
        print("  Aucun overlay trouvé.")

if __name__ == "__main__":
    print(f"\nNombre total de projets : {ProjectAPI.get_save_count()}")

    files = list_lmprj_files()
    if not files:
        print(f"\nAucun fichier .lmprj trouvé dans {LMPRJChunkedSerializer.get_save_dir()}")
        exit()

    print("\nFichiers disponibles :")
    for idx, filename in enumerate(files, 1):
        print(f"{idx}. {filename}")

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

    try:
        loaded_proj = ProjectAPI.load(selected_file)
    except Exception as e:
        print(f"Impossible de charger le projet : {e}")
        exit()

    display_project(loaded_proj)

    clip_count = len(loaded_proj.clips)
    print(f"\nCe projet contient {clip_count} clip(s).")