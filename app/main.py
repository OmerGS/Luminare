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
    """
    Ajoute un FFmpeg portable au PATH si disponible sous vendor/ffmpeg.
    (N'affecte rien si ffmpeg est déjà dans le PATH.)
    """
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
    """
    Optionnel : rend le terminal plus propre.
    Désactive les warnings verbeux de QtMultimedia/FFmpeg.
    """
    os.environ.setdefault(
        "QT_LOGGING_RULES",
        "qt.multimedia.ffmpeg.debug=false;qt.multimedia.ffmpeg.warning=false"
    )

def main():
    root = set_cwd_to_repo_root()
    bootstrap_ffmpeg_on_path(root)
    ensure_cache_dirs(root)
    quiet_qt_multimedia_logs()   # <- enlève si tu veux voir les logs Qt

    from PySide6.QtWidgets import QApplication
    from app.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
