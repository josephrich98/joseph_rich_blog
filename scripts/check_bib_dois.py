#!/usr/bin/env python3
"""Validate the DOIs in one or more BibTeX files.

Given a list of ``.bib`` file paths, this parses each BibTeX entry, pulls out
its ``doi`` field, and confirms the DOI actually resolves to a real record --
the same "does this citation exist?" check that doi2bib performs.

doi2bib.org itself is a browser-only single-page app with no scriptable bib
endpoint (``api.doi2bib.org`` no longer resolves), so under the hood it -- like
this script -- relies on DOI content negotiation: a GET to
``https://doi.org/<DOI>`` with ``Accept: application/x-bibtex`` returns the
BibTeX record for a valid DOI and an error for an unknown one. That is the
authoritative source doi2bib wraps.

Exit status:
    0  every DOI resolved (or could not be verified due to a network problem,
       unless BIB_CHECK_STRICT=1)
    1  at least one DOI is invalid, or (with BIB_CHECK_STRICT=1) unverifiable

Entries with no ``doi`` field are reported as warnings but do not fail the
check -- website / ``@misc`` references legitimately have no DOI.

Environment:
    BIB_CHECK_STRICT=1   treat "could not verify" (network/timeout) as failure
"""

from __future__ import annotations

import os
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import quote

TIMEOUT = 30  # seconds per DOI lookup
USER_AGENT = "joseph-rich-blog-precommit/1.0 (mailto:josephrich98@gmail.com)"

# Matches a BibTeX entry header: @article{key,  ->  captures (type, key) and
# the offset so we can slice out the entry body up to the next header.
ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s}]+)\s*,", re.IGNORECASE)
# doi = {10.x/y} | doi = "10.x/y" | doi = 10.x/y  (anywhere in the entry body,
# whether the field is on its own line or inline). \bdoi avoids matching the
# tail of fields like "eprintdoi".
DOI_RE = re.compile(
    r'(?i)\bdoi\s*=\s*(?:\{([^{}]+)\}|"([^"]+)"|([^,}\s]+))'
)


class Entry:
    __slots__ = ("kind", "key", "doi", "line")

    def __init__(self, kind: str, key: str, doi: str | None, line: int):
        self.kind = kind
        self.key = key
        self.doi = doi
        self.line = line


def parse_entries(text: str) -> list[Entry]:
    """Extract (type, key, doi, line-number) for every entry in a .bib file."""
    entries: list[Entry] = []
    matches = list(ENTRY_RE.finditer(text))
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end]
        doi_match = DOI_RE.search(body)
        doi = None
        if doi_match:
            doi = next(g for g in doi_match.groups() if g is not None).strip()
        line = text.count("\n", 0, start) + 1
        entries.append(Entry(m.group(1), m.group(2), doi, line))
    return entries


def resolve_doi(doi: str) -> tuple[str, str]:
    """Return (status, detail) for a DOI.

    status is one of: 'ok', 'invalid', 'unverified'.
    """
    # DOIs may contain characters that need escaping in a URL path, but the
    # slash separating prefix/suffix must be preserved.
    url = "https://doi.org/" + quote(doi, safe="/:")
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/x-bibtex", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", "replace").strip()
        if resp.status == 200 and body.startswith("@"):
            return "ok", ""
        return "invalid", f"unexpected response (HTTP {resp.status})"
    except urllib.error.HTTPError as e:
        return "invalid", f"HTTP {e.code} from doi.org (DOI not found)"
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return "unverified", f"could not reach doi.org: {e}"


def check_file(path: str) -> tuple[int, int, int]:
    """Validate one .bib file. Returns (n_invalid, n_unverified, n_missing)."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        print(f"  ✗ cannot read {path}: {e}", file=sys.stderr)
        return 1, 0, 0

    entries = parse_entries(text)
    print(f"{path}: {len(entries)} entr{'y' if len(entries) == 1 else 'ies'}")

    n_invalid = n_unverified = n_missing = 0
    for e in entries:
        label = f"{e.kind}:{e.key} (line {e.line})"
        if not e.doi:
            print(f"  ⚠ {label}: no DOI field — skipped", file=sys.stderr)
            n_missing += 1
            continue
        status, detail = resolve_doi(e.doi)
        if status == "ok":
            print(f"  ✓ {label}: {e.doi}")
        elif status == "invalid":
            print(f"  ✗ {label}: {e.doi} — {detail}", file=sys.stderr)
            n_invalid += 1
        else:  # unverified
            print(f"  ? {label}: {e.doi} — {detail}", file=sys.stderr)
            n_unverified += 1
    return n_invalid, n_unverified, n_missing


def main(argv: list[str]) -> int:
    paths = argv[1:]
    if not paths:
        print("usage: check_bib_dois.py <file.bib> [file.bib ...]", file=sys.stderr)
        return 2

    strict = os.environ.get("BIB_CHECK_STRICT") == "1"
    total_invalid = total_unverified = total_missing = 0
    for path in paths:
        inv, unv, mis = check_file(path)
        total_invalid += inv
        total_unverified += unv
        total_missing += mis

    if total_missing:
        print(f"\n{total_missing} entr"
              f"{'y' if total_missing == 1 else 'ies'} had no DOI (not checked).",
              file=sys.stderr)
    if total_unverified:
        print(f"{total_unverified} DOI(s) could not be verified "
              f"(network issue){' — failing due to BIB_CHECK_STRICT' if strict else ''}.",
              file=sys.stderr)
    if total_invalid:
        print(f"\n{total_invalid} invalid DOI(s) found.", file=sys.stderr)
        return 1
    if strict and total_unverified:
        return 1

    print("\nAll DOIs valid." if paths else "")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
