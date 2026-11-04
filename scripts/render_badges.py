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


def _fit(text, face, size, max_width):
    if svgtext.text_width(text, face, size, 0) <= max_width:
        return text
    stem = text
    while stem and svgtext.text_width(stem + "...", face, size, 0) > max_width:
        stem = stem[:-1].rstrip()
    return (stem + "...") if stem else "..."


def _draw_width(badge):
    slot = int(badge["w"])
    catalog = json.loads(BADGES.read_text(encoding="utf-8"))
    row = [item for item in catalog if item.get("row") == badge.get("row")]
    if row and row[-1]["id"] == badge["id"]:
        return slot
    return slot - 3


def _num(value):
    text = f"{float(value):.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def _cup(x, y, fill):
    """12×12 pixel cup: body, right handle, two 1×2 steam ticks. Rects only."""
    body = y + 4
    return (
        f'<rect x="{x + 3}" y="{y}" width="1" height="2" fill="{fill}"/>'
        f'<rect x="{x + 7}" y="{y}" width="1" height="2" fill="{fill}"/>'
        f'<rect x="{x}" y="{body}" width="8" height="1" fill="{fill}"/>'
        f'<rect x="{x}" y="{body}" width="1" height="7" fill="{fill}"/>'
        f'<rect x="{x + 7}" y="{body}" width="1" height="7" fill="{fill}"/>'
        f'<rect x="{x}" y="{body + 6}" width="8" height="1" fill="{fill}"/>'
        f'<rect x="{x + 8}" y="{body + 1}" width="3" height="1" fill="{fill}"/>'
        f'<rect x="{x + 10}" y="{body + 1}" width="1" height="4" fill="{fill}"/>'
        f'<rect x="{x + 8}" y="{body + 4}" width="3" height="1" fill="{fill}"/>'
    )


def render_badge(badge, live, theme_name, preset=None, index=0):
    """One brutalist cell: role tab | label | rule | value, 1px hard frame."""
    spec = layout.load(preset)
    badge_h = spec["badge_h"]
    theme = tokens.THEMES[theme_name]
    value = _value(badge, live)
    size = _size(badge_h)
    pad = 4
    width = int(badge["w"])
    draw = _draw_width(badge)
    baseline = round(badge_h / 2 + 0.34 * size, 2)
    if badge.get("style") == "cta":
        ink = theme["inverse_ink"]
        ground = theme["warn"]
        cup = 12
        cup_x = 6
        cup_y = max(0, (badge_h - cup) // 2)
        label_x = cup_x + cup + 6
        arrow_w = svgtext.text_width(value, FACE, size, 0)
        arrow_x = round(draw - 6 - arrow_w, 2)
        label = svgtext.render(badge["label"], FACE, size, label_x, baseline, ink, 0)
        arrow = svgtext.render(value, FACE, size, arrow_x, baseline, ink, 0)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{badge_h}" '
            f'viewBox="0 0 {width} {badge_h}">'
            f'<rect class="value" width="{draw}" height="{badge_h}" fill="{ground}"/>'
            f"{_cup(cup_x, cup_y, ink)}"
            f'<g class="value-ink" fill="{ink}">{label}{arrow}</g>'
            f"<!-- manifest:{badge['label']}={value} -->"
            f"</svg>"
        )
    tab = 3
    label_x = tab + pad
    rule_x = round(label_x + svgtext.text_width(badge["label"], FACE, size, 0) + pad, 1)
    value_x = rule_x + 1
    if badge["group"] == "link":
        arrow_w = svgtext.text_width(value, FACE, size, 0)
        text_x = round(draw - 6 - arrow_w, 2)
        shown = value
    else:
        text_x = value_x + pad
        shown = _fit(value, FACE, size, draw - pad - text_x)
    ground = theme["sunken"]
    label = svgtext.render(badge["label"], FACE, size, label_x, baseline, theme["label"], 0)
    value_text = svgtext.render(shown, FACE, size, text_x, baseline, theme["text"], 0)
    wait = motion.delay_s(index, 0.04, motion.MOTION["badge_stagger_ms"] / 1000)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{badge_h}" '
        f'viewBox="0 0 {width} {badge_h}">'
        f"{motion.badge_style(wait)}"
        f'<rect width="{_num(rule_x)}" height="{badge_h}" fill="{ground}"/>'
        f'<rect class="value" x="{_num(rule_x)}" width="{_num(draw - rule_x)}" height="{badge_h}" fill="{ground}"/>'
        f'<rect class="tab" width="{tab}" height="{badge_h}" fill="{theme[ROLE[badge["group"]]]}"/>'
        f'<rect class="rule" x="{_num(rule_x)}" width="1" height="{badge_h}" fill="{theme["border"]}"/>'
        f"{label}"
        f'<g class="value-ink" fill="{theme["text"]}">{value_text}</g>'
        f'<rect class="frame" x="0.5" y="0.5" width="{_num(draw - 1)}" height="{badge_h - 1}" '
        f'fill="none" stroke="{theme["border"]}" stroke-width="1"/>'
        f"<!-- manifest:{badge['label']}={shown} -->"
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
