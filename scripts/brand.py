"""Terminalcore lockup. Pretendard 860 wordmark plus the square aperture mark."""

import re
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import motion
import svgtext
import tokens

ROOT = Path(__file__).resolve().parents[1]
FONT = Path(
    "/Users/woojin/Desktop/02_Areas/09_Me/Branding/output/"
    "woojin-go-theme-terminalcore/css/fonts/PretendardVariable.woff2"
)
OUT = ROOT / "assets" / "brand"
MODULE = "M28 28H88V61.84A40 40 0 0 0 61.84 88H28Z"
WORD = "WOOJIN GO"
INK_SPAN = 144.0
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")


def _num(value):
    text = f"{float(value):.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def _quantize(commands):
    def repl(match):
        value = round(float(match.group(0)), 2)
        return _num(value)

    return _NUMBER.sub(repl, commands)


def _wordmark(fill):
    font = instantiateVariableFont(TTFont(FONT), {"wght": 860}, inplace=False)
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upem = font["head"].unitsPerEm
    cap = int(getattr(font["OS/2"], "sCapHeight", 0) or 0) or int(upem * 0.72)
    tracking = -0.02 * upem
    cursor = 0.0
    paths = []
    xmin = ymin = 10**9
    xmax = ymax = -10**9
    for index, char in enumerate(WORD):
        glyph = glyphs[cmap[ord(char)]]
        bounds = BoundsPen(glyphs)
        glyph.draw(bounds)
        if bounds.bounds:
            x0, y0, x1, y1 = bounds.bounds
            xmin = min(xmin, x0 + cursor)
            xmax = max(xmax, x1 + cursor)
            ymin = min(ymin, y0)
            ymax = max(ymax, y1)
        pen = SVGPathPen(glyphs)
        glyph.draw(pen)
        path = _quantize(pen.getCommands() or "")
        if path:
            paths.append(
                f'<path fill="{fill}" d="{path}" transform="translate({_num(cursor)} 0)"/>'
            )
        cursor += glyph.width + (tracking if index < len(WORD) - 1 else 0)
    return "".join(paths), cursor, cap, upem, (xmin, ymin, xmax, ymax)


def symbol_markup(prefix, fill):
    """Four solid modules. The aperture is the void between the arcs, not a hole."""
    offsets = ((-18, -18), (18, -18), (18, 18), (-18, 18))
    still = ['<g class="mark-still">']
    live = ['<g class="mark-live">']
    step = motion.MOTION["chrome_stagger_s"]
    dur = motion.MOTION["chrome_ms"] / 1000
    for index, (dx, dy) in enumerate(offsets):
        angle = index * 90
        path = f'<path fill="{fill}" d="{MODULE}" transform="rotate({angle} 100 100)"/>'
        still.append(path)
        steps = []
        for stage in range(4):
            left = 3 - stage
            steps.append(f"{_num(dx * left / 3)} {_num(dy * left / 3)}")
        live.append(
            f"<g>{path}"
            f'<animateTransform attributeName="transform" type="translate" '
            f'calcMode="discrete" begin="{_num(index * step)}s" dur="{_num(dur)}s" fill="freeze" '
            f'values="{";".join(steps)}"/></g>'
        )
    still.append("</g>")
    live.append("</g>")
    style = (
        "<style>"
        ".mark-live { display: none; } .mark-still { display: inline; }"
        "@media (prefers-reduced-motion: no-preference) {"
        ".mark-live { display: inline; } .mark-still { display: none; }"
        "}"
        "@media (prefers-reduced-motion: reduce) {"
        ".mark-live { display: none !important; } .mark-still { display: inline !important; }"
        "}"
        "</style>"
    )
    return style + "".join(still) + "".join(live)


