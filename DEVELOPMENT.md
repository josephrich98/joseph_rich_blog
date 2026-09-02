# Development

Developer/maintainer guide for this repository: authoring posts, building them to
PDF, publishing them to [joseph-rich.com](https://joseph-rich.com), and testing.
Reader-facing instructions (repo layout, running the notebooks) live in
[`README.md`](README.md); the website itself is documented in
[`site/README.md`](site/README.md).

## ➕ Adding a new post

Copy the `posts/template/` scaffold to `posts/<new-post-name>/` and fill it in.
Two things must be renamed to the new post's name:

- the `name:` in the post's `environment.yml` (this is the conda env/kernel name), and
- the post name in the `Dockerfile` (in the `conda activate`, `ipykernel install`,
  and kernel display name), matching that `name:`.

List the post's pinned pip dependencies in its `requirements.txt`; the
`environment.yml` only pins Python + pip and installs the rest via
`-r requirements.txt`, so it doesn't need to be edited for dependency changes.
Because pip resolves that relative path from the working directory, run
`conda env create -f environment.yml` (or `pip install -r requirements.txt`) from
inside the post directory.

Directories named `template` are skipped by the publish step and the test suite.

## 📝 Writing & Building Posts

Posts are written in Markdown (`posts/<post>/main.md`) and rendered to PDF with
[pandoc](https://pandoc.org/) using the bundled
[Eisvogel](https://github.com/Wandmalfarbe/pandoc-latex-template) template.

The Eisvogel template is committed at `templates/eisvogel.latex`. To download or
update it (e.g. to a newer release):

```bash
scripts/download_eisvogel.sh            # uses the version in templates/EISVOGEL_VERSION
scripts/download_eisvogel.sh v3.4.0     # or pin an explicit version
```

Build a post's PDF (requires `pandoc` and a LaTeX engine such as `xelatex`/`pdflatex`):

```bash
cd posts/2026-06-02-radiology-ai-vs-computer-vision
pandoc main.md -o main.pdf \
  --from markdown \
  --template ../../templates/eisvogel.latex \
  --listings \
  --citeproc
```

`--citeproc` resolves the post's `[@key]` citations against its
`references.bib` and renders the reference list at the end. The `bibliography:`
(the `.bib`) and `csl:` (`../../templates/csl/american-medical-association.csl`,
an AMA/Vancouver numeric style) paths live in the `main.md` front matter, so a
post with no citations just omits `references.bib` and produces no list. Manage
the `.bib` in a reference manager (Zotero → Better BibTeX export); the citekeys
in `[@key]` must match its keys.

Eisvogel options (title page, table of contents, colored links, …) are set in
the YAML front matter at the top of each `main.md`. See the
[Eisvogel documentation](https://github.com/Wandmalfarbe/pandoc-latex-template#custom-template-variables)
for the full list of variables.

## 🌐 Publishing posts to the website

Each `posts/<name>/main.md` is automatically converted into a Jekyll blog post at
`site/_posts/YYYY-MM-DD-<slug>.md` so it appears on
[joseph-rich.com](https://joseph-rich.com). Post directories are named
`YYYY-MM-DD-<name>`, matching the generated filename and the
`site/images/posts/<name>/` figure folder; the leading date is stripped only to
form the dateless `<slug>` used in the permalink URL, and the date in the output
filename comes from the front matter. The conversion is done by
[`scripts/sync_posts.py`](scripts/sync_posts.py), which:

- maps the post's front matter (`title`, `date`, optional `excerpt`/`tags`/`toc`)
  to Jekyll front matter and drops the pandoc/Eisvogel-only keys,
- copies referenced local images into `site/images/posts/<name>/` and rewrites the
  image paths,
- rewrites inline `$…$` math into kramdown's `$$…$$` so MathJax renders it
  (leaving `$$…$$` display blocks and fenced code untouched),
- indents multi-line footnote continuations so kramdown doesn't truncate them,
- resolves `[@key]` citations against `references.bib` with pandoc + citeproc —
  substituting the numbered inline markers and appending the same reference list
  the PDF shows (as self-contained HTML kramdown passes through), so the web and
  PDF references stay in sync from the one `.bib` — and
- appends a footer linking back to the post's source folder on GitHub so readers
  can reproduce the analyses.

This runs automatically on every commit via the committed pre-commit hook in
[`.githooks/`](.githooks/). **One-time setup per clone** (so git uses that hook):

```bash
git config core.hooksPath .githooks
```

You can also run it by hand at any time:

```bash
python3 scripts/sync_posts.py
```

> Add blog-only metadata (`excerpt:`, `tags:`) to a post's `main.md` front
> matter — pandoc ignores those keys when building the PDF, and `sync_posts.py`
> uses them for the website. Directories named `template` are skipped.

## 🚧 Unpublished sections

This repository is **public**, and Vercel builds joseph-rich.com from whatever
is committed to `main`. So a draft is held back by *not committing it* —
`published: false` in front matter would keep it off the site but still publish
the text on GitHub.

The "Unpublished site sections" block at the bottom of `.gitignore` holds three
**name patterns**, so that committed file never names what is being drafted:

| Pattern | For |
| --- | --- |
| `site/**/*.draft.*` | a draft page or collection entry — permalink and date come from front matter, so the filename is free |
| `site/_data/*_local.yml` | a draft section's content, or draft entries overlaid onto an existing section |
| `site/images/drafts/` | any image those drafts use |

Anything matching builds on a local `jekyll serve` and cannot be committed, even
by `git add -A`. There are three shapes of draft:

**1. A whole new section** (this is how `/models/` is staged):

| Piece | Where | Committed? |
| --- | --- | --- |
| The page | `site/_pages/<name>.draft.html`, with `permalink: /<name>/` | no |
| Its content | `site/_data/<name>_local.yml`, read by the page | no |
| Its images | `site/images/drafts/` | no |
| Its nav entry | `site/_data/navigation.yml` | yes, with `requires_data:` |

The nav entry is the one committed piece, because `navigation.yml` is a shared
file. It carries `requires_data: <name>_local`, naming the `_data` file that
ships with the section; `site/_includes/masthead.html` skips any link whose
`requires_data` file is missing. Locally that file exists and the link shows; on
Vercel it does not, so there is no link and no page. Its styles can stay in
`_sass/` — class names give nothing away — or go in a `<style>` block inside the
draft page if even that matters.

**2. A draft entry in a section that is already public.** `_data/software.yml`
and `_data/videos.yml` are single tracked files, so an entry cannot be held back
inside one. Put it in `_data/<name>_local.yml` instead; the section's page
appends that overlay when it exists (see the `concat` in `_pages/software.html`,
which is the pattern to copy for another section). Overlay entries render after
the tracked ones, so in a sorted section — software is ordered by GitHub stars —
a draft lands at the end regardless of where it belongs.

**3. A draft entry in a file-per-item collection** (`_publications/`, `_posts/`):
name it `<usual-name>.draft.md`. A publication category heading only renders when
it has at least one entry, so an ignored file takes its heading with it.

**Checking what is held back.** The patterns are deliberately uninformative, so
ask git rather than reading `.gitignore`:

```bash
git status --ignored --short site   # lines starting with !! are held back
```

**Going public.** Rename the file out of the draft pattern — drop `.draft`, move
`<name>_local.yml` to `<name>.yml` (updating the page and the nav entry's
`requires_data`), move images from `images/drafts/` to the section's image
folder — then commit. For an overlay entry, move its block into the tracked
`.yml` at the right position in the ordering. The section appears on the next
deploy.

## 🔖 Validating citations

The same pre-commit hook also validates references. Whenever a commit **creates
or modifies a `references.bib` file**, [`scripts/check_bib_dois.py`](scripts/check_bib_dois.py)
runs on just those files and confirms each entry's DOI resolves — the check
[doi2bib](https://doi2bib.org) performs, via DOI content negotiation against
`https://doi.org/<DOI>`. A commit is **blocked** if any DOI is unknown. Entries
without a `doi` field (e.g. `@misc` websites) are reported but not failed.

You can run it by hand on any `.bib` file(s):

```bash
python3 scripts/check_bib_dois.py posts/<name>/references.bib
```

> If a DOI can't be verified because you're offline, the check warns but doesn't
> block. Set `BIB_CHECK_STRICT=1` to fail on unverifiable DOIs, or bypass all
> hooks for one commit with `git commit --no-verify`.

## 🧪 Testing

The test suite under `tests/` automatically discovers every post in `posts/` and runs three independent checks, each parametrized over all posts:

- `test_post_pdf_builds` – each `main.md` renders to a PDF via pandoc + the Eisvogel template.
- `test_notebook_runs_lax` – each `notebook.ipynb` executes top-to-bottom without errors, ignoring stored outputs (via [`nbval`](https://github.com/computationalmodelling/nbval) `--nbval-lax`).
- `test_notebook_runs_strict` – each `notebook.ipynb` reproduces its stored outputs exactly (via `nbval --nbval`).

Install the test dependencies, then run:

```bash
conda activate joseph_rich_blog
conda install -c conda-forge pytest nbval nbformat nbdime pandoc
# A LaTeX distribution (xelatex/pdflatex) and the Eisvogel-required packages are
# also needed for the PDF tests, e.g.:
#   sudo apt-get install texlive-xetex texlive-latex-extra texlive-fonts-recommended

pytest
```

The test path and default flags live in `pytest.ini`, so a bare `pytest`
discovers and runs the suite under `tests/`.

Notebook tests are skipped automatically if `nbval` is not installed, and the
PDF tests are skipped if `pandoc`, a LaTeX engine, or `templates/eisvogel.latex`
is missing.

Each check has its own opt-out list at the top of `tests/test_notebooks.py`, so a
post can be excluded from one check without affecting the others. Add the post's
directory name to:

- `POSTS_TO_EXCLUDE_MARKDOWN` – skip the PDF build for that post,
- `POSTS_TO_EXCLUDE_NOTEBOOK_LAX` – skip the lax notebook run for that post,
- `POSTS_TO_EXCLUDE_NOTEBOOK_STRICT` – skip the strict (stored-output) notebook run for that post.

Because the strict check runs on every notebook by default, cells whose output is not reproducible (timestamps, random values, plots, ...) need a marker on their first line or they will fail strict:

- `# NBVAL_IGNORE_OUTPUT` – don't compare this cell's output, and
- `# NBVAL_CHECK_OUTPUT` – do compare this cell's output even in the lax run.

These tests also run automatically on every push and pull request via GitHub Actions (see `.github/workflows/Notebooks.yml`).
