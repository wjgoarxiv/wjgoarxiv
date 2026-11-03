"""Self-rendered shields. Values come from a fixture, not a third-party host."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BANNED = ("shields.io", "vercel", "demolab", "komarev", "wakatime", "capsule-render")
FIXTURE = ROOT / "tests" / "fixtures" / "live.json"


def _channel(value):
    value = value / 255
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def _luminance(hex_color):
    raw = hex_color.lstrip("#")
    red, green, blue = (int(raw[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def _contrast(left, right):
    hi, lo = sorted((_luminance(left), _luminance(right)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _height(svg):
    match = re.search(r'viewBox="0 0 [0-9.]+ ([0-9.]+)"', svg)
    return float(match.group(1))


def test_default_badge_height_is_16():
    from scripts.layout import load
    from scripts.render_badges import render_badge

    assert load()["badge_h"] == 16
    assert load("compact")["badge_h"] == 14
    assert load("tall")["badge_h"] == 20
    live = json.loads(FIXTURE.read_text(encoding="utf-8"))
    badge = json.loads((ROOT / "data" / "badges.json").read_text(encoding="utf-8"))[0]
    svg = render_badge(badge, live, "night")
    assert _height(svg) == 16
    assert "scale(0.009)" in svg


def test_brutalist_cell_frame_tab_and_rule():
    from scripts import tokens
    from scripts.render_badges import ROLE, render_badge

    live = json.loads(FIXTURE.read_text(encoding="utf-8"))
    badges = json.loads((ROOT / "data" / "badges.json").read_text(encoding="utf-8"))
    for badge in badges:
        for theme_name in ("night", "day"):
            theme = tokens.THEMES[theme_name]
            svg = render_badge(badge, live, theme_name)
            # one cell: value chip shares the sunken ground, no two-tone block
            chip = re.search(r'class="value"[^>]*fill="(#[0-9A-Fa-f]{6})"', svg).group(1)
            assert chip.lower() == theme["sunken"].lower()
            # hard 1px frame in the brand border colour, square corners
            assert re.search(rf'class="frame"[^>]*stroke="{theme["border"]}"[^>]*stroke-width="1"', svg)
            assert " rx=" not in svg and " ry=" not in svg
            # role tab on the left in the role colour, divider rule between label and value
            tab = re.search(r'class="tab"[^>]*fill="(#[0-9A-Fa-f]{6})"', svg).group(1)
            assert tab.lower() == theme[ROLE[badge["group"]]].lower()
            assert 'class="rule"' in svg


def test_stars_badge_is_compact():
    from scripts.render_badges import render_badge

    live = json.loads(FIXTURE.read_text(encoding="utf-8"))
    badge = json.loads((ROOT / "data" / "badges.json").read_text(encoding="utf-8"))[0]
    width = float(re.search(r'viewBox="0 0 ([0-9.]+) ', render_badge(badge, live, "night")).group(1))
    assert width <= 64, width


def test_fixture_stars_height_contrast_hosts_and_files(tmp_path):
    from scripts.layout import load
    from scripts.render_badges import write_badges

    badges = json.loads((ROOT / "data" / "badges.json").read_text(encoding="utf-8"))
    write_badges(FIXTURE, tmp_path)
    badge_h = load()["badge_h"]
    ids = [badge["id"] for badge in badges]
    files = sorted(tmp_path.glob("*.svg"))
    assert len(files) == len(ids) * 2
    for badge_id in ids:
        for theme in ("night", "day"):
            path = tmp_path / f"{badge_id}-{theme}.svg"
            assert path.is_file()
            svg = path.read_text(encoding="utf-8")
            assert _height(svg) == badge_h
            assert "<text" not in svg.lower()
            chip = re.search(r'class="value"[^>]*fill="(#[0-9A-Fa-f]{6})"', svg).group(1)
            ink = re.search(r'class="value-ink"[^>]*fill="(#[0-9A-Fa-f]{6})"', svg).group(1)
            assert _contrast(ink, chip) >= 4.5, (badge_id, theme, ink, chip, round(_contrast(ink, chip), 2))
            lowered = svg.lower()
            assert not any(host in lowered for host in BANNED)
    manifest = re.search(r"<!-- manifest:(.*?) -->", (tmp_path / "stars-night.svg").read_text(encoding="utf-8"))
    assert manifest and "371" in manifest.group(1)
    catalog = (ROOT / "data" / "badges.json").read_text(encoding="utf-8").lower()
    assert not any(host in catalog for host in BANNED)


def test_link_badges_are_label_plus_arrow():
    from scripts.render_badges import render_badge

    live = json.loads(FIXTURE.read_text(encoding="utf-8"))
    badges = json.loads((ROOT / "data" / "badges.json").read_text(encoding="utf-8"))
    links = [badge for badge in badges if badge["group"] == "link"]
    assert links
    for badge in links:
        svg = render_badge(badge, live, "night")
        assert f"<!-- manifest:{badge['label']}=→ -->" in svg
        width = float(re.search(r'viewBox="0 0 ([0-9.]+) ', svg).group(1))
        assert width <= 7 + len(badge["label"]) * 5.5 + 4 + 1 + 4 + 5.5 + 4 + 0.5, (badge["id"], width)
