"""Brutalist terminalcore badges. Outlined Meslo, no third-party image host."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layout
import motion
import svgtext
import tokens

ROOT = Path(__file__).resolve().parents[1]
BADGES = ROOT / "data" / "badges.json"
FACE = "meslo-regular"
ROLE = {"id": "lab", "link": "workshop", "live": "warn"}


def _load_live(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _value(badge, live):
    if badge["group"] == "link":
        return "→"
    if badge.get("live_key"):
        return str(live[badge["live_key"]])
    return str(badge["value"])


def _size(badge_h):
    if badge_h >= 20:
        return 11
    if badge_h >= 16:
        return 9
    return 8


def render_badge(badge, live, theme_name, preset=None, index=0):
    """One brutalist cell: role tab | label | rule | value, 1px hard frame."""
    spec = layout.load(preset)
    badge_h = spec["badge_h"]
    theme = tokens.THEMES[theme_name]
    value = _value(badge, live)
    size = _size(badge_h)
    pad = 4
    tab = 3
    label_x = tab + pad
    rule_x = round(label_x + svgtext.text_width(badge["label"], FACE, size, 0) + pad, 1)
    value_x = rule_x + 1
    width = round(value_x + pad + svgtext.text_width(value, FACE, size, 0) + pad, 1)
    baseline = round(badge_h / 2 + 0.34 * size, 2)
    ground = theme["sunken"]
    label = svgtext.render(badge["label"], FACE, size, label_x, baseline, theme["label"], 0)
    value_text = svgtext.render(value, FACE, size, value_x + pad, baseline, theme["text"], 0)
    wait = motion.delay_s(index, 0.04, motion.MOTION["badge_stagger_ms"] / 1000)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{badge_h}" '
        f'viewBox="0 0 {width} {badge_h}">'
        f"{motion.badge_style(wait)}"
        f'<rect width="{rule_x}" height="{badge_h}" fill="{ground}"/>'
        f'<rect class="value" x="{rule_x}" width="{round(width - rule_x, 1)}" height="{badge_h}" fill="{ground}"/>'
        f'<rect class="tab" width="{tab}" height="{badge_h}" fill="{theme[ROLE[badge["group"]]]}"/>'
        f'<rect class="rule" x="{rule_x}" width="1" height="{badge_h}" fill="{theme["border"]}"/>'
        f"{label}"
        f'<g class="value-ink" fill="{theme["text"]}">{value_text}</g>'
        f'<rect class="frame" x="0.5" y="0.5" width="{round(width - 1, 1)}" height="{badge_h - 1}" '
        f'fill="none" stroke="{theme["border"]}" stroke-width="1"/>'
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
        for index, badge in enumerate(badges):
            dest = out_dir / f"{badge['id']}-{theme_name}.svg"
            dest.write_text(render_badge(badge, live, theme_name, preset, index), encoding="utf-8")
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
