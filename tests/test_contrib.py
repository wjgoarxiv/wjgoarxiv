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


LIVE = ROOT / "data" / "contrib.json"
FACE = "meslo-regular"
DEPTH_Y = -9.0


def _live():
    return json.loads(LIVE.read_text(encoding="utf-8"))


def _peak_cell(model):
    """Maximum count. Ties resolve to the most recent date, then the later cell."""
    dates = model.get("dates")
    best = None
    for col, week in enumerate(model["weeks"]):
        for row, count in enumerate(week):
            stamp = dates[col][row] if dates else ""
            rank = (count, stamp, col, row)
            if best is None or rank[:2] > best[:2] or (rank[:2] == best[:2] and (col, row) > (best[2], best[3])):
                best = (count, stamp, col, row)
    if best is None or best[0] <= 0:
        return None
    return best


def _point(model, width=1200, height=300):
    weeks = model["weeks"]
    cols = len(weeks)
    rows = len(weeks[0]) if weeks else 0
    week_pitch, box_w = 21.0, 12.0
    day_dx, day_dy = 7.0, -11.0
    grid_w = (max(cols - 1, 0) * week_pitch) + (max(rows - 1, 0) * day_dx) + box_w
    origin_x = (width - grid_w) / 2 + box_w / 2
    baseline = height - 24

    def point(col, row):
        return origin_x + col * week_pitch + row * day_dx, baseline + row * day_dy

    return point, cols, rows


def _tier(distance):
    if distance <= 10:
        return 0
    if distance <= 25:
        return 1
    if distance <= 40:
        return 2
    return 3


def _style_block(svg):
    return "\n".join(re.findall(r"<style>(.*?)</style>", svg, re.S))


def _medias(svg, kind):
    blocks = re.findall(
        rf"@media \(prefers-reduced-motion: {kind}\) \{{(.*?)\n\}}",
        svg,
        re.S,
    )
    assert blocks, kind
    return blocks


def test_peak_callout_matches_data():
    from scripts import crt

    model = _live()
    count, stamp, col, row = _peak_cell(model)
    assert (count, stamp) == (150, "2026-10-28")
    svg = _render(model, "night")
    point, cols, rows = _point(model)
    px, py = point(col, row)
    width = 1200
    ink = THEMES["night"]["text"]
    label = f"PEAK {count} · {stamp}"
    text_x = px - crt.width(label, FACE, 11) if px > width * 0.6 else px
    top = py - 4 * 30 + DEPTH_Y
    leader = (
        f'<rect class="leader" x="{px - 0.5:.1f}" y="62" width="1" '
        f'height="{top - 62:.1f}" fill="{ink}"/>'
    )
    callout = (
        f'<g class="callout" data-count="{count}" data-date="{stamp}">'
        f"{leader}{crt.text(label, FACE, 11, text_x, 58, ink)}</g>"
    )
    assert callout in svg
    assert "callout" not in _style_block(svg)
    circles = re.findall(r'class="node" cx="[0-9.]+" cy="([0-9.]+)"', svg)
    assert circles
    assert max(float(cy) for cy in circles) == 276
    assert f'data-count="{count}" data-h="120.0" data-col="{col}" data-row="{row}"' in svg

    far = {"weeks": [[0] * 7 for _ in range(53)], "start": "2025-11-02"}
    far["weeks"][-1][-1] = 40
    far_svg = _render(far, "night")
    view = re.search(r'<symbol id="v4" viewBox="[^ ]+ ([^ ]+)', far_svg)
    assert view
    min_y = float(view.group(1))
    uses = [
        float(y)
        for y in re.findall(
            rf'y="([0-9.]+)"[^>]*class="voxel c{cols - 1} r{rows - 1} ',
            far_svg,
        )
    ]
    assert uses
    lifted = min(uses) - min_y + (-30 + DEPTH_Y) - 12
    assert lifted >= 66

    tied = {
        "weeks": [[0, 0, 0], [0, 0, 0]],
        "dates": [["2026-01-01", "2026-01-02", "2026-01-03"], ["2026-06-01", "2026-06-02", "2026-06-03"]],
    }
    tied["weeks"][0][0] = 9
    tied["weeks"][1][1] = 9
    tied_svg = _render(tied, "night")
    assert 'data-count="9" data-date="2026-06-02"' in tied_svg
    assert 'data-date="2026-01-01"' not in tied_svg
    tpx, _tpy = _point(tied, width=1200, height=300)[0](1, 1)
    assert tpx <= 1200 * 0.6
    left = crt.text("PEAK 9 · 2026-06-02", FACE, 11, tpx, 58, ink)
    assert left in tied_svg


def test_all_zero_has_no_callout():
    empty = {"weeks": [[0] * 7 for _ in range(53)], "start": "2025-11-02"}
    svg = _render(empty, "night")
    assert 'class="callout"' not in svg
    assert 'class="leader"' not in svg
    assert "PEAK" not in svg


def test_no_beam_or_bob():
    svg = _render(_live(), "night")
    assert 'class="beam"' not in svg
    assert ".beam" not in svg
    assert "@keyframes beam" not in svg
    assert "voxel-bob" not in svg
    assert 'class="peak"' not in svg
    assert ".peak" not in _style_block(svg)


