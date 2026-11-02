"""Status strip: fixture determinism, lint, and a failed fetch that does not touch the file."""

import ast
import hashlib
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
    assert "#ffb000" not in text
    uptime = (date(2026, 11, 2) - date(2023, 8, 1)).days
    line = render_status.status_line(
        {"latest": "v1.4.0", "stars": 167, "last_push": "2026-10-20", "updated": "2026-11-02"}
    )
    assert "v1.4.0" in line and "167" in line and str(uptime) in line
    assert "2026-11-02" in line
    stale = render_status.render_svg(
        {"latest": "v0", "stars": 1, "last_push": "2026-01-01", "updated": "2026-11-02"}
    )
    assert "#ffb000" in stale


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
