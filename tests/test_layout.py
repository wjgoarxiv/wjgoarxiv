"""Layout presets drive viewBox heights. Cards keep their own size."""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _height(svg):
    match = re.search(r'viewBox="0 0 [0-9.]+ ([0-9.]+)"', svg)
    assert match, svg[:80]
    return float(match.group(1))


def test_default_hero_viewbox_height():
    from scripts.render_hero import render

    assert _height(render()) == 360


def test_tall_hero_is_taller_than_default():
    from scripts.render_hero import render

    assert _height(render(preset="tall")) > _height(render(preset="default"))


def test_compact_hero_is_shorter_than_default():
    from scripts.render_hero import render

    assert _height(render(preset="compact")) < _height(render(preset="default"))


def test_unknown_preset_raises():
    from scripts.layout import load

    with pytest.raises(ValueError):
        load("no-such-preset")


def test_pane_heights_follow_preset():
    from scripts.layout import load
    from scripts.render_panels import render_lab, render_workshop

    default = load()["pane_h"]
    assert _height(render_lab()) == default
    assert _height(render_workshop()) == default
    assert _height(render_lab(preset="tall")) > default
    assert _height(render_lab(preset="compact")) < default
    assert _height(render_workshop(preset="tall")) > _height(render_workshop(preset="compact"))


def test_frame_x_flush_and_gutter():
    from scripts.layout import GUTTER, INSET, frame_x

    assert INSET == 28
    assert GUTTER == 12
    assert frame_x(0, 2, 600) == (0, 594)
    assert frame_x(1, 2, 600) == (6, 600)
    assert frame_x(0, 1, 1200) == (0, 1200)
    assert frame_x(1, 3, 600) == (6, 594)


def _rects(svg):
    found = []
    for chunk in re.findall(r"<rect\b([^>]*)/?>", svg):
        if re.search(r'fill="none"', chunk):
            continue

        def attr(name, default=0.0, chunk=chunk):
            match = re.search(rf'\b{name}="([0-9.]+)"', chunk)
            return float(match.group(1)) if match else default

        found.append((attr("x"), attr("y"), attr("width"), attr("height")))
    return found


def _frame_box(svg):
    """Screen ground: the filled rect as tall as the viewport."""
    height = _height(svg)
    screen = [rect for rect in _rects(svg) if rect[3] == height and rect[2] > 100]
    assert len(screen) == 1, screen
    return screen[0]


def test_blocks_share_outer_edges():
    from scripts.layout import frame_x
    from scripts.render_panels import PANE_W, render_lab, render_workshop

    lab = render_lab()
    shop = render_workshop()
    assert re.search(rf'viewBox="0 0 {PANE_W} [0-9.]+"', lab)
    assert re.search(rf'viewBox="0 0 {PANE_W} [0-9.]+"', shop)
    left = frame_x(0, 2, PANE_W)
    right = frame_x(1, 2, PANE_W)
    lab_x, _lab_y, lab_w, _lab_h = _frame_box(lab)
    shop_x, _shop_y, shop_w, _shop_h = _frame_box(shop)
    assert (lab_x, lab_x + lab_w) == left
    assert (shop_x, shop_x + shop_w) == right
    for svg, (x0, x1) in ((lab, left), (shop, right)):
        bars = [rect for rect in _rects(svg) if rect[1] == 0 and rect[3] == 28]
        assert bars, svg[:120]
        assert (bars[0][0], bars[0][0] + bars[0][2]) == (x0, x1)


def _glyph_xs(svg, y=None):
    origins = [
        (float(x), float(origin_y))
        for x, origin_y in re.findall(r"translate\(([0-9.]+) ([0-9.]+)\) scale\(", svg)
    ]
    if y is None:
        return [x for x, _origin_y in origins]
    return [x for x, origin_y in origins if origin_y == y]


