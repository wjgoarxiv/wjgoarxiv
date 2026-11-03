"""Hydrate-lattice contribution view. Cabinet projection, stdlib only."""

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crt
import layout
import tokens

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "contrib.svg"
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
ANCHOR = date(2025, 11, 2)

STYLE = """<style>
.rise { transform: none; }
@media (prefers-reduced-motion: no-preference) {
  .rise { transform-box: fill-box; transform-origin: 50% 100%; animation: rise 0.4s ease-out forwards; }
  __DELAYS__
}
@keyframes rise {
  from { transform: scaleY(0); }
  to { transform: scaleY(1); }
}
@media (prefers-reduced-motion: reduce) {
  .rise { animation: none !important; transform: none !important; }
}
</style>"""


def _mix(left, right, amount):
    def channel(index):
        a = int(left[index : index + 2], 16)
        b = int(right[index : index + 2], 16)
        return int(round(a * (1 - amount) + b * amount))

    return "#" + "".join(f"{channel(index):02x}" for index in (1, 3, 5))


def _levels(weeks):
    positive = [count for week in weeks for count in week if count > 0]
    peak = max(positive) if positive else 0
    below_peak = [count for count in positive if count < peak]
    grid = []
    for week in weeks:
        row = []
        for count in week:
            if count <= 0:
                row.append(0)
            elif count == peak:
                row.append(4)
            elif not below_peak:
                row.append(4)
            else:
                below = sum(1 for item in below_peak if item < count)
                row.append(min(3, max(1, 1 + (below * 3) // len(below_peak))))
        grid.append(row)
    return grid


def _streak(weeks):
    best = run = 0
    for week in weeks:
        for count in week:
            if count > 0:
                run += 1
                best = max(best, run)
            else:
                run = 0
    return best


def _poly(points):
    head = f"M{points[0][0]:.1f} {points[0][1]:.1f}"
    return head + "".join(f"L{x:.1f} {y:.1f}" for x, y in points[1:]) + "Z"


def _delays(count):
    step = 1.6 / max(count - 1, 1)
    return "\n  ".join(f".w{index} {{ animation-delay: {index * step:.3f}s; }}" for index in range(count))


def _dates(model, cols, rows):
    given = model.get("dates")
    if given:
        return given
    start = date.fromisoformat(model["start"]) if model.get("start") else ANCHOR
    grid = []
    for col in range(cols):
        grid.append([(start + timedelta(days=col * 7 + row)).isoformat() for row in range(rows)])
    return grid


def _ramp(theme, lab, bg):
    """Four columns as (top, front, side). Top is the lightest face."""
    if theme == "day":
        light = "#e7f6c4"
        deep = "#2c4a16"
        tops = tuple(_mix(lab, light, amount) for amount in (0.64, 0.48, 0.32, 0.16))
        return tuple((top, _mix(top, deep, 0.42), _mix(top, deep, 0.68), deep) for top in tops)
    tops = (
        _mix(_mix(lab, bg, 0.62), "#8a8f98", 0.35),
        _mix(lab, bg, 0.46),
        _mix(lab, bg, 0.22),
        lab,
    )
    edge = "#07080c"
    return tuple((top, _mix(top, bg, 0.32), _mix(top, edge, 0.42), edge) for top in tops)


def render_svg(model, theme="night", preset=None):
    spec = layout.load(preset)
    width = spec["width"]
    height = spec["contrib_h"]
    weeks = model["weeks"]
    cols = len(weeks)
    rows = len(weeks[0]) if weeks else 0
    levels = _levels(weeks)
    total = sum(count for week in weeks for count in week)
    dates = _dates(model, cols, rows)
    p = crt.Chrome(theme)
    ramp = _ramp(theme, p.LAB, p.BG)
    # Cabinet: weeks run on x, days recede up-right, columns rise straight up.
    week_pitch = 21.0
    box_w = 12.0
    day_dx, day_dy = 7.0, -11.0
    column_unit = 85.0 / 4
    depth = (7.5, -9.0)
    grid_w = (max(cols - 1, 0) * week_pitch) + (max(rows - 1, 0) * day_dx) + box_w
    origin_x = (width - grid_w) / 2 + box_w / 2
    floor_span = (max(rows - 1, 0) * abs(day_dy)) + (4 * column_unit)
    top_chrome = 56
    bottom_pad = 20
    slack = max(0.0, (height - bottom_pad - top_chrome) - floor_span)
    baseline = top_chrome + slack / 2 + floor_span

    def point(col, row):
        return origin_x + col * week_pitch + row * day_dx, baseline + row * day_dy

    bonds = []
    nodes = []
    if theme == "day":
        bond_ink = _mix(p.GRID, p.LAB, 0.55)
        node_ink = _mix(p.LAB, "#2c4a16", 0.25)
    else:
        bond_ink = _mix(p.GRID, p.LAB, 0.42)
        node_ink = _mix(p.LAB, p.BG, 0.48)
    for col in range(cols):
        for row in range(rows):
            x, y = point(col, row)
            nodes.append(f'<circle class="node" cx="{x:.1f}" cy="{y:.1f}" r="1.6" fill="{node_ink}"/>')
            if col + 1 < cols:
                x2, y2 = point(col + 1, row)
                bonds.append(f"M{x:.1f} {y:.1f}L{x2:.1f} {y2:.1f}")
            if row + 1 < rows:
                x2, y2 = point(col, row + 1)
                bonds.append(f"M{x:.1f} {y:.1f}L{x2:.1f} {y2:.1f}")
    floor = (
        f'<path class="bond" d="{"".join(bonds)}" fill="none" stroke="{bond_ink}" '
        f'stroke-width="1.05" stroke-dasharray="1.6 1.7"/>'
    )
    node_markup = "".join(nodes)
    weeks_markup = ['<g class="lattice-still">']
    meta = []
    for col, week in enumerate(weeks):
        faces = []
        for row in range(rows - 1, -1, -1):
            count = week[row]
            level = levels[col][row]
            if level <= 0:
                continue
            px, py = point(col, row)
            rise = level * column_unit
            left = px - box_w / 2
            right = px + box_w / 2
            front = (
                (left, py),
                (right, py),
                (right, py - rise),
                (left, py - rise),
            )
            side = (
                front[1],
                (right + depth[0], py + depth[1]),
                (right + depth[0], py - rise + depth[1]),
                front[2],
            )
            top = (
                front[3],
                front[2],
                side[2],
                (left + depth[0], py - rise + depth[1]),
            )
            top_c, front_c, side_c, edge = ramp[level - 1]
            stroke = f' stroke="{edge}" stroke-width="0.8" stroke-linejoin="miter"'
            faces.append(f'<path fill="{side_c}"{stroke} d="{_poly(side)}"/>')
            faces.append(f'<path fill="{front_c}"{stroke} d="{_poly(front)}"/>')
            faces.append(f'<path fill="{top_c}"{stroke} d="{_poly(top)}"/>')
            meta.append(f'<g class="column" data-count="{count}" data-h="{rise:.1f}"></g>')
        if faces:
            weeks_markup.append(f'<g class="rise w{col}">{"".join(faces)}</g>')
    weeks_markup.append("</g>")
    title = "CONTRIB.LATTICE · last 52w"
    total_label = f"TOTAL {total}"
    streak_label = f"STREAK {_streak(weeks)} d"
    legend = ['<g class="legend">']
    legend.append(crt.text("less", "meslo-regular", 11, 18, 46, p.TEXT))
    cursor = 18 + crt.width("less", "meslo-regular", 11) + 8
    for level in range(4):
        legend.append(
            f'<rect x="{cursor:.1f}" y="36" width="9" height="9" fill="{ramp[level][0]}" stroke="{ramp[level][3]}" stroke-width="0.6"/>'
        )
        cursor += 13
    legend.append(crt.text("more", "meslo-regular", 11, cursor + 2, 46, p.TEXT))
    legend.append("</g>")
    months = []
    seen = None
    for col in range(cols):
        stamp = dates[col][0]
        key = stamp[:7]
        if key == seen:
            continue
        seen = key
        label = MONTHS[int(stamp[5:7]) - 1]
        x, y = point(col, 0)
        months.append(crt.text(label, "meslo-regular", 11, x, y + 16, p.DIM))
    parts = [
        crt.svg_open(width, height),
        STYLE.replace("__DELAYS__", _delays(cols)),
        p.DEFS,
        p.screen(width, height),
        crt.ticks(width, height, p.LAB),
        f'<g class="readout" fill="{p.TEXT}">',
        crt.text(title, "meslo-bold", 15, 18, 24, p.TEXT),
        crt.text(total_label, "meslo-regular", 13, width - 18 - crt.width(total_label, "meslo-regular", 13), 22, p.TEXT),
        crt.text(
            streak_label,
            "meslo-regular",
            13,
            width - 18 - crt.width(streak_label, "meslo-regular", 13),
            42,
            p.TEXT,
        ),
        "</g>",
        "".join(legend),
        floor,
        node_markup,
        "".join(weeks_markup),
        "".join(months),
        "".join(meta),
        "</svg>",
    ]
    return "".join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--preset", default=None)
    parser.add_argument("--theme", choices=tuple(tokens.THEMES))
    args = parser.parse_args(argv)
    source = args.fixture or (ROOT / "data" / "contrib.json")
    model = json.loads(Path(source).read_text(encoding="utf-8"))
    themes = (args.theme,) if args.theme else tuple(tokens.THEMES)
    for theme in themes:
        tokens.themed_path(args.out, theme).write_text(render_svg(model, theme, args.preset), encoding="utf-8")
    if args.out == OUT:
        tokens.retire_unthemed(OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
