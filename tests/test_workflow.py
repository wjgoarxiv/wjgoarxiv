"""Structural checks for the weekly status workflow. No YAML dependency."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "status.yml"


def check_workflow(text):
    assert "workflow_dispatch" in text
    assert "17 3 * * 1" in text
    assert "contents: write" in text
    assert "pip install" not in text
    assert "fonttools" not in text.lower()
    assert "fetch_live.py" in text
    assert "render_hero.py" in text
    assert "render_badges.py" in text
    assert "render_contrib.py" in text
    assert "assets/hero-night.svg" in text
    assert "assets/hero-day.svg" in text
    assert "assets/badges" in text
    assert "assets/contrib-night.svg" in text
    assert "assets/contrib-day.svg" in text
    assert "status-" not in text
    assert "git diff --cached --quiet" in text


def test_status_workflow():
    check_workflow(WORKFLOW.read_text(encoding="utf-8"))


def test_missing_dispatch_fails(tmp_path):
    text = WORKFLOW.read_text(encoding="utf-8").replace("workflow_dispatch", "workflow_call")
    try:
        check_workflow(text)
    except AssertionError:
        return
    raise AssertionError("workflow without workflow_dispatch was accepted")
