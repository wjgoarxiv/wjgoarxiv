"""Live fetch: fixture copy makes no network call; a dead API leaves files untouched."""

import json
import os
import subprocess
import sys
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PY = ROOT / ".venv" / "bin" / "python"
SCRIPT = ROOT / "scripts" / "fetch_live.py"
LIVE = ROOT / "tests" / "fixtures" / "live.json"
CONTRIB = ROOT / "tests" / "fixtures" / "contrib.json"


def test_fixture_mode_copies_without_network(tmp_path):
    env = os.environ.copy()
    env["GITHUB_TOKEN"] = "dummy-not-a-real-token"
    result = subprocess.run(
        [
            str(PY),
            str(SCRIPT),
            "--fixture",
            "--out",
            str(tmp_path),
            "--api-base",
            "http://127.0.0.1:9",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "dummy-not-a-real-token" not in result.stdout + result.stderr
    live = json.loads((tmp_path / "live.json").read_text(encoding="utf-8"))
    contrib = json.loads((tmp_path / "contrib.json").read_text(encoding="utf-8"))
    assert live == json.loads(LIVE.read_text(encoding="utf-8"))
    assert contrib == json.loads(CONTRIB.read_text(encoding="utf-8"))
    assert live["stars"] == 371
    assert "pypi" not in live
    total = sum(count for week in contrib["weeks"] for count in week)
    assert f"stars {live['stars']}" in result.stdout
    assert f"followers {live['followers']}" in result.stdout
    assert f"contributions {total}" in result.stdout


def test_network_error_leaves_files(tmp_path):
    live = tmp_path / "live.json"
    contrib = tmp_path / "contrib.json"
    live.write_text("KEEP", encoding="utf-8")
    contrib.write_text("KEEP", encoding="utf-8")
    before = (live.stat().st_mtime_ns, contrib.stat().st_mtime_ns)
    env = os.environ.copy()
    env["GITHUB_TOKEN"] = "dummy-not-a-real-token"
    result = subprocess.run(
        [str(PY), str(SCRIPT), "--out", str(tmp_path), "--api-base", "http://127.0.0.1:9"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert live.read_text(encoding="utf-8") == "KEEP"
    assert contrib.read_text(encoding="utf-8") == "KEEP"
    assert (live.stat().st_mtime_ns, contrib.stat().st_mtime_ns) == before
    assert "dummy-not-a-real-token" not in result.stdout + result.stderr


def test_missing_release_falls_back(monkeypatch):
    from scripts import fetch_live

    def missing(url, token, payload=None):
        raise urllib.error.HTTPError(url, 404, "missing", hdrs=None, fp=None)

    monkeypatch.setattr(fetch_live, "_request", missing)
    public = [{"name": "litfamily", "pushed_at": "2026-01-02T00:00:00Z"}]
    assert fetch_live._release("https://api.github.com", "token", public) == "litfamily 2026-01-02"
