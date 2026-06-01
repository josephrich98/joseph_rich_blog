#!/usr/bin/env python3
"""Sync blog posts from posts/<name>/main.md into site/_posts/.

Each post lives in its own directory under posts/ (alongside its notebook,
figures, and the per-post Dockerfile/environment.yml). The written article is
posts/<name>/main.md, authored in pandoc/Eisvogel Markdown so it can also be
rendered to PDF. This script converts each main.md into a Jekyll blog post at
site/_posts/YYYY-MM-DD-<name>.md so it shows up on the website.

It is idempotent: re-running regenerates the same output. It is invoked
automatically by the committed pre-commit hook (.githooks/pre-commit), and can
also be run by hand:

    python3 scripts/sync_posts.py

What it does per post:
  * reads the YAML front matter (title, date required; excerpt, tags, toc
    optional) and maps it to Jekyll blog front matter,
  * drops pandoc/Eisvogel-only keys (titlepage, colorlinks, listings, ...),
  * copies figures/ images into site/images/posts/<name>/ and rewrites the
    Markdown image paths to point there,
  * rewrites inline math $...$ into kramdown's $$...$$ delimiters (display
    $$...$$ blocks and fenced code are left untouched) so MathJax renders it.

Directories named "template" are skipped (scaffold, not a real post).
"""

from __future__ import annotations

import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "posts")
OUT_DIR = os.path.join(ROOT, "site", "_posts")
IMG_ROOT = os.path.join(ROOT, "site", "images", "posts")

SKIP_DIRS = {"template"}
# Base URL of the GitHub repo, used for the "reproduce" footer link on each post.
REPO_URL = "https://github.com/josephrich98/joseph_rich_blog"
# pandoc/Eisvogel-only front matter keys that must not leak into the blog post
PANDOC_ONLY = {
    "author", "titlepage", "toc-own-page", "colorlinks", "linkcolor",
    "urlcolor", "listings", "titlepage-color", "titlepage-text-color",
    "titlepage-rule-color", "book", "classoption", "geometry", "fontsize",
    "mainfont", "header-includes",
}

GENERATED_MARKER = (
    "<!-- Generated from posts/{name}/main.md by scripts/sync_posts.py. "
    "Do not edit here; edit the source and re-commit. -->"
)


def parse_front_matter(text):
    """Return (front_matter_dict, body). Minimal YAML: scalars + simple lists."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip("\n")
    body = text[end + 4:]
    if body.startswith("\n"):
        body = body[1:]

    fm = {}
    current_list_key = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        # list item belonging to the previous "key:" line
        m = re.match(r"^(\s*)-\s+(.*)$", line)
        if m and current_list_key:
            fm[current_list_key].append(_unquote(m.group(2).strip()))
            continue
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val == "":
            fm[key] = []
            current_list_key = key
        else:
            fm[key] = _unquote(val)
            current_list_key = None
    return fm, body


def _unquote(v):
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def split_code_fences(body):
    """Yield (is_code, segment) chunks, splitting on ``` fenced blocks."""
    parts = re.split(r"(```.*?\n.*?```)", body, flags=re.DOTALL)
    for part in parts:
        yield part.startswith("```"), part


def fix_footnote_continuations(body):
    """Indent the continuation lines of multi-line footnote definitions.

    Pandoc accepts an unindented continuation under ``[^id]: ...``, but kramdown
    keeps only the first line unless the rest is indented — so multi-line
    footnotes get truncated. Indent each continuation line (up to the next blank
    line) by four spaces. Lines inside fenced code blocks are left alone."""
    out = []
    in_code = False
    in_footnote = False
    for line in body.split("\n"):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            in_footnote = False
            out.append(line)
        elif in_code:
            out.append(line)
        elif re.match(r"^\[\^[^\]]+\]:", line):
            in_footnote = True
            out.append(line)
        elif in_footnote and line.strip() == "":
            in_footnote = False
            out.append(line)
        elif in_footnote and not line[:1].isspace():
            out.append("    " + line)
        else:
            out.append(line)
    return "\n".join(out)


