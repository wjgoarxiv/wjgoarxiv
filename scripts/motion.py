"""Shared motion tokens. CSS timings come from here so the easings cannot drift."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgtext

EASE = {
    "out_expo": "cubic-bezier(0.16, 1, 0.3, 1)",
    "out_quint": "cubic-bezier(0.22, 1, 0.36, 1)",
    "in_out": "cubic-bezier(0.65, 0, 0.35, 1)",
}

STEPS = "steps(3, end)"
MOTION = {
    "ease": EASE,
    "power_ms": 380,
    "line_ms": 420,
    "name_ms": 520,
    "stagger_ms": 60,
    "line_start_s": 0.40,
    "reel_ms": 780,
    "reel_stagger_ms": 55,
    "reel_start_s": 0.36,
    "cage_in_ms": 700,
    "cage_dur_s": 8,
    "cage_hold_s": 0.4,
    "cage_rotate_s": 1.6,
    "column_ms": 520,
    "column_step_s": 0.012,
    "column_k": 1,
    "floor_ms": 400,
    "row_ms": 450,
    "row_stagger_ms": 45,
    "badge_ms": 600,
    "badge_stagger_ms": 50,
    "hero_intro_s": 1.84,
    "page_intro_s": 2.0,
    "overshoot_limit": 0.06,
    "chrome_ms": 240,
    "chrome_stagger_s": 0.08,
    "wordmark_delay_s": 0.72,
    "boot_delay_s": 1.04,
    "status_delay_s": 1.60,
    "wave_s": 10,
    "wave_step_s": 0.035,
}

FACE = "meslo-regular"


def _num(value):
    text = f"{float(value):.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def _bezier_y(t, y1, y2):
    return 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t ** 2 * y2 + t ** 3


def _bezier_x(t, x1, x2):
    return _bezier_y(t, x1, x2)


def ease_in_out(u):
    """Progress at time u for the in-out token. u and the result are 0..1."""
    target = min(1.0, max(0.0, u))
    lo, hi = 0.0, 1.0
    for _ in range(28):
        mid = (lo + hi) / 2
        if _bezier_x(mid, 0.65, 0.35) < target:
            lo = mid
        else:
            hi = mid
    return _bezier_y((lo + hi) / 2, 0.0, 1.0)


def inverse_in_out(progress):
    """Time at which in-out easing reaches this progress. Slow at both ends."""
    target = min(1.0, max(0.0, progress))
    lo, hi = 0.0, 1.0
    for _ in range(28):
        mid = (lo + hi) / 2
        if ease_in_out(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def column_delay(col, row, step=None, k=None):
    step = MOTION["column_step_s"] if step is None else step
    k = MOTION["column_k"] if k is None else k
    return round((col + row * k) * step, 3)


def voxel_delay(col, row, index, step=0.01, k=None, stack=0.06):
    """Diagonal wave plus a bottom-up stack offset. The intro stays under 1.8 s."""
    k = MOTION["column_k"] if k is None else k
    return round((col + row * k) * step + index * stack, 3)


def voxel_delay_css(cols, rows, stacks=4):
    bits = []
    k = MOTION["column_k"]
    for col in range(cols):
        bits.append(f".c{col}{{--c:{col * 0.01:.2f}s}}")
    for row in range(rows):
        bits.append(f".r{row}{{--r:{row * k * 0.01:.2f}s}}")
    for index in range(stacks):
        bits.append(f".s{index}{{--s:{index * 0.06:.2f}s}}")
    return "".join(bits)


def delay_s(index, start, step):
    return round(start + index * step, 3)


def reel_pitch(size):
    return round(size * 0.9, 2)


def reel_shift(digit, size):
    return round(int(digit) * reel_pitch(size), 2)


def reel_width(value, size, face=FACE):
    return svgtext.text_width("0", face, size, 0) * len(str(value))


def digit_advance(size, face=FACE):
    return svgtext.text_width("0", face, size, 0)


def digit_defs(size, fill, face=FACE, prefix="odo"):
    glyphs = svgtext._glyphs(face)
    scale = size / 1000.0
    bits = []
    for ch in "0123456789":
        path = svgtext._escape(glyphs[ch]["d"])
        bits.append(
            f'<g id="{prefix}-{ch}" fill="{fill}">'
            f'<path d="{path}" transform="scale({_num(scale)})"/></g>'
        )
    return "".join(bits)


def _digit(ch, size, x, y, fill, face=FACE):
    glyph = svgtext._glyphs(face)[ch]
    path = svgtext._escape(glyph["d"])
    scale = size / 1000.0
    return (
        f'<path fill="{fill}" d="{path}" '
        f'transform="translate({_num(x)} {_num(y)}) scale({_num(scale)})"/>'
    )


def odometer(value, x, baseline, size, ident, fill, delay=None, stagger=None):
    """Clipped digit reels. The attribute transform is the finished number."""
    text = str(value)
    pitch = reel_pitch(size)
    advance = digit_advance(size)
    delay = MOTION["reel_start_s"] if delay is None else delay
    stagger = MOTION["reel_stagger_ms"] / 1000 if stagger is None else stagger
    top = round(-size * 0.82, 2)
    clips = [digit_defs(size, fill, prefix=f"odo-{ident}")]
    body = [f'<g class="odo" data-odo="{text}" data-odo-size="{int(size)}">']
    cursor = x
    spline = EASE["out_quint"].removeprefix("cubic-bezier(").removesuffix(")").replace(",", "")
    for index, ch in enumerate(text):
        shift = reel_shift(int(ch), size)
        wait = delay_s(index, delay, stagger)
        clip = f"clip-{ident}-{index}"
        clips.append(
            f'<clipPath id="{clip}"><rect x="{_num(cursor - 0.6)}" y="{_num(baseline + top)}" '
            f'width="{_num(advance + 1.2)}" height="{_num(pitch)}"/></clipPath>'
        )
        stack = "".join(
            f'<use href="#odo-{ident}-{number}" transform="translate({_num(cursor)} {_num(baseline - number * pitch)})"/>'
            for number in range(10)
        )
        body.append(f'<g class="odo-col" clip-path="url(#{clip})">')
        body.append(
            f'<g class="odo-still"><g class="odo-reel" data-digit="{ch}" '
            f'transform="translate(0 {_num(shift)})">{stack}</g></g>'
        )
        body.append(
            f'<g class="odo-live">{stack}'
            f'<animateTransform attributeName="transform" type="translate" '
            f'begin="{wait:.3f}s" dur="{MOTION["reel_ms"]}ms" fill="freeze" '
            f'calcMode="spline" keyTimes="0;1" keySplines="{spline}" '
            f'from="0 0" to="0 {_num(shift)}"/></g></g>'
        )
        cursor += advance
    body.append("</g>")
    return "".join(clips), "".join(body), cursor - x


def reel_css(_size=None):
    """Reels move in user units via SMIL. CSS transforms would be screen pixels."""
    return """
