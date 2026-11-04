"""README contract: local images, public links, the five papers."""

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
README = ROOT / "README.md"
DOIS = (
    "10.1016/j.cej.2021.134098",
    "10.1016/j.energy.2019.06.025",
    "10.1016/j.fuel.2022.125479",
    "10.1016/j.apenergy.2024.123523",
    "10.1016/j.cej.2024.157251",
)
BANNED_HOSTS = ("shields.io", "vercel.app", "demolab.com", "capsule-render", "komarev.com", "wakatime")
PRIVATE = ("wjgoarxiv/claviscage", "wjgoarxiv/hysys-companion)")


def test_readme_contract():
    text = README.read_text(encoding="utf-8")
    lowered = text.lower()
    for host in BANNED_HOSTS:
        assert host not in lowered
    for doi in DOIS:
        assert doi in text
    for repo in PRIVATE:
        assert repo not in text
    for src in re.findall(r'(?:src|srcset)="([^"]+)"', text):
        assert not src.startswith("http"), src
        assert (ROOT / src).is_file(), src
    pictures = re.findall(r"<picture>.*?</picture>", text, re.DOTALL)
    assert pictures
    assert "<img" not in re.sub(r"<picture>.*?</picture>", "", text, flags=re.DOTALL)
    for pic in pictures:
        assert 'media="(prefers-color-scheme: dark)"' in pic
        assert 'media="(prefers-color-scheme: light)"' in pic
        night = re.search(r'srcset="([^"]+-night\.svg)"', pic)
        day = re.search(r'srcset="([^"]+-day\.svg)"', pic)
        img = re.search(r'<img[^>]*src="([^"]+)"', pic)
        assert night and day and img
        assert (ROOT / night.group(1)).is_file()
        assert (ROOT / day.group(1)).is_file()
        assert img.group(1) == night.group(1)
    assert "lockup-dark.svg" not in text
    assert "lockup-light.svg" not in text
    assert "whoami" in text
    assert "nameplate" in text
    assert "assets/footer-night.svg" in text
    assert "assets/footer-day.svg" in text
    assert "── EOT ──" not in text
    preview = (ROOT / "scripts" / "filmstrip.mjs").read_text(encoding="utf-8")
    assert "── EOT ──" not in preview
    assert "footer-${theme}.svg" in preview
    projects = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
    papers = json.loads((ROOT / "data" / "papers.json").read_text(encoding="utf-8"))
    for project in projects:
        for theme in ("night", "day"):
            card = f'assets/cards/{project["name"]}-{theme}.svg'
            assert card in text
            assert (ROOT / card).is_file()
        assert project["url"] in text
        assert project["name"] in text
    for paper in papers:
        for theme in ("night", "day"):
            strip = f'assets/papers/{paper["year"]}-{paper["slug"]}-{theme}.svg'
            assert strip in text
            assert (ROOT / strip).is_file()
        assert paper["url"] in text
        assert paper["title"] in text


SUMMARIES = (
    "<summary><samp>/projects/litfamily · 7</samp></summary>",
    "<summary><samp>/projects/science-mcp · 4</samp></summary>",
    "<summary><samp>/projects/env · 5</samp></summary>",
    "<summary><samp>/papers · 5</samp></summary>",
)
V1_LINKS = (
    "https://woojingo.notion.site",
    "https://scholar.google.com/citations?user=V95iNggAAAAJ",
    "https://orcid.org/0000-0003-4021-8621",
    "https://www.linkedin.com/in/woojingo/",
    "https://pypi.org/user/wjgo/",
    "https://www.researchgate.net/profile/Woojin-Go",
    "mailto:woo_go@yahoo.com",
    "https://www.buymeacoffee.com/woojingo",
)


def test_folds_badges_contrib_and_orphans():
    text = README.read_text(encoding="utf-8")
    assert len(re.findall(r"<details>", text)) == 4
    for summary in SUMMARIES:
        assert summary in text
    assert "hdr-" not in text
    assert "status-" not in text
    assert "assets/contrib-night.svg" in text
    assert "assets/contrib-day.svg" in text
    assert "https://github.com/wjgoarxiv?tab=overview" in text
    badges = json.loads((ROOT / "data" / "badges.json").read_text(encoding="utf-8"))
    for badge in badges:
        assert badge["url"] in text
        assert f'assets/badges/{badge["id"]}-night.svg' in text
        assert f'assets/badges/{badge["id"]}-day.svg' in text
    for url in V1_LINKS:
        assert url in text
    referenced = set(re.findall(r'(?:src|srcset)="([^"]+)"', text))
    for svg in (ROOT / "assets").rglob("*.svg"):
        rel = svg.relative_to(ROOT).as_posix()
        if rel.startswith("assets/atlas/") or rel.startswith("assets/brand/") or "lockup-" in rel:
            continue
        assert rel in referenced, rel


