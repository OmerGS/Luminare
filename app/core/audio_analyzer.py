from __future__ import annotations
import hashlib, json, wave, subprocess, shutil
from pathlib import Path
import numpy as np

def _hash(s: str) -> str:
    import hashlib as _h
    return _h.sha1(s.encode("utf-8")).hexdigest()[:16]

def _cache_dir() -> Path:
    d = Path("cache") / "wave"
    d.mkdir(parents=True, exist_ok=True)
    return d

def _which_ffmpeg() -> str:
    """
    Trouve ffmpeg (PATH ou vendor/ffmpeg/*/bin/ffmpeg[.exe]).
    Lève une exception explicite si introuvable.
    """
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    # fallback vendor
    candidates = [
        Path("vendor/ffmpeg/windows/bin/ffmpeg.exe"),
        Path("vendor/ffmpeg/win64/bin/ffmpeg.exe"),
        Path("vendor/ffmpeg/linux/bin/ffmpeg"),
        Path("vendor/ffmpeg/macos/bin/ffmpeg"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    raise FileNotFoundError("FFmpeg introuvable. Ajoute-le au PATH ou place-le dans vendor/ffmpeg/...")

def extract_audio_wav(src_path: str, dst_wav: Path, sr: int = 8000) -> None:
    """
    Utilise FFmpeg pour extraire l'audio en mono PCM WAV (16-bit), downsamplé.
    Écrase si le fichier existe déjà.
    """
    dst_wav.parent.mkdir(parents=True, exist_ok=True)
    ff = _which_ffmpeg()
    cmd = [
        ff, "-hide_banner", "-loglevel", "error", "-nostdin",
        "-y",                      # overwrite
        "-i", src_path,
        "-vn", "-ac", "1", "-ar", str(sr), "-sample_fmt", "s16",
        str(dst_wav)
    ]
    # capture les erreurs pour les remonter propres
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg a échoué ({res.returncode}).\nCmd: {' '.join(cmd)}\nStderr:\n{res.stderr}")

def compute_rms_envelope(wav_path: Path, window_ms: int = 10) -> tuple[np.ndarray, int]:
    """
    Calcule une enveloppe RMS normalisée (0..1) par fenêtres glissantes.
    Retourne (array[N], samples_per_second_for_envelope).
    """
    with wave.open(str(wav_path), "rb") as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        fr = wf.getframerate()
        n_frames = wf.getnframes()
        if not (n_channels == 1 and sample_width == 2):
            raise ValueError(f"WAV inattendu (channels={n_channels}, sbytes={sample_width})")
        raw = wf.readframes(n_frames)

    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    hop = max(1, int(fr * (window_ms / 1000.0)))
    n = max(1, len(x) // hop)
    env = np.zeros(n, dtype=np.float32)
    for i in range(n):
        seg = x[i*hop : (i+1)*hop]
        if seg.size:
            env[i] = np.sqrt(np.mean(seg * seg))

    p95 = float(np.percentile(env, 95)) if env.size else 1.0
    scale = p95 if p95 > 1e-6 else 1.0
    env = np.clip(env / scale, 0.0, 1.0)
    sps = int(round(1000.0 / window_ms))
    return env, sps

def analyze_waveform(src_path: str, sr: int = 8000, window_ms: int = 10) -> tuple[np.ndarray, int]:
    """
    Analyse avec cache (WAV et NPY). Renvoie (enveloppe, samples_per_second).
    """
    cache = _cache_dir()
    h = _hash(f"{src_path}|{sr}|{window_ms}")
    wav_path = cache / f"{h}.wav"
    npy_path = cache / f"{h}.npy"
    meta_path = cache / f"{h}.json"

    if npy_path.exists() and meta_path.exists():
        try:
            env = np.load(npy_path)
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            return env, int(meta.get("sps", 100))
        except Exception:
            pass

    if not wav_path.exists():
        extract_audio_wav(src_path, wav_path, sr=sr)

    env, sps = compute_rms_envelope(wav_path, window_ms=window_ms)
    np.save(npy_path, env)
    meta_path.write_text(json.dumps({"sps": sps}), encoding="utf-8")
    return env, sps
