"""Render the status strip from a fixture or the public GitHub API. Stdlib only."""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date
from email.utils import parsedate_to_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crt

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "assets" / "status.svg"
API = "https://api.github.com"
PHD = date(2023, 8, 1)
LITFAMILY = (
    "litfamily",
    "litgravity",
    "litclaude",
    "litcodex",
    "litopencode",
    "lithermes",
    "litgrok",
)
W, H = 1200, 72


def status_line(model):
    updated = date.fromisoformat(model["updated"])
    pushed = date.fromisoformat(model["last_push"])
    uptime = (updated - PHD).days
    return (
        f"SYS ▸ LAB ● online   WORK ● online   │ latest {model['latest']}"
        f"  │ ★ {model['stars']}  │ last push {model['last_push']}"
        f"  │ up {uptime}d  │ updated {model['updated']}"
    )


def _stale(model):
    updated = date.fromisoformat(model["updated"])
    pushed = date.fromisoformat(model["last_push"])
    return (updated - pushed).days > 30


def _short_rel(latest):
    parts = str(latest).split()
    if len(parts) == 2 and len(parts[1]) >= 10 and parts[1][4:5] == "-":
        return f"REL {parts[0]} {parts[1][5:10]}"
    return f"REL {latest}"


def render_svg(model):
    stale = _stale(model)
    updated = date.fromisoformat(model["updated"])
    uptime = (updated - PHD).days
    push = model["last_push"][5:10]
    cells = (
        ("SYS", crt.TEXT),
        ("LAB ● ON", crt.LAB),
        ("WORK ● ON", crt.WORK),
        (_short_rel(model["latest"]), crt.TEXT),
        (f"★ {model['stars']}", crt.TEXT),
        (f"PUSH {push}", crt.WARN if stale else crt.TEXT),
        (f"UP {uptime}d", crt.TEXT),
        (f"UPD {model['updated']}", crt.TEXT),
    )
    size = 15
    x = 10
    bits = [crt.svg_open(W, H), crt.DEFS, crt.screen(W, H), crt.ticks(W, H, crt.GRID)]
    for label, fill in cells:
        cell_w = crt.width(label, "meslo-regular", size) + 18
        bits.append(f'<rect x="{x:.1f}" y="16" width="{cell_w:.1f}" height="40" fill="none" stroke="#3d5c7a"/>')
        bits.append(crt.text(label, "meslo-regular", size, x + 8, 42, fill))
        x += cell_w + 6
    bits.append("</svg>")
    return "".join(bits)


def render_file(fixture, out):
    model = json.loads(Path(fixture).read_text(encoding="utf-8"))
    _write(out, render_svg(model))


def _write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _token():
    return os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""


def _get(url, token):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "wjgoarxiv-profile-status",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
        return payload, resp.headers


def _repos(api, token):
    url = f"{api}/users/wjgoarxiv/repos?per_page=100&type=owner"
    found = []
    headers = None
    while url:
        payload, headers = _get(url, token)
        if not isinstance(payload, list):
            raise ValueError("repo list was not a list")
        found.extend(payload)
        url = None
        link = headers.get("Link") or ""
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
    return found, headers


def fetch_live(api, token):
    if not token:
        raise RuntimeError("missing token")
    repos, headers = _repos(api, token)
    public = [repo for repo in repos if not repo.get("private") and not repo.get("fork")]
    if not public:
        raise RuntimeError("no public repos")
    stars = sum(int(repo.get("stargazers_count") or 0) for repo in public)
    last = max(public, key=lambda repo: repo.get("pushed_at") or "")
    last_push = (last.get("pushed_at") or "")[:10]
    latest = None
    try:
        release, _ = _get(f"{api}/repos/wjgoarxiv/litgravity/releases/latest", token)
        latest = release.get("tag_name")
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
    if not latest:
        family = [repo for repo in public if repo.get("name") in LITFAMILY]
        pool = family or public
        picked = max(pool, key=lambda repo: repo.get("pushed_at") or "")
        latest = f"{picked.get('name')} {(picked.get('pushed_at') or '')[:10]}"
    updated = None
    raw_date = headers.get("Date") if headers else None
    if raw_date:
        updated = parsedate_to_datetime(raw_date).date().isoformat()
    if not updated:
        updated = last_push
    return {
        "latest": latest,
        "stars": stars,
        "last_push": last_push,
        "updated": updated,
    }


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--api-base", default=os.environ.get("GITHUB_API", API))
    args = parser.parse_args(argv)
    try:
        if args.fixture:
            render_file(args.fixture, args.out)
            return 0
        model = fetch_live(args.api_base.rstrip("/"), _token())
        _write(args.out, render_svg(model))
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    sys.exit(main())