def test_badges_have_no_whitespace_gap():
    text = README.read_text(encoding="utf-8")
    paragraph = next(
        block
        for block in re.findall(r"<p\b[^>]*>.*?</p>", text, re.DOTALL)
        if "stars-night.svg" in block and "coffee-night.svg" in block
    )
    assert "<br>" in paragraph
    assert re.search(r"</a>\s+<a", paragraph) is None
    row1, row2 = paragraph.split("<br>", 1)
    order = ("stars", "followers", "release", "phd", "research")
    positions = [row1.index(f"assets/badges/{badge_id}-night.svg") for badge_id in order]
    assert positions == sorted(positions)
    assert "homepage-night.svg" not in row1
    assert "coffee-night.svg" in row2


def test_panes_have_no_whitespace_gap():
    text = README.read_text(encoding="utf-8")
    paragraph = next(
        block
        for block in re.findall(r"<p\b[^>]*>.*?</p>", text, re.DOTALL)
        if "lab-night.svg" in block and "workshop-night.svg" in block
    )
    anchors = re.findall(r"<a\b.*?</a>", paragraph, re.DOTALL)
    assert len(anchors) == 2
    between = paragraph.split(anchors[0], 1)[1].split(anchors[1], 1)[0]
    assert between == ""
    assert 'width="50%"' in anchors[0]
    assert 'width="50%"' in anchors[1]
    assert 'width="49%"' not in paragraph


CARD_ROWS = {
    "/projects/litfamily · 7": [
        [("litfamily", 100.0)],
        [("litgravity", 33.33), ("litclaude", 33.33), ("litcodex", 33.33)],
        [("litopencode", 33.33), ("lithermes", 33.33), ("litgrok", 33.33)],
    ],
    "/projects/science-mcp · 4": [
        [("ovito-mcp", 50.0), ("pymol-mcp", 50.0)],
        [("multiflash-assistant", 50.0), ("hysys-companion-releases", 50.0)],
    ],
    "/projects/env · 5": [
        [("pretty-terminal", 33.33), ("my-tmux-settings", 33.33), ("my-nvim-settings", 33.33)],
        [("proxlsx-skill", 50.0), ("publisher-docx-skill", 50.0)],
    ],
}


def _card_rows(fold):
    rows = []
    for paragraph in re.findall(r"<p\b[^>]*>.*?</p>", fold, re.DOTALL):
        if "assets/cards/" not in paragraph:
            continue
        assert re.search(r"</a>\s+<a", paragraph) is None
        row = []
        for anchor in re.findall(r"<a\b.*?</a>", paragraph, re.DOTALL):
            name = re.search(r"assets/cards/([a-z0-9-]+)-night\.svg", anchor).group(1)
            width = float(re.search(r'width="([0-9.]+)%"', anchor).group(1))
            row.append((name, width))
        rows.append(row)
    return rows


def test_card_rows_have_no_orphans():
    text = README.read_text(encoding="utf-8")
    folds = re.findall(r"<details>(.*?)</details>", text, re.DOTALL)
    seen = {}
    for fold in folds:
        summary = re.search(r"<summary><samp>([^<]+)</samp></summary>", fold)
        assert summary
        if "assets/cards/" not in fold:
            continue
        label = summary.group(1)
        rows = _card_rows(fold)
        for row in rows:
            total = sum(width for _name, width in row)
            assert 99.9 <= total <= 100.1, (label, row, total)
        seen[label] = [[name for name, _width in row] for row in rows]
        expect = [[name for name, _width in row] for row in CARD_ROWS[label]]
        assert seen[label] == expect
        for got, want in zip(rows, CARD_ROWS[label]):
            assert [width for _name, width in got] == [width for _name, width in want]
    assert set(seen) == set(CARD_ROWS)


def test_card_group_without_row_spec_raises():
    from scripts.render_cards import card_slots

    with pytest.raises(ValueError):
        card_slots([{"group": "other", "name": "x"}])


def test_footer_has_no_licence_line():
    text = README.read_text(encoding="utf-8")
    assert "Outlined glyphs" not in text
    assert 'href="LICENSES/"' not in text
    assert (ROOT / "LICENSES" / "Pretendard-OFL.txt").is_file()
    atlas = json.loads((ROOT / "assets" / "atlas" / "glyphs.json").read_text(encoding="utf-8"))
    capital_o = atlas["faces"]["meslo-regular"]["glyphs"]["O"]["d"]
    for theme in ("night", "day"):
        svg = (ROOT / "assets" / f"footer-{theme}.svg").read_text(encoding="utf-8")
        assert "<text" not in svg.lower()
        assert 'width="280"' in svg and 'height="28"' in svg
        assert capital_o not in svg


def test_shields_in_a_copy_fails(tmp_path):
    bad = README.read_text(encoding="utf-8") + "\nhttps://img.shields.io/x\n"
    assert "shields.io" in bad.lower()
    try:
        for host in BANNED_HOSTS:
            if host in bad.lower():
                raise AssertionError(host)
    except AssertionError:
        return
    raise AssertionError("shields host was accepted")
