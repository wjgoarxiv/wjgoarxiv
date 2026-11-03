"""Preview report written by scripts/preview.mjs."""

import re
from pathlib import Path

REPORT = Path(__file__).resolve().parents[2] / ".litclaude" / "evidence" / "profile-readme-v2" / "report.md"


def test_collapsed_height_and_cage_diff():
    text = REPORT.read_text(encoding="utf-8")
    height = int(re.search(r"collapsed height: (\d+)", text).group(1))
    diff = float(re.search(r"cage pixel diff: ([0-9.]+)", text).group(1))
    assert height < 1200
    assert diff > 0.01
