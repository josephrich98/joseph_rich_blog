# Joseph Rich – Blog Code Repository

This repository contains the code and content that accompanies the blog posts on [joseph-rich.com](https://joseph-rich.com).

> **Maintaining the blog?** Authoring, building, publishing, and testing posts are
> documented in [`DEVELOPMENT.md`](DEVELOPMENT.md).

## 📂 Repository Structure

- `site/` – The **website** behind [joseph-rich.com](https://joseph-rich.com): a
  Jekyll site (academicpages theme) with the blog, publications,
  giscus comments, and Vercel deployment. See [`site/README.md`](site/README.md)
  for local dev and the one-time giscus/Vercel setup.

- `posts/` – One directory per blog post, named `YYYY-MM-DD-<slug>` after the post's date and slug (e.g. `posts/2026-06-02-radiology-ai-vs-computer-vision/`) so it sorts chronologically and mirrors the generated `site/_posts/YYYY-MM-DD-<slug>.md`, plus a `posts/template/` scaffold for starting a new one. Each post directory contains:
  - `notebook.ipynb` – the Jupyter notebook with the analyses and examples for that post.
  - `main.md` – the Markdown source for the written article. Rendered to PDF with the Eisvogel template **and** auto-published to the website.
  - `figures/` – generated plots (PNG/PDF) referenced by the post.
  - `scripts/` – any scripts used to generate the figures or run the analysis (e.g. Python scripts, shell scripts, etc.).
  - `data/` – datasets used in the post, with a `README.md` describing each source.
  - `requirements.txt` – the pinned pip packages needed to run that post's notebook.
  - `environment.yml` – a thin Conda wrapper that pins Python + pip and then installs everything in that post's `requirements.txt`.
  - `Dockerfile` – a container definition for running that post's notebook in an isolated environment. It is tailored to the post: the conda environment it creates and the Jupyter kernel it registers are named after the post (matching the `name:` in that post's `environment.yml`), so each post builds and runs independently.

- `templates/` – The bundled [Eisvogel](https://github.com/Wandmalfarbe/pandoc-latex-template) pandoc LaTeX template (`eisvogel.latex`) used to render posts to PDF.

- `tests/` – Test suite that runs every post notebook and builds every `main.md` to PDF.

Each post is self-contained: its `requirements.txt`, `environment.yml`, and
`Dockerfile` live alongside the post's notebook so it can be reproduced on its own.

## 🚀 Running the Notebooks

### Option 1: Using Conda (recommended for local development)

Create the environment from the post you want to run:

```bash
cd posts/2026-06-02-radiology-ai-vs-computer-vision
conda env create -f environment.yml
conda activate radiology-ai-vs-computer-vision  # as specified in environment.yml
jupyter notebook
```

Then open that post's `notebook.ipynb`.

If you'd rather not use Conda, the post's `requirements.txt` holds the same pinned
pip packages, so you can install into any Python 3.10 virtual environment instead:

```bash
cd posts/2026-06-02-radiology-ai-vs-computer-vision
pip install -r requirements.txt
jupyter notebook
```

### Option 2: Using Google Colab
You can also run the notebooks directly in Google Colab. Just open the desired `posts/<post>/notebook.ipynb` file in Colab via the Colab link at the top of the notebook.

### Option 3: Using Docker
If you prefer to run a post's notebook in a containerized environment, you can use Docker.
Each post ships its own `Dockerfile`, tailored to that post (it creates and registers a
conda env/kernel named after the post). Build from inside the post directory:
```bash
cd posts/2026-06-02-radiology-ai-vs-computer-vision
docker build -t radiology-ai-vs-computer-vision .
docker run -p 8888:8888 -v "$(pwd):/home/jovyan/work" radiology-ai-vs-computer-vision
```
Then open your browser to `http://localhost:8888` to access the Jupyter interface, and
select the **Python (radiology-ai-vs-computer-vision)** kernel (named after the post).
