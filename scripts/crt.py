"""Shared CRT chrome. Standard library only."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgtext

BG = "#05070d"
GRID = "#13203a"
TEXT = "#c9d6e8"
LAB = "#39ff88"
WORK = "#3da9ff"
WARN = "#ffb000"
DIM = "#8ea3bb"

# 5x7, rows of 5 bits. Uppercase, slash, hyphen.
_GLYPH = {
    "A": "01110,10001,10001,11111,10001,10001,10001",
    "B": "11110,10001,10001,11110,10001,10001,11110",
    "C": "01111,10000,10000,10000,10000,10000,01111",
    "D": "11110,10001,10001,10001,10001,10001,11110",
    "E": "11111,10000,10000,11110,10000,10000,11111",
    "F": "11111,10000,10000,11110,10000,10000,10000",
    "G": "01111,10000,10000,10111,10001,10001,01110",
    "H": "10001,10001,10001,11111,10001,10001,10001",
    "I": "11111,00100,00100,00100,00100,00100,11111",
    "J": "00111,00010,00010,00010,10010,10010,01100",
    "K": "10001,10010,10100,11000,10100,10010,10001",
    "L": "10000,10000,10000,10000,10000,10000,11111",
    "M": "10001,11011,10101,10101,10001,10001,10001",
    "N": "10001,11001,10101,10011,10001,10001,10001",
    "O": "01110,10001,10001,10001,10001,10001,01110",
    "P": "11110,10001,10001,11110,10000,10000,10000",
    "Q": "01110,10001,10001,10001,10101,10010,01101",
    "R": "11110,10001,10001,11110,10100,10010,10001",
    "S": "01111,10000,10000,01110,00001,00001,11110",
    "T": "11111,00100,00100,00100,00100,00100,00100",
    "U": "10001,10001,10001,10001,10001,10001,01110",
    "V": "10001,10001,10001,10001,10001,01010,00100",
    "W": "10001,10001,10001,10101,10101,10101,01010",
    "X": "10001,10001,01010,00100,01010,10001,10001",
    "Y": "10001,10001,01010,00100,00100,00100,00100",
    "Z": "11111,00001,00010,00100,01000,10000,11111",
    "/": "00001,00001,00010,00100,01000,10000,10000",
    "-": "00000,00000,00000,11111,00000,00000,00000",
    "0": "01110,10001,10011,10101,11001,10001,01110",
    "1": "00100,01100,00100,00100,00100,00100,01110",
    "2": "01110,10001,00001,00010,00100,01000,11111",
    "3": "11110,00001,00001,01110,00001,00001,11110",
    "4": "00010,00110,01010,10010,11111,00010,00010",
    "5": "11111,10000,10000,11110,00001,00001,11110",
    "6": "00110,01000,10000,11110,10001,10001,01110",
    "7": "11111,00001,00010,00100,01000,01000,01000",
    "8": "01110,10001,10001,01110,10001,10001,01110",
    "9": "01110,10001,10001,01111,00001,00010,01100",
}

DEFS = """<defs>
<pattern id="scan" width="3" height="3" patternUnits="userSpaceOnUse">
  <rect width="3" height="2" fill="#10192c"/>
  <rect y="2" width="3" height="1" fill="#000000" opacity="0.22"/>
</pattern>
<pattern id="dither" width="4" height="4" patternUnits="userSpaceOnUse">
  <rect width="1" height="1" fill="#c9d6e8" opacity="0.09"/>
  <rect x="2" y="2" width="1" height="1" fill="#c9d6e8" opacity="0.06"/>
</pattern>
<radialGradient id="vig" cx="50%" cy="42%" r="68%">
  <stop offset="58%" stop-color="#000000" stop-opacity="0"/>
  <stop offset="100%" stop-color="#000000" stop-opacity="0.62"/>
</radialGradient>
<filter id="bloom" x="-12%" y="-50%" width="124%" height="200%">
  <feGaussianBlur in="SourceGraphic" stdDeviation="2.4" result="blur"/>
  <feColorMatrix in="blur" type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.85 0" result="glow"/>
  <feMerge>
    <feMergeNode in="glow"/>
    <feMergeNode in="SourceGraphic"/>
  </feMerge>
