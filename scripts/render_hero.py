"""CRT boot hero."""

from pathlib import Path

import crt

OUT = Path(__file__).resolve().parents[1] / "assets" / "hero.svg"
LOCKUP = Path(__file__).resolve().parents[1] / "assets" / "lockup-dark.svg"
W, SCREEN, BEZEL = 1200, 420, 104
H = SCREEN + BEZEL

STYLE = """<style>
.line { opacity: 1; clip-path: none; }
.cursor { opacity: 1; }
.cagedot { opacity: 1; }
.sweep { opacity: 0; }
.hdd { opacity: 0.28; }
@media (prefers-reduced-motion: no-preference) {
  .line { opacity: 0; animation: reveal 0.4s linear forwards; }
  .l1 { animation-delay: 0s; }
  .l2 { animation-delay: 0.65s; }
  .l3 { animation-delay: 1.3s; }
  .l4 { animation-delay: 1.95s; }
  .l5 { animation-delay: 2.6s; }
  .l6 { animation-delay: 3.25s; }
  .cursor { animation: blink 1s steps(2, end) infinite; }
  .cagedot { animation: vertex 6s steps(1, end) infinite; }
  .sweep { opacity: 0.35; animation: sweep 6s linear infinite; }
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
@keyframes vertex {
  0%, 70% { opacity: 1; }
  71%, 100% { opacity: 0.35; }
}
@keyframes sweep {
  from { transform: translateY(70px); }
  to { transform: translateY(360px); }
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
  .cagedot { animation: none !important; opacity: 1 !important; }
  .sweep { animation: none !important; opacity: 0 !important; }
  .hdd { animation: none !important; opacity: 0.28 !important; }
}
</style>"""

LINES = (
    ("l1", "[ OK ] mounting /lab/hydrate", crt.LAB),
    ("l2", "[ OK ] loading litfamily.agents", crt.WORK),
    ("l3", "[ OK ] link: ovito-mcp · pymol-mcp · claviscage", crt.TEXT),
    ("l4", "wjgo@lab:~$ whoami", crt.TEXT),
    ("l6", "Researcher · agent tool builder", crt.DIM),
)


def _name(x, y, size):
    latin = "Woojin Go, Ph.D. · "
    return crt.text(latin, "meslo-regular", size, x, y, crt.TEXT) + crt.text(
        "고우진", "pretendard-regular", size, x + crt.width(latin, "meslo-regular", size), y, crt.TEXT
    )


def _nameplate():
    raw = LOCKUP.read_text(encoding="utf-8")
    inner = raw.split(">", 1)[1].rsplit("</svg>", 1)[0]
    # Uniform scale only: 300/1500 = 72/360 = 0.2. Clearspace stays inside the lockup.
    return (
        f'<svg id="nameplate" x="28" y="{SCREEN + 16}" width="300" height="72" '
        f'viewBox="0 0 1500 360">{inner}</svg>'
    )


def render():
    size = 18
    x = 28
    first = 118
    leading = 30
    parts = [
        crt.svg_open(W, H),
        STYLE,
        crt.DEFS,
        '<defs><linearGradient id="bezel" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#16181c"/><stop offset="1" stop-color="#1d2026"/>'
        '</linearGradient><clipPath id="screen"><rect width="1200" height="420"/></clipPath></defs>',
        '<g clip-path="url(#screen)">',
        crt.screen(W, SCREEN),
        crt.ticks(W, SCREEN, crt.LAB),
        crt.coords(SCREEN),
        crt.blocks(("TTY1", "PID 0x2A", "1200x420", "UTF-8"), crt.LAB),
        f'<line x1="16" y1="30" x2="{W - 16}" y2="30" stroke="{crt.GRID}" stroke-width="1"/>',
        f'<g filter="url(#bloom)">{crt.dot_text("WJGO // RESEARCH TERMINAL", 28, 40, 3, crt.LAB)}</g>',
        f'<line x1="16" y1="78" x2="760" y2="78" stroke="{crt.GRID}" stroke-width="1"/>',
        '<g filter="url(#bloom)">',
    ]
    row = 0
    for cls, label, fill in LINES:
        y = first + row * leading
        parts.append(f'<g class="line {cls}">{crt.text(label, "meslo-regular", size, x, y, fill)}</g>')
        row += 1
        if cls == "l4":
            parts.append(f'<g class="line l5">{_name(x, y + leading, size)}</g>')
            row += 1
    parts.append("</g>")
    cursor_y = first + row * leading
    parts.append(f'<rect class="cursor" x="{x}" y="{cursor_y - 16}" width="11" height="18" fill="{crt.LAB}"/>')
    parts.append(f'<g filter="url(#bloom)">{crt.cage(980, 188, 36, crt.LAB)}</g>')
    parts.append(crt.text("5^12  CAGE", "meslo-regular", 12, 930, 318, crt.LAB))
    parts.append(f'<line x1="16" y1="372" x2="{W - 16}" y2="372" stroke="{crt.GRID}" stroke-width="1"/>')
    parts.append(crt.text("MEM", "meslo-regular", 13, 28, 396, crt.TEXT))
    parts.append(crt.meter(64, 386, 92, crt.LAB, 5, 7))
    parts.append(crt.text("71%   SYNC ● OK   LOC SEOUL·KR   MODE: HYDRATE/AGENTS", "meslo-regular", 13, 168, 396, crt.TEXT))
    parts.append(
        f'<rect class="sweep" x="860" y="0" width="280" height="3" fill="{crt.LAB}" opacity="0.35"/>'
    )
    parts.append("</g>")
    parts.append(
        f'<rect x="0" y="{SCREEN}" width="{W}" height="{BEZEL}" fill="url(#bezel)"/>'
        f'<line x1="0" y1="{SCREEN}" x2="{W}" y2="{SCREEN}" stroke="#2a2e36" stroke-width="1"/>'
        f'<line x1="0" y1="{H - 1}" x2="{W}" y2="{H - 1}" stroke="#0a0c10" stroke-width="1"/>'
    )
    parts.append(_nameplate())
    parts.append(f'<circle cx="760" cy="{SCREEN + 36}" r="4" fill="{crt.LAB}"/>')
    parts.append(crt.text("PWR", "meslo-regular", 13, 772, SCREEN + 40, crt.DIM))
    parts.append(
        f'<circle cx="860" cy="{SCREEN + 36}" r="4" fill="none" stroke="{crt.DIM}" stroke-width="1.2"/>'
        f'<circle class="hdd" cx="860" cy="{SCREEN + 36}" r="2.4" fill="{crt.DIM}"/>'
    )
    parts.append(crt.text("HDD", "meslo-regular", 13, 872, SCREEN + 40, crt.DIM))
    parts.append(crt.text("MODEL WJ-2023", "meslo-regular", 11, 760, SCREEN + 68, "#6d7580"))
    for i in range(7):
        parts.append(
            f'<rect x="{1040 + i * 10}" y="{SCREEN + 34}" width="3" height="22" fill="#101216"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


def main():
    OUT.write_text(render(), encoding="utf-8")


if __name__ == "__main__":
    main()
