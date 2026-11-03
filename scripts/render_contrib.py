"""Hydrate-lattice contribution view. Cabinet projection, stdlib only."""

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crt
import layout
import motion
import tokens

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "contrib.svg"
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
ANCHOR = date(2025, 11, 2)

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


def _dates(model, cols, rows):
    given = model.get("dates")
    if given:
        return given
    start = date.fromisoformat(model["start"]) if model.get("start") else ANCHOR
    grid = []
    for col in range(cols):
        grid.append([(start + timedelta(days=col * 7 + row)).isoformat() for row in range(rows)])
    return grid


def _ramp(theme):
    """Brand levels 0–4. The top face is the token; the other faces are the same hue, darker."""
    toward = "#07080c" if theme == "night" else "#12141c"
    faces = []
    for color in tokens.THEMES[theme]["contrib"]:
        faces.append(
            (
                color,
                _mix(color, toward, 0.28),
                _mix(color, toward, 0.48),
                _mix(color, toward, 0.66),
            )
        )
    return tuple(faces)


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
    ramp = _ramp(theme)
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
        f'<g class="floor"><path class="bond" d="{"".join(bonds)}" fill="none" stroke="{bond_ink}" '
        f'stroke-width="1.05" stroke-dasharray="1.6 1.7"/>'
    )
    node_markup = "".join(nodes) + "</g>"
    cube_h = column_unit
    half = box_w / 2
    dx, dy = depth
    local_front = ((-half, 0.0), (half, 0.0), (half, -cube_h), (-half, -cube_h))
    local_side = (
        local_front[1],
        (half + dx, dy),
        (half + dx, -cube_h + dy),
        local_front[2],
    )
    local_top = (
        local_front[3],
        local_front[2],
        local_side[2],
        (-half + dx, -cube_h + dy),
    )
    xs = [x for shape in (local_front, local_side, local_top) for x, _y in shape]
    ys = [y for shape in (local_front, local_side, local_top) for _x, y in shape]
    pad = 1.0
    min_x, min_y = min(xs) - pad, min(ys) - pad
    max_x, max_y = max(xs) + pad, max(ys) + pad
    symbol_w, symbol_h = max_x - min_x, max_y - min_y
    symbols = ['<defs>']
    for level in range(1, 5):
        top_c, front_c, side_c, edge = ramp[level]
        stroke = f' stroke="{edge}" stroke-width="0.8" stroke-linejoin="miter"'
        symbols.append(
            f'<symbol id="v{level}" viewBox="{min_x:.1f} {min_y:.1f} {symbol_w:.1f} {symbol_h:.1f}" overflow="visible">'
            f'<path fill="{side_c}"{stroke} d="{_poly(local_side)}"/>'
            f'<path fill="{front_c}"{stroke} d="{_poly(local_front)}"/>'
            f'<path class="top" fill="{top_c}"{stroke} d="{_poly(local_top)}"/>'
            f"</symbol>"
        )
    symbols.append("</defs>")
    weeks_markup = ['<g class="lattice-still">']
    meta = []
    for col, week in enumerate(weeks):
        for row in range(rows - 1, -1, -1):
            count = week[row]
            level = levels[col][row]
            if level <= 0:
                continue
            px, py = point(col, row)
            rise = level * column_unit
            cubes = []
            for index in range(level):
                floor_y = py - index * cube_h
                classes = f"voxel c{col} r{row} s{index}"
                if level == 4 and index == level - 1:
                    classes += " peak"
                cubes.append(
                    f'<use href="#v{level}" x="{px + min_x:.1f}" y="{floor_y + min_y:.1f}" '
                    f'width="{symbol_w:.1f}" height="{symbol_h:.1f}" class="{classes}"/>'
                )
            meta.append(f'<g class="column" data-count="{count}" data-h="{rise:.1f}" data-col="{col}" data-row="{row}"></g>')
            weeks_markup.append("".join(cubes))
    weeks_markup.append("</g>")
    title = "~/CONTRIB"
    readout_size = 13
    total_value = total
    streak_value = _streak(weeks)
    legend = ['<g class="legend">']
    legend.append(crt.text("less", "meslo-regular", 11, 18, 46, p.TEXT))
    cursor = 18 + crt.width("less", "meslo-regular", 11) + 8
    for level in range(5):
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
    total_label = "TOTAL "
    streak_label = "STREAK "
    suffix = " d"
    total_w = crt.width(total_label, "meslo-regular", readout_size) + motion.reel_width(total_value, readout_size)
    streak_w = (
        crt.width(streak_label, "meslo-regular", readout_size)
        + motion.reel_width(streak_value, readout_size)
        + crt.width(suffix, "meslo-regular", readout_size)
    )
    total_x = width - 18 - total_w
    streak_x = width - 18 - streak_w
    total_clips, total_body, _total_used = motion.odometer(
        total_value,
        total_x + crt.width(total_label, "meslo-regular", readout_size),
        19,
        readout_size,
        "total",
        p.t["inverse_ink"],
    )
    streak_digits_x = streak_x + crt.width(streak_label, "meslo-regular", readout_size)
    streak_clips, streak_body, streak_used = motion.odometer(
        streak_value, streak_digits_x, 42, readout_size, "streak", p.TEXT
    )
    beam = (
        f'<rect class="beam" x="0" y="58" width="28" height="{height - 78}" fill="{p.LAB}" opacity="0"/>'
    )
    parts = [
        crt.svg_open(width, height),
        motion.contrib_style(readout_size, cols, rows),
        p.DEFS,
        "".join(symbols),
        f"<defs>{total_clips}{streak_clips}</defs>",
        p.screen(width, height),
        p.plot_grid(width, height, 28),
        f'<g class="readout" fill="{p.TEXT}">',
        f'<rect x="0" y="0" width="{width}" height="28" fill="{p.t["inverse_bg"]}"/>',
        crt.text(title, "meslo-regular", 14, 12, 19, p.t["inverse_ink"]),
        crt.text(total_label, "meslo-regular", readout_size, total_x, 19, p.t["inverse_ink"]),
        total_body,
        crt.text(streak_label, "meslo-regular", readout_size, streak_x, 42, p.TEXT),
        streak_body,
        crt.text(suffix, "meslo-regular", readout_size, streak_digits_x + streak_used, 42, p.TEXT),
        "</g>",
        "".join(legend),
        floor,
        node_markup,
        "".join(weeks_markup),
        beam,
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
