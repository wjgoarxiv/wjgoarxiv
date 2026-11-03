"""CRT boot hero."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crt
import layout
import tokens

OUT = Path(__file__).resolve().parents[1] / "assets" / "hero.svg"
ASSETS = OUT.parent
BEZEL = 104

STYLE = """<style>
.line { opacity: 1; clip-path: none; }
.cursor { opacity: 1; }
.sweep { opacity: 0; }
.hdd { opacity: 0.28; }
@media (prefers-reduced-motion: no-preference) {
  .line { opacity: 0; animation: reveal 0.35s linear forwards; }
  .l1 { animation-delay: 0s; }
  .l2 { animation-delay: 0.45s; }
  .l3 { animation-delay: 0.9s; }
  .l4 { animation-delay: 1.35s; }
  .l5 { animation-delay: 1.8s; }
  .cursor { animation: blink 1s steps(2, end) infinite; }
  .sweep { opacity: 0.35; animation: sweep 5s linear infinite; }
  .hdd { animation: hdd 4.2s steps(1, end) forwards; }
}
@keyframes reveal {
  0% { opacity: 0; clip-path: inset(0 100% 0 0); }
  100% { opacity: 1; clip-path: inset(0 0 0 0); }
}
@keyframes blink {
  0%, 49% { opacity: 1; }
  50%, 100% { opacity: 0; }
}
@keyframes sweep {
  from { transform: translateY(48px); }
  to { transform: translateY(240px); }
}
@keyframes hdd {
  0%, 18% { opacity: 0.28; }
  19%, 28% { opacity: 1; }
  29%, 46% { opacity: 0.28; }
  47%, 54% { opacity: 1; }
  55%, 100% { opacity: 0.28; }
}
@media (prefers-reduced-motion: reduce) {
  .line { animation: none !important; animation-delay: 0s !important; opacity: 1 !important; clip-path: none !important; }
  .cursor { animation: none !important; opacity: 1 !important; }
  .sweep { animation: none !important; opacity: 0 !important; }
  .hdd { animation: none !important; opacity: 0.28 !important; }
}
</style>"""


def _lines(p):
    return (
        ("l1", "[ OK ] mounting /lab/hydrate", p.LAB),
        ("l2", "[ OK ] loading litfamily.agents", p.WORK),
        ("l3", "wjgo@lab:~$ whoami", p.TEXT),
    )


def _name(p, x, y, size):
    latin = "Woojin Go, Ph.D. · "
    return crt.text(latin, "meslo-regular", size, x, y, p.TEXT) + crt.text(
        "고우진", "pretendard-regular", size, x + crt.width(latin, "meslo-regular", size), y, p.TEXT
    )


def _nameplate(theme, screen_h):
    spec = tokens.THEMES[theme]
    raw = (ASSETS / spec["lockup"]).read_text(encoding="utf-8")
    view = re.search(r'viewBox="([^"]+)"', raw).group(1)
    inner = raw.split(">", 1)[1].rsplit("</svg>", 1)[0]
    inner = re.sub(r'<rect\b[^>]*fill="transparent"[^>]*/>\s*', "", inner)
    # Uniform scale only. The box matches the night lockup; day letterboxes inside it.
    return (
        f'<svg id="nameplate" x="28" y="{screen_h + 16}" width="280" height="72" '
        f'viewBox="{view}" preserveAspectRatio="xMidYMid meet">{inner}</svg>'
    )


def _load_model(model):
    if model is not None:
        return model
    return json.loads((ASSETS.parent / "data" / "live.json").read_text(encoding="utf-8"))


def _boot_layout(screen_h):
    size = 16 if screen_h >= 230 else 14
    leading = 26 if screen_h >= 230 else 22
    first = 86 if screen_h >= 230 else 78
    return size, leading, first


def render(theme="night", preset=None, model=None):
    spec = layout.load(preset)
    out_w = spec["width"]
    out_h = spec["hero_h"]
    screen_h = out_h - BEZEL
    model = _load_model(model)
    p = crt.Chrome(theme)
    size, leading, first = _boot_layout(screen_h)
    x = 28
    parts = [
        crt.svg_open(out_w, out_h),
        STYLE,
        p.DEFS,
        "<defs>"
        f'<linearGradient id="bezel" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{p.t["bezel_top"]}"/>'
        f'<stop offset="1" stop-color="{p.t["bezel_bottom"]}"/>'
        f"</linearGradient>"
        f'<clipPath id="screen"><rect width="{out_w}" height="{screen_h}"/></clipPath>'
        "</defs>",
        '<g clip-path="url(#screen)">',
        p.screen(out_w, screen_h),
        crt.ticks(out_w, screen_h, p.LAB),
        p.blocks(("TTY1", "PID 0x2A", f"{out_w}x{screen_h}", "UTF-8"), p.LAB),
        f'<line x1="16" y1="30" x2="{out_w - 16}" y2="30" stroke="{p.GRID}" stroke-width="1"/>',
        p.bloom(crt.dot_text("WJGO // RESEARCH TERMINAL", 28, 40, 3, p.LAB)),
        p.bloom("".join(_boot_lines(p, x, first, leading, size))),
    ]
    cursor_y = first + 5 * leading
    parts.append(f'<rect class="cursor" x="{x}" y="{cursor_y - 14}" width="10" height="16" fill="{p.LAB}"/>')
    parts.append(_scope(p, out_w, first))
    parts.append("</g>")
    parts.append(
        f'<rect x="0" y="{screen_h}" width="{out_w}" height="{BEZEL}" fill="url(#bezel)"/>'
        f'<line x1="0" y1="{screen_h}" x2="{out_w}" y2="{screen_h}" stroke="{p.t["bezel_highlight"]}" stroke-width="1"/>'
        f'<line x1="0" y1="{out_h - 1}" x2="{out_w}" y2="{out_h - 1}" stroke="{p.t["bezel_shadow"]}" stroke-width="1"/>'
    )
    parts.append(_nameplate(theme, screen_h))
    parts.append(_status(p, model, screen_h, out_w))
    lamp_y = screen_h + 36
    parts.append(f'<circle cx="{out_w - 250}" cy="{lamp_y}" r="4" fill="{p.LAB}"/>')
    parts.append(crt.text("PWR", "meslo-regular", 12, out_w - 238, lamp_y + 4, p.t["bezel_text"]))
    parts.append(
        f'<circle cx="{out_w - 170}" cy="{lamp_y}" r="4" fill="none" stroke="{p.t["bezel_text"]}" stroke-width="1.2"/>'
        f'<circle class="hdd" cx="{out_w - 170}" cy="{lamp_y}" r="2.4" fill="{p.t["bezel_text"]}"/>'
    )
    parts.append(crt.text("HDD", "meslo-regular", 12, out_w - 158, lamp_y + 4, p.t["bezel_text"]))
    for i in range(7):
        parts.append(
            f'<rect x="{out_w - 110 + i * 10}" y="{lamp_y - 8}" width="3" height="18" fill="{p.t["bezel_vent"]}"/>'
        )
    parts.append(f"<!-- manifest:stars={model['stars']} -->")
    parts.append("</svg>")
    return "".join(parts)


def _status(p, model, screen_h, width):
    release = model.get("release") or model.get("latest") or "n/a"
    push = str(model.get("last_push", ""))[5:10]
    cells = (
        ("LAB ● ONLINE", p.LAB),
        ("WORK ● ONLINE", p.WORK),
        (f"REL {release}", p.t["bezel_text"]),
        (f"★ {model['stars']}", p.t["bezel_text"]),
        (f"PUSH {push}", p.t["bezel_text"]),
        (f"UPD {model.get('updated', '')}", p.t["bezel_text"]),
    )
    lamp_left = width - 270
    size = 12
    gap = 14
    while size > 8:
        widths = [crt.width(label, "meslo-regular", size) for label, _fill in cells]
        if 324 + sum(widths) + gap * (len(cells) - 1) <= lamp_left:
            break
        size -= 1
        gap = 8
    x = 324
    y = screen_h + 48
    bits = []
    for label, fill in cells:
        bits.append(crt.text(label, "meslo-regular", size, x, y, fill))
        x += crt.width(label, "meslo-regular", size) + gap
    return "".join(bits)


def _scope(p, width, first):
    """Right-hand instrument block. Static, so reduced motion shows the same frame."""
    x = 760
    top = first - 8
    bits = [
        f'<rect x="{x - 12}" y="{top - 8}" width="{width - x - 16}" height="168" fill="none" stroke="{p.GRID}" stroke-width="1"/>'
    ]
    trace = []
    for index in range(42):
        px = x + index * 8.4
        wave = (index * 37 % 23) - 11
        if index % 9 == 0:
            wave = 16
        py = top + 28 - wave * 0.7
        trace.append(f"{px:.1f},{py:.1f}")
    bits.append(
        f'<polyline fill="none" stroke="{p.DIM}" stroke-width="1.2" opacity="0.8" points="{" ".join(trace)}"/>'
    )
    rows = (("MEM", "64K OK"), ("LINK", "litfamily"), ("NODE", "ovito · pymol"))
    y = top + 78
    for label, value in rows:
        bits.append(crt.text(label, "meslo-regular", 13, x, y, p.LAB))
        bits.append(crt.text(value, "meslo-regular", 13, x + 58, y, p.DIM))
        y += 22
    return "".join(bits)


def _boot_lines(p, x, first, leading, size):
    bits = []
    row = 0
    for cls, label, fill in _lines(p):
        y = first + row * leading
        bits.append(f'<g class="line {cls}">{crt.text(label, "meslo-regular", size, x, y, fill)}</g>')
        row += 1
    bits.append(f'<g class="line l4">{_name(p, x, first + row * leading, size)}</g>')
    row += 1
    tagline = "Researcher · agent tool builder"
    bits.append(
        f'<g class="line l5">{crt.text(tagline, "meslo-regular", size, x, first + row * leading, p.DIM)}</g>'
    )
    return "".join(bits)


def main(argv=None):
    themes, preset = tokens.options(argv)
    for theme in themes:
        tokens.themed_path(OUT, theme).write_text(render(theme, preset), encoding="utf-8")
    tokens.retire_unthemed(OUT)


if __name__ == "__main__":
    main()
