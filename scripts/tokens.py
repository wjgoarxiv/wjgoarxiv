"""Theme tokens. Hex values are resolved folke/tokyonight extras.

Source: extras/lua/tokyonight_night.lua and extras/lua/tokyonight_day.lua
(the day extra is the inverted storm/moon result, not the raw day.lua stub).
"""

import argparse
from pathlib import Path

LOCKUP_DARK = "#F3EFE7"
LOCKUP_LIGHT = "#26282D"

# Semantic roles. Texture keys are intensity, not a second palette.
THEMES = {
    "night": {
        "screen_bg": "#1a1b26",  # bg
        "screen_bg_alt": "#16161e",  # bg_dark
        "grid": "#414868",  # terminal_black
        "border": "#414868",  # terminal_black
        "grid_soft": "#292e42",  # bg_highlight
        "text": "#c0caf5",  # fg
        "text_dim": "#a9b1d6",  # fg_dark
        "lab": "#9ece6a",  # green
        "workshop": "#7aa2f7",  # blue
        "accent2": "#7dcfff",  # cyan
        "env": "#a9b1d6",  # fg_dark
        "warn": "#e0af68",  # yellow
        "bezel_top": "#16181c",
        "bezel_bottom": "#1d2026",
        "bezel_highlight": "#2a2e36",
        "bezel_shadow": "#0a0c10",
        "bezel_label": "#6d7580",
        "bezel_text": "#8ea3bb",
        "bezel_vent": "#101216",
        "scan": "#000000",
        "scan_opacity": "0.34",
        "dither": "#c0caf5",
        "dither_opacity": "0.07",
        "dither_opacity_alt": "0.045",
        "vig": "#000000",
        "vig_opacity": "0.50",
        "bloom_opacity": "0.85",
        "bloom_blur": "2.4",
        "lockup": "lockup-dark.svg",
        "lockup_fill": LOCKUP_DARK,
    },
    "day": {
        "screen_bg": "#e1e2e7",  # bg
        "screen_bg_alt": "#d0d5e3",  # bg_dark
        "grid": "#a1a6c5",  # terminal_black
        "border": "#8990b3",  # dark3 — terminal_black is 1.85:1 and drops the frame
        "grid_soft": "#c4c8da",  # bg_highlight
        "text": "#3760bf",  # fg
        # blue5, not fg_dark: fg_dark is 3.57:1 on day bg, under 4.5 for small type.
        "text_dim": "#006a83",  # blue5
        "lab": "#587539",  # green
        # blue1, not blue: named blue is 3.11:1 and sits on top of fg.
        "workshop": "#188092",  # blue1
        "accent2": "#007197",  # cyan
        # blue5, not fg_dark: fg_dark is 3.57:1 and the dot-matrix ENV bar disappears.
        "env": "#006a83",  # blue5
        "warn": "#b15c00",  # orange
        "bezel_top": "#e0dcd4",
        "bezel_bottom": "#c8c4bc",
        "bezel_highlight": "#eeeae3",
        "bezel_shadow": "#9e998f",
        "bezel_label": "#5c574e",
        "bezel_text": "#4a463f",
        "bezel_vent": "#b3aea4",
        "scan": "#3760bf",
        "scan_opacity": "0.08",
        "dither": "#6172b0",
        "dither_opacity": "0.035",
        "dither_opacity_alt": "0.02",
        "vig": "#1a1b26",
        "vig_opacity": "0.08",
        "bloom_opacity": "0",
        "bloom_blur": "0",
        "lockup": "lockup-light.svg",
        "lockup_fill": LOCKUP_LIGHT,
    },
}


def themed_path(path, theme):
    path = Path(path)
    stem = path.stem
    if stem.endswith("-night") or stem.endswith("-day"):
        stem = stem.rsplit("-", 1)[0]
    return path.with_name(f"{stem}-{theme}{path.suffix}")


def retire_unthemed(path):
    path = Path(path)
    if path.is_file() and not path.stem.endswith(("-night", "-day")):
        path.unlink()


def chosen(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", choices=tuple(THEMES))
    args = parser.parse_args(argv)
    return (args.theme,) if args.theme else tuple(THEMES)
