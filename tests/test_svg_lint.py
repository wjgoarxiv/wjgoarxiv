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
    text = lint_svg(ASSETS / "hero.svg")
    assert "@keyframes" in text
    assert "prefers-reduced-motion" in text
    assert 'viewBox="0 0 1200 524"' in text


def test_hero_nameplate():
    hero = (ASSETS / "hero.svg").read_text(encoding="utf-8")
    lockup = (ASSETS / "lockup-dark.svg").read_text(encoding="utf-8")
    wordmark = re.search(r'<g id="wordmark" fill="#F3EFE7">.*?</g>', lockup).group(0)
    symbol = re.search(r'<g id="reverse-symbol"[^>]*>.*?</g>', lockup).group(0)
    assert wordmark in hero
    assert symbol in hero
    plate = re.search(r'<svg id="nameplate"[^>]*>.*?</svg>', hero, re.DOTALL).group(0)
    assert "filter=" not in plate
    assert "url(#scan)" not in plate and "url(#dither)" not in plate and "url(#bloom)" not in plate
    assert 'fill="#F3EFE7"' in plate


def test_hero_reduced_motion_shows_final_frame():
    import subprocess

    evidence = ROOT.parent / ".litclaude" / "evidence" / "profile-readme"
    out = evidence / "task-8-hero-rm.png"
    hero = (ASSETS / "hero.svg").read_text(encoding="utf-8")
    html = evidence / "task-8-hero-rm.html"
    html.write_text(
        "<!doctype html><meta charset='utf-8'><style>html,body{margin:0;background:#05070d}</style>"
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
    # Final frame has the name line and the researcher line; mid-boot does not.
    # Sample two text bands: name (~y 250) and tagline (~y 280) should not be empty navy.
    import struct
    import zlib

    data = out.read_bytes()
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

    def ink(y0, y1):
        count = 0
        for y in range(y0, y1):
            row = rows[y]
            for x in range(40, 700):
                i = x * channels
                if row[i] > 40 or row[i + 1] > 80 or row[i + 2] > 40:
                    count += 1
        return count

    # Name line and tagline bands in the 1200x524 hero. Mid-boot leaves these empty.
    assert ink(230, 270) > 200, "name line missing in reduced motion"
    assert ink(270, 310) > 200, "tagline missing in reduced motion"


def test_panels_share_viewbox():
    lab = lint_svg(ASSETS / "lab.svg")
    workshop = lint_svg(ASSETS / "workshop.svg")
    lab_box = re.search(r'viewBox="([^"]+)"', lab).group(1)
    shop_box = re.search(r'viewBox="([^"]+)"', workshop).group(1)
    assert lab_box == shop_box
    assert "#39ff88" in lab
    assert "#3da9ff" in workshop
    assert "prefers-reduced-motion" in lab and "prefers-reduced-motion" in workshop
