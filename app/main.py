# main.py (entrypoint racine)
from __future__ import annotations
import os
from pathlib import Path
import platform
import sys



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
    root = set_cwd_to_repo_root()
    bootstrap_ffmpeg_on_path(root)
    ensure_cache_dirs(root)
    quiet_qt_multimedia_logs()

    from PySide6.QtWidgets import QApplication, QStackedWidget, QWidget, QVBoxLayout
    from app.ui.menu.home.home_menu import MainMenu
    from app.ui.editor.main_window import EditorWindow

    app = QApplication(sys.argv)

    # StackedWidget pour gérer navigation menu <-> éditeur
    stacked = QStackedWidget()

    # Menu principal
    def go_to_editor():
        stacked.setCurrentWidget(editor)

    main_menu = MainMenu(go_to_editor)

    # Éditeur
    def go_back_to_menu():
        stacked.setCurrentWidget(main_menu)

    editor = EditorWindow()

    # Ajouter dans le stack
    stacked.addWidget(main_menu)  # index 0
    stacked.addWidget(editor)     # index 1
    stacked.setCurrentWidget(main_menu)  # <- démarrage sur menu

    # Fenêtre principale
    window = QWidget()
    layout = QVBoxLayout(window)
    layout.addWidget(stacked)
    window.setWindowTitle("Luminare")
    window.showMaximized()  # plein écran

    sys.exit(app.exec())

def main():
    root = set_cwd_to_repo_root()
    bootstrap_ffmpeg_on_path(root)
    ensure_cache_dirs(root)
    quiet_qt_multimedia_logs()

    from PySide6.QtWidgets import QApplication, QStackedWidget, QWidget, QVBoxLayout
    from app.ui.menu.home.home_menu import MainMenu
    from app.ui.editor.main_window import EditorWindow
    from core.store import Store

    app = QApplication(sys.argv)

    store_instance = Store()
    store_instance.start_auto_save() 
    stacked = QStackedWidget()
    editor = EditorWindow(store=store_instance) 

    # Menu principal
    def go_to_editor():
        """
        Bascule vers l'éditeur. Exécute la logique de choix Nouveau/Charger avant de montrer l'éditeur.
        """
        editor.setup_project_on_entry()        
        stacked.setCurrentWidget(editor)

    main_menu = MainMenu(go_to_editor)

    def go_back_to_menu():
        stacked.setCurrentWidget(main_menu)

    stacked.addWidget(main_menu)
    stacked.addWidget(editor)
    stacked.setCurrentWidget(main_menu)

    window = QWidget()
    layout = QVBoxLayout(window)
    layout.addWidget(stacked)
    window.setWindowTitle(f"Luminare - {store_instance.project().name}") 
    window.showMaximized()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()