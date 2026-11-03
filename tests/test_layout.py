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
