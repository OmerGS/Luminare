# core/save_system/serializers.py
import os
import json
import struct
import platform
from typing import List
from core.project import Project, Clip, TextOverlay, Filters

class LMPRJChunkedSerializer:
    EXTENSION = ".lmprj"
    APP_NAME = "Luminare"
    VERSION = "0.0.1"

    @staticmethod
    def get_save_dir() -> str:
        system = platform.system()
        if system == "Windows":
            base = os.path.join(os.environ.get('USERPROFILE', '.'), "Desktop")
        else:
            base = os.getenv("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        save_dir = os.path.join(base, LMPRJChunkedSerializer.APP_NAME)
        os.makedirs(save_dir, exist_ok=True)
        return save_dir

    @staticmethod
    def write_chunk(f, chunk_id: str, data: bytes):
        f.write(chunk_id.encode("ascii"))
        f.write(struct.pack("I", len(data)))
        f.write(data)

    @staticmethod
    def save(project: Project, filename: str) -> str:
        if not filename.endswith(LMPRJChunkedSerializer.EXTENSION):
            filename += LMPRJChunkedSerializer.EXTENSION
        filepath = os.path.join(LMPRJChunkedSerializer.get_save_dir(), filename)

        with open(filepath, "wb") as f:
            proj_meta = {"version": LMPRJChunkedSerializer.VERSION, "name": project.name}
            LMPRJChunkedSerializer.write_chunk(f, "PROJ", json.dumps(proj_meta).encode("utf-8"))

            # Resolution
            LMPRJChunkedSerializer.write_chunk(f, "RESO", struct.pack("II", *project.resolution))
            # FPS
            LMPRJChunkedSerializer.write_chunk(f, "FPS ", struct.pack("f", project.fps))
            # Output
            LMPRJChunkedSerializer.write_chunk(f, "OUTP", project.output.encode("utf-8"))
            # Audio normalize
            LMPRJChunkedSerializer.write_chunk(f, "AUDN", struct.pack("?", project.audio_normalize))
            # Filters
            LMPRJChunkedSerializer.write_chunk(f, "FILT", json.dumps(vars(project.filters)).encode("utf-8"))

            if project.imported_assets:
                imported_data = json.dumps(project.imported_assets).encode("utf-8")
                LMPRJChunkedSerializer.write_chunk(f, "IMPT", imported_data)

            # Clips
            for clip in project.clips:
                LMPRJChunkedSerializer.write_chunk(f, "CLIP", json.dumps({"path": clip.path, "in_s": clip.in_s, "out_s": clip.out_s, "duration_s": clip.duration_s}).encode("utf-8"))
            # Text overlays
            for ov in project.text_overlays:
                LMPRJChunkedSerializer.write_chunk(f, "OVER", json.dumps(vars(ov)).encode("utf-8"))

        return filepath

    @staticmethod
    def load(filename: str) -> Project:
        filepath = os.path.join(LMPRJChunkedSerializer.get_save_dir(), filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"{filepath} n'existe pas")

        proj = Project()
        with open(filepath, "rb") as f:
            while True:
                header = f.read(8)
                if not header:
                    break
                try:
                    chunk_id, length = struct.unpack("4sI", header)
                    chunk_id = chunk_id.decode("ascii")
                    data = f.read(length)
                except Exception as e:
                    print(f"Erreur de lecture d’un chunk : {e}")
                    continue

                try:
                    if chunk_id == "PROJ":
                        meta = json.loads(data.decode("utf-8"))
                        proj.name = meta.get("name", proj.name)
                    elif chunk_id == "RESO":
                        proj.resolution = struct.unpack("II", data)
                    elif chunk_id == "FPS ":
                        proj.fps = struct.unpack("f", data)[0]
                    elif chunk_id == "OUTP":
                        proj.output = data.decode("utf-8")
                    elif chunk_id == "AUDN":
                        proj.audio_normalize = struct.unpack("?", data)[0]
                    elif chunk_id == "FILT":
                        filt = json.loads(data.decode("utf-8"))
                        proj.filters = Filters(**filt)
                    elif chunk_id == "IMPT":
                        proj.imported_assets = json.loads(data.decode("utf-8"))
                    elif chunk_id == "CLIP":
                        clip_data = json.loads(data.decode("utf-8"))
                        proj.clips.append(Clip(**clip_data))
                    elif chunk_id == "OVER":
                        ov_data = json.loads(data.decode("utf-8"))
                        proj.text_overlays.append(TextOverlay(**ov_data))
                    else:
                        continue
                except Exception as e:
                    print(f"Erreur de décodage du chunk {chunk_id} : {e}")

        return proj

    # --- Utils ---
    @staticmethod
    def list_projects() -> List[str]:
        save_dir = LMPRJChunkedSerializer.get_save_dir()
        if not os.path.exists(save_dir):
            return []
        return [f for f in os.listdir(save_dir) if f.endswith(LMPRJChunkedSerializer.EXTENSION)]

    @staticmethod
    def get_project_clip_count(filename: str) -> int:
        proj = LMPRJChunkedSerializer.load(filename)
        return len(proj.clips)

    @staticmethod
    def get_save_count() -> int:
        return len(LMPRJChunkedSerializer.list_projects())