#!/usr/bin/env python3
"""Sync blog posts from posts/<name>/main.md into site/_posts/.

Each post lives in its own directory under posts/ (alongside its notebook,
figures, and the per-post Dockerfile/environment.yml). The directory is named
either <slug> or <YYYY-MM-DD>-<slug> (the latter mirrors the site/_posts naming
so both trees sort chronologically); the leading date, if present, is stripped
to recover the slug. The written article is posts/<name>/main.md, authored in
pandoc/Eisvogel Markdown so it can also be rendered to PDF. This script converts
each main.md into a Jekyll blog post at site/_posts/YYYY-MM-DD-<slug>.md (the
date coming from the front matter) so it shows up on the website.

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
    $$...$$ blocks and fenced code are left untouched) so MathJax renders it,
  * resolves pandoc [@key] citations against the post's references.bib (if any)
    by rendering them once with pandoc + citeproc, splicing the numbered inline
    markers into the body and appending the formatted reference list at the
    bottom (see resolve_citations).

Directories named "template" are skipped (scaffold, not a real post).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
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
    # citation/bibliography keys: consumed by pandoc + citeproc for the PDF and,
    # via resolve_citations, for the web — never emitted into Jekyll front matter.
    "bibliography", "csl", "link-citations", "reference-section-title", "nocite",
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


def pad_display_math(body):
    """Surround standalone $$...$$ display-math blocks with blank lines.

    Pandoc renders a $$...$$ block as display math even when it is glued to the
    surrounding text, but kramdown only treats it as display ($$\\[...\\]$$)
    rather than inline ($$\\(...\\)$$) when the block stands alone as its own
    paragraph. So a block written pandoc-style::

        ...both can differ:
        $$
        P(X, Y) \\neq Q(X, Y).
        $$
        Decompose it...

    must get a blank line before the opening ``$$`` and after the closing
    ``$$``. Only lines that are exactly ``$$`` are delimiters (inline math is
    ``$$...$$`` with text on the same line); fenced code is left untouched."""
    out = []
    in_code = False
    in_display = False
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        if not in_code and stripped == "$$":
            if not in_display:  # opening delimiter
                if out and out[-1].strip() != "":
                    out.append("")
                out.append(line)
                in_display = True
            else:  # closing delimiter
                out.append(line)
                out.append("")
                in_display = False
            continue
        out.append(line)
    return "\n".join(out)


# A pandoc inline-citation span in citeproc HTML output, e.g.
#   <span class="citation" data-cites="zech2018">...</span>
# The data-cites attribute holds the space-separated keys (in source order); the
# inner HTML is the fully-rendered marker (<sup><a href="#ref-...">1</a></sup>).
CITATION_SPAN_RE = re.compile(
    r'<span class="citation"[^>]*\bdata-cites="([^"]*)"[^>]*>(.*?)</span>',
    re.DOTALL,
)
# The formatted reference list pandoc appends; it is the last block of the
# fragment, so a greedy match to the final </div> captures the whole thing.
REFS_DIV_RE = re.compile(r'<div id="refs".*</div>', re.DOTALL)
# A bracketed pandoc citation in the source, e.g. [@key] or [@k1; @k2]. Requires
# an @ so it never matches footnote refs ([^id]) or ordinary links.
CITATION_BRACKET_RE = re.compile(r"\[[^\]]*@[^\]]*\]")
# A single citekey following @ (pandoc's permitted citekey characters).
CITEKEY_RE = re.compile(r"@([A-Za-z0-9_][\w:.#$%&+?<>~/-]*)")


def resolve_citations(name, src_dir, body):
    """Resolve pandoc ``[@key]`` citations for the web build.

    Returns ``(body, bib_html)``: ``body`` with every inline ``[@key]`` marker
    replaced by its fully-rendered HTML, and ``bib_html`` the ``<div id="refs">``
    reference list to append at the bottom (``None`` when the post has no
    ``references.bib``).

    The numbering, grouping and range-collapsing are delegated to pandoc +
    citeproc so the web markers match the PDF exactly: pandoc renders the post to
    HTML once, and we harvest each citation's rendered form (keyed by its
    ``data-cites`` keys) and the formatted bibliography. Both are self-contained
    HTML (superscript links, ``<em>``, ``<a href>``) that kramdown passes through
    verbatim, so the inline ``$…$`` math and image rewriting downstream are
    unaffected. The bibliography/csl paths come from the main.md front matter,
    resolved relative to the post directory (pandoc runs there).
    """
    if not os.path.isfile(os.path.join(src_dir, "references.bib")):
        return body, None

    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError(
            f"{name}: references.bib is present but pandoc is not on PATH; "
            f"pandoc resolves the [@key] citations for the web build (it is "
            f"pinned in the post's environment.yml)."
        )

    proc = subprocess.run(
        [pandoc, "main.md", "--citeproc", "--to", "html", "--wrap=none"],
        cwd=src_dir,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{name}: pandoc citeproc failed:\n{proc.stderr}")
    # citeproc reports an undefined key only as a warning (exit 0) and renders it
    # as bold literal text; treat that as fatal so a typo'd [@key] never ships.
    if "not found" in proc.stderr.lower():
        raise RuntimeError(
            f"{name}: unresolved citation — every [@key] must have a matching "
            f"entry in references.bib:\n{proc.stderr.strip()}"
        )
    html = proc.stdout

    rendered = {
        tuple(cites.split()): inner.strip()
        for cites, inner in CITATION_SPAN_RE.findall(html)
    }
    refs_match = REFS_DIV_RE.search(html)
    bib_html = refs_match.group(0) if refs_match else None

    def replace_in(segment):
        def repl(match):
            keys = tuple(CITEKEY_RE.findall(match.group(0)))
            # Leave anything we didn't render (e.g. a [@...] inside inline code)
            # untouched rather than dropping it.
            return rendered.get(keys, match.group(0))
        return CITATION_BRACKET_RE.sub(repl, segment)

    # Skip fenced code blocks so a literal [@key] in an example stays literal.
    body = "".join(
        seg if is_code else replace_in(seg)
        for is_code, seg in split_code_fences(body)
    )
    return body, bib_html


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

    # The post directory is named "<YYYY-MM-DD>-<slug>" (mirroring the generated
    # site/_posts/<YYYY-MM-DD>-<slug>.md so both trees sort chronologically); a
    # bare "<slug>" with no date prefix is still accepted. The full directory
    # name (`name`) is what the post is known by — it names the output file and
    # the site/images/posts/<name>/ figure folder. The date is stripped only to
    # form the `slug` used in the (dateless) permalink URL.
    dm = re.match(r"^\d{4}-\d{2}-\d{2}-(.+)$", name)
    slug = dm.group(1) if dm else name

    # Resolve [@key] citations against references.bib (if any) before the other
    # transforms; bib_html (the formatted reference list) is appended at the end.
    body, bib_html = resolve_citations(name, src_dir, body)

    # Copy figures and rewrite image paths to /images/posts/<name>/...
    dest_img = os.path.join(IMG_ROOT, name)
    body, copied = rewrite_images(body, src_dir, dest_img, name)

    body = fix_footnote_continuations(body)
    body = inline_math_to_kramdown(body)
    body = pad_display_math(body)

    body = body.rstrip("\n")

    # Reference list (rendered by pandoc from references.bib) at the bottom of
    # the article, above the reproduce footer. The <div id="refs"> block is
    # self-contained HTML, which kramdown passes through untouched.
    if bib_html:
        body += "\n\n# References\n\n" + bib_html

    # The boilerplate "reproduce" footer is rendered by the single.html layout
    # (after {{ content }}) rather than being baked into the body here. This lets
    # kramdown's auto-generated footnotes list — which it always emits at the very
    # end of the content — sit above the footer instead of below it, giving the
    # order: article -> References -> footnotes -> reproduce footer. The source
    # folder URL is passed to the layout via the `repro_url` front-matter field.
    repro_url = f"{REPO_URL}/tree/main/posts/{name}"

    # Build Jekyll front matter
    out_fm = ['---']
    out_fm.append(f'title: "{title}"')
    out_fm.append(f"date: {date}")
    out_fm.append(f"permalink: /posts/{year}/{month}/{slug}/")
    out_fm.append(f"repro_url: {repro_url}")
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
    out_path = os.path.join(OUT_DIR, f"{date}-{slug}.md")
    rel_out = os.path.relpath(out_path, ROOT)
    prev = None
    if os.path.isfile(out_path):
        with open(out_path, encoding="utf-8") as f:
            prev = f.read()
    changed = prev != content
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return rel_out, copied, changed


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
    changed_count = 0
    for name in sorted(os.listdir(POSTS_DIR)):
        if name in SKIP_DIRS or name.startswith("."):
            continue
        if not os.path.isdir(os.path.join(POSTS_DIR, name)):
            continue
        result = sync_post(name)
        if result:
            out_path, copied, changed = result
            status = "changed" if changed else "unchanged"
            print(f"  synced {name} -> {out_path} ({copied} image(s), {status})")
            total += 1
            changed_count += changed
    print(f"sync_posts: regenerated {total} post(s), {changed_count} changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
