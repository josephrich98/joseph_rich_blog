"""Tests for the blog post repository.

Three independent checks run for every post under ``posts/<name>/``. Each is its
own test, parametrized over all discovered posts, and each has its own opt-out
list so a single post can be excluded from one check without affecting the
others:

1. ``test_post_pdf_builds`` – the ``main.md`` Markdown source renders to a PDF
   with ``pandoc`` using the bundled Eisvogel template
   (``templates/eisvogel.latex``). Exclude via ``POSTS_TO_EXCLUDE_MARKDOWN``.
2. ``test_notebook_runs_lax`` – the ``notebook.ipynb`` executes top-to-bottom
   without raising, ignoring stored outputs (``nbval --nbval-lax``). Exclude via
   ``POSTS_TO_EXCLUDE_NOTEBOOK_LAX``.
3. ``test_notebook_runs_strict`` – the ``notebook.ipynb`` reproduces its stored
   outputs exactly (``nbval --nbval``). Exclude via
   ``POSTS_TO_EXCLUDE_NOTEBOOK_STRICT``.

Posts are discovered automatically, so adding a new ``posts/<name>/`` directory
needs no changes here.

Notes for authoring notebooks (these affect the strict check):
  - Add ``# NBVAL_IGNORE_OUTPUT`` at the top of a cell whose output is not
    expected to be reproducible (timestamps, random values, plots, ...).
  - Add ``# NBVAL_CHECK_OUTPUT`` at the top of a cell whose output *should* be
    compared even when running in lax mode.
"""

import importlib.util
import os
import shutil
import subprocess
import sys

import nbformat
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(REPO_ROOT, "posts")

# Per-check opt-out lists. Add a post's directory name (e.g. "post1") to skip it
# for that one check only; the other checks still run for that post.
POSTS_TO_EXCLUDE_MARKDOWN = set()        #* posts to skip in test_post_pdf_builds
POSTS_TO_EXCLUDE_NOTEBOOK_LAX = set()    #* posts to skip in test_notebook_runs_lax
POSTS_TO_EXCLUDE_NOTEBOOK_STRICT = set() #* posts to skip in test_notebook_runs_strict

NBVAL_AVAILABLE = importlib.util.find_spec("nbval") is not None
PANDOC_BIN = shutil.which("pandoc")
LATEX_BIN = shutil.which("xelatex") or shutil.which("lualatex") or shutil.which("pdflatex")
EISVOGEL_TEMPLATE = os.path.join(REPO_ROOT, "templates", "eisvogel.latex")


def discover(filename):
    """Return (post_name, path) for every ``posts/<name>/<filename>`` file."""
    if not os.path.isdir(POSTS_DIR):
        return []
    found = []
    for name in sorted(os.listdir(POSTS_DIR)):
        path = os.path.join(POSTS_DIR, name, filename)
        if os.path.isfile(path):
            found.append((name, path))
    return found


NOTEBOOKS = discover("notebook.ipynb")
MD_FILES = discover("main.md")


def clear_notebook_output(notebook_path):
    """Remove all outputs and execution counts from a Jupyter notebook."""
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    for cell in nb["cells"]:
        if "outputs" in cell:
            cell["outputs"] = []
        if "execution_count" in cell:
            cell["execution_count"] = None

    with open(notebook_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)


def run_nbval(notebook_path, strict):
    """Execute ``notebook_path`` with nbval in a fresh subprocess.

    Running pytest as a subprocess (rather than a nested ``pytest.main`` call)
    keeps the inner nbval session isolated from the outer one, which is what
    made the previous version of these tests unreliable.
    """
    mode = "--nbval" if strict else "--nbval-lax"
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        mode,
        "--nbval-current-env",  # use the env pytest runs in, ignore kernelspec
        "--tb=short",
        "-p",
        "no:cacheprovider",
        notebook_path,
    ]
    result = subprocess.run(cmd, cwd=os.path.dirname(notebook_path))
    return result.returncode


@pytest.mark.skipif(not PANDOC_BIN, reason="pandoc not installed")
@pytest.mark.skipif(not LATEX_BIN, reason="no LaTeX engine on PATH")
@pytest.mark.skipif(
    not os.path.isfile(EISVOGEL_TEMPLATE),
    reason="templates/eisvogel.latex missing (run scripts/download_eisvogel.sh)",
)
@pytest.mark.parametrize(
    "post_name,md_path",
    MD_FILES,
    ids=[name for name, _ in MD_FILES],
)
def test_post_pdf_builds(tmp_path, post_name, md_path):
    """Each post's main.md renders to a PDF via pandoc + the Eisvogel template."""
    if post_name in POSTS_TO_EXCLUDE_MARKDOWN:
        pytest.skip(f"{post_name} is in POSTS_TO_EXCLUDE_MARKDOWN")

    output_pdf = os.path.join(tmp_path, f"{post_name}.pdf")
    cmd = [
        PANDOC_BIN,
        "main.md",
        "--from",
        "markdown",
        "--template",
        EISVOGEL_TEMPLATE,
        "--listings",
        "-o",
        output_pdf,
    ]
    # Run in the post directory so relative images/links resolve.
    result = subprocess.run(
        cmd, cwd=os.path.dirname(md_path), capture_output=True, text=True
    )
    assert result.returncode == 0, (
        f"pandoc build failed for {post_name}:\n{result.stderr[-3000:]}"
    )
    assert os.path.isfile(output_pdf), f"No PDF produced for {post_name}"


@pytest.mark.skipif(not NBVAL_AVAILABLE, reason="nbval plugin not installed")
@pytest.mark.parametrize(
    "post_name,notebook_path",
    NOTEBOOKS,
    ids=[name for name, _ in NOTEBOOKS],
)
def test_notebook_runs_lax(tmp_path, post_name, notebook_path):
    """Each post notebook executes top-to-bottom without raising (lax)."""
    if post_name in POSTS_TO_EXCLUDE_NOTEBOOK_LAX:
        pytest.skip(f"{post_name} is in POSTS_TO_EXCLUDE_NOTEBOOK_LAX")

    temp_notebook_path = os.path.join(tmp_path, "notebook.ipynb")
    shutil.copy(notebook_path, temp_notebook_path)
    clear_notebook_output(temp_notebook_path)  # lax mode only needs it to run

    rc = run_nbval(temp_notebook_path, strict=False)
    assert rc == 0, f"Notebook for {post_name} failed to execute"


@pytest.mark.skipif(not NBVAL_AVAILABLE, reason="nbval plugin not installed")
@pytest.mark.parametrize(
    "post_name,notebook_path",
    NOTEBOOKS,
    ids=[name for name, _ in NOTEBOOKS],
)
def test_notebook_runs_strict(tmp_path, post_name, notebook_path):
    """Each post notebook reproduces its stored outputs exactly (strict)."""
    if post_name in POSTS_TO_EXCLUDE_NOTEBOOK_STRICT:
        pytest.skip(f"{post_name} is in POSTS_TO_EXCLUDE_NOTEBOOK_STRICT")

    temp_notebook_path = os.path.join(tmp_path, "notebook.ipynb")
    shutil.copy(notebook_path, temp_notebook_path)  # keep stored outputs to compare

    rc = run_nbval(temp_notebook_path, strict=True)
    assert rc == 0, f"Notebook for {post_name} did not reproduce its stored outputs"
