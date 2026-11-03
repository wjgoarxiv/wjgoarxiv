"""WCAG contrast for both theme token sets."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.tokens import THEMES


def _channel(value):
    value = value / 255
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def luminance(hex_color):
    raw = hex_color.lstrip("#")
    red, green, blue = (int(raw[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def contrast(left, right):
    hi, lo = sorted((luminance(left), luminance(right)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_body_and_accents_clear_both_themes():
    for name, theme in THEMES.items():
        bg = theme["screen_bg"]
        assert contrast(theme["text"], bg) >= 4.5, name
        assert contrast(theme["text_dim"], bg) >= 4.5, name
        for role in ("lab", "workshop", "warn", "env", "accent2"):
            ratio = contrast(theme[role], bg)
            assert ratio >= 3.0, (name, role, round(ratio, 2))
