"""v3 motion: shared easings, reduced-motion, cage remap, lattice wave, odometer."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FIXTURE = ROOT / "tests" / "fixtures" / "live.json"
CONTRIB = ROOT / "tests" / "fixtures" / "contrib.json"


def _style(svg):
    return "\n".join(re.findall(r"<style>(.*?)</style>", svg, re.S))


def _timings(css):
    return re.findall(
        r"cubic-bezier\([^)]+\)|steps\([^)]+\)|\blinear\b|\bease(?:-in-out|-in|-out)?\b",
        css,
    )


def test_chrome_steps_finish_after_the_modules():
    from scripts.motion import MOTION
    from scripts.render_hero import render

    live = json.loads(FIXTURE.read_text(encoding="utf-8"))
    hero = render("night", model=live)
    assert "steps(3, end)" in hero
    delays = [float(item) for item in re.findall(r'class="line l\d"[^>]*style="--d:([0-9.]+)s"', hero)]
    assert len(delays) >= 6
    assert min(delays) >= 0.7
    assert max(delays) + MOTION["chrome_ms"] / 1000 <= 2.0
    status = float(re.search(r'class="chrome-status"[^>]*style="--d:([0-9.]+)s"', hero).group(1))
    assert status >= max(delays)
    assert status + MOTION["chrome_ms"] / 1000 <= 2.0
    assert 'begin="0.24s"' in hero


def test_tokens_are_the_shared_easings():
    from scripts.motion import EASE, MOTION

    assert EASE["out_expo"] == "cubic-bezier(0.16, 1, 0.3, 1)"
    assert EASE["out_quint"] == "cubic-bezier(0.22, 1, 0.36, 1)"
    assert EASE["in_out"] == "cubic-bezier(0.65, 0, 0.35, 1)"
    assert "back_out" not in EASE
    assert MOTION["stagger_ms"] == 60
    assert 40 <= MOTION["row_stagger_ms"] <= 70
    assert MOTION["hero_intro_s"] <= 2.6
    assert MOTION["page_intro_s"] <= 3.0


def test_animated_css_uses_only_token_beziers():
    from scripts.motion import EASE
    from scripts.render_badges import render_badge
    from scripts.render_contrib import render_svg
    from scripts.render_hero import render
    from scripts.render_panels import render_lab, render_workshop

    live = json.loads(FIXTURE.read_text(encoding="utf-8"))
    badges = json.loads((ROOT / "data" / "badges.json").read_text(encoding="utf-8"))
    model = json.loads(CONTRIB.read_text(encoding="utf-8"))
    svgs = [
        render("night", model=live),
        render("day", model=live),
        render_lab("night"),
        render_workshop("night"),
        render_svg(model, "night"),
        render_badge(badges[0], live, "night", index=0),
    ]
    allowed = set(EASE.values()) | {"steps(3, end)"}
    for svg in svgs:
        css = _style(svg)
        assert css
        found = _timings(css)
        assert found, "expected a timing function"
        for timing in found:
            assert timing in allowed, timing
        assert " linear" not in css
        assert "cubic-bezier(0.34, 1.56, 0.64, 1)" not in css


def test_every_animated_svg_guards_reduced_motion():
    from scripts.render_badges import render_badge
    from scripts.render_contrib import render_svg
    from scripts.render_hero import render
    from scripts.render_panels import render_lab, render_workshop

    live = json.loads(FIXTURE.read_text(encoding="utf-8"))
    badges = json.loads((ROOT / "data" / "badges.json").read_text(encoding="utf-8"))
    model = json.loads(CONTRIB.read_text(encoding="utf-8"))
    svgs = (
        render("night", model=live),
        render_lab("day"),
        render_workshop("day"),
        render_svg(model, "day"),
        render_badge(badges[1], live, "night", index=1),
    )
    for svg in svgs:
        assert "@keyframes" in svg or "<animate" in svg
        assert "prefers-reduced-motion: reduce" in svg
        assert "prefers-reduced-motion: no-preference" in svg
        reduce = re.search(
            r"@media \(prefers-reduced-motion: reduce\) \{(.+?)\}\s*(?:@|</style>)",
            svg,
            re.S,
        )
        assert reduce, "missing reduce block"
        assert "animation: none" in reduce.group(1)


def test_cage_hold_is_a_seamless_time_remap():
    from scripts.cage import spin_schedule
    from scripts.render_panels import render_lab

    frames, times = spin_schedule()
    assert times[0] == 0
    assert times[-1] == 1
    assert frames[0] == frames[-1] == 0
    gaps = [round(b - a, 4) for a, b in zip(times, times[1:])]
    assert len(set(gaps)) > 1
    assert any(frames[i] == frames[i + 1] for i in range(len(frames) - 1))
    svg = render_lab("night")
    chunk = re.search(r'attributeName="d"[^>]*keyTimes="([^"]+)" values="([^"]+)"', svg)
    assert chunk
    key_times = [float(part) for part in chunk.group(1).split(";")]
    values = chunk.group(2).split(";")
    assert key_times[0] == 0 and key_times[-1] == 1
    assert len({round(b - a, 4) for a, b in zip(key_times, key_times[1:])}) > 1
    assert any(values[i] == values[i + 1] for i in range(len(values) - 1))
    assert values[0] == values[-1]
    assert 'dur="8s"' in svg
    assert 'calcMode="spline"' in svg
    assert "keySplines=" in svg


def test_contrib_delays_follow_the_diagonal_and_stay_under_1_8s():
    from scripts.motion import voxel_delay
    from scripts.render_contrib import render_svg

    model = json.loads(CONTRIB.read_text(encoding="utf-8"))
    svg = render_svg(model, "night")
    found = re.findall(r'class="([^"]*\bvoxel\b[^"]*)"', svg)
    assert found
    delays = []
    for classes in found:
        col = int(re.search(r"\bc(\d+)\b", classes).group(1))
        row = int(re.search(r"\br(\d+)\b", classes).group(1))
        stack = int(re.search(r"\bs(\d+)\b", classes).group(1))
        expected = voxel_delay(col, row, stack)
        delays.append(expected)
        assert abs(expected - ((col + row) * 0.01 + stack * 0.06)) < 1e-9
    assert max(delays) <= 1.8
    assert "cubic-bezier(0.22, 1, 0.36, 1)" in svg
    assert "cubic-bezier(0.34, 1.56, 0.64, 1)" not in svg


def test_odometer_clip_and_final_translate_match_the_fixture():
    from scripts.motion import reel_pitch, reel_shift  # noqa: E402
    from scripts.render_contrib import render_svg
    from scripts.render_hero import render

    live = json.loads(FIXTURE.read_text(encoding="utf-8"))
    hero = render("night", model=live)
    assert 'data-odo="371"' in hero
    assert 'data-odo="48"' in hero
    assert 'class="odo-col"' in hero
    assert "clip-path=" in hero
    size = 12
    while f'data-odo-size="{size}"' not in hero and size > 8:
        size -= 1
    assert f'data-odo-size="{size}"' in hero
    pitch = reel_pitch(size)
    for digit, shift in re.findall(
        r'class="odo-reel" data-digit="(\d)" transform="translate\(0 ([0-9.]+)\)"',
        hero,
    ):
        assert abs(float(shift) - reel_shift(int(digit), size)) < 1e-6
        assert abs(float(shift) - int(digit) * pitch) < 1e-6

    model = json.loads(CONTRIB.read_text(encoding="utf-8"))
    lattice = render_svg(model, "night")
    assert 'data-odo="1087"' in lattice
    assert 'data-odo="21"' in lattice
    assert lattice.count('class="odo-col"') >= 6
    _assert_reel_window(hero)
    _assert_reel_window(lattice)


def _assert_reel_window(svg):
    """The frozen translate puts that digit's glyph in the clip, in user units."""
    from scripts.motion import reel_pitch

    assert "reel-d" not in svg
    without_wave = re.sub(r"@keyframes wave \{.*?\n\}\s*", "", svg, flags=re.S)
    assert "translateY" not in without_wave
    parts = svg.split('<g class="odo" ')[1:]
    assert parts
    for part in parts:
        value = re.search(r'data-odo="(\d+)"', part).group(1)
        size = int(re.search(r'data-odo-size="(\d+)"', part).group(1))
        pitch = reel_pitch(size)
        shown = re.findall(
            r'class="odo-reel" data-digit="(\d)" transform="translate\(0 ([0-9.]+)\)"',
            part,
        )
        assert "".join(digit for digit, _shift in shown) == value
        ends = [float(item) for item in re.findall(r'to="0 ([0-9.]+)"', part)]
        assert len(ends) == len(shown)
        for (digit, shift), end in zip(shown, ends):
            offset = float(shift)
            assert abs(offset - int(digit) * pitch) < 1e-6
            assert int(round(offset / pitch)) == int(digit)
            assert abs(end - offset) < 1e-6
