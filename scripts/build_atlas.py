"""Build a deterministic glyph atlas from local fonts. Local use only."""

import json
import re
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONT_DIR = Path.home() / "Library" / "Fonts"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "atlas" / "glyphs.json"
EXTRA = Path(__file__).with_name("extra_chars.txt")

BOX = "─│┌┐└┘├┤┬┴┼═║╔╗╚╝"
SYMBOLS = "●○▸▶█░▒▓★·⟷→✓"

# Primary file, then the plan's file fallback, then fonts that can fill holes.
FACES = (
    ("meslo-regular", "MesloLGS NF Regular.ttf", "MesloLGSNerdFontMono-Regular.ttf", ("Pretendard-Regular.otf",)),
    ("meslo-bold", "MesloLGS NF Bold.ttf", "MesloLGSNerdFontMono-Bold.ttf", ("Pretendard-Bold.otf",)),
    ("pretendard-regular", "Pretendard-Regular.otf", None, ("MesloLGS NF Regular.ttf", "MesloLGSNerdFontMono-Regular.ttf")),
    ("pretendard-semibold", "Pretendard-SemiBold.otf", None, ("MesloLGS NF Regular.ttf", "MesloLGSNerdFontMono-Regular.ttf")),
    ("pretendard-bold", "Pretendard-Bold.otf", None, ("MesloLGS NF Bold.ttf", "MesloLGSNerdFontMono-Bold.ttf")),
)

_NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")


def required_chars():
    chars = [chr(code) for code in range(32, 127)]
    chars.extend(BOX)
    chars.extend(SYMBOLS)
    if EXTRA.exists():
        for line in EXTRA.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0]
            chars.extend(ch for ch in line if not ch.isspace())
    seen = set()
    ordered = []
    for ch in chars:
        if ch not in seen:
            seen.add(ch)
            ordered.append(ch)
    return ordered


def resolve_font(primary, fallback):
    primary_path = FONT_DIR / primary
    if primary_path.is_file():
        print(f"font file: {primary_path}", flush=True)
        return primary_path
    if fallback:
        fallback_path = FONT_DIR / fallback
        if fallback_path.is_file():
            print(f"font file: {fallback_path} (fallback; {primary} missing)", flush=True)
            return fallback_path
        raise SystemExit(f"missing font {primary} and fallback {fallback}")
    raise SystemExit(f"missing font {primary}; no fallback named")


def quantize_path(commands):
    if not commands:
        return ""

    def repl(match):
        value = round(float(match.group(0)), 2)
        text = f"{value:.2f}".rstrip("0").rstrip(".")
        return "0" if text in ("", "-0") else text

    return _NUMBER.sub(repl, commands)


def draw_glyph(font, ch):
    cmap = font.getBestCmap() or {}
    name = cmap.get(ord(ch))
    if not name or name == ".notdef":
        return None
    glyphset = font.getGlyphSet()
    scale = 1000 / font["head"].unitsPerEm
    pen = SVGPathPen(glyphset)
    glyphset[name].draw(TransformPen(pen, (scale, 0, 0, -scale, 0, 0)))
    path = quantize_path(pen.getCommands())
    advance = round(glyphset[name].width * scale, 3)
    if ch != " " and not path.strip():
        return None
    return {"advance": advance, "d": path}


def load_font(path, cache):
    key = str(path)
    if key not in cache:
        cache[key] = TTFont(key)
    return cache[key]


def build(out_path=OUT):
    chars = required_chars()
    cache = {}
    faces = {}
    for face_id, primary, fallback, fillers in FACES:
        chosen = resolve_font(primary, fallback)
        chain = [chosen]
        if fallback and chosen.name != fallback:
            other = FONT_DIR / fallback
            if other.is_file():
                chain.append(other)
        for name in fillers:
            path = FONT_DIR / name
            if not path.is_file():
                raise SystemExit(f"missing fill font {name}; no fallback named")
            chain.append(path)
        glyphs = {}
        borrowed = {}
        for ch in chars:
            drawn = None
            used = None
            for path in chain:
                drawn = draw_glyph(load_font(path, cache), ch)
                if drawn is not None:
                    used = path
                    break
            if drawn is None:
                raise SystemExit(f"{face_id} has no glyph for {ch!r} (U+{ord(ch):04X})")
            glyphs[ch] = drawn
            if used != chosen:
                borrowed.setdefault(used.name, 0)
                borrowed[used.name] += 1
        for name, count in sorted(borrowed.items()):
            print(f"glyph fill {face_id}: {count} from {name}", flush=True)
        faces[face_id] = {"font": chosen.name, "glyphs": glyphs}
    payload = {"faces": faces, "units_per_em": 1000}
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    return out_path


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    build(target)


if __name__ == "__main__":
    main()
