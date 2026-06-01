# Joseph Rich – Blog Code Repository

This repository contains the code and content that accompanies the blog posts on [joseph-rich.com](https://joseph-rich.com).

## 📂 Repository Structure

- `site/` – The **website** behind [joseph-rich.com](https://joseph-rich.com): a
  Jekyll site (academicpages theme) with the blog, tags, publications, and CV,
  giscus comments, and Vercel deployment. See [`site/README.md`](site/README.md)
  for local dev and the one-time giscus/Vercel setup.

- `posts/` – One directory per blog post (e.g. `posts/post1/`). Each post directory contains:
  - `notebook.ipynb` – the Jupyter notebook with the analyses and examples for that post.
  - `main.md` – the Markdown source for the written article, rendered to PDF with the Eisvogel template.
  - `figures/` – generated plots (PNG/PDF) referenced by the post.
  - `scripts/` – any scripts used to generate the figures or run the analysis (e.g. Python scripts, shell scripts, etc.).
  - `data/` – datasets used in the post, with a `README.md` describing each source.

- `templates/` – The bundled [Eisvogel](https://github.com/Wandmalfarbe/pandoc-latex-template) pandoc LaTeX template (`eisvogel.latex`) used to render posts to PDF. Re-download/update it with `scripts/download_eisvogel.sh`.

- `tests/` – Test suite that runs every post notebook and builds every `main.md` to PDF (see [Testing](#-testing)).

- `environment.yml` – The Conda environment needed to run the notebooks and build the posts locally.

- `Dockerfile` – A container definition for running the notebooks in an isolated environment.

## 🚀 Running the Notebooks

### Option 1: Using Conda (recommended for local development)

Create the environment:

```bash
conda env create -f environment.yml
conda activate joseph_rich_blog
jupyter notebook
```

Then open the notebook for a post, e.g. `posts/post1/notebook.ipynb`.

### Option 2: Using Google Colab
You can also run the notebooks directly in Google Colab. Just open the desired `posts/<post>/notebook.ipynb` file in Colab via the Colab link at the top of the notebook.

### Option 3: Using Docker
If you prefer to run the notebooks in a containerized environment, you can use Docker:
```bash
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
cd posts/post1
pandoc main.md -o main.pdf \
  --from markdown \
  --template ../../templates/eisvogel.latex \
  --listings
```

Eisvogel options (title page, table of contents, colored links, …) are set in
the YAML front matter at the top of each `main.md`. See the
[Eisvogel documentation](https://github.com/Wandmalfarbe/pandoc-latex-template#custom-template-variables)
for the full list of variables.

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