def inline_math_to_kramdown(body):
    """Convert pandoc inline $...$ to kramdown $$...$$, leaving $$ blocks and
    fenced code untouched. kramdown needs $$ delimiters and does not parse
    Markdown inside them, which protects subscripts like $a_b$ from emphasis.

    Inline math may be line-wrapped in the source (a single newline inside the
    $...$), so the content matches across single newlines but stops at a blank
    line (paragraph break) and never crosses a $, which keeps $$ display blocks
    untouched."""
    out = []
    for is_code, seg in split_code_fences(body):
        if is_code:
            out.append(seg)
            continue
        seg = re.sub(
            r"(?<![\$\\])\$(?!\$)((?:[^\n$]|\n(?!\n))+?)(?<!\\)\$(?!\$)",
            r"$$\1$$",
            seg,
        )
        out.append(seg)
    return "".join(out)


def sync_post(name):
    src_dir = os.path.join(POSTS_DIR, name)
    main_md = os.path.join(src_dir, "main.md")
    if not os.path.isfile(main_md):
        return None

    with open(main_md, encoding="utf-8") as f:
        text = f.read()
    fm, body = parse_front_matter(text)

    title = fm.get("title")
    date = fm.get("date")
    if not title or not date:
        print(f"  skip {name}: missing title or date in front matter", file=sys.stderr)
        return None
    date = str(date)[:10]
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", date)
    if not m:
        print(f"  skip {name}: date '{date}' is not YYYY-MM-DD", file=sys.stderr)
        return None
    year, month = m.group(1), m.group(2)

    # Copy figures and rewrite image paths to /images/posts/<name>/...
    dest_img = os.path.join(IMG_ROOT, name)
    body, copied = rewrite_images(body, src_dir, dest_img, name)

    body = fix_footnote_continuations(body)
    body = inline_math_to_kramdown(body)

    # Boilerplate footer linking to the post's source folder (notebook, data,
    # scripts) so readers can reproduce the analyses.
    body = body.rstrip("\n") + (
        f"\n\n---\n\n*Reproduce all analyses in this post "
        f"[here]({REPO_URL}/tree/main/posts/{name}).*\n"
    )

    # Build Jekyll front matter
    out_fm = ['---']
    out_fm.append(f'title: "{title}"')
    out_fm.append(f"date: {date}")
    out_fm.append(f"permalink: /posts/{year}/{month}/{name}/")
    if fm.get("excerpt"):
        out_fm.append(f'excerpt: "{fm["excerpt"]}"')
    tags = fm.get("tags")
    if isinstance(tags, list) and tags:
        out_fm.append("tags:")
        out_fm.extend(f"  - {t}" for t in tags)
    if str(fm.get("toc", "")).lower() == "true":
        out_fm.append("toc: true")
    out_fm.append("comments: true")
    out_fm.append("---")

    content = "\n".join(out_fm) + "\n" + GENERATED_MARKER.format(name=name) + "\n\n" + body
    if not content.endswith("\n"):
        content += "\n"

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, f"{date}-{name}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.relpath(out_path, ROOT), copied


def rewrite_images(body, src_dir, dest_img, name):
    """Copy referenced local images into dest_img and rewrite their paths."""
    copied = 0
    made_dir = False

    def repl(match):
        nonlocal copied, made_dir
        alt, path = match.group(1), match.group(2).strip()
        if "://" in path or path.startswith("/"):
            return match.group(0)  # external or already-absolute
        src_file = os.path.join(src_dir, path)
        if not os.path.isfile(src_file):
            return match.group(0)
        if not made_dir:
            os.makedirs(dest_img, exist_ok=True)
            made_dir = True
        fname = os.path.basename(path)
        shutil.copy2(src_file, os.path.join(dest_img, fname))
        copied += 1
        return f"![{alt}](/images/posts/{name}/{fname})"

    # ![alt](path) — alt may span lines, so use DOTALL on the alt group
    body = re.sub(r"!\[(.*?)\]\(([^)]+)\)", repl, body, flags=re.DOTALL)
    return body, copied


def main():
    if not os.path.isdir(POSTS_DIR):
        print("no posts/ directory; nothing to sync")
        return 0
    total = 0
    for name in sorted(os.listdir(POSTS_DIR)):
        if name in SKIP_DIRS or name.startswith("."):
            continue
        if not os.path.isdir(os.path.join(POSTS_DIR, name)):
            continue
        result = sync_post(name)
        if result:
            out_path, copied = result
            print(f"  synced {name} -> {out_path} ({copied} image(s))")
            total += 1
    print(f"sync_posts: wrote {total} post(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
