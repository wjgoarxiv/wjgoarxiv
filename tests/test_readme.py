"""README contract: local images, public links, the five papers."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
