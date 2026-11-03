"""Lint every shipped SVG. Hero and panels have extra rules."""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ASSETS = ROOT / "assets"
MAX_BYTES = 300 * 1024


def lint_svg(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    ET.fromstring(text)
    lowered = text.lower()
    assert "<text" not in lowered, path.name
    assert "<script" not in lowered, path.name
    assert "foreignobject" not in lowered, path.name
    urls = re.findall(r"https?://[^\s\"')<]+", text, re.I)
    external = [url for url in urls if "www.w3.org" not in url]
    assert not external, (path.name, external)
    assert not re.search(r"url\(\s*['\"]?https?:", text, re.I), path.name
    assert path.stat().st_size < MAX_BYTES, path.name
    return text


def test_cards_and_papers_are_small():
    for folder in ("cards", "papers"):
        files = sorted((ASSETS / folder).glob("*.svg"))
        assert files, folder
        for path in files:
            lint_svg(path)
            assert path.stat().st_size < 60 * 1024, path.name


def test_every_svg_under_assets():
    files = sorted(ASSETS.rglob("*.svg"))
    assert files, "no svgs to lint"
    for path in files:
        lint_svg(path)


def test_hero_motion():
    for name in ("hero-night.svg", "hero-day.svg"):
        text = lint_svg(ASSETS / name)
        assert "@keyframes" in text
        assert "prefers-reduced-motion" in text
        assert 'viewBox="0 0 1200 524"' in text


def _plate(hero):
    return re.search(r'<svg id="nameplate"[^>]*>.*?</svg>', hero, re.DOTALL).group(0)


def test_hero_nameplate():
    night = (ASSETS / "hero-night.svg").read_text(encoding="utf-8")
    day = (ASSETS / "hero-day.svg").read_text(encoding="utf-8")
    dark = (ASSETS / "lockup-dark.svg").read_text(encoding="utf-8")
    light = (ASSETS / "lockup-light.svg").read_text(encoding="utf-8")
    night_plate = _plate(night)
    day_plate = _plate(day)
    assert re.search(r'<g id="wordmark" fill="#F3EFE7">.*?</g>', dark).group(0) in night
    assert re.search(r'<g id="reverse-symbol"[^>]*>.*?</g>', dark).group(0) in night
    assert re.search(r'<g id="wordmark" fill="#26282D">.*?</g>', light).group(0) in day
    assert re.search(r'<g id="horizontal-symbol"[^>]*>.*?</g>', light).group(0) in day
    for plate, fill in ((night_plate, "#F3EFE7"), (day_plate, "#26282D")):
        assert "filter=" not in plate
        assert "url(#scan)" not in plate and "url(#dither)" not in plate and "url(#bloom)" not in plate
        assert f'fill="{fill}"' in plate
    assert 'fill="transparent"' not in day_plate
    assert 'width="1400"' not in day_plate


def _shot_reduced(hero_name, png_name, background):
    import subprocess

    evidence = ROOT.parent / ".litclaude" / "evidence" / "profile-readme"
    evidence.mkdir(parents=True, exist_ok=True)
    out = evidence / png_name
    hero = (ASSETS / hero_name).read_text(encoding="utf-8")
    html = evidence / f"{png_name}.html"
    html.write_text(
        f"<!doctype html><meta charset='utf-8'><style>html,body{{margin:0;background:{background}}}</style>"
        f"<body>{hero}</body>",
        encoding="utf-8",
    )
    script = f"""
const {{ chromium }} = require("/Users/woojin/.nvm/versions/node/v22.22.0/lib/node_modules/playwright");
(async () => {{
  const browser = await chromium.launch({{ channel: "chrome" }});
  const page = await browser.newPage({{
    viewport: {{ width: 1200, height: 524 }},
    deviceScaleFactor: 1,
    reducedMotion: "reduce",
  }});
  await page.goto({html.as_uri()!r});
  await page.waitForTimeout(200);
  await page.screenshot({{ path: {str(out)!r} }});
  await browser.close();
}})();
"""
    subprocess.run(["node", "-e", script], check=True)
    return out


def _png_rows(path):
    import struct
    import zlib

    data = Path(path).read_bytes()
    pos = 8
    width = height = color = None
    idat = b""
    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        kind = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color = struct.unpack(">IIBB", chunk[:10])
        elif kind == b"IDAT":
            idat += chunk
        elif kind == b"IEND":
            break
    raw = zlib.decompress(idat)
    channels = {2: 3, 6: 4}[color]
    stride = width * channels
    rows = []
    index = 0
    prev = bytearray(stride)

    def paeth(a, b, c):
        p = a + b - c
        pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
        if pa <= pb and pa <= pc:
            return a
        return b if pb <= pc else c

    for _ in range(height):
        filt = raw[index]
        index += 1
        row = bytearray(raw[index : index + stride])
        index += stride
        recon = bytearray(stride)
        for i, value in enumerate(row):
            left = recon[i - channels] if i >= channels else 0
            up = prev[i]
            ul = prev[i - channels] if i >= channels else 0
            if filt == 0:
                recon[i] = value
            elif filt == 1:
                recon[i] = (value + left) & 255
            elif filt == 2:
                recon[i] = (value + up) & 255
            elif filt == 3:
                recon[i] = (value + ((left + up) // 2)) & 255
            else:
                recon[i] = (value + paeth(left, up, ul)) & 255
        rows.append(recon)
        prev = recon
    return rows, channels


def test_hero_reduced_motion_shows_final_frame():
    shots = (
        ("hero-night.svg", "task-8-hero-rm-night.png", "#1a1b26", (26, 27, 38)),
        ("hero-day.svg", "task-8-hero-rm-day.png", "#e1e2e7", (225, 226, 231)),
    )
    for hero_name, png_name, background, bg in shots:
        out = _shot_reduced(hero_name, png_name, background)
        rows, channels = _png_rows(out)

        def ink(y0, y1, bg=bg, rows=rows, channels=channels):
            count = 0
            for y in range(y0, y1):
                row = rows[y]
                for x in range(40, 700):
                    i = x * channels
                    delta = abs(row[i] - bg[0]) + abs(row[i + 1] - bg[1]) + abs(row[i + 2] - bg[2])
                    if delta > 80:
                        count += 1
            return count

        # Glyphs sit above the baseline: name ~238, tagline ~268. Mid-boot leaves both empty.
        assert ink(218, 246) > 200, f"name line missing in {hero_name}"
        assert ink(248, 272) > 200, f"tagline missing in {hero_name}"


def test_panels_share_viewbox():
    sys.path.insert(0, str(ROOT))
    from scripts.tokens import THEMES

    for theme in ("night", "day"):
        lab = lint_svg(ASSETS / f"lab-{theme}.svg")
        workshop = lint_svg(ASSETS / f"workshop-{theme}.svg")
        lab_box = re.search(r'viewBox="([^"]+)"', lab).group(1)
        shop_box = re.search(r'viewBox="([^"]+)"', workshop).group(1)
        assert lab_box == shop_box
        assert THEMES[theme]["lab"] in lab
        assert THEMES[theme]["workshop"] in workshop
        assert "prefers-reduced-motion" in lab and "prefers-reduced-motion" in workshop
