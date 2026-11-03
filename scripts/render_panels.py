"""LAB and WORKSHOP CRT panels."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cage
import crt
import layout
import tokens
from render_cards import Glyphs

ROOT = Path(__file__).resolve().parents[1]
PANE_W = 600

STYLE = """<style>
.dot { animation: pulse 2.8s ease-in-out infinite; }
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.28; }
}
@media (prefers-reduced-motion: reduce) {
  .dot { animation: none; opacity: 1; }
}
.cage-spin { display: none; }
.cage-still { display: inline; }
@media (prefers-reduced-motion: no-preference) {
  .cage-spin { display: inline; }
  .cage-still { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  .cage-spin { display: none; }
  .cage-still { display: inline; }
}
</style>"""


def _box(preset):
    return PANE_W, layout.load(preset)["pane_h"]


def _chrome(p, accent, title, cell, box_w, box_h):
    return "".join(
        (
            crt.svg_open(box_w, box_h),
            STYLE,
            p.DEFS,
            p.screen(box_w, box_h),
            crt.ticks(box_w, box_h, accent),
            p.blocks(("TTY1", "PID 0x2A", "UTF-8"), accent),
            f'<line x1="14" y1="30" x2="{box_w - 14}" y2="30" stroke="{p.GRID}" stroke-width="1"/>',
            p.bloom(crt.dot_text(title, 18, 38, cell, accent)),
            f'<circle class="dot" cx="{box_w - 18}" cy="16" r="3.5" fill="{accent}"/>',
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


def _lab_regions(box_w, box_h):
    footer_y = box_h - 16
    rule_y = footer_y - 16
    paper_ys = (rule_y - 26, rule_y - 10)
    cage_top = 32
    cage_h = box_h * 0.58
    cage_bottom = min(cage_top + cage_h, paper_ys[0] - 38)
    if cage_bottom - cage_top < box_h * 0.55:
        cage_bottom = cage_top + box_h * 0.55
    split = box_w * 0.50
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
    footer_y, rule_y, paper_ys, tag_ys, cage_top, cage_bottom, split = _lab_regions(box_w, box_h)
    y0 = cage_top + 2
    y1 = cage_bottom - 2
    x_room = box_w - 16 - (split + 8)
    cx = split + 8 + x_room / 2
    cy = (y0 + y1) / 2
    scale = cage.fit_scale(y0, y1, x_room)
    rows = (
        "kinetic & thermodynamic inhibitors",
        "flow assurance",
        "CO2 hydrate / CCS",
        "MD & clathrate cage analysis",
        "process sim · HYSYS / Multiflash",
    )
    parts = [_chrome(p, p.LAB, "LAB", 4, box_w, box_h)]
    parts.append(cage.sprite(cx, cy, scale, p.LAB))
    parts.append(_notation(glyphs, cx, cage_bottom + 18, p.DIM))
    tag_width = split - 28
    for text, y in zip(rows, tag_ys):
        parts.append(glyphs.text(_fit(text, "meslo-regular", 12, tag_width), "meslo-regular", 12, 16, y, p.TEXT))
    max_line = box_w - 32
    for paper, y in zip(newest, paper_ys):
        line = _fit(
            f"{paper['year']} · {paper['full_venue']} · {paper['title']}",
            "meslo-regular",
            13,
            max_line,
        )
        parts.append(glyphs.text(line, "meslo-regular", 13, 16, y, p.LAB))
    parts.append(f'<line x1="14" y1="{rule_y}" x2="{box_w - 14}" y2="{rule_y}" stroke="{p.GRID}" stroke-width="1"/>')
    latin = "Ph.D. UNIST 2023 · "
    parts.append(glyphs.text(latin, "meslo-regular", 13, 16, footer_y, p.DIM))
    parts.append(
        glyphs.text(
            "가스 하이드레이트",
            "pretendard-regular",
            13,
            16 + crt.width(latin, "meslo-regular", 13),
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


def _workshop_row(parts, glyphs, p, project, accent, x, right, y, size):
    parts.append(f'<rect x="{x:.1f}" y="{y - size + 3:.1f}" width="7" height="7" fill="{accent}"/>')
    flag = "label" if project.get("label_only") else project["status"]
    flag_fill = p.DIM if project.get("label_only") else accent
    flag_w = crt.width(flag, "meslo-regular", size)
    flag_x = right - flag_w
    name_w = flag_x - (x + 14) - 8
    parts.append(
        glyphs.text(_fit(project["name"], "meslo-regular", size, name_w), "meslo-regular", size, x + 14, y, p.TEXT)
    )
    parts.append(glyphs.text(flag, "meslo-regular", size, flag_x, y, flag_fill))


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
    parts = [_chrome(p, p.WORK, "WORKSHOP", 3, box_w, box_h)]
    left = 16
    mid = box_w * 0.38
    right_x = mid + 16
    y_left = top + lead
    parts.append(glyphs.text("litfamily", "meslo-bold", size, left, y_left, p.WORK))
    y_left += lead
    for project in grouped["litfamily"]:
        _workshop_row(parts, glyphs, p, project, p.WORK, left, mid - 10, y_left, size)
        y_left += lead
    y_right = top + lead
    for key, rows in (("science/mcp", science), ("env", grouped["env"])):
        accent = _group_accent(p, key)
        parts.append(glyphs.text(key, "meslo-bold", size, right_x, y_right, accent))
        y_right += lead
        for project in rows:
            _workshop_row(parts, glyphs, p, project, accent, right_x, box_w - 16, y_right, size)
            y_right += lead
    parts.append(f'<line x1="14" y1="{rule_y}" x2="{box_w - 14}" y2="{rule_y}" stroke="{p.GRID}" stroke-width="1"/>')
    parts.append(glyphs.text("LINK ● AGENTS    QUEUE 0", "meslo-regular", 13, 16, footer_y, p.DIM))
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
