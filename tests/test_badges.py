"""Self-rendered shields. Values come from a fixture, not a third-party host."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BANNED = ("shields.io", "github-readme-stats", "demolab", "komarev", "wakatime", "capsule-render")
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


def test_default_badge_height_is_20():
    from scripts.layout import load
    from scripts.render_badges import render_badge

    assert load()["badge_h"] == 20
    assert load("compact")["badge_h"] == 14
    assert load("tall")["badge_h"] == 20
    live = json.loads(FIXTURE.read_text(encoding="utf-8"))
    badge = json.loads((ROOT / "data" / "badges.json").read_text(encoding="utf-8"))[0]
    svg = render_badge(badge, live, "night")
    assert _height(svg) == 20
    assert "scale(0.011)" in svg


def test_brutalist_cell_frame_tab_and_rule():
    from scripts import tokens
    from scripts.render_badges import ROLE, render_badge

    live = json.loads(FIXTURE.read_text(encoding="utf-8"))
    badges = json.loads((ROOT / "data" / "badges.json").read_text(encoding="utf-8"))
    for badge in badges:
        if badge.get("style") == "cta":
            continue
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


def _view_width(svg):
    return float(re.search(r'viewBox="0 0 ([0-9.]+) ', svg).group(1))


def _frame_width(svg):
    tag = re.search(r'<rect class="frame"[^>]*>', svg).group(0)
    return float(re.search(r'(?<![\w-])width="([0-9.]+)"', tag).group(1))


def _draw_width(badge, badges):
    row = [item for item in badges if item["row"] == badge["row"]]
    gap = 0 if row[-1]["id"] == badge["id"] else 3
    return badge["w"] - gap


def test_stars_badge_is_compact():
    from scripts.render_badges import render_badge

    live = json.loads(FIXTURE.read_text(encoding="utf-8"))
    badges = json.loads((ROOT / "data" / "badges.json").read_text(encoding="utf-8"))
    badge = badges[0]
    assert badge["id"] == "stars"
    assert badge["w"] == 84
    svg = render_badge(badge, live, "night")
    assert _view_width(svg) == 84
    assert _frame_width(svg) == _draw_width(badge, badges) - 1


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
    from scripts import svgtext
    from scripts.layout import load
    from scripts.render_badges import _size, render_badge

    live = json.loads(FIXTURE.read_text(encoding="utf-8"))
    badges = json.loads((ROOT / "data" / "badges.json").read_text(encoding="utf-8"))
    links = [badge for badge in badges if badge["group"] == "link"]
    assert links
    size = _size(load()["badge_h"])
    arrow_w = svgtext.text_width("→", "meslo-regular", size, 0)
    for badge in links:
        svg = render_badge(badge, live, "night")
        assert f"<!-- manifest:{badge['label']}=→ -->" in svg
        assert _view_width(svg) == badge["w"]
        draw = _draw_width(badge, badges)
        xs = [float(item) for item in re.findall(r"translate\(([0-9.]+) ", svg)]
        assert xs
        assert max(xs) == round(draw - 6 - arrow_w, 2)


SLOT_W = {
    1: (("stars", 84), ("followers", 108), ("release", 232), ("phd", 130), ("research", 292)),
    2: (
        ("homepage", 103),
        ("scholar", 96),
        ("orcid", 83),
        ("linkedin", 103),
        ("pypi", 76),
        ("researchgate", 129),
        ("mail", 76),
        ("coffee", 180),
    ),
}


def test_rows_sum_to_article_width():
    badges = json.loads((ROOT / "data" / "badges.json").read_text(encoding="utf-8"))
    by_id = {badge["id"]: badge for badge in badges}
    assert len(by_id) == len(badges)
    for row, slots in SLOT_W.items():
        assert [badge["id"] for badge in badges if badge["row"] == row] == [slot[0] for slot in slots]
        assert sum(slot[1] for slot in slots) == 846
        for badge_id, width in slots:
            assert by_id[badge_id]["w"] == width
            assert by_id[badge_id]["row"] == row


def test_row_last_cell_is_flush():
    from scripts.render_badges import render_badge

    live = json.loads(FIXTURE.read_text(encoding="utf-8"))
    badges = json.loads((ROOT / "data" / "badges.json").read_text(encoding="utf-8"))
    by_id = {badge["id"]: badge for badge in badges}
    stars = render_badge(by_id["stars"], live, "night")
    assert _view_width(stars) == 84
    assert _frame_width(stars) == 84 - 3 - 1
    research = render_badge(by_id["research"], live, "night")
    assert _view_width(research) == 292
    assert _frame_width(research) == 292 - 1
    coffee = render_badge(by_id["coffee"], live, "day")
    assert _view_width(coffee) == 180
    ground = re.search(r'class="value"[^>]*width="([0-9.]+)"', coffee)
    assert ground and float(ground.group(1)) == 180


def test_long_value_truncates_inside_slot():
    from scripts import svgtext
    from scripts.layout import load
    from scripts.render_badges import _size, render_badge

    live = json.loads(FIXTURE.read_text(encoding="utf-8"))
    live["release"] = "R" * 40
    badges = json.loads((ROOT / "data" / "badges.json").read_text(encoding="utf-8"))
    badge = next(item for item in badges if item["id"] == "release")
    svg = render_badge(badge, live, "night")
    shown = re.search(r"<!-- manifest:release=(.*?) -->", svg).group(1)
    assert shown.endswith("...")
    assert shown != live["release"]
    assert live["release"] not in svg
    size = _size(load()["badge_h"])
    draw = _draw_width(badge, badges)
    assert svgtext.text_width(live["release"], "meslo-regular", size, 0) > draw
    xs = [float(item) for item in re.findall(r"translate\(([0-9.]+) ", svg)]
    right = max(xs) + svgtext.text_width(".", "meslo-regular", size, 0)
    assert right <= draw + 0.05


def test_coffee_cell_is_filled_and_contrasty():
    import sys

    sys.path.insert(0, str(ROOT / "tests"))
    from scripts import tokens
    from scripts.render_badges import render_badge
    from test_contrast import contrast

    live = json.loads(FIXTURE.read_text(encoding="utf-8"))
    badges = json.loads((ROOT / "data" / "badges.json").read_text(encoding="utf-8"))
    coffee = next(item for item in badges if item["id"] == "coffee")
    assert coffee["label"] == "buy me a coffee"
    assert coffee["style"] == "cta"
    for theme_name in ("night", "day"):
        theme = tokens.THEMES[theme_name]
        svg = render_badge(coffee, live, theme_name)
        assert f'fill="{theme["warn"]}"' in svg
        assert theme["inverse_ink"] in svg
        assert 'class="tab"' not in svg
        assert 'class="rule"' not in svg
        assert 'class="frame"' not in svg
        assert "<text" not in svg.lower()
        assert "gradient" not in svg.lower() and "filter=" not in svg.lower()
        assert contrast(theme["inverse_ink"], theme["warn"]) >= 4.5
        assert svg.lower().count("<rect") >= 4
