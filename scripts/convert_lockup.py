"""Replace lockup <text> with Monument Extended paths. Local fontTools only."""

import re
import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

BRAND = Path(
    "/Users/woojin/Desktop/02_Areas/09_Me/Branding/output/woojin-go-brand-v1-r7-r6-ci/vector"
)
ROOT = Path(__file__).resolve().parents[1]
FONT = Path.home() / "Library" / "Fonts" / "MonumentExtended-Ultrabold.otf"
PAIRS = (
    ("woojin-go-lockup-reverse.svg", "lockup-dark.svg", True),
    ("woojin-go-lockup-horizontal.svg", "lockup-light.svg", False),
)
DARK_BACKGROUND = '<rect width="1500" height="360" fill="#26282D"/>\n'
TEXT_RE = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.DOTALL)
NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")


def _attrs(blob):
    return dict(re.findall(r'([\w:-]+)="([^"]*)"', blob))


def _quantize(commands):
    if not commands:
        return ""

    def repl(match):
        value = round(float(match.group(0)), 2)
        text = f"{value:.2f}".rstrip("0").rstrip(".")
        return "0" if text in ("", "-0") else text

    return NUMBER.sub(repl, commands)


def _shape(text, font_size, letter_spacing):
    """HarfBuzz kern (GPOS kern) plus SVG letter-spacing in user units."""
    blob = hb.Blob.from_file_path(str(FONT))
    face = hb.Face(blob)
    hb_font = hb.Font(face)
    hb_font.scale = (face.upem, face.upem)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb_font, buf, {"kern": True})
    scale = font_size / face.upem
    cursor = 0.0
    placed = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        placed.append((info.codepoint, cursor + pos.x_offset * scale, pos.y_offset * scale))
        cursor += pos.x_advance * scale + letter_spacing
    return placed


def _wordmark(font, text, x, y, font_size, letter_spacing, fill):
    glyphset = font.getGlyphSet()
    order = font.getGlyphOrder()
    scale = font_size / font["head"].unitsPerEm
    paths = []
    for gid, dx, dy in _shape(text, font_size, letter_spacing):
        name = order[gid]
        pen = SVGPathPen(glyphset)
        # HarfBuzz y is up; SVG y is down. Baseline is the text y.
        glyphset[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x + dx, y - dy)))
        commands = _quantize(pen.getCommands())
        if commands:
            paths.append(f'<path d="{commands}"/>')
    body = "".join(paths)
    return f'<g id="wordmark" fill="{fill}">{body}</g>'


def convert_one(source, dest, font, drop_background=False):
    svg = source.read_text(encoding="utf-8")
    match = TEXT_RE.search(svg)
    if not match:
        raise SystemExit(f"no <text> in {source}")
    attrs = _attrs(match.group(1))
    if attrs.get("font-family") != "Monument Extended":
        raise SystemExit(f"unexpected font-family in {source.name}")
    replacement = _wordmark(
        font,
        match.group(2),
        float(attrs["x"]),
        float(attrs["y"]),
        float(attrs["font-size"]),
        float(attrs.get("letter-spacing", "0")),
        attrs["fill"],
    )
    svg = svg[: match.start()] + replacement + svg[match.end() :]
    if drop_background:
        if DARK_BACKGROUND not in svg:
            raise SystemExit(f"missing full-canvas background rect in {source.name}")
        svg = svg.replace(DARK_BACKGROUND, "", 1)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(svg, encoding="utf-8")


def convert_all():
    if not FONT.is_file():
        raise SystemExit(f"missing font {FONT.name}; no fallback named")
    print(f"font file: {FONT}", flush=True)
    font = TTFont(str(FONT))
    for src_name, out_name, drop_background in PAIRS:
        convert_one(BRAND / src_name, ROOT / "assets" / out_name, font, drop_background)


def main():
    convert_all()


if __name__ == "__main__":
    main()
