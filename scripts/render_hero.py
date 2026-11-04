"""CRT boot hero."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crt
import layout
import motion
import tokens

OUT = Path(__file__).resolve().parents[1] / "assets" / "hero.svg"
ASSETS = OUT.parent
BEZEL = 104
BEZEL_MARK_W = 20

def _lines(p):
    return (
        ("l1", "$ mounting /lab/hydrate", p.LAB),
        ("l2", "$ loading litfamily", p.WORK),
        ("l3", "$ whoami → woojin go", p.TEXT),
    )


def _nameplate(theme, screen_h):
    spec = tokens.THEMES[theme]
    raw = (ASSETS / spec["lockup"]).read_text(encoding="utf-8")
    view = re.search(r'viewBox="([^"]+)"', raw).group(1)
    cap = float(re.search(r'data-cap="([0-9.]+)"', raw).group(1))
    _x, _y, vb_w, vb_h = (float(part) for part in view.split())
    cap_px = 52.0
    height = cap_px * vb_h / cap
    width = height * vb_w / vb_h
    max_h = BEZEL - 38
    max_w = 760.0
    if height > max_h or width > max_w:
        height = min(height, max_h)
        width = height * vb_w / vb_h
        if width > max_w:
            width = max_w
            height = width * vb_h / vb_w
    y = screen_h + 32
    inner = raw.split(">", 1)[1].rsplit("</svg>", 1)[0]
    # The module's left ink sits at local x=28, inset from the lockup viewBox origin.
    placed = re.search(
        r'transform="translate\(([-\d.]+) [-\d.]+\)"><g transform="translate\(([-\d.]+) [-\d.]+\) scale\(([-\d.]+)\)"',
        raw,
    )
    shift, inner_x, scale = (float(part) for part in placed.groups())
    ink = 28 * scale + inner_x + shift
    x = layout.INSET - (ink - _x) * (width / vb_w)
    return (
        f'<svg id="nameplate" x="{x:.2f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" '
        f'viewBox="{view}" data-cap="{cap:.0f}" preserveAspectRatio="xMidYMid meet">{inner}</svg>'
    )


def _load_model(model):
    if model is not None:
        return model
    return json.loads((ASSETS.parent / "data" / "live.json").read_text(encoding="utf-8"))


def _boot_layout(screen_h):
    # About 1.3× the previous 16 px boot face, pulled up so the screen is not a dead band.
    if screen_h >= 240:
        return 21, 28, 46
    if screen_h >= 200:
        return 16, 22, 36
    return 13, 18, 30


def render(theme="night", preset=None, model=None):
    spec = layout.load(preset)
    out_w = spec["width"]
    out_h = spec["hero_h"]
    screen_h = out_h - BEZEL
    model = _load_model(model)
    p = crt.Chrome(theme)
    size, leading, first = _boot_layout(screen_h)
    status_x = layout.INSET + BEZEL_MARK_W + 10
    status_size = _status_size(model, out_w, status_x)
    x = 28
    status_defs, status_body = _status(p, model, screen_h, out_w, status_size, status_x)
    band_x, band_w = _ticker_band(out_w, screen_h)
    parts = [
        crt.svg_open(out_w, out_h),
        motion.hero_style(status_size),
        p.DEFS,
        "<defs>"
        f'<clipPath id="screen"><rect width="{out_w}" height="{screen_h}"/></clipPath>'
        f'<clipPath id="ticker"><rect x="{band_x:.1f}" y="{screen_h - 22}" width="{band_w:.1f}" height="16"/></clipPath>'
        f"{status_defs}"
        "</defs>",
        '<g clip-path="url(#screen)">',
        p.screen(out_w, screen_h, scan=True),
        _corners(p, out_w, screen_h),
        f'<g class="boot" data-size="{size}">',
        "".join(_boot_lines(p, x, first, leading, size)),
    ]
    prompt_y = first + 3 * leading
    prompt = _prompt(p, x, prompt_y, size)
    cursor_h = round(size * 0.86)
    cursor_x = x + crt.width("~/", "meslo-regular", size) + crt.width("woojin-go ", "meslo-regular", size)
    cursor = (
        f'<rect class="cursor" x="{cursor_x:.1f}" y="{prompt_y - cursor_h}" '
        f'width="{max(8, round(size * 0.5))}" height="{cursor_h}" fill="{p.t["cyan"]}"/>'
    )
    parts.append(f'<g class="line l4" style="--d:{_line_delay(3)}s" data-copy="~/woojin-go">{prompt}{cursor}</g>')
    parts.append("</g>")
    parts.append(_identity(p, x, prompt_y, screen_h))
    parts.append(_ticker(p, model, out_w, screen_h, band_x))
    parts.append("</g>")
    parts.append(
        f'<rect x="0" y="{screen_h}" width="{out_w}" height="{BEZEL}" fill="{p.t["sunken"]}"/>'
        f'<line x1="0" y1="{screen_h}" x2="{out_w}" y2="{screen_h}" stroke="{p.t["bezel_highlight"]}" stroke-width="1"/>'
    )
    parts.append(_bezel_mark(theme, screen_h))
    parts.append(_nameplate(theme, screen_h))
    lamp_y = screen_h + 16
    lamps = [f'<circle cx="{out_w - 250}" cy="{lamp_y}" r="4" fill="{p.LAB}"/>']
    lamps.append(crt.text("PWR", "meslo-regular", 12, out_w - 238, lamp_y + 4, p.t["bezel_text"]))
    lamps.append(
        f'<circle cx="{out_w - 170}" cy="{lamp_y}" r="4" fill="none" stroke="{p.t["bezel_text"]}" stroke-width="1.2"/>'
        f'<circle class="hdd" cx="{out_w - 170}" cy="{lamp_y}" r="2.4" fill="{p.t["bezel_text"]}"/>'
    )
    lamps.append(crt.text("HDD", "meslo-regular", 12, out_w - 158, lamp_y + 4, p.t["bezel_text"]))
    for i in range(7):
        lamps.append(
            f'<rect x="{out_w - 110 + i * 10}" y="{lamp_y - 8}" width="3" height="18" fill="{p.t["bezel_vent"]}"/>'
        )
    parts.append(
        f'<g class="chrome-status" style="--d:{motion.MOTION["status_delay_s"]}s">{status_body}{"".join(lamps)}</g>'
    )
    parts.append(f"<!-- manifest:stars={model['stars']} -->")
    parts.append("</svg>")
    return "".join(parts)


def _status_cells(model):
    release = model.get("release") or model.get("latest") or "n/a"
    push = str(model.get("last_push", ""))[5:10]
    cells = [
        ("text", "LAB ● ONLINE", "lab"),
        ("text", "WORK ● ONLINE", "work"),
        ("text", f"REL {release}", "bezel"),
        ("odo", "★ ", model["stars"], "stars"),
        ("odo", "FOL ", model.get("followers", 0), "followers"),
        ("text", f"PUSH {push}", "bezel"),
        ("text", f"UPD {model.get('updated', '')}", "bezel"),
    ]
    return cells


def _cell_width(cell, size):
    if cell[0] == "text":
        return crt.width(cell[1], "meslo-regular", size)
    return crt.width(cell[1], "meslo-regular", size) + motion.reel_width(cell[2], size)


def _status_size(model, width, x0):
    cells = _status_cells(model)
    lamp_left = width - 270
    size = 12
    gap = 14
    while size > 8:
        widths = [_cell_width(cell, size) for cell in cells]
        if x0 + sum(widths) + gap * (len(cells) - 1) <= lamp_left:
            break
        size -= 1
        gap = 8
    return size


def _status(p, model, screen_h, width, size, x0):
    cells = _status_cells(model)
    gap = 14 if size >= 12 else 8
    fills = {"lab": p.LAB, "work": p.WORK, "bezel": p.t["bezel_text"]}
    x = x0
    y = screen_h + 20
    clips = []
    bits = []
    for cell in cells:
        fill = fills[cell[-1] if cell[0] == "text" else "bezel"]
        if cell[0] == "text":
            bits.append(crt.text(cell[1], "meslo-regular", size, x, y, fill))
            x += crt.width(cell[1], "meslo-regular", size) + gap
            continue
        label, value, ident = cell[1], cell[2], cell[3]
        bits.append(crt.text(label, "meslo-regular", size, x, y, fill))
        x += crt.width(label, "meslo-regular", size)
        clip, body, used = motion.odometer(value, x, y, size, ident, fill)
        clips.append(clip)
        bits.append(body)
        x += used + gap
    return "".join(clips), "".join(bits)


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


def _line_delay(index):
    return round(motion.MOTION["boot_delay_s"] + index * motion.MOTION["chrome_stagger_s"], 2)


def _boot_lines(p, x, first, leading, size):
    bits = []
    for row, (cls, label, fill) in enumerate(_lines(p)):
        y = first + row * leading
        bits.append(
            f'<g class="line {cls}" style="--d:{_line_delay(row)}s" data-copy="{label}">'
            f'{crt.text(label, "meslo-regular", size, x, y, fill)}</g>'
        )
    return bits


def _identity(p, x, prompt_y, screen_h):
    name = "Woojin Go, Ph.D. · 고우진"
    role = "Researcher · agent tool builder"
    name_y = prompt_y + 40
    role_y = name_y + 30
    if role_y > screen_h - 36:
        name_y = prompt_y + 28
        role_y = name_y + 22
    name_size = 26 if screen_h >= 240 else 18
    role_size = 16 if screen_h >= 240 else 13
    return (
        f'<g class="line l5" style="--d:{_line_delay(4)}s" data-copy="{name}">'
        f'{crt.text(name, "pretendard-semibold", name_size, x, name_y, p.TEXT)}</g>'
        f'<g class="line l6" style="--d:{_line_delay(5)}s" data-copy="{role}">'
        f'{crt.text(role, "meslo-regular", role_size, x, role_y, p.DIM)}</g>'
    )


def _prompt(p, x, y, size):
    slash = "~/"
    return crt.text(slash, "meslo-regular", size, x, y, p.t["phosphor"]) + crt.text(
        "woojin-go", "meslo-regular", size, x + crt.width(slash, "meslo-regular", size), y, p.TEXT
    )


def _corners(p, width, height):
    ink = p.t["cyan"]
    label = p.t["label"]
    marks = [crt.ticks(width, height, ink)]
    marks.append(crt.text("0,0", "meslo-regular", 10, 18, 22, label))
    right = f"{width},0"
    marks.append(crt.text(right, "meslo-regular", 10, width - 18 - crt.width(right, "meslo-regular", 10), 22, label))
    bottom = f"0,{height}"
    marks.append(crt.text(bottom, "meslo-regular", 10, 18, height - 8, label))
    far = f"{width},{height}"
    marks.append(
        crt.text(far, "meslo-regular", 10, width - 18 - crt.width(far, "meslo-regular", 10), height - 8, label)
    )
    return "".join(marks)


def _bezel_mark(theme, screen_h):
    raw = (ASSETS / "brand" / f"symbol-{theme}.svg").read_text(encoding="utf-8")
    inner = raw.split(">", 1)[1].rsplit("</svg>", 1)[0]
    return (
        f'<svg id="bezel-mark" x="{layout.INSET}" y="{screen_h + 6}" width="{BEZEL_MARK_W}" height="20" '
        f'viewBox="28 28 144 144">{inner}</svg>'
    )


def _ticker_band(width, height):
    """Inner band that clears the bottom corner labels and their crosses."""
    left = f"0,{int(height)}"
    right = f"{int(width)},{int(height)}"
    left_end = 18 + crt.width(left, "meslo-regular", 10)
    right_start = width - 18 - crt.width(right, "meslo-regular", 10)
    x0 = left_end + 20
    x1 = right_start - 20
    return x0, max(0.0, x1 - x0)


def _ticker(p, model, width, screen_h, band_x):
    facts = (
        f"MARK 200u  APER r40  INK {p.t['text']}  PHOS {p.t['phosphor']}  "
        f"★ {model['stars']}  FOL {model.get('followers', 0)}  REL {model.get('release') or 'n/a'}  "
        f"PUSH {str(model.get('last_push', ''))[:10]}"
    )
    text = facts + "    " + facts
    y = screen_h - 8
    return (
        f'<g clip-path="url(#ticker)"><g class="ticker">'
        f'{crt.text(text, "meslo-regular", 11, band_x, y, p.t["label"])}'
        f"</g></g>"
    )


def main(argv=None):
    themes, preset = tokens.options(argv)
    for theme in themes:
        tokens.themed_path(OUT, theme).write_text(render(theme, preset), encoding="utf-8")
    tokens.retire_unthemed(OUT)


if __name__ == "__main__":
    main()
