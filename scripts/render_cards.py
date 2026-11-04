"""CRT project cards, section bars, and paper strips. Stdlib plus the glyph atlas."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crt
import layout
import svgtext
import tokens

ROOT = Path(__file__).resolve().parents[1]
CARD_W, CARD_H = 400, 190
BAR_W, BAR_H = 1200, 56
PAPER_W, PAPER_H = 1200, 118
SPAN_WIDTH = {1: 1200, 2: 600, 3: 400}
ROW_SPEC = {
    "litfamily": (
        ("litfamily",),
        ("litgravity", "litclaude", "litcodex"),
        ("litopencode", "lithermes", "litgrok"),
    ),
    "science/mcp": (
        ("ovito-mcp", "pymol-mcp"),
        ("multiflash-assistant", "hysys-companion-releases"),
    ),
    "env": (
        ("pretty-terminal", "my-tmux-settings", "my-nvim-settings"),
        ("proxlsx-skill", "publisher-docx-skill"),
    ),
}


class Glyphs:
    def __init__(self):
        self.paths = {}

    def text(self, value, face, size, x, y, fill):
        glyphs = svgtext.load_atlas()["faces"][face]["glyphs"]
        scale = size / 1000.0
        parts = [f'<g fill="{fill}">']
        cursor = x
        for char in value:
            glyph = glyphs[char]
            code = {"meslo-regular": "r", "meslo-bold": "b", "pretendard-regular": "p"}[face]
            key = f"g{code}{ord(char)}"
            if glyph["d"] and key not in self.paths:
                self.paths[key] = glyph["d"]
            if glyph["d"]:
                parts.append(
                    f'<use href="#{key}" transform="translate({cursor:.1f} {y:.1f}) scale({scale:.4f})"/>'
                )
            cursor += glyph["advance"] * scale
        parts.append("</g>")
        return "".join(parts)

    def width(self, value, face, size):
        return svgtext.text_width(value, face, size, 0)

    def defs(self):
        return "".join(f'<path id="{key}" d="{path}"/>' for key, path in self.paths.items())


def wrap(text, face, size, max_width, max_lines):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if svgtext.text_width(trial, face, size, 0) <= max_width:
            current = trial
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) == max_lines:
            current = ""
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    used = " ".join(lines)
    if used != text and lines:
        stem = lines[-1]
        while stem and svgtext.text_width(stem + "...", face, size, 0) > max_width:
            stem = stem[:-1].rstrip()
        lines[-1] = (stem + "...") if stem else "..."
    return lines


def _accent(p, group):
    return {"litfamily": p.WORK, "science/mcp": p.LAB, "env": p.ENV}[group]


def card_slots(projects):
    """Column and span for each project. A group with no row spec raises."""
    grouped = {}
    for project in projects:
        grouped.setdefault(project["group"], []).append(project["name"])
    slots = {}
    for group, names in grouped.items():
        rows = ROW_SPEC.get(group)
        if rows is None:
            raise ValueError(f"no row spec for {group}")
        expected = [name for row in rows for name in row]
        if names != expected:
            raise ValueError(f"row spec does not match {group} order")
        for row in rows:
            cols = len(row)
            if cols not in SPAN_WIDTH:
                raise ValueError(f"unsupported span {cols}")
            for col, name in enumerate(row):
                slots[name] = (col, cols)
    return slots


def _card(project, glyphs, p, col, cols):
    accent = _accent(p, project["group"])
    width = SPAN_WIDTH[cols]
    x0, x1 = layout.frame_x(col, cols, width)
    frame_w = x1 - x0
    text_x = x0 + layout.INSET
    size = 20
    lines = wrap(project["description"], "meslo-regular", size, x1 - layout.INSET - text_x, 3)
    status_x = x1 - (CARD_W - 250)
    body = [
        p.screen(frame_w, CARD_H, origin=x0),
        f'<g transform="translate({x0} 0)">{crt.ticks(frame_w, CARD_H, accent)}</g>',
        f'<rect x="{text_x}" y="12" width="10" height="10" fill="{accent}"/>',
        glyphs.text(project["name"], "meslo-bold", size, text_x + 12, 22, accent),
        f'<line x1="{x0 + 14}" y1="34" x2="{x1 - 14}" y2="34" stroke="{p.GRID}" stroke-width="1"/>',
        glyphs.text("AUTHOR", "meslo-regular", size, text_x, 60, p.TEXT),
        glyphs.text(project["status"], "meslo-regular", size, status_x, 60, accent),
    ]
    y = 92
    for line in lines:
        body.append(glyphs.text(line, "meslo-regular", size, text_x, y, p.TEXT))
        y += 26
    return "".join(
        [
            crt.svg_open(width, CARD_H),
            "<defs>",
            p.DEFS.replace("<defs>", "").replace("</defs>", ""),
            glyphs.defs(),
            "</defs>",
            *body,
            "</svg>",
        ]
    )


def _paper(paper, glyphs, p, paper_w=PAPER_W, paper_h=PAPER_H):
    left = layout.INSET
    title = wrap(paper["title"], "meslo-regular", 20, paper_w - 2 * layout.INSET, 2)
    body = [
        p.screen(paper_w, paper_h),
        crt.ticks(paper_w, paper_h, p.LAB),
        glyphs.text(f"ARCHIVE  {paper['year']}", "meslo-bold", 18, left, 28, p.LAB),
        glyphs.text(paper["short_venue"], "meslo-regular", 16, 280, 28, p.LAB),
        glyphs.text(paper["doi"], "meslo-regular", 14, left, 104, p.DIM),
    ]
    marker = "→ DOI"
    body.append(
        glyphs.text(
            marker,
            "meslo-regular",
            16,
            paper_w - layout.INSET - glyphs.width(marker, "meslo-regular", 16),
            104,
            p.DIM,
        )
    )
    y = 58
    for line in title:
        body.append(glyphs.text(line, "meslo-regular", 20, left, y, p.TEXT))
        y += 24
    return "".join(
        [
            crt.svg_open(paper_w, paper_h),
            "<defs>",
            p.DEFS.replace("<defs>", "").replace("</defs>", ""),
            glyphs.defs(),
            "</defs>",
            *body,
            "</svg>",
        ]
    )


def metrics(preset=None):
    spec = layout.load(preset)
    return {
        "card_w": CARD_W,
        "card_h": CARD_H,
        "bar_w": spec["width"],
        "bar_h": BAR_H,
        "paper_w": spec["width"],
        "paper_h": PAPER_H,
    }


def render_all(theme="night", preset=None):
    size = metrics(preset)
    p = crt.Chrome(theme)
    projects = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
    papers = json.loads((ROOT / "data" / "papers.json").read_text(encoding="utf-8"))
    slots = card_slots(projects)
    cards = ROOT / "assets" / "cards"
    strips = ROOT / "assets" / "papers"
    cards.mkdir(parents=True, exist_ok=True)
    strips.mkdir(parents=True, exist_ok=True)
    for project in projects:
        col, cols = slots[project["name"]]
        dest = cards / f"{project['name']}.svg"
        tokens.themed_path(dest, theme).write_text(_card(project, Glyphs(), p, col, cols), encoding="utf-8")
        tokens.retire_unthemed(dest)
    for paper in papers:
        dest = strips / f"{paper['year']}-{paper['slug']}.svg"
        tokens.themed_path(dest, theme).write_text(
            _paper(paper, Glyphs(), p, size["paper_w"], size["paper_h"]), encoding="utf-8"
        )
        tokens.retire_unthemed(dest)


def main(argv=None):
    themes, preset = tokens.options(argv)
    for theme in themes:
        render_all(theme, preset)


if __name__ == "__main__":
    main()
