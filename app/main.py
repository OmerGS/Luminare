# main.py (entrypoint racine)
from __future__ import annotations
import os
from pathlib import Path
import platform
import sys

# --- Configuration initiale du chemin ---
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def set_cwd_to_repo_root():
    """Garantit que le process tourne à la racine du repo."""
    root = Path(__file__).resolve().parent
    if Path.cwd() != root:
        os.chdir(root)
    return root

def bootstrap_ffmpeg_on_path(root: Path):
    """Ajoute un FFmpeg portable au PATH si disponible sous vendor/ffmpeg."""
    system = platform.system().lower()
    candidates = []
    if system.startswith("win"):
        candidates += [
            root / "vendor" / "ffmpeg" / "windows" / "bin",
            root / "vendor" / "ffmpeg" / "win64" / "bin",
        ]
    elif system == "darwin":
        candidates += [root / "vendor" / "ffmpeg" / "macos" / "bin"]
    else:
        candidates += [root / "vendor" / "ffmpeg" / "linux" / "bin"]

    for p in candidates:
        if p.exists():
            os.environ["PATH"] = str(p) + os.pathsep + os.environ.get("PATH", "")
            print(f"FFmpeg bootstrapped from: {p}")
            break

def ensure_cache_dirs(root: Path):
    """Crée les répertoires de cache si absents."""
    for d in [root / "cache", root / "cache" / "wave"]:
        d.mkdir(parents=True, exist_ok=True)

def quiet_qt_multimedia_logs():
    """Optionnel : rend le terminal plus propre (désactive logs QtMultimedia)."""
    os.environ.setdefault(
        "QT_LOGGING_RULES",
        "qt.multimedia.ffmpeg.debug=false;qt.multimedia.ffmpeg.warning=false"
    )

def main():
    # --- 1. Bootstrap de l'environnement ---
    root = set_cwd_to_repo_root()
    bootstrap_ffmpeg_on_path(root)
    ensure_cache_dirs(root)
    quiet_qt_multimedia_logs()

    # --- 2. Imports (après modification du sys.path) ---
    from PySide6.QtWidgets import QApplication, QStackedWidget, QWidget, QVBoxLayout
    from app.ui.menu.home.home_menu import MainMenu
    from app.ui.editor.main_window import EditorWindow
    from core.store import Store
    
    # Imports pour l'injection de dépendance
    from core.export.export_service import ExportService
    from core.export.ffmpeg_engine import FfmpegRenderEngine

    # --- 3. Démarrage de l'application Qt ---
    app = QApplication(sys.argv)

    # --- 4. Instanciation des Services (Couche Logique) ---
    
    # Le Store (Singleton/Source de vérité)
    store_instance = Store()
    store_instance.start_auto_save() 
    
    # Le Moteur de Rendu (Implémentation concrète)
    render_engine = FfmpegRenderEngine()
    
    # Le Service d'Export (Interface)
    # Nous injectons le moteur *dans* le service.
    export_service = ExportService(engine=render_engine)

    # --- 5. Instanciation de l'UI (Couche Vue) ---
    
    stacked = QStackedWidget()
    
    # Injection des services dans la fenêtre de l'éditeur
    editor = EditorWindow(
        store=store_instance, 
        export_service=export_service
    ) 

    # --- 6. Configuration de la Navigation ---
    def go_to_editor():
        """
        Bascule vers l'éditeur. Exécute la logique de choix 
        Nouveau/Charger avant de montrer l'éditeur.
        """
        editor.setup_project_on_entry()       
        stacked.setCurrentWidget(editor)

    main_menu = MainMenu(go_to_editor)

    # Note: La logique "go_back_to_menu" est (probablement) gérée
    # à l'intérieur de EditorWindow via un signal.

    stacked.addWidget(main_menu)
    stacked.addWidget(editor)
    stacked.setCurrentWidget(main_menu)

    # --- 7. Fenêtre Principale ---
    window = QWidget()
    layout = QVBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0) # Remplir la fenêtre
    layout.addWidget(stacked)
    
    # Connexion du titre de la fenêtre au Store
    window.setWindowTitle(f"Luminare - {store_instance.project().name}")
    store_instance.changed.connect(
        lambda: window.setWindowTitle(f"Luminare - {store_instance.project().name}")
    )
    
    window.showMaximized() # Démarrer en plein écran

    # --- 8. Exécution ---
    sys.exit(app.exec())

if __name__ == "__main__":
    main()