"""Fetch stars, followers, release and the contribution calendar. Stdlib urllib only."""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USER = "wjgoarxiv"
API = "https://api.github.com"
LITFAMILY = (
    "litfamily",
    "litgravity",
    "litclaude",
    "litcodex",
    "litopencode",
    "lithermes",
    "litgrok",
)
QUERY = (
    "query { user(login: \"wjgoarxiv\") { contributionsCollection { contributionCalendar "
    "{ weeks { contributionDays { contributionCount date } } } } } }"
)
LIVE_FIXTURE = ROOT / "tests" / "fixtures" / "live.json"
CONTRIB_FIXTURE = ROOT / "tests" / "fixtures" / "contrib.json"


def _token():
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def _request(url, token, payload=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "wjgoarxiv-profile",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    body = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8")), response.headers


def _repos(api, token):
    url = f"{api}/users/{USER}/repos?per_page=100&type=owner"
    found = []
    while url:
        payload, headers = _request(url, token)
        if not isinstance(payload, list):
            raise RuntimeError("repo list was not a list")
        found.extend(payload)
        url = None
        for part in (headers.get("Link") or "").split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
    return found


def _release(api, token, public):
    best = None
    for name in LITFAMILY:
        try:
            payload, _headers = _request(f"{api}/repos/{USER}/{name}/releases/latest", token)
        except urllib.error.HTTPError:
            continue
        tag = payload.get("tag_name") or ""
        published = payload.get("published_at") or ""
        if tag and (best is None or published > best[0]):
            best = (published, tag)
    if best:
        return best[1]
    family = [repo for repo in public if repo.get("name") in LITFAMILY]
    pool = family or public
    picked = max(pool, key=lambda repo: repo.get("pushed_at") or "")
    return f"{picked.get('name')} {(picked.get('pushed_at') or '')[:10]}"


def _calendar(api, token):
    payload, _headers = _request(f"{api}/graphql", token, {"query": QUERY})
    if payload.get("errors"):
        raise RuntimeError("contribution calendar failed")
    weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    grid = []
    dates = []
    for week in weeks:
        days = list(week["contributionDays"])
        counts = [int(day["contributionCount"]) for day in days]
        stamps = [day["date"] for day in days]
        if len(counts) < 7 and stamps:
            missing = 7 - len(counts)
            first = date.fromisoformat(stamps[0])
            stamps = [(first - timedelta(days=missing - index)).isoformat() for index in range(missing)] + stamps
            counts = [0] * missing + counts
        grid.append(counts[:7])
        dates.append(stamps[:7])
    if not grid:
        raise RuntimeError("empty contribution calendar")
    return {"weeks": grid, "dates": dates}


def fetch(api, token):
    if not token:
        raise RuntimeError("missing token")
    repos = _repos(api, token)
    public = [repo for repo in repos if not repo.get("private") and not repo.get("fork")]
    if not public:
        raise RuntimeError("no public repos")
    user, headers = _request(f"{api}/users/{USER}", token)
    updated = date.today().isoformat()
    raw_date = headers.get("Date") if headers else None
    if raw_date:
        updated = parsedate_to_datetime(raw_date).date().isoformat()
    last = max(public, key=lambda repo: repo.get("pushed_at") or "")
    live = {
        "stars": sum(int(repo.get("stargazers_count") or 0) for repo in public),
        "followers": int(user.get("followers") or 0),
        "release": _release(api, token, public),
        "last_push": (last.get("pushed_at") or "")[:10],
        "updated": updated,
    }
    return live, _calendar(api, token)


def _write_pair(out, live, contrib):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    live_text = json.dumps(live, indent=2) + "\n"
    contrib_text = json.dumps(contrib) + "\n"
    for name, text in (("live.json", live_text), ("contrib.json", contrib_text)):
        dest = out / name
        tmp = dest.with_suffix(dest.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, dest)


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--out", default=str(ROOT / "data"))
    parser.add_argument("--api-base", default=os.environ.get("GITHUB_API", API))
    args = parser.parse_args(argv)
    try:
        if args.fixture:
            live = json.loads(LIVE_FIXTURE.read_text(encoding="utf-8"))
            contrib = json.loads(CONTRIB_FIXTURE.read_text(encoding="utf-8"))
        else:
            live, contrib = fetch(args.api_base.rstrip("/"), _token())
        _write_pair(args.out, live, contrib)
        total = sum(count for week in contrib["weeks"] for count in week)
        print(f"stars {live['stars']}")
        print(f"followers {live['followers']}")
        print(f"contributions {total}")
        return 0
    except Exception as exc:
        if isinstance(exc, urllib.error.HTTPError):
            print(f"fetch failed: HTTP {exc.code}", file=sys.stderr)
        else:
            print(f"fetch failed: {type(exc).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
