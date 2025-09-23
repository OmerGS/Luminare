# mvp_editor.py
import ffmpeg
from pathlib import Path

# ---- Définition d'un "projet" minimal ----
project = {
    "clips": [
        {"path": "assets/Fluid_Sim_Hue_Test.mp4", "trim": (0, 5)},
    ],
    "resolution": (1920, 1080),
    "filters": {
        "brightness": 0.05,   # -1.0 .. +1.0
        "contrast": 1.10,     # 0.0 .. inf (1.0 = neutre)
        "saturation": 1.15,   # 0.0 .. inf
        "vignette": True
    },
    "text_overlays": [
        {
            "text": "Mon titre",
            "x": "(w-text_w)/2", "y": "h*0.1",   # expressions FFmpeg
            "fontsize": 48, "fontcolor": "white",
            "box": True, "boxcolor": "black@0.5", "boxborderw": 10,
            "start": 0.5, "end": 4.5, "fontfile": "C:\\Windows\\Fonts\\arial.ttf"
        }
    ],
    "output": "exports/output.mp4",
    "fps": 30,
    "audio_normalize": True
}

def make_trimmed_stream(clip, fps):
    inp = ffmpeg.input(clip["path"])
    if "trim" in clip:
        start, end = clip["trim"]
        dur = max(0, end - start)
        inp = ffmpeg.trim(inp, start=start, duration=dur).setpts('PTS-STARTPTS')
        aud = (ffmpeg.input(clip["path"])
               .filter_('atrim', start=start, duration=dur)
               .filter_('asetpts', 'PTS-STARTPTS'))
    else:
        aud = inp.audio
    # force fps pour une concat propre
    vid = inp.filter('fps', fps=fps)
    return vid, aud

def build_filter_chain(vid, cfg):
    # Taille
    w, h = cfg["resolution"]
    vid = vid.filter("scale", w, h)
    # Correction couleur via eq
    f = cfg["filters"]
    vid = vid.filter('eq',
                     brightness=f.get("brightness", 0.0),
                     contrast=f.get("contrast", 1.0),
                     saturation=f.get("saturation", 1.0))
    # Vignette optionnelle
    if f.get("vignette", False):
        vid = vid.filter('vignette', angle='PI/4', x0='w/2', y0='h/2')

    return vid

def apply_text_overlays(vid, overlays):
    for ov in overlays:
        draw = {
            'text': ov["text"],
            'x': ov.get("x", "0"),
            'y': ov.get("y", "0"),
            'fontsize': ov.get("fontsize", 36),
            'fontcolor': ov.get("fontcolor", "white"),
            'enable': f"between(t,{ov.get('start',0)},{ov.get('end',1e9)})",
        }
        if "fontfile" in ov: draw['fontfile'] = ov["fontfile"]
        if ov.get("box", False):
            draw['box'] = 1
            draw['boxcolor'] = ov.get("boxcolor", "black@0.4")
            draw['boxborderw'] = ov.get("boxborderw", 8)
        vid = vid.filter('drawtext', **draw)
    return vid

def main(cfg: dict):
    fps = cfg.get("fps", 30)

    # 1) Charger + trimmer chaque clip
    videos, audios = [], []
    for clip in cfg["clips"]:
        v, a = make_trimmed_stream(clip, fps)
        videos.append(v); audios.append(a)

    # 2) Concat (vidéo + audio)
    concat = ffmpeg.concat(*[x for pair in zip(videos, audios) for x in pair],
                           v=1, a=1).node
    vcat, acat = concat[0], concat[1]

    # 3) Filtres vidéo globaux
    v = build_filter_chain(vcat, cfg)

    # 4) Overlays de texte
    v = apply_text_overlays(v, cfg.get("text_overlays", []))

    # 5) Audio : normalisation optionnelle
    a = acat
    if cfg.get("audio_normalize", False):
        a = a.filter('loudnorm', i='-16', tp='-1.5', lra='11')

    # 6) Export
    out = Path(cfg["output"])
    out.parent.mkdir(parents=True, exist_ok=True)

    stream = ffmpeg.output(
        v, a, str(out),
        r=fps,
        vcodec='libx264', preset='medium', crf=18, pix_fmt='yuv420p',
        acodec='aac', audio_bitrate='192k',
        movflags='+faststart'
    )
    print("Commande FFmpeg :", ffmpeg.compile(stream))
    ffmpeg.run(stream, overwrite_output=True)

if __name__ == "__main__":
    main(project)
