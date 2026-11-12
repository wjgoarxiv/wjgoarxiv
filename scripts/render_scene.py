"""Signature scene: three acts (sI hydrate, agentvfx, LitFamily) as one looping SVG.

GitHub serves README images without JS, so the scene is pre-rendered: 36 frame groups switched by a
step-end CSS animation (12 frames per act, 0.25 s each, then a hold on the last frame). The default,
and the reduced-motion state, is a still triptych of each act's final frame. Standard library only.
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crt
import layout
import tokens
from render_cards import Glyphs

ROOT = Path(__file__).resolve().parents[1]
W, H = 1200, 300
BAR = 28
FRAMES_PER_ACT = 12
STEP_S = 0.25
HOLD_S = 2.0
DRAW = (400, 48, 1172, 286)  # free drawing box, right of the caption column
TEXT_X = layout.INSET

CAPTIONS = (
    ("I · sI hydrate", ("water first", "cages close", "CO2 inside")),
    ("II · agentvfx", ("my own track", "on the beat", "every frame checked")),
    ("III · LitFamily", ("one word: lit", "seven agents", "handoff written")),
)
AGENTS = ("LitClaude", "LitCodex", "LitOpenCode", "LitHermes", "LitGrok", "LitMuse", "LitGravity")
PROMPT = "> fix the flaky test lit"


class Labels:
    """Draws each distinct label once in <defs> and places it with <use>, so repeated frames stay small."""

    def __init__(self):
        self.glyphs = Glyphs()
        self.ids, self.body = {}, []

    def width(self, value, face, size):
        return self.glyphs.width(value, face, size)

    def text(self, value, face, size, x, y, fill, subject=False):
        key = (value, face, size, fill, subject)
        if key not in self.ids:
            self.ids[key] = f"t{len(self.ids)}"
            tag = ' data-subject="1"' if subject else ""
            self.body.append(f'<g id="{self.ids[key]}"{tag}>' + self.glyphs.text(value, face, size, 0, 0, fill).replace("<g fill=", f"<g{tag} fill=", 1) + "</g>")
        return f'<use href="#{self.ids[key]}" x="{x:.0f}" y="{y:.0f}"/>'

    def defs(self):
        return self.glyphs.defs() + "".join(self.body)


def _hash(n):
    x = math.sin(n * 12.9898) * 43758.5453
    return x - math.floor(x)


class Ink:
    """Collects square dots and dotted edges per colour, then writes one path per colour."""

    def __init__(self):
        self.dots, self.lines, self.raw = {}, {}, []

    def dot(self, x, y, size, color, subject=False):
        s = max(1, round(size))
        key = (color, subject)
        self.dots.setdefault(key, []).append(f"M{round(x - s / 2)} {round(y - s / 2)}h{s}v{s}h-{s}z")

    def line(self, ax, ay, bx, by, color, subject=False):
        self.lines.setdefault((color, subject), []).append(f"M{ax:.0f} {ay:.0f}L{bx:.0f} {by:.0f}")

    def add(self, markup):
        self.raw.append(markup)

    def svg(self):
        out = []
        for (color, subject), segs in self.lines.items():
            tag = ' data-subject="1"' if subject else ""
            out.append(f'<path{tag} d="{"".join(segs)}" stroke="{color}" stroke-width="1.5" stroke-dasharray="1.5 3.5" fill="none"/>')
        for (color, subject), segs in self.dots.items():
            tag = ' data-subject="1"' if subject else ""
            out.append(f'<path{tag} d="{"".join(segs)}" fill="{color}"/>')
        return "".join(out) + "".join(self.raw)


def _project(p, yaw, box, unit, tilt=0.42, cam=40.0):
    x, y, z = p
    ca, sa, ct, st = math.cos(yaw), math.sin(yaw), math.cos(tilt), math.sin(tilt)
    x1, z1 = x * ca + z * sa, -x * sa + z * ca
    y2, z2 = y * ct - z1 * st, y * st + z1 * ct
    k = cam / (cam + z2)
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    return cx + x1 * unit * k, cy + y2 * unit * k, z2


# ---- Act I: sI hydrate ---------------------------------------------------------------------------

def _fit_unit(points, yaw, box):
    """Scale that keeps the projected slab inside the box (measured at the last frame's yaw)."""
    pts = [_project(p, yaw, (0, 0, 0, 0), 1.0) for p in points]
    w = max(abs(x) for x, _, _ in pts) * 2 * 1.08
    h = max(abs(y) for _, y, _ in pts) * 2 * 1.08
    return min((box[2] - box[0]) / w, (box[3] - box[1]) / h)


def _hydrate(ink, f, box, t, data):
    stage, local = f // 4, (f % 4) / 3
    unit = _fit_unit(data["o"], 0.5 + 11 * 0.035, box)
    yaw = 0.5 + f * 0.035
    k = local if stage == 0 else 1
    pts = []
    for i, p in enumerate(data["o"]):
        off = [(_hash(i * 3 + j) - 0.5) * 7 * (1 - k) for j in range(3)]
        pts.append(_project([p[j] + off[j] for j in range(3)], yaw, box, unit))
    zs = [p[2] for p in pts]
    zmin, zmax = min(zs), max(zs)
    tones = (t["text"], t["text_dim"], t["label"])
    if stage >= 1:
        edges = sorted(data["edges"], key=lambda e: data["o"][e[0]][0] + data["o"][e[1]][0])
        shown = edges if stage == 2 else edges[: round(len(edges) * (local * 0.75 + 0.25))]
        for a, b in shown:
            ink.line(pts[a][0], pts[a][1], pts[b][0], pts[b][1], t["label"])
    for x, y, z in pts:
        band = min(2, int(3 * (z - zmin) / (zmax - zmin + 1e-9)))
        ink.dot(x, y, 4 - band, tones[band] if stage else t["label"])
    if stage == 2:
        cages = data["cages"]
        n = max(1, math.ceil(len(cages) * (local * 0.75 + 0.25)))
        for ci, cage in enumerate(cages[:n]):
            cx, cy, _ = _project(cage["c"], yaw, box, unit)
            a = f * 0.45 + ci
            dx, dy = math.cos(a) * 6, math.sin(a) * 3
            ink.dot(cx, cy, 5, t["workshop"], subject=True)
            ink.dot(cx - dx, cy - dy, 3, t["workshop"], subject=True)
            ink.dot(cx + dx, cy + dy, 3, t["workshop"], subject=True)
    full = data["full"]
    if stage == 0:
        return f"{round(full['o'] * (0.25 + 0.75 * local))} / {full['o']}", "water placed", False
    if stage == 1:
        return f"{round(full['edges'] * (0.25 + 0.75 * local))} / {full['edges']}", "H-bonds", False
    return f"{round(56 * (0.25 + 0.75 * local))} / {full['cages']}", "cages hold CO2", False


# ---- Act II: agentvfx ----------------------------------------------------------------------------

def _amp(tau):
    beat = tau % 1
    kick = math.exp(-beat * 6)
    hat = 0.35 * math.exp(-((tau * 2) % 1) * 9)
    return min(1.0, 0.18 + 0.7 * kick + hat + 0.12 * _hash(math.floor(tau * 8)))


def _vfx(ink, f, box, t, defs):
    stage, local = f // 4, (f % 4) / 3
    x0, y0, x1, y1 = box
    cols, beats = 48, 16
    colw = (x1 - x0) / cols
    wave_mid = y0 + (y1 - y0) * (0.42 if stage < 2 else 0.24)
    amp_h = (y1 - y0) * (0.34 if stage < 2 else 0.18)
    tau0 = f * 0.5
    for c in range(cols):
        tau = tau0 + c * beats / cols
        h = max(2, _amp(tau) * amp_h)
        x = x0 + (c + 0.5) * colw
        play = c == cols // 4
        if play:
            ink.line(x, wave_mid - h, x, wave_mid + h, t["workshop"], subject=True)
        else:
            ink.line(x, wave_mid - h, x, wave_mid + h, t["text_dim"])
    if stage >= 1:
        locked = beats if stage == 2 else round(beats * (local * 0.75 + 0.25))
        for b in range(beats):
            x = x0 + ((b - (tau0 % 1)) * cols / beats + 0.5) * colw
            if x0 <= x <= x1:
                ink.dot(x, wave_mid - amp_h - 12, 5 if b < locked else 3, t["text"] if b < locked else t["label"])
    if stage == 2:
        tc, tr, gap = 12, 2, 10
        ts = min(((x1 - x0) - (tc - 1) * gap) / tc, 34)
        gx = x0 + ((x1 - x0) - (tc * ts + (tc - 1) * gap)) / 2
        gy = y0 + (y1 - y0) * 0.5
        checked = round(tc * tr * (local * 0.75 + 0.25))
        for i in range(tc * tr):
            x, y = gx + (i % tc) * (ts + gap), gy + (i // tc) * (ts + gap)
            ink.add(f'<use href="#tile{(i * 7 + f) % 4}" x="{x:.0f}" y="{y:.0f}"/>')
            color = t["phosphor"] if i < checked else t["label"]
            ink.add(f'<use href="#{"ok" if i < checked else "no"}{round(ts)}" x="{x - 3:.0f}" y="{y - 3:.0f}"/>')
            defs.setdefault(f'{"ok" if i < checked else "no"}{round(ts)}', _bracket_path(ts + 6, 6, color))
        ty = gy + tr * (ts + gap) + 6
        for c in range(cols):
            x = x0 + (c + 0.5) * colw
            ink.dot(x, ty + 10 - 8 * _hash(c + f), 2, t["phosphor"])
        ink.line(x0, ty - 2, x1, ty - 2, t["label"])
    if stage == 0:
        return "128 BPM", "tempo read from the track", False
    if stage == 1:
        return f"{round(32 * (local * 0.75 + 0.25))} / 32", "beats locked", False
    done = round(720 * (local * 0.75 + 0.25))
    return (f"{done} / 720 ✓" if done == 720 else f"{done} / 720"), "frames under the flash limit", done == 720


def _bracket_path(s, arm, color):
    """Square corner brackets around an s × s box, as one reusable path."""
    d = f"M0 {arm}V0H{arm}M{s - arm:g} 0H{s:g}V{arm}M{s:g} {s - arm:g}V{s:g}H{s - arm:g}M{arm} {s:g}H0V{s - arm:g}"
    return f'<path d="{d}" stroke="{color}" stroke-width="1.5" fill="none"/>'



def _tile_defs(t):
    """Four small dot patterns, drawn once and reused by every tile."""
    out = []
    for k in range(4):
        segs = []
        for j in range(16):
            gx, gy = j % 4, j // 4
            if _hash(k * 31 + j) > (0.35 + 0.1 * k):
                segs.append(f"M{4 + gx * 7} {4 + gy * 7}h3v3h-3z")
        out.append(f'<g id="tile{k}"><path d="{"".join(segs)}" fill="{t["text_dim"]}"/></g>')
    return "".join(out)


# ---- Act III: LitFamily --------------------------------------------------------------------------

def _lit(ink, f, box, t, glyphs):
    stage, local = f // 4, (f % 4) / 3
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    size = 16
    chars = len(PROMPT) if stage else max(3, round(len(PROMPT) * (0.25 + 0.75 * local)))
    shown = PROMPT[:chars]
    tw = glyphs.width(PROMPT, "meslo-regular", size)
    bx0, bx1, by0, by1 = cx - tw / 2 - 14, cx + tw / 2 + 14, cy - 18, cy + 14
    compact = (x1 - x0) < 500  # a still-triptych panel: no names, a tighter ring
    rx, ry = (x1 - x0) * (0.42 if compact else 0.4), (y1 - y0) * (0.4 if compact else 0.44)
    nodes = [
        (cx + rx * math.cos(-math.pi / 2 + i * 2 * math.pi / 7 + f * 0.03), cy + ry * math.sin(-math.pi / 2 + i * 2 * math.pi / 7 + f * 0.03))
        for i in range(7)
    ]
    if stage >= 1:
        for i, (x, y) in enumerate(nodes):
            ink.line(cx, cy, x, y, t["label"])
            u = ((f * 0.27 + i * 0.37) % 1)
            ink.dot(cx + (x - cx) * u, cy + (y - cy) * u, 4, t["workshop"], subject=True)
        done = 0 if stage == 1 else round(7 * (local * 0.75 + 0.25))
        for i, (x, y) in enumerate(nodes):
            ok = i < done
            ink.dot(x, y, 10, t["phosphor"] if ok else t["text"])
            if compact:
                continue
            name = AGENTS[i] + (" ✓" if ok else "")
            right = x >= cx
            nx = x + 12 if right else x - 12 - glyphs.width(name, "meslo-regular", 13)
            ink.add(glyphs.text(name, "meslo-regular", 13, nx, y + 4, t["phosphor"] if ok else t["text_dim"]))
    ink.add(f'<rect x="{bx0:.0f}" y="{by0:.0f}" width="{bx1 - bx0:.0f}" height="{by1 - by0:.0f}" fill="{t["screen_bg"]}" stroke="{t["border"]}"/>')
    base = shown[:-3] if shown.endswith("lit") else shown
    ink.add(glyphs.text(base, "meslo-regular", size, cx - tw / 2, cy + 3, t["text"]))
    if shown.endswith("lit"):
        lx = cx - tw / 2 + glyphs.width(base, "meslo-regular", size)
        ink.add(glyphs.text("lit", "meslo-bold", size, lx, cy + 3, t["workshop"], subject=True))
    if stage == 2 and local == 1:
        hx, hy = min(cx + 40, x1 - 200), min(cy + 26, y1 - 60)
        ink.add(f'<rect x="{hx:.0f}" y="{hy:.0f}" width="196" height="58" fill="{t["screen_bg"]}" stroke="{t["text"]}"/>')
        ink.add(glyphs.text("HANDOFF.md", "meslo-bold", 13, hx + 10, hy + 18, t["text"]))
        ink.add(glyphs.text("checks  7 / 7 ✓", "meslo-regular", 12, hx + 10, hy + 34, t["phosphor"]))
        ink.add(glyphs.text("next    resume with lit", "meslo-regular", 12, hx + 10, hy + 49, t["text_dim"]))
    if stage == 0:
        return "1 word", "added to the prompt", False
    if stage == 1:
        return "7 agents", "same rules in each harness", False
    done = round(7 * (local * 0.75 + 0.25))
    return (f"{done} / 7 ✓" if done == 7 else f"{done} / 7"), "checks passed · handoff written", done == 7


# ---- Assembly ------------------------------------------------------------------------------------

ACTS = (_hydrate, _vfx, _lit)


def _act(i, f, box, t, data, glyphs, defs):
    ink = Ink()
    draw = ACTS[i]
    if i == 0:
        value, label, ok = draw(ink, f, box, t, data)
    elif i == 1:
        value, label, ok = draw(ink, f, box, t, defs)
    else:
        value, label, ok = draw(ink, f, box, t, glyphs)
    return ink, value, label, ok


def _frame(index, t, data, glyphs, defs):
    act, f = divmod(index, FRAMES_PER_ACT)
    ink, value, label, ok = _act(act, f, DRAW, t, data, glyphs, defs)
    tag, heads = CAPTIONS[act]
    stage = f // 4
    parts = [ink.svg()]
    parts.append(glyphs.text(f"{tag} · 0{stage + 1}", "meslo-regular", 13, TEXT_X, 70, t["label"]))
    parts.append(glyphs.text(heads[stage], "meslo-bold", 26, TEXT_X, 112, t["text"]))
    parts.append(glyphs.text(value, "meslo-regular", 34, TEXT_X, 236, t["phosphor"] if ok else t["text"]))
    parts.append(glyphs.text(label, "meslo-regular", 13, TEXT_X, 262, t["label"]))
    last = " last" if index == 3 * FRAMES_PER_ACT - 1 else ""
    return f'<g class="f{last}" style="animation-delay:{index * STEP_S:.2f}s">{"".join(parts)}</g>'


def _still(t, data, glyphs, defs):
    """Reduced motion and the default: each act's final frame, side by side."""
    third = W / 3
    parts = ['<g class="still">']
    for act in range(3):
        x0 = act * third
        box = (x0 + 24, BAR + 40, x0 + third - 24, H - 52)
        ink, value, _label, ok = _act(act, FRAMES_PER_ACT - 1, box, t, data, glyphs, defs)
        tag, heads = CAPTIONS[act]
        parts.append('<g class="still-panel">')
        parts.append(ink.svg())
        parts.append(glyphs.text(tag, "meslo-regular", 13, x0 + TEXT_X, BAR + 26, t["label"]))
        parts.append(glyphs.text(f"{heads[-1]} · {value}", "meslo-bold", 15, x0 + TEXT_X, H - 22, t["phosphor"] if ok else t["text"]))
        parts.append("</g>")
        if act:
            parts.append(f'<line x1="{x0:.0f}" y1="{BAR}" x2="{x0:.0f}" y2="{H}" stroke="{t["border"]}" stroke-width="1"/>')
    parts.append("</g>")
    return "".join(parts)


def _style():
    cycle = 3 * FRAMES_PER_ACT * STEP_S + HOLD_S
    one = STEP_S / cycle * 100
    last = (STEP_S + HOLD_S) / cycle * 100
    return (
        "<style>.f{opacity:0}"
        "@media (prefers-reduced-motion: no-preference){"
        ".still{display:none}"
        f".f{{animation:sc {cycle:g}s step-end infinite}}"
        ".f.last{animation-name:sclast}"
        f"@keyframes sc{{0%{{opacity:1}}{one:.3f}%{{opacity:0}}100%{{opacity:0}}}}"
        f"@keyframes sclast{{0%{{opacity:1}}{last:.3f}%{{opacity:0}}100%{{opacity:0}}}}"
        "}</style>"
    )


def render(theme="night"):
    t = tokens.THEMES[theme]
    p = crt.Chrome(theme)
    data = json.loads((ROOT / "data" / "scene.json").read_text(encoding="utf-8"))
    glyphs, defs = Labels(), {}
    body = [_frame(i, t, data, glyphs, defs) for i in range(3 * FRAMES_PER_ACT)]
    still = _still(t, data, glyphs, defs)
    head = "".join(
        (
            crt.svg_open(W, H),
            _style(),
            p.DEFS,
            p.screen(W, H),
            p.plot_grid(W, H, BAR),
            f'<rect x="0" y="0" width="{W}" height="{BAR}" fill="{t["inverse_bg"]}"/>',
            glyphs.text("~/scene · three acts", "meslo-regular", 14, TEXT_X, 19, t["inverse_ink"]),
            glyphs.text("hydrate · agentvfx · LitFamily", "meslo-regular", 12, W - TEXT_X - glyphs.width("hydrate · agentvfx · LitFamily", "meslo-regular", 12), 19, t["inverse_ink"]),
        )
    )
    return head + "".join(body) + still + f"<defs>{glyphs.defs()}{_tile_defs(t)}{''.join(f'<g id=\"{k}\">{v}</g>' for k, v in defs.items())}</defs></svg>"


def write(out_dir=None):
    out_dir = Path(out_dir) if out_dir else ROOT / "assets"
    paths = []
    for theme in ("day", "night"):
        path = out_dir / f"scene-{theme}.svg"
        path.write_text(render(theme), encoding="utf-8")
        paths.append(path)
    return paths


def main():
    for path in write():
        print(f"{path.name} {path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
