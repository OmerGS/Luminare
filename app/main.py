from __future__ import annotations
import os

from core.save_system.save_api import ProjectAPI
os.environ["QT_MEDIA_USE_HARDWARE_DECODER"] = "0"
os.environ["QT_MEDIA_BACKEND"] = "ffmpeg"
from pathlib import Path
from ui import styles

import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def set_cwd_to_repo_root():
    root = Path(__file__).resolve().parent
    if Path.cwd() != root:
        os.chdir(root)
    return root

def bootstrap_ffmpeg_on_path(root: Path):
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
    for d in [root / "cache", root / "cache" / "wave"]:
        d.mkdir(parents=True, exist_ok=True)

def quiet_qt_multimedia_logs():
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
    from PySide6.QtCore import QUrl
    from app.ui.menu.home.home_menu import MainMenu
    from app.ui.editor.main_window import EditorWindow
    from core.store import Store
    
    from core.export.export_service import ExportService
    from core.export.ffmpeg_engine import FfmpegRenderEngine

    app = QApplication(sys.argv)

    store_instance = Store()
    store_instance.start_auto_save() 
    
    render_engine = FfmpegRenderEngine()
    
    export_service = ExportService(engine=render_engine)

    stacked = QStackedWidget()
    
    editor = EditorWindow(
        store=store_instance, 
        export_service=export_service
    ) 

    def go_to_editor():
        editor.setup_project_on_entry()       
        stacked.setCurrentWidget(editor)


    def go_to_editor_with_project_name(project_name):
        """
        Charge le projet spécifié par `project_name` et bascule vers l'éditeur.
        """
        store = editor.store
        try:
            store.load_project(project_name)
            proj = store.project()
            
            if proj.clips:
                 editor.seq.seek_ms(0)
                 
            editor._on_store_clips_changed() 
            
        except Exception as e:
            print(f"Erreur lors du chargement du projet '{project_name}' : {e}")
            
        stacked.setCurrentWidget(editor)
        editor.setWindowTitle(f"Luminare — {editor.store.project().name}")
        
        

    project_list_data = ProjectAPI.list_projects()

    main_menu = MainMenu(go_to_editor,go_to_editor_with_project_name, project_list_data)

    stacked.addWidget(main_menu)
    stacked.addWidget(editor)
    stacked.setCurrentWidget(main_menu)

    window = QWidget()
    layout = QVBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(stacked)
    
    window.setWindowTitle(f"Luminare - {store_instance.project().name}")
    store_instance.changed.connect(
        lambda: window.setWindowTitle(f"Luminare - {store_instance.project().name}")
    )
    
    window.showMaximized()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()