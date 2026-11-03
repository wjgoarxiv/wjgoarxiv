"""Isometric contribution lattice: determinism, floor, height, motion, contrast."""

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.tokens import THEMES
from tests.test_contrast import contrast
from tests.test_svg_lint import lint_svg

FIXTURE = ROOT / "tests" / "fixtures" / "contrib.json"


def _model():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _render(model, theme="night", preset=None):
    from scripts.render_contrib import render_svg

    return render_svg(model, theme, preset)


def test_fixture_is_deterministic_and_small(tmp_path):
    model = _model()
    first = _render(model, "night")
    second = _render(model, "night")
    assert hashlib.sha256(first.encode()).hexdigest() == hashlib.sha256(second.encode()).hexdigest()
    dest = tmp_path / "contrib-night.svg"
    dest.write_text(first, encoding="utf-8")
    lint_svg(dest)
    assert dest.stat().st_size < 300 * 1024
    assert 'viewBox="0 0 1200 300"' in first


def test_all_zero_keeps_the_lattice_floor():
    empty = {"weeks": [[0] * 7 for _ in range(53)]}
    svg = _render(empty, "night")
    assert 'class="column"' not in svg
    assert 'class="bond"' in svg
    assert 'class="node"' in svg


def test_max_count_is_the_tallest_column():
    weeks = [[(week + day) % 5 for day in range(7)] for week in range(53)]
    weeks[10][3] = 40
    svg = _render({"weeks": weeks}, "night")
    pairs = re.findall(r'data-count="(\d+)" data-h="([0-9.]+)"', svg)
    assert pairs
    heights = [float(height) for _count, height in pairs]
    tallest = max(float(height) for count, height in pairs if count == "40")
    assert tallest == max(heights)
    assert all(float(height) < tallest for count, height in pairs if count != "40")


def test_voxels_stack_to_the_level_and_settle_within_1_8s():
    from scripts.motion import voxel_delay

    weeks = [[0] * 7 for _ in range(53)]
    weeks[0][0] = 3
    weeks[4][2] = 9
    weeks[8][1] = 40
    svg = _render({"weeks": weeks, "start": "2025-11-02"}, "night")
    assert 'id="v1"' in svg and 'id="v2"' in svg and 'id="v3"' in svg and 'id="v4"' in svg
    uses = re.findall(r'<use\b[^>]*href="#v(\d)"[^>]*>', svg)
    assert uses
    by_level = {}
    for level in uses:
        by_level[level] = by_level.get(level, 0) + 1
    # Levels from the quantile: 3 → 1 cube, 9 → 2 cubes, 40 → 4 cubes.
    assert by_level == {"1": 1, "2": 2, "4": 4}
    for tag in re.findall(r'<use\b[^>]*href="#v\d"[^>]*>', svg):
        assert ' x="' in tag and ' y="' in tag
    found = re.findall(r'class="([^"]*\bvoxel\b[^"]*)"', svg)
    assert found
    assert 'style="--d:' not in svg
    delays = []
    for classes in found:
        col = int(re.search(r"\bc(\d+)\b", classes).group(1))
        row = int(re.search(r"\br(\d+)\b", classes).group(1))
        stack = int(re.search(r"\bs(\d+)\b", classes).group(1))
        delays.append(voxel_delay(col, row, stack))
    assert max(delays) <= 1.8
    assert "360ms" in svg
    assert "translate(0, -24px)" in svg
    assert "cubic-bezier(0.34, 1.56, 0.64, 1)" not in svg


def test_brand_ramp_colours():
    from scripts.tokens import THEMES

    model = _model()
    for theme in ("night", "day"):
        svg = _render(model, theme)
        for color in THEMES[theme]["contrib"]:
            assert f'fill="{color}"' in svg


def test_reduced_motion_and_readout_contrast():
    model = _model()
    for theme in ("night", "day"):
        svg = _render(model, theme)
        assert "prefers-reduced-motion" in svg
        assert 'class="lattice-still"' in svg
        readout = re.search(r'class="readout" fill="(#[0-9A-Fa-f]{6})"', svg)
        assert readout, theme
        assert contrast(readout.group(1), THEMES[theme]["screen_bg"]) >= 4.5
