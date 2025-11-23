# app/core/utils_timeline.py
from __future__ import annotations
from typing import List, Dict, Any
from dataclasses import is_dataclass

def _clip_bounds_seconds(c: Any) -> tuple[float, float]:
    # Nouveau modèle
    if hasattr(c, "in_s") and hasattr(c, "out_s"):
        start = float(getattr(c, "in_s", 0.0))
        out_s = float(getattr(c, "out_s", 0.0))
        dur = float(getattr(c, "duration_s", 0.0))
        if out_s <= 0.0 and dur > 0.0:
            end = start + dur
        else:
            end = out_s
        return max(0.0, start), max(start, end)

    # fallback
    return 0.0, 0.0


def clips_to_timeline_items(clips: List[Any]) -> List[Dict]:
    """
    Convertit Project.clips -> items pour TimelineView :
      [{ "start": <sec>, "duration": <sec>, "label": "<nom>", "color": "#RRGGBB" }, ...]
    """
    items: List[Dict] = []
    acc = 0.0
    for c in clips:
        start_s, end_s = _clip_bounds_seconds(c)
        if end_s <= start_s:
            continue
        dur = end_s - start_s
        items.append({
            "start": acc,
            "duration": dur,
            "label": getattr(c, "path", "clip"),
            "color": "#7fb3ff",
        })
        acc += dur
    return items


def total_sequence_duration_ms(clips: List[Any]) -> int:
    acc = 0.0
    for c in clips:
        s, e = _clip_bounds_seconds(c)
        if e > s:
            acc += (e - s)
    return int(acc * 1000)