def _visible_mark_left(hero):
    attrs = re.search(r'<svg id="nameplate"([^>]*)>', hero).group(1)
    origin = float(re.search(r'\bx="([0-9.]+)"', attrs).group(1))
    width = float(re.search(r'\bwidth="([0-9.]+)"', attrs).group(1))
    box = [float(part) for part in re.search(r'viewBox="([^"]+)"', attrs).group(1).split()]
    block = re.search(r'<svg id="nameplate".*?</svg>', hero, re.DOTALL).group(0)
    placed = re.search(
        r'transform="translate\(([-\d.]+) [-\d.]+\)"><g transform="translate\(([-\d.]+) [-\d.]+\) scale\(([-\d.]+)\)"',
        block,
    )
    assert placed, "lockup padding transform missing"
    shift, inner, scale = (float(part) for part in placed.groups())
    # Module path starts at local x=28; the viewBox origin is further left.
    ink = 28 * scale + inner + shift
    return origin + (ink - box[0]) * (width / box[2])


def test_text_inset_is_shared():
    from scripts.layout import INSET, frame_x
    from scripts.render_contrib import render_svg
    from scripts.render_hero import render
    from scripts.render_panels import PANE_W, render_lab, render_workshop
    import json

    lab = render_lab()
    shop = render_workshop()
    lab_x = frame_x(0, 2, PANE_W)[0] + INSET
    shop_x = frame_x(1, 2, PANE_W)[0] + INSET
    assert min(_glyph_xs(lab)) == lab_x
    assert min(_glyph_xs(lab, 19)) == lab_x
    assert min(_glyph_xs(shop)) == shop_x
    assert min(_glyph_xs(shop, 19)) == shop_x

    model = json.loads((ROOT / "data" / "contrib.json").read_text(encoding="utf-8"))
    contrib = render_svg(model)
    assert min(_glyph_xs(contrib, 19)) == INSET
    assert min(_glyph_xs(contrib, 46)) == INSET

    hero = render()
    boot = re.search(r'data-copy="\$ mounting /lab/hydrate"', hero)
    assert boot
    assert _glyph_xs(hero[boot.end() : boot.end() + 20000])[0] == INSET
    assert abs(_visible_mark_left(hero) - INSET) < 0.15
    bezel = re.search(r'<svg id="bezel-mark"([^>]*)>', hero).group(1)
    assert float(re.search(r'\bx="([0-9.]+)"', bezel).group(1)) == INSET


def test_card_title_shares_the_inset():
    import json

    from scripts.layout import INSET, frame_x
    from scripts.render_cards import SPAN_WIDTH, Glyphs, _card, card_slots
    from scripts.svgtext import text_width
    import crt

    projects = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
    slots = card_slots(projects)
    chrome = crt.Chrome("night")
    for project in projects:
        col, cols = slots[project["name"]]
        svg = _card(project, Glyphs(), chrome, col, cols)
        x0, x1 = frame_x(col, cols, SPAN_WIDTH[cols])
        inset = x0 + INSET
        accent = [rect for rect in _rects(svg) if rect[2] == 10 and rect[3] == 10]
        assert len(accent) == 1
        assert accent[0][0] == inset
        assert _glyph_xs(svg, 60)[0] == inset
        assert _glyph_xs(svg, 92)[0] == inset
        name_x = _glyph_xs(svg, 22)[0]
        assert name_x == inset + 12
        name_w = text_width(project["name"], "meslo-bold", 20, 0)
        assert name_x + name_w <= x1 - INSET


def test_cards_keep_width_and_read_canvas_width():
    from scripts.layout import load
    from scripts.render_cards import metrics

    for name in ("compact", "default", "tall"):
        size = metrics(name)
        assert size["card_w"] == 400
        assert size["card_h"] == 190
        assert size["bar_w"] == load(name)["width"]
        assert size["paper_w"] == load(name)["width"]
    with pytest.raises(ValueError):
        metrics("no-such-preset")