.odo-live { display: none; }
.odo-still { display: inline; }
@media (prefers-reduced-motion: no-preference) {
  .odo-live { display: inline; }
  .odo-still { display: none; }
}
"""


def hero_style(size):
    dur = MOTION["chrome_ms"]
    return f"""<style>
{reel_css(size)}
.line, .chrome-status {{ clip-path: inset(0 0 0 0); }}
.cursor {{ opacity: 1; }}
.ticker {{ transform: none; }}
@media (prefers-reduced-motion: no-preference) {{
  .line, .chrome-status {{ animation: plot-in {dur}ms steps(3, end) both; animation-delay: var(--d, 0s); }}
  .ticker {{ animation: ticker 18s {EASE['in_out']} infinite; }}
}}
@keyframes plot-in {{
  from {{ clip-path: inset(0 100% 0 0); }}
  to {{ clip-path: inset(0 0 0 0); }}
}}
@keyframes ticker {{
  from {{ transform: translateX(0); }}
  to {{ transform: translateX(-50%); }}
}}
@media (prefers-reduced-motion: reduce) {{
  .line, .ticker, .chrome-status, .odo-reel {{ animation: none !important; }}
  .line, .chrome-status {{ clip-path: inset(0 0 0 0) !important; }}
  .ticker {{ transform: none !important; }}
  .cursor {{ opacity: 1 !important; }}
}}
</style>"""


def lab_style():
    ease = EASE
    return f"""<style>
