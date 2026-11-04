"""LAB and WORKSHOP CRT panels."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cage
import crt
import layout
import motion
import tokens
from render_cards import Glyphs

ROOT = Path(__file__).resolve().parents[1]
PANE_W = 600

def _box(preset):
    return PANE_W, layout.load(preset)["pane_h"]


def _num(value):
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.1f}"


def _pane_frame(col, box_w):
    return layout.frame_x(col, 2, box_w)


def _chrome(p, accent, title, cell, box_w, box_h, style, x0, x1):
    bar = 28
    frame_w = x1 - x0
    return "".join(
        (
            crt.svg_open(box_w, box_h),
            style,
            p.DEFS,
            p.screen(frame_w, box_h, origin=x0),
            p.plot_grid(frame_w, box_h, bar, origin=x0),
            f'<rect x="{_num(x0)}" y="0" width="{_num(frame_w)}" height="{bar}" fill="{p.t["inverse_bg"]}"/>',
            crt.text(f"~/{title}", "meslo-regular", 14, x0 + layout.INSET, 19, p.t["inverse_ink"]),
        )
    )


def newest_papers(papers, count=2):
    ranked = sorted(enumerate(papers), key=lambda item: (int(item[1]["year"]), item[0]), reverse=True)
    return [paper for _index, paper in ranked[:count]]


def _fit(text, face, size, max_width):
    if crt.width(text, face, size) <= max_width:
        return text
    stem = text
    while stem and crt.width(stem + "...", face, size) > max_width:
        stem = stem[:-1].rstrip()
    return (stem + "...") if stem else "..."


def _lab_regions(x0, x1, box_h):
    footer_y = box_h - 16
    rule_y = footer_y - 16
    paper_ys = (rule_y - 26, rule_y - 10)
    cage_top = 32
    cage_h = box_h * 0.58
    cage_bottom = min(cage_top + cage_h, paper_ys[0] - 38)
    if cage_bottom - cage_top < box_h * 0.55:
        cage_bottom = cage_top + box_h * 0.55
    split = x0 + (x1 - x0) * 0.50
    tag_ys = tuple(96 + index * 18 for index in range(5))
    return footer_y, rule_y, paper_ys, tag_ys, cage_top, cage_bottom, split


def _advance(text, size):
    return crt.width(text, "meslo-regular", size)


def _notation(glyphs, cx, y, fill):
    """5¹²6² over sI · CO₂ / CH₄, centered on cx. Exponents rise; guest numbers drop."""
    size, small = 14, 9
    line_one = (("5", size, y, 0.0), ("12", small, y - 5, 0.0), ("6", size, y, 1.5), ("2", small, y - 5, 0.0))
    drop = y + 16
    line_two = (
        ("sI · CO", size, drop, 0.0),
        ("2", small, drop + 3, 0.0),
        (" / CH", size, drop, 1.0),
        ("4", small, drop + 3, 0.0),
    )

    def draw(parts):
        span = 0.0
        for text, sz, _baseline, gap in parts:
            span += gap + _advance(text, sz)
        cursor = cx - span / 2
        bits = []
        for text, sz, baseline, gap in parts:
            cursor += gap
            bits.append(glyphs.text(text, "meslo-regular", sz, cursor, baseline, fill))
            cursor += _advance(text, sz)
        return "".join(bits)

    return draw(line_one) + draw(line_two)


def render_lab(theme="night", preset=None):
    box_w, box_h = _box(preset)
    p = crt.Chrome(theme)
    glyphs = Glyphs()
    papers = json.loads((ROOT / "data" / "papers.json").read_text(encoding="utf-8"))
    newest = newest_papers(papers, 2)
    x0, x1 = _pane_frame(0, box_w)
    text_x = x0 + layout.INSET
    text_r = x1 - layout.INSET
    footer_y, rule_y, paper_ys, tag_ys, cage_top, cage_bottom, split = _lab_regions(x0, x1, box_h)
    y0 = cage_top + 2
    y1 = cage_bottom - 2
    cage_gap = 8
    x_room = text_r - (split + cage_gap)
    cx = split + cage_gap + x_room / 2
    cy = (y0 + y1) / 2
    scale = cage.fit_scale(y0, y1, x_room)
    rows = (
        "kinetic & thermodynamic inhibitors",
        "flow assurance",
        "CO2 hydrate / CCS",
        "MD & clathrate cage analysis",
        "process sim · HYSYS / Multiflash",
    )
    parts = [_chrome(p, p.LAB, "LAB", 4, box_w, box_h, motion.lab_style(), x0, x1)]
    parts.append(cage.sprite(cx, cy, scale, p.LAB))
    parts.append(
        f'<g class="lab-in" style="--d:0.46s">{_notation(glyphs, cx, cage_bottom + 18, p.DIM)}</g>'
    )
    tag_width = split - cage_gap - text_x
    step = motion.MOTION["stagger_ms"] / 1000
    for index, (text, y) in enumerate(zip(rows, tag_ys)):
        wait = motion.delay_s(index, 0.52, step)
        parts.append(
            f'<g class="lab-in" style="--d:{wait:.2f}s">'
            + glyphs.text(_fit(text, "meslo-regular", 12, tag_width), "meslo-regular", 12, text_x, y, p.TEXT)
            + "</g>"
        )
    max_line = text_r - text_x
    for index, (paper, y) in enumerate(zip(newest, paper_ys)):
        line = _fit(
            f"{paper['year']} · {paper['full_venue']} · {paper['title']}",
            "meslo-regular",
            13,
            max_line,
        )
        wait = motion.delay_s(index, 0.84, step)
        parts.append(
            f'<g class="lab-in" style="--d:{wait:.2f}s">'
            + glyphs.text(line, "meslo-regular", 13, text_x, y, p.LAB)
            + "</g>"
        )
    parts.append(
        f'<line x1="{_num(text_x)}" y1="{rule_y}" x2="{_num(text_r)}" y2="{rule_y}" stroke="{p.GRID}" stroke-width="1"/>'
    )
    latin = "Ph.D. UNIST 2023 · "
    parts.append(glyphs.text(latin, "meslo-regular", 13, text_x, footer_y, p.DIM))
    parts.append(
        glyphs.text(
            "가스 하이드레이트",
            "pretendard-regular",
            13,
            text_x + crt.width(latin, "meslo-regular", 13),
            footer_y,
            p.DIM,
        )
    )
    hook = " ".join(f"{paper['year']}:{paper['slug']}" for paper in newest)
    parts.append(f"<defs>{glyphs.defs()}</defs>")
    parts.append(f"<!-- papers:{hook} -->")
    parts.append("</svg>")
    return "".join(parts)


def _group_accent(chrome, group):
    return {"litfamily": chrome.WORK, "science/mcp": chrome.LAB, "env": chrome.ENV}[group]


def _workshop_row(glyphs, p, project, accent, x, right, y, size):
    flag = "label" if project.get("label_only") else project["status"]
    flag_fill = p.DIM if project.get("label_only") else accent
    flag_w = crt.width(flag, "meslo-regular", size)
    flag_x = right - flag_w
    name_w = flag_x - (x + 14) - 8
    body = (
        f'<rect class="dot" x="{x:.1f}" y="{y - size + 3:.1f}" width="7" height="7" fill="{accent}"/>'
        + glyphs.text(_fit(project["name"], "meslo-regular", size, name_w), "meslo-regular", size, x + 14, y, p.TEXT)
        + glyphs.text(flag, "meslo-regular", size, flag_x, y, flag_fill)
    )
    return y, x, body


def render_workshop(theme="night", preset=None):
    box_w, box_h = _box(preset)
    p = crt.Chrome(theme)
    glyphs = Glyphs()
    projects = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
    order = ("litfamily", "science/mcp", "env")
    grouped = {key: [item for item in projects if item["group"] == key] for key in order}
    science = list(grouped["science/mcp"])
    science.append({"name": "claviscage", "status": "label", "label_only": True})
    footer_y = box_h - 16
    rule_y = footer_y - 14
    # Dot-matrix title occupies y=38..66. Two columns start under it.
    top = 78
    left_slots = 1 + len(grouped["litfamily"])
    right_slots = 2 + len(science) + len(grouped["env"])
    room = rule_y - 10 - top
    lead = room / max(left_slots, right_slots)
    size = 15 if lead >= 17 else 14
    x0, x1 = _pane_frame(1, box_w)
    text_x = x0 + layout.INSET
    text_r = x1 - layout.INSET
    parts = [_chrome(p, p.WORK, "WORKSHOP", 3, box_w, box_h, motion.workshop_style(), x0, x1)]
    left = text_x
    mid = x0 + (x1 - x0) * 0.38
    right_x = mid + 16
    rows = []
    y_left = top + lead
    rows.append((y_left, left, glyphs.text("litfamily", "meslo-bold", size, left, y_left, p.WORK)))
    y_left += lead
    for project in grouped["litfamily"]:
        rows.append(_workshop_row(glyphs, p, project, p.WORK, left, mid - 10, y_left, size))
        y_left += lead
    y_right = top + lead
    for key, grouped_rows in (("science/mcp", science), ("env", grouped["env"])):
        accent = _group_accent(p, key)
        rows.append((y_right, right_x, glyphs.text(key, "meslo-bold", size, right_x, y_right, accent)))
        y_right += lead
        for project in grouped_rows:
            rows.append(_workshop_row(glyphs, p, project, accent, right_x, text_r, y_right, size))
            y_right += lead
    step = 0.08
    for index, (_y, _x, body) in enumerate(sorted(rows, key=lambda item: (item[0], item[1]))):
        wait = motion.delay_s(index, 0.08, step)
        parts.append(f'<g class="row" style="--d:{wait:.3f}s">{body}</g>')
    parts.append(
        f'<line x1="{_num(text_x)}" y1="{rule_y}" x2="{_num(text_r)}" y2="{rule_y}" stroke="{p.GRID}" stroke-width="1"/>'
    )
    parts.append(glyphs.text("LINK ● AGENTS    QUEUE 0", "meslo-regular", 13, text_x, footer_y, p.DIM))
    names = "|".join(project["name"] for project in projects)
    parts.append(f"<defs>{glyphs.defs()}</defs>")
    parts.append(f"<!-- data-names:{names} -->")
    parts.append("<!-- label:claviscage -->")
    parts.append("</svg>")
    return "".join(parts)


def main(argv=None):
    themes, preset = tokens.options(argv)
    for theme in themes:
        lab = ROOT / "assets" / "lab.svg"
        shop = ROOT / "assets" / "workshop.svg"
        tokens.themed_path(lab, theme).write_text(render_lab(theme, preset), encoding="utf-8")
        tokens.themed_path(shop, theme).write_text(render_workshop(theme, preset), encoding="utf-8")
        tokens.retire_unthemed(lab)
        tokens.retire_unthemed(shop)


if __name__ == "__main__":
    main()
