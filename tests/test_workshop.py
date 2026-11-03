"""WORKSHOP pane lists every project at the configured height."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.test_svg_lint import lint_svg


def _height(svg):
    match = re.search(r'viewBox="0 0 [0-9.]+ ([0-9.]+)"', svg)
    return float(match.group(1))


def test_workshop_lists_every_project_at_pane_height(tmp_path):
    from scripts.layout import load
    from scripts.render_panels import render_workshop

    projects = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
    expected = [project["name"] for project in projects]
    pane_h = load()["pane_h"]
    for theme in ("night", "day"):
        svg = render_workshop(theme)
        assert _height(svg) == pane_h
        manifest = re.search(r"<!-- data-names:([^>]*) -->", svg)
        assert manifest, "missing data-names comment"
        names = manifest.group(1).split("|")
        assert names == expected
        assert "claviscage" not in names
        assert "<!-- label:claviscage -->" in svg
        dest = tmp_path / f"workshop-{theme}.svg"
        dest.write_text(svg, encoding="utf-8")
        lint_svg(dest)
        assert dest.stat().st_size < 300 * 1024
