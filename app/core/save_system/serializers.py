import os
import platform
import struct
from core.project import Project

class LMPRJChunkedSerializer:
    EXTENSION = ".lmprj"
    APP_NAME = "Luminare"

    @staticmethod
    def get_save_dir() -> str:
        system = platform.system()
        if system == "Windows":
            base = os.path.join(os.environ['USERPROFILE'], "Desktop")
        else:            base = os.getenv("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
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
            LMPRJChunkedSerializer.write_chunk(f, "NAME", project.name.encode("utf-8"))
            LMPRJChunkedSerializer.write_chunk(f, "RESO", struct.pack("II", *project.resolution))
            LMPRJChunkedSerializer.write_chunk(f, "FPS ", struct.pack("f", project.fps))
            LMPRJChunkedSerializer.write_chunk(f, "OUTP", project.output.encode("utf-8"))
            LMPRJChunkedSerializer.write_chunk(f, "AUDN", struct.pack("?", project.audio_normalize))
            for clip in project.clips:
                clip_data = clip["path"].encode("utf-8") + b'\0' + struct.pack("ff", *clip.get("trim", (0.0,0.0)))
                LMPRJChunkedSerializer.write_chunk(f, "CLIP", clip_data)
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
                if not header: break
                chunk_id, length = struct.unpack("4sI", header)
                chunk_id = chunk_id.decode("ascii")
                data = f.read(length)

                if chunk_id == "NAME":
                    proj.name = data.decode("utf-8")
                elif chunk_id == "RESO":
                    proj.resolution = struct.unpack("II", data)
                elif chunk_id == "FPS ":
                    proj.fps = struct.unpack("f", data)[0]
                elif chunk_id == "OUTP":
                    proj.output = data.decode("utf-8")
                elif chunk_id == "AUDN":
                    proj.audio_normalize = struct.unpack("?", data)[0]
                elif chunk_id == "CLIP":
                    path, trim_bytes = data.split(b'\0', 1)
                    trim = struct.unpack("ff", trim_bytes)
                    proj.add_clip({"path": path.decode("utf-8"), "trim": trim})

        return proj