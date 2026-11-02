"""Glyph atlas contract. Written before build_atlas.py exists."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FACE_IDS = (
    "meslo-regular",
    "meslo-bold",
    "pretendard-regular",
    "pretendard-semibold",
    "pretendard-bold",
)
BOX = "─│┌┐└┘├┤┬┴┼═║╔╗╚╝"
SYMBOLS = "●○▸▶█░▒▓★·⟷→✓"
MAX_BYTES = int(1.5 * 1024 * 1024)


def required_chars():
    chars = [chr(code) for code in range(32, 127)]
    chars.extend(BOX)
    chars.extend(SYMBOLS)
    extra_path = ROOT / "scripts" / "extra_chars.txt"
    text = extra_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.split("#", 1)[0]
        chars.extend(ch for ch in line if not ch.isspace())
    seen = set()
    ordered = []
    for ch in chars:
        if ch not in seen:
            seen.add(ch)
            ordered.append(ch)
    return ordered


def assert_atlas(data, chars):
    assert data["units_per_em"] == 1000
    assert tuple(data["faces"]) == tuple(sorted(FACE_IDS))
    for face in FACE_IDS:
        glyphs = data["faces"][face]["glyphs"]
        assert list(glyphs) == sorted(glyphs)
        missing = [ch for ch in chars if ch not in glyphs]
        assert not missing, f"{face} missing {missing!r}"
        for ch, glyph in glyphs.items():
            assert isinstance(glyph["advance"], (int, float))
            assert glyph["advance"] >= 0
            path = glyph["d"]
            assert isinstance(path, str)
            if ch != " ":
                assert path.strip(), f"{face} {ch!r} has an empty path"


def test_two_builds_match_and_cover_required_chars():
    import scripts.build_atlas as build_atlas

    out = ROOT / "assets" / "atlas" / "glyphs.json"
    build_atlas.build(out)
    first = out.read_bytes()
    build_atlas.build(out)
    second = out.read_bytes()
    assert hashlib.sha256(first).hexdigest() == hashlib.sha256(second).hexdigest()
    assert len(second) < MAX_BYTES
    assert_atlas(json.loads(second.decode("utf-8")), required_chars())


def test_deleted_char_fails():
    fixture = json.loads(
        (ROOT / "tests" / "fixtures" / "atlas_min.json").read_text(encoding="utf-8")
    )
    face = fixture["faces"]["meslo-regular"]["glyphs"]
    assert "A" in face
    del face["A"]
    try:
        assert_atlas(fixture, ["A", " "])
    except AssertionError as exc:
        assert "A" in str(exc)
    else:
        raise AssertionError("deleted char was accepted")
