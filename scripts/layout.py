"""Canvas sizes. One file, three presets. Standard library only."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "layout.json"
INSET = 28
GUTTER = 12


def _unit(value):
    number = float(value)
    if number.is_integer():
        return int(number)
    return number


def frame_x(col, cols, w):
    """Column frame inside a viewport of width w. Outer edges stay flush; each inner edge steps in by half the gutter."""
    if cols < 1 or not 0 <= col < cols:
        raise ValueError(f"column {col} is outside 0..{cols - 1}")
    half = GUTTER / 2
    x0 = 0 if col == 0 else half
    x1 = w if col == cols - 1 else w - half
    return (_unit(x0), _unit(x1))


def load(preset=None):
    data = json.loads(PATH.read_text(encoding="utf-8"))
    name = data["preset"] if preset is None else preset
    presets = data["presets"]
    if name not in presets:
        known = ", ".join(sorted(presets))
        raise ValueError(f"unknown preset: {name} (known: {known})")
    spec = dict(presets[name])
    spec["preset"] = name
    return spec