.dot {{ opacity: 1; }}
.cage-spin {{ display: none; opacity: 1; }}
.cage-still {{ display: inline; }}
.lab-in {{ opacity: 1; transform: none; }}
@media (prefers-reduced-motion: no-preference) {{
  .cage-spin {{
    display: inline;
    transform-box: fill-box;
    transform-origin: center;
    animation: cage-in {MOTION['cage_in_ms']}ms {ease['out_quint']} both;
  }}
  .cage-still {{ display: none; }}
  .lab-in {{
    animation: line-in 240ms steps(3, end) both;
    animation-delay: var(--d, 0s);
  }}
}}
@keyframes cage-in {{
  from {{ opacity: 0; transform: scale(0.92); }}
  to {{ opacity: 1; transform: scale(1); }}
}}
@keyframes line-in {{
  from {{ transform: translateX(-8px); }}
  to {{ transform: none; }}
}}
@media (prefers-reduced-motion: reduce) {{
  .dot, .cage-spin, .lab-in {{ animation: none !important; }}
  .dot, .lab-in {{ opacity: 1 !important; }}
  .lab-in {{ transform: none !important; }}
  .cage-spin {{ display: none !important; }}
  .cage-still {{ display: inline !important; }}
}}
</style>"""


def workshop_style():
    return """<style>
.row { transform: none; }
@media (prefers-reduced-motion: no-preference) {
  .row {
    animation: row-in 240ms steps(3, end) both;
    animation-delay: var(--d, 0s);
  }
}
@keyframes row-in {
  from { transform: translateX(-8px); }
  to { transform: none; }
}
@media (prefers-reduced-motion: reduce) {
  .row { animation: none !important; transform: none !important; }
}
</style>"""


def _wave_amps():
    return ".a0{--a:-18px}.a1{--a:-16px}.a2{--a:-14px}.a3{--a:-12px}"


def _wave_delays(cols, rows):
    step = MOTION["wave_step_s"]
    span = max(cols - 1, 0) + max(rows - 1, 0)
    delays = []
    for distance in range(span + 1):
        delay = round(distance * step, 2)
        delays.append(f".d{distance}{{animation-delay:calc(2.4s + {delay}s)}}")
    return "".join(delays)


def contrib_style(size, cols=53, rows=7):
    ease = EASE
    return f"""<style>
{reel_css(size)}
{voxel_delay_css(cols, rows)}
{_wave_amps()}
.voxel {{ transform: none; }}
.floor {{ opacity: 1; }}
@media (prefers-reduced-motion: no-preference) {{
  .floor {{ animation: floor-in {MOTION['floor_ms']}ms {ease['out_quint']} both; }}
  .voxel {{
    animation: voxel-drop 360ms {ease['out_quint']} both;
    animation-delay: calc(var(--c, 0s) + var(--r, 0s) + var(--s, 0s));
  }}
  .w {{ animation: wave {MOTION['wave_s']}s {ease['out_quint']} infinite; }}
}}
{_wave_delays(cols, rows)}
@keyframes floor-in {{
  from {{ opacity: 0; clip-path: polygon(0 0, 0 0, 0 0, 0 0); }}
  to {{ opacity: 1; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%); }}
}}
@keyframes voxel-drop {{
  from {{ transform: translate(0, -24px); }}
  to {{ transform: none; }}
}}
@keyframes wave {{
  0% {{ transform: none; }}
  3% {{ transform: translateY(var(--a)); }}
  10%, 100% {{ transform: none; }}
}}
@media (prefers-reduced-motion: reduce) {{
  .voxel, .floor, .odo-reel {{ animation: none !important; }}
  .voxel {{ transform: none !important; }}
  .floor {{ opacity: 1 !important; }}
  .w {{ animation: none !important; transform: none !important; }}
}}
</style>"""


def badge_style(wait=0.0):
    return f"""<style>
@media (prefers-reduced-motion: no-preference) {{
  .tab {{ transform-box: fill-box; transform-origin: 0 100%; animation: tab-in 240ms steps(3, end) {wait:.2f}s both; }}
}}
@keyframes tab-in {{
  from {{ transform: scaleY(0); }}
  to {{ transform: none; }}
}}
@media (prefers-reduced-motion: reduce) {{
  .tab {{ animation: none !important; transform: none !important; }}
}}
</style>"""
