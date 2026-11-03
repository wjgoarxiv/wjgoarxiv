"""Status strip: fixture determinism, lint, and a failed fetch that does not touch the file."""

import ast
import hashlib
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PY = ROOT / ".venv" / "bin" / "python"
SCRIPT = ROOT / "scripts" / "render_status.py"
FIXTURE = ROOT / "tests" / "fixtures" / "status.json"


def test_fixture_is_deterministic(tmp_path):
    import scripts.render_status as render_status
    from tests.test_svg_lint import lint_svg

    first = tmp_path / "a.svg"
    second = tmp_path / "b.svg"
    render_status.render_file(FIXTURE, first)
    render_status.render_file(FIXTURE, second)
    assert hashlib.sha256(first.read_bytes()).hexdigest() == hashlib.sha256(second.read_bytes()).hexdigest()
    lint_svg(first)
    text = first.read_text(encoding="utf-8")
    assert "v1.4.0" not in text  # paths, not text nodes
    assert "<text" not in text.lower()
    from scripts.tokens import THEMES

    assert THEMES["night"]["warn"] not in text
    uptime = (date(2026, 11, 2) - date(2023, 8, 1)).days
    line = render_status.status_line(
        {"latest": "v1.4.0", "stars": 167, "last_push": "2026-10-20", "updated": "2026-11-02"}
    )
    assert "v1.4.0" in line and "167" in line and str(uptime) in line
    assert "2026-11-02" in line
    stale_model = {"latest": "v0", "stars": 1, "last_push": "2026-01-01", "updated": "2026-11-02"}
    fresh_model = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for theme in ("night", "day"):
        fresh = render_status.render_svg(fresh_model, theme)
        stale = render_status.render_svg(stale_model, theme)
        assert THEMES[theme]["warn"] not in fresh
        assert THEMES[theme]["warn"] in stale
        assert THEMES[theme]["screen_bg"] in fresh
        assert THEMES[theme]["lab"] in fresh
    written = render_status.render_both(fresh_model, tmp_path / "status.svg")
    assert {path.name for path in written} == {"status-night.svg", "status-day.svg"}
    workflow = (ROOT / ".github" / "workflows" / "status.yml").read_text(encoding="utf-8")
    assert "git add assets/status-night.svg assets/status-day.svg" in workflow


def test_http_error_leaves_file(tmp_path):
    dest = tmp_path / "status.svg"
    dest.write_text("KEEP", encoding="utf-8")
    before = dest.stat().st_mtime_ns
    env = os.environ.copy()
    env["GH_TOKEN"] = "dummy-not-a-real-token"
    result = subprocess.run(
        [str(PY), str(SCRIPT), "--out", str(dest), "--api-base", "http://127.0.0.1:9"],
        cwd=ROOT.parent,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert dest.read_text(encoding="utf-8") == "KEEP"
    assert dest.stat().st_mtime_ns == before
    assert "dummy-not-a-real-token" not in result.stdout + result.stderr


def test_renderer_imports_no_fonttools():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    banned = {"fontTools", "uharfbuzz", "fonttools"}
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module.split(".")[0]]
        assert not (set(names) & banned)
