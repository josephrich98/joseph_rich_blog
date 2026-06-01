"""
Analysis for: "Genomics Is Not NLP"
Generates the three figures used in main.md. Every number here is either
combinatorial (k-mer counting, 4^-k), demographic (published per-genome variant
counts), or an illustrative simulation (the mRNA-protein scatter). Nothing
requires downloading a genome; the point is the arithmetic of redundancy,
similarity-beyond-chance, the RNA-protein gap, and multiple testing.

Run:  python analysis.py   (writes PNGs into figures/)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

FIG = os.path.join(os.path.dirname(__file__), "figures")
if not os.path.isdir(FIG):
    # when run from inside scripts/, write up one level into the post's figures/
    FIG = os.path.join(os.path.dirname(__file__), "..", "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
})

NAVY, CRIMSON, STEEL, AMBER, MOSS = "#1f3b57", "#9b1d20", "#3d7ca6", "#d99a00", "#4c7a4c"

GENOME_BP = 3.2e9  # haploid human genome, base pairs


# --------------------------------------------------------------------------
# Figure 1: the corpus is nearly one document
# --------------------------------------------------------------------------
def fig_redundancy():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))

    # Panel (a): fraction of positions that differ between two sequences.
    items = [
        ("Two human genomes\n(within-species)", 1.0e-3, CRIMSON),
        ("Human vs chimpanzee", 1.2e-2, NAVY),
        ("Two random DNA strings\n(1 - 1/4)", 0.75, STEEL),
        ("Two unrelated English\ndocuments", 1.0, STEEL),
    ]
    labels = [i[0] for i in items]
    fracs = np.array([i[1] for i in items])
    colors = [i[2] for i in items]
    y = np.arange(len(items))[::-1]
    axes[0].barh(y, fracs, color=colors, alpha=0.9)
    axes[0].set_xscale("log")
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(labels, fontsize=9)
    axes[0].set_xlim(5e-4, 2.0)
    axes[0].set_xlabel("Fraction of positions that differ (log scale)")
    for yi, f in zip(y, fracs):
        axes[0].text(f * 1.3, yi, f"{f:.0e}".replace("e-0", "e-"), va="center",
                     ha="left", fontsize=9)
    axes[0].set_title("(a) Two members of the species are near-duplicates")

    # Panel (b): per-genome variation -- events vs bases affected.
    # SNVs + small indels: ~4.5M events, ~5 Mb of bases (1000G / gnomAD scale).
    # Structural variants (Sudmant 2015): ~2,500 events, ~20 Mb of bases.
    classes = ["SNVs + small\nindels", "Structural\nvariants"]
    events = np.array([4.5e6, 2.5e3])
    bases = np.array([5.0e6, 2.0e7])
    x = np.arange(len(classes))
    w = 0.38
    axes[1].bar(x - w / 2, events, w, color=STEEL, alpha=0.9, label="variant events")
    axes[1].bar(x + w / 2, bases, w, color=CRIMSON, alpha=0.9, label="bases affected")
    axes[1].set_yscale("log")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(classes)
    axes[1].set_ylabel("Count per genome (log scale)")
    axes[1].set_ylim(1e3, 1e8)
    axes[1].legend(fontsize=9, loc="upper right")
    for xi, e, b in zip(x, events, bases):
        axes[1].text(xi - w / 2, e * 1.4, f"{e:,.0f}".replace(",000,000", "M"),
                     ha="center", va="bottom", fontsize=8)
        axes[1].text(xi + w / 2, b * 1.4, f"{b/1e6:.0f} Mb", ha="center",
                     va="bottom", fontsize=8)
    axes[1].set_title("(b) SVs: rare as events, dominant as bases")

    fig.tight_layout()
    out = os.path.join(FIG, "corpus_redundancy.png")
    fig.savefig(out)
    plt.close(fig)
    print("wrote", out)
    print("  SNV/indel sites are ~0.1%% of the genome; SVs touch ~%.1f Mb" % (bases[1] / 1e6))


# --------------------------------------------------------------------------
# Figure 2: similarity beyond chance -- the k-mer argument
# --------------------------------------------------------------------------
def fig_kmer():
    k = np.arange(1, 41)
    # Expected occurrences of a *specific* k-mer in a genome of GENOME_BP bases.
    expected = GENOME_BP * (4.0 ** (-k.astype(float)))
    k_star = np.log(GENOME_BP) / np.log(4.0)  # where expected == 1

    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    ax.plot(k, expected, color=NAVY, lw=2, marker="o", ms=3)
    ax.set_yscale("log")
    ax.axhline(1.0, color=AMBER, ls="--", lw=1.5, label="1 expected occurrence")
    ax.axvline(k_star, color="grey", ls=":", lw=1.2)
    ax.annotate(f"chance crosses 1\nnear k = {k_star:.0f}", (k_star, 1),
                textcoords="offset points", xytext=(8, 40), fontsize=9, color="grey")

    e31 = GENOME_BP * 4.0 ** (-31)
    ax.plot([31], [e31], "o", color=CRIMSON, ms=7)
    ax.annotate(
        f"k = 31:  expected chance\noccurrences $\\approx$ {e31:.0e}".replace("e-0", "e-")
        + "\n(i.e. never by chance)",
        (31, e31), textcoords="offset points", xytext=(-150, 20), fontsize=9,
        color=CRIMSON,
        arrowprops=dict(arrowstyle="->", color=CRIMSON, lw=1))

    ax.set_xlabel("k-mer length k")
    ax.set_ylabel("Expected occurrences of a specific k-mer in 3.2 Gb (log scale)")
    ax.set_title("A shared 31-mer is not coincidence — it is homology")
    ax.legend(fontsize=9, loc="upper right")
    ax.set_ylim(1e-20, 1e9)
    fig.tight_layout()
    out = os.path.join(FIG, "kmer_chance.png")
    fig.savefig(out)
    plt.close(fig)
    print("wrote", out)
    print("  chance crosses 1 near k = %.2f; E[occurrences | k=31] = %.2e" % (k_star, e31))


# --------------------------------------------------------------------------
# Figure 3: the proxy problem and the multiple-testing tax
# --------------------------------------------------------------------------
def fig_proxy_and_testing():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.7))

    # Panel (a): illustrative mRNA vs protein scatter at an empirical-ish corr.
    rng = np.random.default_rng(7)
    n = 2000
    z = rng.standard_normal(n)            # shared latent (true expression program)
    log_mrna = z + 0.9 * rng.standard_normal(n)
    log_prot = z + 1.4 * rng.standard_normal(n)   # protein adds translation/decay noise
    rho, _ = spearmanr(log_mrna, log_prot)
    axes[0].scatter(log_mrna, log_prot, s=6, color=NAVY, alpha=0.35, edgecolors="none")
    axes[0].set_xlabel("mRNA abundance (log, arb. units)")
    axes[0].set_ylabel("Protein abundance (log, arb. units)")
    axes[0].set_title("(a) mRNA is a noisy proxy for protein")
    axes[0].text(0.04, 0.93, f"Spearman $\\rho$ = {rho:.2f}\n(illustrative; empirical 0.4–0.6)",
                 transform=axes[0].transAxes, va="top", fontsize=9.5,
                 bbox=dict(boxstyle="round", fc="white", ec="grey", alpha=0.8))

    # Panel (b): expected false positives vs number of tests, uncorrected.
    m = np.logspace(1, 7, 300)
    alpha = 0.05
    fp = m * alpha
    axes[1].plot(m, fp, color=NAVY, lw=2)
    axes[1].axhline(1.0, color=AMBER, ls="--", lw=1.5, label="1 false positive")
    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Number of hypothesis tests m")
    axes[1].set_ylabel(r"Expected false positives at $\alpha$=0.05 (uncorrected)")
    axes[1].set_title("(b) The multiple-testing tax")
    for mv, name in [(2e4, "transcriptome\n(~20k genes)"), (1e6, "GWAS\n(~1M variants)")]:
        axes[1].plot([mv], [mv * alpha], "o", color=CRIMSON)
        axes[1].annotate(f"{name}\n{mv*alpha:,.0f} FPs", (mv, mv * alpha),
                         textcoords="offset points", xytext=(-70, 8), fontsize=8,
                         color=CRIMSON)
    axes[1].legend(fontsize=9, loc="lower right")
    fig.tight_layout()
    out = os.path.join(FIG, "proxy_and_testing.png")
    fig.savefig(out)
    plt.close(fig)
    print("wrote", out)
    print("  Spearman(mRNA, protein) = %.3f" % rho)
    print("  uncorrected FPs: transcriptome=%.0f, GWAS=%.0f" % (2e4 * 0.05, 1e6 * 0.05))
    print("  Bonferroni genome-wide threshold = 0.05 / 1e6 = %.0e" % (0.05 / 1e6))


if __name__ == "__main__":
    fig_redundancy()
    fig_kmer()
    fig_proxy_and_testing()
    print("done.")
