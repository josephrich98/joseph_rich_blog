# Joseph Rich – Blog Code Repository

This repository contains the code and content that accompanies the blog posts on [joseph-rich.com](https://joseph-rich.com).

## 📂 Repository Structure

- `site/` – The **website** behind [joseph-rich.com](https://joseph-rich.com): a
  Jekyll site (academicpages theme) with the blog, tags, publications, and CV,
  giscus comments, and Vercel deployment. See [`site/README.md`](site/README.md)
  for local dev and the one-time giscus/Vercel setup.

- `posts/` – One directory per blog post (e.g. `posts/radiology-ai-vs-computer-vision/`), plus a `posts/template/` scaffold for starting a new one. Each post directory contains:
  - `notebook.ipynb` – the Jupyter notebook with the analyses and examples for that post.
  - `main.md` – the Markdown source for the written article. Rendered to PDF with the Eisvogel template **and** auto-published to the website (see [Publishing posts to the website](#-publishing-posts-to-the-website)).
  - `figures/` – generated plots (PNG/PDF) referenced by the post.
  - `scripts/` – any scripts used to generate the figures or run the analysis (e.g. Python scripts, shell scripts, etc.).
  - `data/` – datasets used in the post, with a `README.md` describing each source.
  - `environment.yml` – the Conda environment needed to run that post's notebook and build it locally.
  - `Dockerfile` – a container definition for running that post's notebook in an isolated environment.

- `templates/` – The bundled [Eisvogel](https://github.com/Wandmalfarbe/pandoc-latex-template) pandoc LaTeX template (`eisvogel.latex`) used to render posts to PDF. Re-download/update it with `scripts/download_eisvogel.sh`.

- `tests/` – Test suite that runs every post notebook and builds every `main.md` to PDF (see [Testing](#-testing)).

Each post is self-contained: its `environment.yml` and `Dockerfile` live alongside
the post's notebook so it can be reproduced on its own.

## 🚀 Running the Notebooks

### Option 1: Using Conda (recommended for local development)

Create the environment from the post you want to run:

```bash
cd posts/radiology-ai-vs-computer-vision
conda env create -f environment.yml
conda activate joseph_rich_blog
jupyter notebook
```

Then open that post's `notebook.ipynb`.

### Option 2: Using Google Colab
You can also run the notebooks directly in Google Colab. Just open the desired `posts/<post>/notebook.ipynb` file in Colab via the Colab link at the top of the notebook.

### Option 3: Using Docker
If you prefer to run a post's notebook in a containerized environment, you can use Docker.
Build from inside the post directory (each post ships its own `Dockerfile`):
```bash
cd posts/radiology-ai-vs-computer-vision
docker build -t joseph_rich_blog .
docker run -p 8888:8888 -v "$(pwd):/home/jovyan/work" joseph_rich_blog
```
Then open your browser to `http://localhost:8888` to access the Jupyter interface.

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
cd posts/radiology-ai-vs-computer-vision
pandoc main.md -o main.pdf \
  --from markdown \
  --template ../../templates/eisvogel.latex \
  --listings
```

Eisvogel options (title page, table of contents, colored links, …) are set in
the YAML front matter at the top of each `main.md`. See the
[Eisvogel documentation](https://github.com/Wandmalfarbe/pandoc-latex-template#custom-template-variables)
for the full list of variables.

## 🌐 Publishing posts to the website

Each `posts/<name>/main.md` is automatically converted into a Jekyll blog post at
`site/_posts/YYYY-MM-DD-<name>.md` so it appears on
[joseph-rich.com](https://joseph-rich.com). The conversion is done by
[`scripts/sync_posts.py`](scripts/sync_posts.py), which:

- maps the post's front matter (`title`, `date`, optional `excerpt`/`tags`/`toc`)
  to Jekyll front matter and drops the pandoc/Eisvogel-only keys,
- copies referenced local images into `site/images/posts/<name>/` and rewrites the
  image paths,
- rewrites inline `$…$` math into kramdown's `$$…$$` so MathJax renders it
  (leaving `$$…$$` display blocks and fenced code untouched),
- indents multi-line footnote continuations so kramdown doesn't truncate them, and
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

## 🧪 Testing

The test suite under `tests/` automatically discovers every post in `posts/` and checks that:

- each `notebook.ipynb` executes top-to-bottom without errors (via [`nbval`](https://github.com/computationalmodelling/nbval)), and
- each `main.md` renders to a PDF via pandoc + the Eisvogel template.

Install the test dependencies, then run:

```bash
conda activate joseph_rich_blog
conda install -c conda-forge pytest nbval nbformat nbdime pandoc
# A LaTeX distribution (xelatex/pdflatex) and the Eisvogel-required packages are
# also needed for the PDF tests, e.g.:
#   sudo apt-get install texlive-xetex texlive-latex-extra texlive-fonts-recommended

pytest -v tests/
```

Notebook tests are skipped automatically if `nbval` is not installed, and the
PDF tests are skipped if `pandoc`, a LaTeX engine, or `templates/eisvogel.latex`
is missing.

To check that a notebook's stored outputs exactly match a fresh run (instead of
just that it runs without errors), add the post's directory name to
`STRICT_POSTS` in `tests/test_notebooks.py`.

These tests also run automatically on every push and pull request via GitHub Actions (see `.github/workflows/Notebooks.yml`).

