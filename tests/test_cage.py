"""5^12 6^2 cage: topology, rotating frames, reduced motion, size, papers."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.test_svg_lint import lint_svg


def _newest(papers, count=2):
    from scripts.render_panels import newest_papers

    return newest_papers(papers, count)


def test_euler_and_face_counts():
    from scripts.cage import polyhedron

    verts, edges, faces = polyhedron()
    assert len(verts) == 24
    assert len(edges) == 36
    assert len(verts) - len(edges) + len(faces) == 2
    sizes = [len(face) for face in faces]
    assert sizes.count(5) == 12
    assert sizes.count(6) == 2


def test_newest_papers_break_year_ties_by_later_entry():
    papers = [
        {"year": "2019", "slug": "old"},
        {"year": "2024", "slug": "earlier"},
        {"year": "2022", "slug": "mid"},
        {"year": "2024", "slug": "later"},
    ]
    got = _newest(papers)
    assert [paper["slug"] for paper in got] == ["later", "earlier"]
    assert [paper["year"] for paper in got] == ["2024", "2024"]


def _frames(svg):
    values = re.findall(r'attributeName="d"[^>]*values="([^"]*)"', svg)
    assert values
    distinct = set()
    for chunk in values:
        distinct.update(part for part in chunk.split(";") if part)
    return distinct


def test_cage_edges_are_bold_and_glassy():
    from scripts.render_panels import render_lab

    svg = render_lab("night")
    still, spin = svg.split('class="cage-still"', 1)[1].split('class="cage-spin"', 1)
    widths = [
        float(part)
        for values in re.findall(r'attributeName="stroke-width"[^>]*values="([^"]+)"', spin)
        for part in values.split(";")
    ]
    assert widths
    assert max(widths) >= 2.6
    assert max(widths) <= 3.2
    assert min(widths) >= 1.2
    assert min(widths) <= 1.6
    panes = re.findall(r'class="pane"[^>]*fill-opacity="([0-9.]+)"', still)
    assert len(panes) == 14
    assert all(0.05 <= float(value) <= 0.14 for value in panes)
    assert still.count('class="core"') == 36
    assert 'stroke-width="0.8"' in still
    assert 'class="glint"' in still
    assert "linearGradient" not in svg and "radialGradient" not in svg and "<filter" not in svg
    assert 'attributeName="fill-opacity"' in spin


def test_lab_frames_static_group_papers_and_size(tmp_path):
    from scripts.render_panels import render_lab

    papers = json.loads((ROOT / "data" / "papers.json").read_text(encoding="utf-8"))
    newest = _newest(papers)
    for theme in ("night", "day"):
        svg = render_lab(theme)
        dest = tmp_path / f"lab-{theme}.svg"
        dest.write_text(svg, encoding="utf-8")
        lint_svg(dest)
        assert dest.stat().st_size < 300 * 1024
        assert 'class="cage-still"' in svg
        assert "prefers-reduced-motion" in svg
        assert len(_frames(svg)) >= 3
        assert 'dur="8s"' in svg
        assert 'calcMode="linear"' in svg
        assert svg.count('id="cage-e') == 36
        assert svg.count('attributeName="d"') == 50
        assert svg.count('attributeName="stroke-opacity"') == 72
        assert svg.count('attributeName="cx"') == 25
        for paper in newest:
            assert f"{paper['year']}:{paper['slug']}" in svg
