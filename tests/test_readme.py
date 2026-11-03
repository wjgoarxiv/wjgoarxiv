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
    assert "Woojin Go, Ph.D." in text
    assert "Researcher and agent tool builder" in text
    assert "nameplate" in text
    assert "EOT" in text
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
