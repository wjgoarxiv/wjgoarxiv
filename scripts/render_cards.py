"""CRT project cards, section bars, and paper strips. Stdlib plus the glyph atlas."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crt
import svgtext
import tokens

ROOT = Path(__file__).resolve().parents[1]
CARD_W, CARD_H = 400, 190
BAR_W, BAR_H = 1200, 56
PAPER_W, PAPER_H = 1200, 118


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


def _card(project, glyphs, p):
    accent = _accent(p, project["group"])
    size = 20
    lines = wrap(project["description"], "meslo-regular", size, 360, 3)
    body = [
        p.screen(CARD_W, CARD_H),
        crt.ticks(CARD_W, CARD_H, accent),
        f'<rect x="16" y="12" width="10" height="10" fill="{accent}"/>',
        glyphs.text(project["name"], "meslo-bold", size, 32, 22, accent),
        f'<line x1="14" y1="34" x2="{CARD_W - 14}" y2="34" stroke="{p.GRID}" stroke-width="1"/>',
        glyphs.text("AUTHOR", "meslo-regular", size, 16, 60, p.TEXT),
        glyphs.text(project["status"], "meslo-regular", size, 250, 60, accent),
    ]
    y = 92
    for line in lines:
        body.append(glyphs.text(line, "meslo-regular", size, 16, y, p.TEXT))
        y += 26
    return "".join(
        [
            crt.svg_open(CARD_W, CARD_H),
            "<defs>",
            p.DEFS.replace("<defs>", "").replace("</defs>", ""),
            glyphs.defs(),
            "</defs>",
            *body,
            "</svg>",
        ]
    )


def _arrow(x, y, color):
    return f'<path d="M{x} {y} L{x + 10} {y + 6} L{x} {y + 12} Z" fill="{color}"/>'


def _bar(label, color, p):
    return "".join(
        (
            crt.svg_open(BAR_W, BAR_H),
            p.DEFS,
            p.screen(BAR_W, BAR_H),
            crt.ticks(BAR_W, BAR_H, color),
            _arrow(18, 18, color),
            p.bloom(crt.dot_text(label, 36, 12, 4, color)),
            f'<line x1="16" y1="50" x2="{BAR_W - 16}" y2="50" stroke="{p.GRID}" stroke-width="1"/>',
            "</svg>",
        )
    )


def _paper(paper, glyphs, p):
    title = wrap(paper["title"], "meslo-regular", 20, 1140, 2)
    body = [
        p.screen(PAPER_W, PAPER_H),
        crt.ticks(PAPER_W, PAPER_H, p.LAB),
        glyphs.text(f"ARCHIVE  {paper['year']}", "meslo-bold", 18, 18, 28, p.LAB),
        glyphs.text(paper["short_venue"], "meslo-regular", 16, 280, 28, p.LAB),
        glyphs.text(paper["doi"], "meslo-regular", 14, 18, 104, p.DIM),
    ]
    marker = "→ DOI"
    body.append(
        glyphs.text(marker, "meslo-regular", 16, PAPER_W - 18 - glyphs.width(marker, "meslo-regular", 16), 104, p.DIM)
    )
    y = 58
    for line in title:
        body.append(glyphs.text(line, "meslo-regular", 20, 18, y, p.TEXT))
        y += 24
    return "".join(
        [
            crt.svg_open(PAPER_W, PAPER_H),
            "<defs>",
            p.DEFS.replace("<defs>", "").replace("</defs>", ""),
            glyphs.defs(),
            "</defs>",
            *body,
            "</svg>",
        ]
    )


def render_all(theme="night"):
    p = crt.Chrome(theme)
    projects = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
    papers = json.loads((ROOT / "data" / "papers.json").read_text(encoding="utf-8"))
    cards = ROOT / "assets" / "cards"
    strips = ROOT / "assets" / "papers"
    cards.mkdir(parents=True, exist_ok=True)
    strips.mkdir(parents=True, exist_ok=True)
    counts = {}
    for project in projects:
        counts[project["group"]] = counts.get(project["group"], 0) + 1
        dest = cards / f"{project['name']}.svg"
        tokens.themed_path(dest, theme).write_text(_card(project, Glyphs(), p), encoding="utf-8")
        tokens.retire_unthemed(dest)
    bars = {
        "hdr-projects.svg": ("/PROJECTS", p.TEXT),
        "hdr-litfamily.svg": (f"LITFAMILY  {counts['litfamily']:02d} UNITS", p.WORK),
        "hdr-science.svg": (f"SCIENCE / MCP  {counts['science/mcp']:02d} UNITS", p.LAB),
        "hdr-env.svg": (f"ENV  {counts['env']:02d} UNITS", p.ENV),
        "hdr-papers.svg": ("/PAPERS", p.TEXT),
    }
    for name, (label, color) in bars.items():
        dest = cards / name
        tokens.themed_path(dest, theme).write_text(_bar(label, color, p), encoding="utf-8")
        tokens.retire_unthemed(dest)
    for paper in papers:
        dest = strips / f"{paper['year']}-{paper['slug']}.svg"
        tokens.themed_path(dest, theme).write_text(_paper(paper, Glyphs(), p), encoding="utf-8")
        tokens.retire_unthemed(dest)


def main(argv=None):
    for theme in tokens.chosen(argv):
        render_all(theme)


if __name__ == "__main__":
    main()
