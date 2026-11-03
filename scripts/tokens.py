"""Terminalcore role colours. Names stay the ones the renderers already call."""

import argparse
from pathlib import Path

THEMES = {
    "night": {
        "page": "#16161e",
        "screen_bg": "#1a1b26",
        "screen_bg_alt": "#16161e",
        "sunken": "#101018",
        "grid": "#1f2233",
        "grid_major": "#292e42",
        "border": "#3b4261",
        "grid_soft": "#292e42",
        "text": "#c0caf5",
        "text_dim": "#a9b1d6",
        "label": "#8089b3",
        "lab": "#9ece6a",
        "workshop": "#7aa2f7",
        "accent2": "#7dcfff",
        "env": "#8089b3",
        "warn": "#e0af68",
        "negative": "#f7768e",
        "signal": "#7aa2f7",
        "phosphor": "#9ece6a",
        "cyan": "#7dcfff",
        "bezel_top": "#101018",
        "bezel_bottom": "#101018",
        "bezel_highlight": "#292e42",
        "bezel_shadow": "#16161e",
        "bezel_label": "#8089b3",
        "bezel_text": "#a9b1d6",
        "bezel_vent": "#1f2233",
        "scan": "#c0caf5",
        "scan_opacity": "0.055",
        "dither": "#2b3150",
        "dither_opacity": "0.055",
        "dither_opacity_alt": "0.055",
        "inverse_bg": "#c0caf5",
        "inverse_ink": "#16161e",
        "contrib": ("#292e42", "#1f2a4a", "#565f89", "#7aa2f7", "#9ece6a"),
        "lockup": "brand/lockup-night.svg",
        "lockup_fill": "#c0caf5",
    },
    "day": {
        "page": "#e1e2e7",
        "screen_bg": "#eceef3",
        "screen_bg_alt": "#e1e2e7",
        "sunken": "#d0d5e3",
        "grid": "#d0d5e3",
        "grid_major": "#b6bdd3",
        "border": "#3760bf",
        "grid_soft": "#b6bdd3",
        "text": "#1f2335",
        "text_dim": "#343b58",
        "label": "#4c5585",
        "lab": "#3d6b1f",
        "workshop": "#2459c9",
        "accent2": "#005f80",
        "env": "#4c5585",
        "warn": "#7a5200",
        "negative": "#c0174a",
        "signal": "#2459c9",
        "phosphor": "#3d6b1f",
        "cyan": "#005f80",
        "bezel_top": "#d0d5e3",
        "bezel_bottom": "#d0d5e3",
        "bezel_highlight": "#b6bdd3",
        "bezel_shadow": "#e1e2e7",
        "bezel_label": "#4c5585",
        "bezel_text": "#343b58",
        "bezel_vent": "#d0d5e3",
        "scan": "#1f2335",
        "scan_opacity": "0.055",
        "dither": "#b6bdd3",
        "dither_opacity": "0.055",
        "dither_opacity_alt": "0.055",
        "inverse_bg": "#1f2335",
        "inverse_ink": "#e1e2e7",
        "contrib": ("#d0d5e3", "#d5e1f7", "#5d6aa3", "#2459c9", "#3d6b1f"),
        "lockup": "brand/lockup-day.svg",
        "lockup_fill": "#1f2335",
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


def options(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", choices=tuple(THEMES))
    parser.add_argument("--preset", default=None)
    args = parser.parse_args(argv)
    themes = (args.theme,) if args.theme else tuple(THEMES)
    return themes, args.preset


def chosen(argv=None):
    themes, _preset = options(argv)
    return themes
