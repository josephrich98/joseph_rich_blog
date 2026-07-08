"""Figures for the post "How This Blog Is Built".

The post ships no data. The single figure is a schematic of the
commit-to-deploy pipeline, drawn purely from box/arrow geometry so it is fully
reproducible from this script. ``notebook.ipynb`` contains the same drawing code
inline (so it runs standalone, with no local imports), and this module is the
standalone equivalent.

Run standalone:
    python make_figures.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: works in CI and in nbconvert
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

# Two colors carry the whole legend: blue for the steps I trigger by hand,
# black for everything that then happens automatically.
BLUE = "#1565c0"   # manual: writing + the git commands I run
BLACK = "#1b1b1b"  # automatic: whatever those git commands set off


def _box(ax, xy, w, h, text, *, fontsize=11, text_color=BLACK):
    """Draw a rounded white box (black outline) centered at xy with text."""
    x, y = xy
    patch = FancyBboxPatch(
        (x - w / 2, y - h / 2),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.6,
        edgecolor=BLACK,
        facecolor="white",
        zorder=2,
    )
    ax.add_patch(patch)
    ax.text(
        x,
        y,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=text_color,
        zorder=3,
        linespacing=1.35,
    )
    return patch


def _arrow(ax, p0, p1, color=BLACK, style="-|>", lw=1.8, ls="-",
           connectionstyle="arc3,rad=0"):
    ax.add_patch(
        FancyArrowPatch(
            p0,
            p1,
            arrowstyle=style,
            mutation_scale=14,
            linewidth=lw,
            linestyle=ls,
            color=color,
            shrinkA=2,
            shrinkB=2,
            zorder=1,
            connectionstyle=connectionstyle,
        )
    )


def draw_pipeline(outpath):
    """Render the commit-to-deploy workflow schematic to ``outpath``."""
    fig, ax = plt.subplots(figsize=(9.0, 6.6))
    ax.set_xlim(0, 9.0)
    ax.set_ylim(0, 6.6)
    ax.axis("off")

    cx = 3.3     # the three blocks share one vertical spine
    w = 6.0      # wide enough for the longest label

    # --- Block 1: write it (manual) -----------------------------------------
    _box(
        ax,
        (cx, 5.7),
        w,
        0.9,
        "Write $\\tt main.md$ (+ $\\tt notebook.ipynb$)",
        text_color=BLUE,
    )

    # git commit --------------------------------------------------------------
    _arrow(ax, (cx, 5.25), (cx, 4.30))
    ax.text(cx + 0.25, 4.78, "git commit", ha="left", va="center",
            fontsize=10.5, color=BLUE, style="italic")

    # --- Block 2: sync the site + check the citations (automatic) -----------
    _box(
        ax,
        (cx, 3.75),
        w,
        1.1,
        "update site with Jekyll + Vercel\n"
        "validate updated references with doi2bib",
    )

    # git push ----------------------------------------------------------------
    _arrow(ax, (cx, 3.20), (cx, 2.25))
    ax.text(cx + 0.25, 2.72, "git push", ha="left", va="center",
            fontsize=10.5, color=BLUE, style="italic")

    # --- Block 3: deploy + test (automatic) ---------------------------------
    _box(
        ax,
        (cx, 1.70),
        w,
        1.1,
        "deploy site\n"
        "run notebook checks on updated notebooks (strict → lax)",
    )

    # GitHub Actions re-runs the notebook checks on a schedule (self-loop).
    edge = cx + w / 2
    _arrow(ax, (edge, 1.95), (edge, 1.45), connectionstyle="arc3,rad=-2.2")
    ax.text(edge + 0.9, 1.70, "GitHub actions (6mo)", ha="left", va="center",
            fontsize=10, color=BLACK, style="italic")

    fig.tight_layout()
    outpath = Path(outpath)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outpath, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return str(outpath)


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    out = here.parent / "figures" / "pipeline.png"
    print("wrote", draw_pipeline(out))
