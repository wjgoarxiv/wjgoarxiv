"""Terminalcore lockup replaces the retired CI r7 mark."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANNED = ("#F3EFE7", "#f3efe7", "#26282D", "#26282d", "#AEB5A8", "#aeb5a8")


MODULE = "M28 28H88V61.84A40 40 0 0 0 61.84 88H28Z"


def test_brand_files_and_retired_colours():
    for name in ("lockup-night.svg", "lockup-day.svg", "symbol-night.svg", "symbol-day.svg"):
        text = (ROOT / "assets" / "brand" / name).read_text(encoding="utf-8")
        assert MODULE in text
        assert "M28 28H88V88H28Z" not in text
        assert "<mask" not in text
        assert "<circle" not in text
        assert "<text" not in text.lower()
        assert 'type="rotate"' not in text
        assert 'type="scale"' not in text
        box = [float(part) for part in re.search(r'viewBox="([^"]+)"', text).group(1).split()]
        assert box[1] >= -1, name
        if name.startswith("lockup"):
            assert 'data-cap="' in text
            cap = float(re.search(r'data-cap="([0-9.]+)"', text).group(1))
            assert box[3] < cap * 1.6
            assert box[3] > cap * 1.05
    for path in ROOT.rglob("*"):
        if path.suffix.lower() not in {".py", ".svg", ".md", ".json"}:
            continue
        if path.name in {"test_lockup.py", "test_brand.py"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for color in BANNED:
            assert color not in text, (path, color)