</filter>
</defs>"""


def svg_open(width, height):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )


def text(value, face, size, x, y, fill):
    return svgtext.render(value, face, size, x, y, fill, 0)


def width(value, face, size):
    return svgtext.text_width(value, face, size, 0)


def screen(width, height):
    return (
        f'<rect width="{width}" height="{height}" fill="{BG}"/>'
        f'<rect width="{width}" height="{height}" fill="url(#scan)"/>'
        f'<rect width="{width}" height="{height}" fill="url(#dither)"/>'
        f'<rect width="{width}" height="{height}" fill="url(#vig)"/>'
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" fill="none" '
        f'stroke="{GRID}" stroke-width="1"/>'
    )


def ticks(width, height, color):
    s = 14
    marks = []
    corners = ((1, 1, 1, 1), (width - 1, 1, -1, 1), (1, height - 1, 1, -1), (width - 1, height - 1, -1, -1))
    for x, y, dx, dy in corners:
        marks.append(
            f'<path d="M{x + dx * s} {y} H{x} V{y + dy * s}" fill="none" stroke="{color}" stroke-width="1"/>'
        )
        marks.append(
            f'<path d="M{x + dx * 3} {y + dy * 6} H{x + dx * 9} M{x + dx * 6} {y + dy * 3} V{y + dy * 9}" '
            f'fill="none" stroke="{color}" stroke-width="1"/>'
        )
    return "".join(marks)


def coords(height, x=6):
    bits = []
    y = 46
    n = 0
    while y < height - 18 and n < 8:
        bits.append(text(f"{n:02d}", "meslo-regular", 9, x, y, DIM))
        y += 36
        n += 1
    return "".join(bits)


def blocks(labels, accent, y=8, size=11):
    x = 18
    bits = []
    for label in labels:
        tw = width(label, "meslo-regular", size) + 14
        bits.append(f'<rect x="{x}" y="{y}" width="{tw:.1f}" height="16" fill="none" stroke="{GRID}"/>')
        bits.append(f'<rect x="{x}" y="{y}" width="3" height="16" fill="{accent}"/>')
        bits.append(text(label, "meslo-regular", size, x + 7, y + 12, TEXT))
        x += tw + 6
    return "".join(bits)


def dot_text(value, x, y, cell, fill, gap=1):
    step = cell + gap
    cursor = x
    rects = []
    for char in value.upper():
        if char == " ":
            cursor += step * 3
            continue
        rows = _GLYPH.get(char)
        if not rows:
            cursor += step * 6
            continue
        for row_i, row in enumerate(rows.split(",")):
            for col, bit in enumerate(row):
                if bit == "1":
                    rects.append(
                        f'<rect x="{cursor + col * step:.1f}" y="{y + row_i * step:.1f}" '
                        f'width="{cell}" height="{cell}" fill="{fill}"/>'
                    )
        cursor += step * 5 + cell
    return "".join(rects)


def dot_width(value, cell, gap=1):
    step = cell + gap
    total = 0
    for char in value.upper():
        total += step * 3 if char == " " else step * 5 + cell
    return total


def cage(cx, cy, scale, color):
    """Pentagonal dodecahedron: 20 vertices, 30 edges, orthographic."""
    phi = (1 + math.sqrt(5)) / 2
    inv = 1 / phi
    verts = [(x, y, z) for x in (-1.0, 1.0) for y in (-1.0, 1.0) for z in (-1.0, 1.0)]
    for sign in (-1.0, 1.0):
        for other in (-1.0, 1.0):
            verts.append((0.0, sign * inv, other * phi))
            verts.append((sign * inv, other * phi, 0.0))
            verts.append((other * phi, 0.0, sign * inv))
    edge2 = min(
        sum((verts[i][k] - verts[j][k]) ** 2 for k in range(3))
        for i in range(20)
        for j in range(i + 1, 20)
    )
    edges = [
        (i, j)
        for i in range(20)
        for j in range(i + 1, 20)
        if abs(sum((verts[i][k] - verts[j][k]) ** 2 for k in range(3)) - edge2) < 1e-6
    ]
    yaw, pitch = math.radians(25), math.radians(20)
    cyaw, syaw = math.cos(yaw), math.sin(yaw)
    cpitch, spitch = math.cos(pitch), math.sin(pitch)
    rotated = []
    for x, y, z in verts:
        x1 = x * cyaw + z * syaw
        z1 = -x * syaw + z * cyaw
        y2 = y * cpitch - z1 * spitch
        z2 = y * spitch + z1 * cpitch
        rotated.append((x1, y2, z2))
    pts = [(cx + x * scale, cy - y * scale) for x, y, _z in rotated]
    z_mid = sorted(p[2] for p in rotated)[10]
    front = max(range(20), key=lambda i: rotated[i][2])
    parts = []
    for i, j in edges:
        back = (rotated[i][2] + rotated[j][2]) / 2 < z_mid
        x0, y0 = pts[i]
        x1, y1 = pts[j]
        parts.append(
            f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
            f'stroke="{color}" stroke-width="1.1" opacity="{"0.35" if back else "1"}"/>'
        )
    for i, (x, y) in enumerate(pts):
        dim = rotated[i][2] < z_mid
        mark = ' class="cagedot"' if i == front else ""
        parts.append(
            f'<circle{mark} cx="{x:.1f}" cy="{y:.1f}" r="1.7" fill="{color}" opacity="{"0.4" if dim else "1"}"/>'
        )
    return "".join(parts)


def curve(x, y, w, h, color):
    x0, y0 = x, y + h
    x1, y1 = x + w, y
    pts = []
    for i in range(9):
        t = i / 8
        px = x + t * w
        py = y + h - (t ** 1.35) * h * 0.82
        pts.append(f"{px:.1f},{py:.1f}")
    ticks = []
    for i in range(5):
        tx = x + i * w / 4
        ticks.append(f'<path d="M{tx:.1f} {y0} V{y0 + 4}" stroke="{color}" stroke-width="1"/>')
    for i in range(4):
        ty = y + h - i * h / 3
        ticks.append(f'<path d="M{x} {ty:.1f} H{x - 4}" stroke="{color}" stroke-width="1"/>')
    return (
        f'<path d="M{x} {y} V{y0} H{x1}" fill="none" stroke="{color}" stroke-width="1"/>'
        + "".join(ticks)
        + f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="1.6"/>'
        + text("P / MPa", "meslo-regular", 10, x + 8, y + 12, color)
        + text("T / K", "meslo-regular", 10, x + w - 36, y0 - 6, color)
    )


def meter(x, y, w, color, filled=8, total=12):
    gap = 3
    cell = (w - gap * (total - 1)) / total
    bits = []
    for i in range(total):
        fill = color if i < filled else GRID
        bits.append(
            f'<rect x="{x + i * (cell + gap):.1f}" y="{y}" width="{cell:.1f}" height="8" fill="{fill}"/>'
        )
    return "".join(bits)
