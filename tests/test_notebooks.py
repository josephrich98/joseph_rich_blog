"""Tests for the blog post repository.

Two things are checked for every post under ``posts/<name>/``:

1. ``test_notebook_runs`` / ``test_notebook_identical`` – the ``notebook.ipynb``
   executes without raising (lax), and optionally that its stored outputs still
   match a fresh run (strict). Both use the ``nbval`` pytest plugin.
2. ``test_post_pdf_builds`` – the ``main.md`` Markdown source renders to a PDF
   with ``pandoc`` using the bundled Eisvogel template
   (``templates/eisvogel.latex``).

Posts are discovered automatically, so adding a new ``posts/<name>/`` directory
needs no changes here.

Notes for authoring notebooks:
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

# Posts whose stored notebook outputs should match a fresh run exactly
# (checked with ``--nbval`` instead of ``--nbval-lax``). Use the post directory
# name, e.g. "post1".
STRICT_POSTS = set()  #* add post names here for exact-output checking

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


@pytest.mark.skipif(not NBVAL_AVAILABLE, reason="nbval plugin not installed")
@pytest.mark.parametrize(
    "post_name,notebook_path",
    NOTEBOOKS,
    ids=[name for name, _ in NOTEBOOKS],
)
def test_notebook_runs(tmp_path, post_name, notebook_path):
    """Each post notebook executes top-to-bottom without raising."""
    if post_name in STRICT_POSTS:
        pytest.skip(f"{post_name} is checked by test_notebook_identical instead")

    temp_notebook_path = os.path.join(tmp_path, "notebook.ipynb")
    shutil.copy(notebook_path, temp_notebook_path)
    clear_notebook_output(temp_notebook_path)  # lax mode only needs it to run

    rc = run_nbval(temp_notebook_path, strict=False)
    assert rc == 0, f"Notebook for {post_name} failed to execute"


@pytest.mark.skipif(not NBVAL_AVAILABLE, reason="nbval plugin not installed")
@pytest.mark.parametrize(
    "post_name,notebook_path",
    [(n, p) for n, p in NOTEBOOKS if n in STRICT_POSTS],
    ids=[n for n, _ in NOTEBOOKS if n in STRICT_POSTS] or ["<none>"],
)
def test_notebook_identical(tmp_path, post_name, notebook_path):
    """Strict posts produce outputs identical to those stored in the notebook."""
    temp_notebook_path = os.path.join(tmp_path, "notebook.ipynb")
    shutil.copy(notebook_path, temp_notebook_path)

    rc = run_nbval(temp_notebook_path, strict=True)
    assert rc == 0, f"Notebook for {post_name} did not reproduce its stored outputs"


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
