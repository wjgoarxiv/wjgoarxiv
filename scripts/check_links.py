"""Check README links. doi.org may answer 403 to bots."""

import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

OK = {200, 301, 302, 303, 307, 308}
DOI_OK = OK | {403}
# Badge hrefs, the contribution overview, and these profile URLs are checked below.
# These exact profile URLs are required, and this client is refused.
BOT_WALL = {
    "https://scholar.google.com/citations?user=V95iNggAAAAJ": {404},
    "https://www.linkedin.com/in/woojingo/": {999, 403, 405},
    "https://www.researchgate.net/profile/Woojin-Go": {403},
}


def urls_in(text):
    found = re.findall(r"https?://[^\s)>\"]+", text)
    seen = []
    for url in found:
        url = url.rstrip(".,;")
        if url not in seen:
            seen.append(url)
    return seen


def status_of(url):
    request = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": "wjgoarxiv-profile-linkcheck"},
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 405, 501):
            get = urllib.request.Request(url, headers={"User-Agent": "wjgoarxiv-profile-linkcheck"})
            try:
                with urllib.request.urlopen(get, timeout=25) as resp:
                    return resp.status
            except urllib.error.HTTPError as get_exc:
                return get_exc.code
        return exc.code


def main(argv=None):
    path = Path(argv[1] if argv and len(argv) > 1 else "README.md")
    text = path.read_text(encoding="utf-8")
    failed = False
    for url in urls_in(text):
        code = status_of(url)
        allowed = DOI_OK if "doi.org" in url else OK
        bot = code in BOT_WALL.get(url, set())
        mark = "ok" if code in allowed else "FAIL"
        if "doi.org" in url and code == 403:
            mark = "ok-doi-403"
        if bot and mark == "FAIL":
            mark = "bot-wall"
        print(f"{mark}\t{code}\t{url}")
        if mark == "FAIL":
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
