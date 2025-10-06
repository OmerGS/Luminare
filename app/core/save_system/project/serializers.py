import os
import platform
import struct
from project.project import Project

class LMPRJChunkedSerializer:
    EXTENSION = ".lmprj"
    APP_NAME = "Luminare"

    @staticmethod
    def get_save_dir() -> str:
        system = platform.system()
        if system == "Windows":
            base = os.getenv("APPDATA")
            if not base:
                base = os.path.join(os.environ['USERPROFILE'], "AppData", "Roaming")
        else:
            base = os.getenv("XDG_DATA_HOME")
            if not base:
                base = os.path.expanduser("~/.local/share")
        
        save_dir = os.path.join(base, LMPRJChunkedSerializer.APP_NAME)
        os.makedirs(save_dir, exist_ok=True)
        return save_dir


    @staticmethod
    def save(project: Project, filename: str):
        if not filename.endswith(LMPRJChunkedSerializer.EXTENSION):
            filename += LMPRJChunkedSerializer.EXTENSION
        filepath = os.path.join(LMPRJChunkedSerializer.get_save_dir(), filename)

        with open(filepath, "wb") as f:
            def write_chunk(chunk_id: str, data: bytes):
                f.write(chunk_id.encode("ascii"))
                f.write(struct.pack("I", len(data)))
                f.write(data)

            # NAME
            write_chunk("NAME", project.name.encode("utf-8"))
            # RESOLUTION
            write_chunk("RESO", struct.pack("II", *project.resolution))
            # FPS
            write_chunk("FPS ", struct.pack("f", project.fps))
            # OUTPUT
            write_chunk("OUTP", project.output.encode("utf-8"))
            # AUDIO_NORMALIZE
            write_chunk("AUDN", struct.pack("?", project.audio_normalize))
            # CLIPS
            for clip in project.clips:
                clip_data = clip["path"].encode("utf-8") + b'\0' + struct.pack("ff", *clip.get("trim", (0.0,0.0)))
                write_chunk("CLIP", clip_data)

        print(f"✅ Projet sauvegardé dans : {filepath}")
        return filepath

    @staticmethod
    def load(filename: str) -> Project:
        filepath = os.path.join(LMPRJChunkedSerializer.get_save_dir(), filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Le fichier {filepath} n'existe pas !")

        proj = Project()
        with open(filepath, "rb") as f:
            while True:
                header = f.read(8)
                if not header:
                    break
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

        print(f"✅ Projet chargé depuis : {filepath}")
        return proj


# ---------- Petit test ----------
if __name__ == "__main__":
    from .project import Project

    proj = Project("Film V2", resolution=(1280, 720), fps=24)
    proj.add_clip({"path": "assets/video.mp4", "trim": (0,5)})
    proj.add_clip({"path": "assets/video2.mp4", "trim": (10,20)})

    LMPRJChunkedSerializer.save(proj, "project1.lmprj")

    loaded = LMPRJChunkedSerializer.load("project1.lmprj")
    print(loaded.to_dict())