def test_wave_loop_is_slow_and_guarded():
    from scripts.motion import EASE, MOTION

    svg = _render(_live(), "night")
    assert MOTION.get("wave_s", 0) >= 10
    assert MOTION.get("wave_step_s") == 0.035
    pref = _medias(svg, "no-preference")
    match = None
    for block in pref:
        match = re.search(
            rf"\.w\s*\{{[^}}]*animation:\s*wave\s+([0-9.]+)s\s+{re.escape(EASE['out_quint'])}\s+infinite",
            block,
        )
        if match:
            break
    assert match, pref
    assert float(match.group(1)) >= 10
    reduce = "\n".join(_medias(svg, "reduce"))
    assert re.search(
        r"\.w\s*\{\s*animation:\s*none\s*!important;\s*transform:\s*none\s*!important;\s*\}",
        reduce,
    )
    wave = re.search(r"@keyframes wave\s*\{(.+?)\n\}", svg, re.S)
    assert wave
    body = wave.group(1)
    assert "translateY(var(--a))" in body
    assert re.search(r"translateY\(\s*-?\d", body) is None
    stops = re.findall(r"((?:[0-9]+%\s*,\s*)*[0-9]+%)\s*\{([^}]*)\}", body)
    assert stops
    assert "0%" in stops[0][0] and "transform: none" in stops[0][1]
    peak_at = next(i for i, (pct, rule) in enumerate(stops) if "var(--a)" in rule)
    assert peak_at > 0
    for _pct, rule in stops[peak_at + 1 :]:
        assert "transform: none" in rule
        assert "translate" not in rule
    assert any("100%" in pct for pct, _rule in stops)


def test_wave_starts_at_the_last_dated_cell():
    from scripts.motion import MOTION

    model = _live()
    weeks = model["weeks"]
    col0 = len(weeks) - 1
    row0 = len(weeks[-1]) - 1
    assert weeks[col0][row0] > 0
    svg = _render(model, "night")
    groups = re.findall(r'<g class="(w d(\d+) a(\d))">((?:(?!</g>).)*)</g>', svg)
    assert groups
    seen = []
    for classes, distance_s, tier_s, body in groups:
        distance = int(distance_s)
        uses = re.findall(r'class="(voxel c(\d+) r(\d+) s(\d+))"', body)
        assert uses
        cols = {int(col) for _klass, col, _row, _stack in uses}
        rows = {int(row) for _klass, _col, row, _stack in uses}
        assert cols == {int(uses[0][1])} and rows == {int(uses[0][2])}
        col, row = int(uses[0][1]), int(uses[0][2])
        assert distance == abs(col - col0) + abs(row - row0)
        assert int(tier_s) == _tier(distance)
        assert "blink" not in classes and "scale" not in body
        seen.append((col, row, distance))
    assert (col0, row0, 0) in {(col, row, distance) for col, row, distance in seen}
    order = [(col, row) for col, row, _distance in seen]
    assert order == sorted(order, key=lambda item: (item[0], -item[1]))
    step = MOTION["wave_step_s"]
    for distance in {item[2] for item in seen}:
        delay = round(distance * step, 2)
        assert f".d{distance}{{animation-delay:calc(2.4s + {delay}s)}}" in svg
    assert ".a0{--a:-18px}" in svg
    assert ".a1{--a:-16px}" in svg
    assert ".a2{--a:-14px}" in svg
    assert ".a3{--a:-12px}" in svg
    origin = next(body for classes, distance_s, _tier_s, body in groups if distance_s == "0")
    assert 'class="voxel' in origin
    assert "peak" not in origin


def test_streak_is_in_the_title_bar():
    from scripts import crt
    from scripts.motion import reel_width

    model = _live()
    weeks = model["weeks"]
    total = sum(count for week in weeks for count in week)
    best = run = 0
    for week in weeks:
        for count in week:
            if count > 0:
                run += 1
                best = max(best, run)
            else:
                run = 0
    assert (best, total) == (20, 2522)
    svg = _render(model, "night")
    width = 1200
    size = 13
    ink = THEMES["night"]["inverse_ink"]
    gap = crt.width("   ", FACE, size)
    assert gap >= 12
    total_label, streak_label, suffix = "TOTAL ", "STREAK ", " d"
    total_w = crt.width(total_label, FACE, size) + reel_width(total, size)
    streak_w = crt.width(streak_label, FACE, size) + reel_width(best, size) + crt.width(suffix, FACE, size)
    total_x = width - 18 - total_w
    streak_x = total_x - gap - streak_w
    streak_digits = streak_x + crt.width(streak_label, FACE, size)
    assert crt.text(streak_label, FACE, size, streak_x, 19, ink) in svg
    assert crt.text(suffix, FACE, size, streak_digits + reel_width(best, size), 19, ink) in svg
    assert crt.text(total_label, FACE, size, total_x, 19, ink) in svg
    assert f'<g id="odo-streak-0" fill="{ink}">' in svg
    assert f'<g id="odo-total-0" fill="{ink}">' in svg
    assert 'data-odo="20"' in svg and 'data-odo="2522"' in svg
    streak_clip = re.search(r'<clipPath id="clip-streak-0"><rect x="[^"]+" y="([^"]+)"', svg)
    total_clip = re.search(r'<clipPath id="clip-total-0"><rect x="[^"]+" y="([^"]+)"', svg)
    assert streak_clip and total_clip and streak_clip.group(1) == total_clip.group(1)
    assert float(streak_clip.group(1)) < 28
    assert not re.search(r'transform="translate\([0-9.]+ 42\)"', svg)
    assert 'y="42"' not in svg


def test_render_is_deterministic():
    model = _live()
    assert _render(model, "night") == _render(model, "night")
    assert _render(model, "day") == _render(model, "day")
    fixture = _model()
    assert _render(fixture, "night") == _render(fixture, "night")
