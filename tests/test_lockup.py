"""Lockup text must become paths without touching the rest of the SVG."""

import re
import struct
import subprocess
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BRAND = Path(
    "/Users/woojin/Desktop/02_Areas/09_Me/Branding/output/woojin-go-brand-v1-r7-r6-ci/vector"
)
PAIRS = (
    ("woojin-go-lockup-reverse.svg", "lockup-dark.svg"),
    ("woojin-go-lockup-horizontal.svg", "lockup-light.svg"),
)
DARK_BACKGROUND = '<rect width="1500" height="360" fill="#26282D"/>\n'
EVIDENCE = ROOT.parent / ".litclaude" / "evidence" / "profile-readme"
PLAYWRIGHT = "/Users/woojin/.nvm/versions/node/v22.22.0/lib/node_modules/playwright"


def _viewbox(svg):
    return re.search(r'viewBox="[^"]+"', svg).group(0)


def _mask(svg):
    return re.search(r"<mask\b.*?</mask>", svg, re.DOTALL).group(0)


def _fills(svg):
    return re.findall(r'fill="[^"]*"', svg)


def _symbols(svg):
    return re.findall(r"<symbol\b.*?</symbol>", svg, re.DOTALL)


def test_text_replaced_everything_else_kept():
    import scripts.convert_lockup as convert_lockup

    convert_lockup.convert_all()
    for src_name, out_name in PAIRS:
        src = (BRAND / src_name).read_text(encoding="utf-8")
        out = (ROOT / "assets" / out_name).read_text(encoding="utf-8")
        assert "<text" not in out.lower()
        src_cmp = src
        if out_name == "lockup-dark.svg":
            assert DARK_BACKGROUND in src_cmp
            assert DARK_BACKGROUND not in out
            src_cmp = src_cmp.replace(DARK_BACKGROUND, "", 1)
        else:
            assert 'fill="transparent"' in out
        assert _viewbox(src_cmp) == _viewbox(out)
        assert _mask(src_cmp) == _mask(out)
        assert _symbols(src_cmp) == _symbols(out)
        assert _fills(src_cmp) == _fills(out)
        src_rest = re.sub(r"<text\b[^>]*>.*?</text>", "", src_cmp, count=1, flags=re.DOTALL)
        out_rest = re.sub(r'<g id="wordmark"[^>]*>.*?</g>', "", out, count=1, flags=re.DOTALL)
        assert src_rest == out_rest


def _png(path):
    data = Path(path).read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    width = height = color_type = None
    idat = b""
    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        kind = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk[:10])
            assert bit_depth == 8
        elif kind == b"IDAT":
            idat += chunk
        elif kind == b"IEND":
            break
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[color_type]
    raw = zlib.decompress(idat)
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
        out = bytearray(stride)
        for i, value in enumerate(row):
            left = out[i - channels] if i >= channels else 0
            up = prev[i]
            ul = prev[i - channels] if i >= channels else 0
            if filt == 0:
                out[i] = value
            elif filt == 1:
                out[i] = (value + left) & 255
            elif filt == 2:
                out[i] = (value + up) & 255
            elif filt == 3:
                out[i] = (value + ((left + up) // 2)) & 255
            elif filt == 4:
                out[i] = (value + paeth(left, up, ul)) & 255
            else:
                raise AssertionError(f"bad png filter {filt}")
        rows.append(out)
        prev = out
    return width, height, channels, rows


def _shoot(svg_text, png_path, width, height, background="#fff"):
    html_path = png_path.with_suffix(".html")
    html_path.write_text(
        "<!doctype html><meta charset=\"utf-8\">"
        f"<style>html,body{{margin:0;background:{background}}}</style>"
        f"<body>{svg_text}</body>",
        encoding="utf-8",
    )
    script = f"""
const {{ chromium }} = require({PLAYWRIGHT!r});
(async () => {{
  const browser = await chromium.launch({{ channel: "chrome" }});
  const page = await browser.newPage({{
    viewport: {{ width: {width}, height: {height} }},
    deviceScaleFactor: 1,
  }});
  await page.goto({html_path.as_uri()!r});
  await page.evaluate(() => document.fonts.ready);
  const ready = await page.evaluate(() => document.fonts.check('900 112px "Monument Extended"'));
  if (!ready) throw new Error("Monument Extended 900 is not available to Chrome");
  await page.screenshot({{ path: {str(png_path)!r} }});
  await browser.close();
}})();
"""
    subprocess.run(["node", "-e", script], check=True)


def _diff_ratio(left, right):
    lw, lh, lc, lrows = _png(left)
    rw, rh, rc, rrows = _png(right)
    assert (lw, lh, lc) == (rw, rh, rc)
    changed = 0
    total = lw * lh
    for y in range(lh):
        a, b = lrows[y], rrows[y]
        for x in range(lw):
            i = x * lc
            if max(abs(a[i + c] - b[i + c]) for c in range(min(3, lc))) > 24:
                changed += 1
    return changed / total


def test_raster_matches_source_within_one_percent(tmp_path):
    import scripts.convert_lockup as convert_lockup

    convert_lockup.convert_all()
    for src_name, out_name in PAIRS:
        src = (BRAND / src_name).read_text(encoding="utf-8")
        out = (ROOT / "assets" / out_name).read_text(encoding="utf-8")
        width = int(re.search(r'\bwidth="(\d+)"', src).group(1))
        height = int(re.search(r'\bheight="(\d+)"', src).group(1))
        src_png = tmp_path / f"{out_name}-src.png"
        out_png = tmp_path / f"{out_name}-out.png"
        background = "#26282D" if out_name == "lockup-dark.svg" else "#fff"
        _shoot(src, src_png, width, height, background)
        _shoot(out, out_png, width, height, background)
        ratio = _diff_ratio(src_png, out_png)
        assert ratio < 0.01, f"{out_name} pixel diff {ratio:.4%}"
