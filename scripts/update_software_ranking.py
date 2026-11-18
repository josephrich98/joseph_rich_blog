#!/usr/bin/env python3
"""Rank the /software/ entries by GitHub stars + website visits.

Reads site/_data/software.yml, fetches each entry's GitHub stars and GoatCounter
all-time visits, and writes site/_data/software_ranking.json, which
_pages/software.html uses to order the entries.

Score
-----
    score = stars + visits / VISITS_PER_STAR

A star is a deliberate act, a visit is not: across GitHub, roughly 1% of a
repository's visitors star it, so one star is treated as worth ~100 visits.
Stars come from every repo in `repos` (or the single `repo`), plus `stars_repo`
for entries that deliberately show no stars badge. Visits come from every
GoatCounter site in `goatcounter` (a code or a list of codes).

If a count cannot be fetched (rate limit, private repo without a token, network
error) the value from the previous snapshot is kept, so a transient failure never
demotes an entry.

The JSON is rewritten only when the order changes (or with --force), so the
weekly GitHub Action commits — and Vercel redeploys — only when the page would
actually look different.

Usage:
    python scripts/update_software_ranking.py [--force] [--dry-run]

Set GITHUB_TOKEN (or have `gh` authenticated) to read private repos and avoid
the 60-request/hour unauthenticated limit.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

VISITS_PER_STAR = 100

ROOT = Path(__file__).resolve().parents[1]
SOFTWARE_YML = ROOT / "site" / "_data" / "software.yml"
RANKING_JSON = ROOT / "site" / "_data" / "software_ranking.json"


def _token() -> str | None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    if shutil.which("gh"):
        out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    return None


def _get_json(url: str, headers: dict[str, str] | None = None) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "software-ranking", **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def fetch_stars(repo: str, token: str | None) -> int | None:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        return int(_get_json(f"https://api.github.com/repos/{repo}", headers)["stargazers_count"])
    except (urllib.error.URLError, KeyError, ValueError, TimeoutError) as exc:
        print(f"  warning: stars for {repo} unavailable ({exc})", file=sys.stderr)
        return None


def fetch_visits(code: str) -> int | None:
    try:
        data = _get_json(f"https://{code}.goatcounter.com/counter/TOTAL.json")
        # GoatCounter formats with a thin/regular space as thousands separator.
        return int("".join(ch for ch in str(data["count"]) if ch.isdigit()))
    except (urllib.error.URLError, KeyError, ValueError, TimeoutError) as exc:
        print(f"  warning: visits for {code} unavailable ({exc})", file=sys.stderr)
        return None


def _as_list(value) -> list[str]:
    if not value:
        return []
    return [value] if isinstance(value, str) else list(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--force", action="store_true", help="rewrite the snapshot even if the order is unchanged")
    parser.add_argument("--dry-run", action="store_true", help="print the ranking without writing it")
    args = parser.parse_args()

    items = yaml.safe_load(SOFTWARE_YML.read_text())
    previous = json.loads(RANKING_JSON.read_text()) if RANKING_JSON.exists() else {}
    prev_stars = previous.get("stars", {})
    prev_visits = previous.get("visits", {})
    token = _token()

    stars_cache: dict[str, int] = {}
    visits_cache: dict[str, int] = {}
    entries = []
    for index, item in enumerate(items):
        repos = _as_list(item.get("repos")) or _as_list(item.get("repo"))
        repos += [r for r in _as_list(item.get("stars_repo")) if r not in repos]
        sites = _as_list(item.get("goatcounter"))

        for repo in repos:
            if repo not in stars_cache:
                value = fetch_stars(repo, token)
                stars_cache[repo] = value if value is not None else int(prev_stars.get(repo, 0))
        for site in sites:
            if site not in visits_cache:
                value = fetch_visits(site)
                visits_cache[site] = value if value is not None else int(prev_visits.get(site, 0))

        stars = sum(stars_cache[r] for r in repos)
        visits = sum(visits_cache[s] for s in sites)
        score = stars + visits / VISITS_PER_STAR
        entries.append({"title": item["title"], "stars": stars, "visits": visits,
                        "score": round(score, 1), "_index": index})

    # Ties keep the order they have in software.yml.
    entries.sort(key=lambda e: (-e["score"], e["_index"]))
    for e in entries:
        del e["_index"]

    print(f"{'score':>8} {'stars':>6} {'visits':>7}  title")
    for e in entries:
        print(f"{e['score']:>8} {e['stars']:>6} {e['visits']:>7}  {e['title']}")

    order = [e["title"] for e in entries]
    if args.dry_run:
        return 0
    if order == previous.get("order") and not args.force:
        print("Order unchanged; snapshot left as is.")
        return 0

    snapshot = {
        "_comment": "Generated by scripts/update_software_ranking.py; do not edit by hand. "
                    f"score = stars + visits / {VISITS_PER_STAR}.",
        "updated": dt.date.today().isoformat(),
        "order": order,
        "entries": entries,
        "stars": dict(sorted(stars_cache.items())),
        "visits": dict(sorted(visits_cache.items())),
    }
    RANKING_JSON.write_text(json.dumps(snapshot, indent=2) + "\n")
    print(f"Wrote {RANKING_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
