"""Canvas sizes. One file, three presets. Standard library only."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "layout.json"


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