def lockup_svg(theme):
    fill = tokens.THEMES[theme]["lockup_fill"]
    word, _width, cap, upem, bounds = _wordmark(fill)
    xmin, ymin, xmax, ymax = bounds
    mark = 1.2 * cap
    scale = mark / INK_SPAN
    gap = 0.33 * upem
    # Flip the font's y-up outlines into the SVG y-down box, then center the mark on the cap.
    cap_top = ymax - cap
    cap_center = (ymax + cap_top) / 2
    mark_y = cap_center - 100 * scale
    word_x = 172 * scale + gap - xmin
    pad = cap * 0.04
    mark_box = (28 * scale, mark_y + 28 * scale, 172 * scale, mark_y + 172 * scale)
    word_box = (word_x + xmin, ymax - ymax, word_x + xmax, ymax - ymin)
    union_x0 = min(mark_box[0], word_box[0]) - pad
    union_y0 = min(mark_box[1], word_box[1]) - pad
    union_x1 = max(mark_box[2], word_box[2]) + pad
    union_y1 = max(mark_box[3], word_box[3]) + pad
    delay = motion.MOTION["wordmark_delay_s"]
    dur = motion.MOTION["chrome_ms"]
    body = (
        f'<g transform="translate({_num(-union_x0)} {_num(-union_y0)})">'
        f'<g transform="translate(0 {_num(mark_y)}) scale({_num(scale)})">'
        f"{symbol_markup('lk', fill)}</g>"
        f'<g class="wordmark" transform="translate({_num(word_x)} {_num(ymax)}) scale(1 -1)">{word}</g>'
        f"</g>"
    )
    style = (
        "<style>"
        ".wordmark { clip-path: inset(0 0 0 0); }"
        "@media (prefers-reduced-motion: no-preference) {"
        f".wordmark {{ animation: plot-in {dur}ms steps(3, end) both; animation-delay: {delay}s; }}"
        "}"
        "@keyframes plot-in {"
        "from { clip-path: inset(0 100% 0 0); }"
        "to { clip-path: inset(0 0 0 0); }"
        "}"
        "@media (prefers-reduced-motion: reduce) {"
        ".wordmark { animation: none !important; clip-path: inset(0 0 0 0) !important; }"
        "}"
        "</style>"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_num(union_x1 - union_x0)} {_num(union_y1 - union_y0)}" '
        f'data-cap="{_num(cap)}">{style}{body}</svg>'
    )


def symbol_svg(theme):
    fill = tokens.THEMES[theme]["lockup_fill"]
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="28 28 144 144">'
        f"{symbol_markup('sy', fill)}</svg>"
    )


FOOTER_W, FOOTER_H = 280, 28


def footer_svg(theme):
    spec = tokens.THEMES[theme]
    ink = spec["label"]
    scale = 0.111
    mark_left, mark_right = 28, 172
    mark_w = (mark_right - mark_left) * scale
    gap = 28 - (2 + mark_right * scale)
    prompt, rest = "~/", "woojin-go"
    line_w = svgtext.text_width(prompt + rest, "meslo-regular", 14, 0)
    origin = (FOOTER_W - (mark_w + gap + line_w)) / 2
    text_x = origin + mark_w + gap
    prompt_svg = svgtext.render(prompt, "meslo-regular", 14, text_x, 20, spec["phosphor"], 0)
    rest_x = text_x + svgtext.text_width(prompt, "meslo-regular", 14, 0)
    rest_svg = svgtext.render(rest, "meslo-regular", 14, rest_x, 20, ink, 0)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{FOOTER_W}" height="{FOOTER_H}" '
        f'viewBox="0 0 {FOOTER_W} {FOOTER_H}">'
        f'<g transform="translate({_num(origin - mark_left * scale)} 2) scale({_num(scale)})">'
        f'{symbol_markup("ft", ink)}</g>'
        f"{prompt_svg}{rest_svg}</svg>"
    )


def write_all():
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in ("night", "day"):
        (OUT / f"lockup-{theme}.svg").write_text(lockup_svg(theme), encoding="utf-8")
        (OUT / f"symbol-{theme}.svg").write_text(symbol_svg(theme), encoding="utf-8")
        (ROOT / "assets" / f"footer-{theme}.svg").write_text(footer_svg(theme), encoding="utf-8")


if __name__ == "__main__":
    write_all()
