import re
import sys
from xml.etree import ElementTree
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import render_scene
import tokens

MAX_BYTES = 300 * 1024


def _svg(theme):
    return render_scene.render(theme)


def test_both_themes_fit_the_budget_and_are_clean():
    for theme in ("night", "day"):
        svg = _svg(theme)
        assert len(svg.encode("utf-8")) < MAX_BYTES, theme
        lowered = svg.lower()
        assert "<text" not in lowered
        assert "<script" not in lowered
        assert svg.startswith("<svg") and svg.endswith("</svg>")
        ElementTree.fromstring(svg)  # GitHub shows a broken image for malformed XML


def test_three_acts_of_stepped_frames():
    svg = _svg("night")
    frames = re.findall(r'<g class="f( last)?" style="animation-delay:([0-9.]+)s"', svg)
    assert len(frames) == 3 * render_scene.FRAMES_PER_ACT
    assert [m for m in frames if m[0]] == [frames[-1]]
    delays = [float(d) for _, d in frames]
    assert delays == sorted(delays)
    assert "step-end" in svg
    assert "ease" not in svg.lower()


def test_still_state_is_the_default_and_reduced_motion_keeps_it():
    svg = _svg("night")
    assert 'class="still"' in svg
    assert svg.count('class="still-panel"') == 3
    motion_block = svg.split("@media (prefers-reduced-motion: no-preference)", 1)[1]
    assert ".still{display:none}" in motion_block.replace(" ", "")


def test_accent_only_on_the_subject():
    t = tokens.THEMES["night"]
    svg = _svg("night")
    accent = t["workshop"]
    tagged = re.findall(r'<[^>]*data-subject[^>]*>', svg)
    assert tagged, "subject marks are tagged"
    untagged = [tag for tag in re.findall(r"<[^>]+>", svg) if accent in tag and "data-subject" not in tag]
    assert untagged == [], untagged[:3]


def test_written_files_match_render(tmp_path):
    out = render_scene.write(tmp_path)
    assert sorted(p.name for p in out) == ["scene-day.svg", "scene-night.svg"]
    assert out[0].read_text(encoding="utf-8") == render_scene.render("day" if "day" in out[0].name else "night")
