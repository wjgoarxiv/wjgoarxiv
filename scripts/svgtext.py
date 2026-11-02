"""Draw atlas glyphs as SVG paths. Standard library only."""

import json
from pathlib import Path

ATLAS = Path(__file__).resolve().parents[1] / "assets" / "atlas" / "glyphs.json"
_CACHE = {}


def load_atlas(path=None):
    target = Path(path) if path else ATLAS
    key = str(target)
    if key not in _CACHE:
        _CACHE[key] = json.loads(target.read_text(encoding="utf-8"))
    return _CACHE[key]


def _glyphs(face, path=None):
    atlas = load_atlas(path)
    try:
        return atlas["faces"][face]["glyphs"]
    except KeyError as exc:
        raise KeyError(face) from exc


def _require(glyphs, ch):
    try:
        return glyphs[ch]
    except KeyError as exc:
        raise KeyError(ch) from exc


def text_width(text, face, size, letter_spacing=0):
    glyphs = _glyphs(face)
    if not text:
        return 0.0
    advance = 0.0
    for ch in text:
        advance += _require(glyphs, ch)["advance"]
    width = advance * (size / 1000.0)
    if len(text) > 1 and letter_spacing:
        width += letter_spacing * (len(text) - 1)
    return width


def _num(value):
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def _escape(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render(text, face, size, x, y, fill, letter_spacing=0):
    glyphs = _glyphs(face)
    scale = size / 1000.0
    cursor = x
    parts = [f'<g fill="{_escape(fill)}">']
    for index, ch in enumerate(text):
        glyph = _require(glyphs, ch)
        path = glyph["d"]
        if path:
            parts.append(
                f'<path d="{_escape(path)}" transform="translate({_num(cursor)} {_num(y)}) scale({_num(scale)})"/>'
            )
        cursor += glyph["advance"] * scale
        if index != len(text) - 1:
            cursor += letter_spacing
    parts.append("</g>")
    return "".join(parts)


def render_grid(lines, face, size, x, y, fill, letter_spacing=0, line_height=None):
    if line_height is None:
        line_height = size * 1.2
    parts = ["<g>"]
    for index, line in enumerate(lines):
        parts.append(render(line, face, size, x, y + index * line_height, fill, letter_spacing))
    parts.append("</g>")
    return "".join(parts)
