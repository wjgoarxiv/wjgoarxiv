"""Shields-style badges. Outlined Meslo, no third-party image host."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layout
import svgtext
import tokens

ROOT = Path(__file__).resolve().parents[1]
BADGES = ROOT / "data" / "badges.json"
FACE = "meslo-regular"
ROLE = {"id": "lab", "link": "workshop", "live": "warn"}


def _load_live(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _value(badge, live):
    if badge.get("live_key"):
        return str(live[badge["live_key"]])
    return str(badge["value"])


def _ink(theme_name):
    # Day role colors sit under 4.5 against screen_bg. White clears them.
    # Night role colors are the light phosphor, so the screen background is the ink.
    if theme_name == "day":
        return "#ffffff"
    return tokens.THEMES[theme_name]["screen_bg"]


def _label_ink(theme_name):
    if theme_name == "day":
        return tokens.LOCKUP_LIGHT
    return tokens.THEMES[theme_name]["text"]


def _size(badge_h):
    if badge_h >= 32:
        return 13
    if badge_h >= 28:
        return 12
    return 10


def render_badge(badge, live, theme_name, preset=None):
    spec = layout.load(preset)
    badge_h = spec["badge_h"]
    theme = tokens.THEMES[theme_name]
    value = _value(badge, live)
    size = _size(badge_h)
    pad = 6
    dot = 3.0
    label_text_x = pad + dot + 4
    label_w = label_text_x + svgtext.text_width(badge["label"], FACE, size, 0) + pad
    value_w = svgtext.text_width(value, FACE, size, 0) + pad * 2
    width = round(label_w + value_w, 1)
    label_w = round(label_w, 1)
    value_w = round(width - label_w, 1)
    baseline = round(badge_h / 2 + 0.34 * size, 2)
    chip = theme[ROLE[badge["group"]]]
    ink = _ink(theme_name)
    label_ink = _label_ink(theme_name)
    dot_y = round(badge_h / 2 - dot / 2, 2)
    label = svgtext.render(badge["label"], FACE, size, label_text_x, baseline, label_ink, 0)
    value_text = svgtext.render(value, FACE, size, label_w + pad, baseline, ink, 0)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{badge_h}" '
        f'viewBox="0 0 {width} {badge_h}">'
        f"<defs><clipPath id=\"badge\">"
        f'<rect width="{width}" height="{badge_h}" rx="3" ry="3"/></clipPath></defs>'
        f'<g clip-path="url(#badge)">'
        f'<rect width="{label_w}" height="{badge_h}" fill="{theme["grid_soft"]}"/>'
        f'<rect class="value" x="{label_w}" width="{value_w}" height="{badge_h}" fill="{chip}"/>'
        f"</g>"
        f'<rect x="{pad}" y="{dot_y}" width="{dot}" height="{dot}" fill="{label_ink}"/>'
        f"{label}"
        f'<g class="value-ink" fill="{ink}">{value_text}</g>'
        f"<!-- manifest:{badge['label']}={value} -->"
        f"</svg>"
    )


def write_badges(fixture, out_dir, preset=None, themes=None):
    live = _load_live(fixture)
    badges = json.loads(BADGES.read_text(encoding="utf-8"))
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for theme_name in themes or ("night", "day"):
        for badge in badges:
            dest = out_dir / f"{badge['id']}-{theme_name}.svg"
            dest.write_text(render_badge(badge, live, theme_name, preset), encoding="utf-8")
            written.append(dest)
    return written


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=ROOT / "assets" / "badges")
    parser.add_argument("--preset", default=None)
    parser.add_argument("--theme", choices=tuple(tokens.THEMES))
    args = parser.parse_args(argv)
    if args.fixture is None:
        args.fixture = ROOT / "data" / "live.json"
        if not args.fixture.exists():
            raise SystemExit("render_badges.py needs data/live.json or --fixture")
    themes = (args.theme,) if args.theme else None
    write_badges(args.fixture, args.out, args.preset, themes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
