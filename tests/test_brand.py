"""Brand don'ts: no gradient, filter, rounded corners, or retired colours."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_rendered_svg_has_no_gradient_filter_or_radius():
    for path in (ROOT / "assets").rglob("*.svg"):
        text = path.read_text(encoding="utf-8")
        assert "linearGradient" not in text, path.name
        assert "radialGradient" not in text, path.name
        assert "<filter" not in text, path.name
        assert not re.search(r"\brx=", text), path.name
        assert not re.search(r"\bry=", text), path.name
