"""Path text renderer contract. Written before svgtext.py exists."""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_meslo_abc_width_is_three_advances():
    import scripts.svgtext as svgtext

    atlas = svgtext.load_atlas()
    advance = atlas["faces"]["meslo-regular"]["glyphs"]["a"]["advance"]
    assert atlas["faces"]["meslo-regular"]["glyphs"]["b"]["advance"] == advance
    assert atlas["faces"]["meslo-regular"]["glyphs"]["c"]["advance"] == advance
    assert svgtext.text_width("abc", "meslo-regular", 1000, 0) == 3 * advance


def test_render_is_paths_not_text():
    import scripts.svgtext as svgtext

    markup = svgtext.render("wjgo@lab:~$ whoami", "meslo-regular", 16, 8, 40, "#39ff88", 0)
    assert markup.startswith("<g")
    assert "<path" in markup
    assert "<text" not in markup
    assert "</g>" in markup


def test_unknown_char_names_itself():
    import scripts.svgtext as svgtext

    try:
        svgtext.render("😀", "meslo-regular", 16, 0, 0, "#c9d6e8", 0)
    except KeyError as exc:
        assert "😀" in str(exc)
    else:
        raise AssertionError("emoji was rendered")


def test_svgtext_imports_stdlib_only():
    tree = ast.parse((ROOT / "scripts" / "svgtext.py").read_text(encoding="utf-8"))
    allowed = set(sys.stdlib_module_names)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                raise AssertionError("svgtext must not use relative imports")
            names = [(node.module or "").split(".")[0]]
        else:
            continue
        foreign = [name for name in names if name not in allowed]
        assert not foreign, foreign


def test_grid_stacks_lines():
    import scripts.svgtext as svgtext

    markup = svgtext.render_grid(["ab", "c"], "meslo-regular", 16, 0, 20, "#c9d6e8", 0, 24)
    assert markup.count("<path") >= 3
    assert "<text" not in markup
