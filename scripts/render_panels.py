"""LAB and WORKSHOP CRT panels."""

from pathlib import Path

import crt
import tokens

ROOT = Path(__file__).resolve().parents[1]
W, H = 430, 360

STYLE = """<style>
.dot { animation: pulse 2.8s ease-in-out infinite; }
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.28; }
}
@media (prefers-reduced-motion: reduce) {
  .dot { animation: none; opacity: 1; }
}
</style>"""


def _chrome(p, accent, title, cell):
    return "".join(
        (
            crt.svg_open(W, H),
            STYLE,
            p.DEFS,
            p.screen(W, H),
            crt.ticks(W, H, accent),
            p.blocks(("TTY1", "PID 0x2A", "UTF-8"), accent),
            f'<line x1="14" y1="30" x2="{W - 14}" y2="30" stroke="{p.GRID}" stroke-width="1"/>',
            p.bloom(crt.dot_text(title, 18, 38, cell, accent)),
            f'<circle class="dot" cx="{W - 18}" cy="16" r="3.5" fill="{accent}"/>',
        )
    )


def render_lab(theme="night"):
    p = crt.Chrome(theme)
    rows = (
        "kinetic & thermodynamic inhibitors",
        "flow assurance",
        "CO2 hydrate / CCS",
        "MD & clathrate cage analysis",
        "process simulation (HYSYS / Multiflash)",
    )
    parts = [_chrome(p, p.LAB, "LAB", 4)]
    y = 104
    for label in rows:
        parts.append(crt.text(label, "meslo-regular", 16, 16, y, p.TEXT))
        y += 20
    plot_x, plot_y, plot_w, plot_h = 22, 214, 188, 68
    parts.append(crt.curve(plot_x, plot_y, plot_w, plot_h, p.LAB))
    caption = "EQ READOUT"
    parts.append(
        crt.text(
            caption,
            "meslo-regular",
            11,
            plot_x + plot_w - crt.width(caption, "meslo-regular", 11) - 2,
            plot_y - 2,
            p.DIM,
        )
    )
    parts.append(f'<line x1="14" y1="318" x2="{W - 14}" y2="318" stroke="{p.GRID}" stroke-width="1"/>')
    latin = "Ph.D. UNIST 2023 · "
    parts.append(crt.text(latin, "meslo-regular", 13, 16, 340, p.DIM))
    parts.append(
        crt.text("가스 하이드레이트", "pretendard-regular", 13, 16 + crt.width(latin, "meslo-regular", 13), 340, p.DIM)
    )
    parts.append("</svg>")
    return "".join(parts)


def render_workshop(theme="night"):
    p = crt.Chrome(theme)
    parts = [_chrome(p, p.WORK, "WORKSHOP", 3)]
    groups = (
        ("litfamily", "[RUN]", ("litgravity · litclaude · litcodex", "litopencode · lithermes · litgrok"), 9),
        ("science/", "[OK]", ("ovito-mcp · pymol-mcp · claviscage",), 8),
        ("env/", "[OK]", ("pretty-terminal · tmux · nvim",), 6),
    )
    y = 100
    for name, flag, lines, filled in groups:
        parts.append(crt.text(name, "meslo-bold", 15, 18, y, p.WORK))
        parts.append(crt.text(flag, "meslo-regular", 13, W - 62, y, p.WORK))
        y += 20
        for line in lines:
            parts.append(crt.text(line, "meslo-regular", 14, 28, y, p.TEXT))
            y += 20
        parts.append(p.meter(28, y - 4, 180, p.WORK, filled))
        y += 22
    parts.append(f'<line x1="14" y1="318" x2="{W - 14}" y2="318" stroke="{p.GRID}" stroke-width="1"/>')
    parts.append(crt.text("LINK ● AGENTS    QUEUE 0", "meslo-regular", 13, 16, 340, p.DIM))
    parts.append("</svg>")
    return "".join(parts)


def main(argv=None):
    for theme in tokens.chosen(argv):
        lab = ROOT / "assets" / "lab.svg"
        shop = ROOT / "assets" / "workshop.svg"
        tokens.themed_path(lab, theme).write_text(render_lab(theme), encoding="utf-8")
        tokens.themed_path(shop, theme).write_text(render_workshop(theme), encoding="utf-8")
        tokens.retire_unthemed(lab)
        tokens.retire_unthemed(shop)


if __name__ == "__main__":
    main()
