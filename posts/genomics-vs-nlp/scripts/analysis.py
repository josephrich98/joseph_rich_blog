"""
Analysis for: "Genomics Is Not NLP"
Generates the figures used in main.md. Most numbers here are combinatorial
(k-mer counting, 4^-k) or demographic (published per-genome variant counts).
The one empirical panel is the mRNA-protein scatter (Fig 3a), which plots real
measured per-gene copy numbers from Schwanhaeusser et al. 2011 (bundled as a
CSV in data/, so nothing is downloaded at runtime). The point throughout is the
arithmetic of redundancy, similarity-beyond-chance, the RNA-protein gap, and
multiple testing.

Each panel is written to its own file so the post can embed panels
independently:
    corpus_redundancy_a.png   Fig 1a  (monochrome)
    corpus_redundancy_b.png   Fig 1b
    kmer_chance.png           Fig 2
    proxy_scatter.png         Fig 3a
    multiple_testing.png      Fig 3b
    unit_length_scales.png    Fig 4

Run:  python analysis.py   (writes PNGs into figures/)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, pearsonr

FIG = os.path.join(os.path.dirname(__file__), "figures")
if not os.path.isdir(FIG):
    # when run from inside scripts/, write up one level into the post's figures/
    FIG = os.path.join(os.path.dirname(__file__), "..", "figures")
os.makedirs(FIG, exist_ok=True)

# Bundled data tables (real measured data used by Fig 3a).
DATA = os.path.join(os.path.dirname(__file__), "data")
if not os.path.isdir(DATA):
    DATA = os.path.join(os.path.dirname(__file__), "..", "data")

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
# Fig 1a is intentionally monochrome (no color encoding).
GREY = "#4d4d4d"

GENOME_BP = 3.2e9  # haploid human genome, base pairs


# --------------------------------------------------------------------------
# Figure 1a: two members of the species are near-duplicates (monochrome)
# --------------------------------------------------------------------------
def fig_redundancy_a():
    items = [
        ("Two human genomes\n(within-species)", 1.0e-3),
        ("Human vs chimpanzee", 1.2e-2),
        ("Two random DNA strings\n(1 - 1/4)", 0.75),
        ("Two unrelated English\ndocuments", 1.0),
    ]
    labels = [i[0] for i in items]
    fracs = np.array([i[1] for i in items])
    y = np.arange(len(items))[::-1]

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.barh(y, fracs, color=GREY)
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlim(5e-4, 2.0)
    ax.set_xlabel("Fraction of positions that differ (log scale)")
    for yi, f in zip(y, fracs):
        ax.text(f * 1.3, yi, f"{f:.0e}".replace("e-0", "e-"), va="center",
                ha="left", fontsize=9)
    ax.set_title("Two members of the species are near-duplicates")

    fig.tight_layout()
    out = os.path.join(FIG, "corpus_redundancy_a.png")
    fig.savefig(out)
    plt.close(fig)
    print("wrote", out)


# --------------------------------------------------------------------------
# Figure 1b: SVs are rare as events but dominant as bases
# --------------------------------------------------------------------------
def fig_redundancy_b():
    # SNVs + small indels: ~4.5M events, ~5 Mb of bases (1000G / gnomAD scale).
    # Structural variants (Sudmant 2015): ~2,500 events, ~20 Mb of bases.
    classes = ["SNVs + small\nindels", "Structural\nvariants"]
    events = np.array([4.5e6, 2.5e3])
    bases = np.array([5.0e6, 2.0e7])
    x = np.arange(len(classes))
    w = 0.38

    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    ax.bar(x - w / 2, events, w, color=STEEL, alpha=0.9, label="variant events")
    ax.bar(x + w / 2, bases, w, color=CRIMSON, alpha=0.9, label="bases affected")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(classes)
    ax.set_ylabel("Count per genome (log scale)")
    ax.set_ylim(1e3, 3e8)
    ax.legend(fontsize=9, loc="upper left")
    for xi, e, b in zip(x, events, bases):
        ax.text(xi - w / 2, e * 1.4, f"{e:,.0f}".replace(",000,000", "M"),
                ha="center", va="bottom", fontsize=8)
        ax.text(xi + w / 2, b * 1.4, f"{b/1e6:.0f} Mb", ha="center",
                va="bottom", fontsize=8)
    ax.set_title("SVs: rare as events, dominant as bases")

    fig.tight_layout()
    out = os.path.join(FIG, "corpus_redundancy_b.png")
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
# Figure 3a: the proxy problem -- mRNA is a noisy proxy for protein
#
# Real measured data, not a simulation: per-gene mRNA and protein copy numbers
# in mouse NIH3T3 fibroblasts from Schwanhaeusser et al. 2011 (Nature 473:337).
# The tidy table lives in data/ so the figure reproduces with no download.
# --------------------------------------------------------------------------
def fig_proxy_scatter():
    import pandas as pd

    csv = os.path.join(DATA, "schwanhausser_2011_nih3t3.csv")
    df = pd.read_csv(csv, comment="#")
    df = df[(df["mrna"] > 0) & (df["protein"] > 0)].dropna(subset=["mrna", "protein"])

    # Spearman is rank-based (scale-free); Pearson is on log10 copies/cell.
    rho, _ = spearmanr(df["mrna"], df["protein"])
    r, _ = pearsonr(np.log10(df["mrna"]), np.log10(df["protein"]))

    fig, ax = plt.subplots(figsize=(6.0, 4.7))
    ax.scatter(df["mrna"], df["protein"], s=6, color=NAVY, alpha=0.35, edgecolors="none")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("mRNA abundance (copies per cell)")
    ax.set_ylabel("Protein abundance (copies per cell)")
    ax.set_title("mRNA is a noisy proxy for protein")
    ax.text(0.04, 0.96,
            f"Spearman $\\rho$ = {rho:.2f}   Pearson $r$ = {r:.2f} (log)\n"
            f"Schwanhäusser et al. 2011 · NIH3T3 · n = {len(df):,}",
            transform=ax.transAxes, va="top", fontsize=9,
            bbox=dict(boxstyle="round", fc="white", ec="grey", alpha=0.8))
    fig.tight_layout()
    out = os.path.join(FIG, "proxy_scatter.png")
    fig.savefig(out)
    plt.close(fig)
    print("wrote", out)
    print("  n = %d genes; Spearman = %.3f; Pearson(log10) = %.3f (R^2 = %.3f)"
          % (len(df), rho, r, r ** 2))


# --------------------------------------------------------------------------
# Figure 3b: the multiple-testing tax
# --------------------------------------------------------------------------
def fig_multiple_testing():
    m = np.logspace(1, 7, 300)
    alpha = 0.05
    fp = m * alpha

    fig, ax = plt.subplots(figsize=(6.0, 4.7))
    ax.plot(m, fp, color=NAVY, lw=2)
    ax.axhline(1.0, color=AMBER, ls="--", lw=1.5, label="1 false positive")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Number of hypothesis tests m")
    ax.set_ylabel(r"Expected false positives at $\alpha$=0.05 (uncorrected)")
    ax.set_title("The multiple-testing tax")
    for mv, name in [(2e4, "transcriptome\n(~20k genes)"), (1e6, "GWAS\n(~1M variants)")]:
        ax.plot([mv], [mv * alpha], "o", color=CRIMSON)
        ax.annotate(f"{name}\n{mv*alpha:,.0f} FPs", (mv, mv * alpha),
                    textcoords="offset points", xytext=(-70, 8), fontsize=8,
                    color=CRIMSON)
    ax.legend(fontsize=9, loc="lower right")
    fig.tight_layout()
    out = os.path.join(FIG, "multiple_testing.png")
    fig.savefig(out)
    plt.close(fig)
    print("wrote", out)
    print("  uncorrected FPs: transcriptome=%.0f, GWAS=%.0f" % (2e4 * 0.05, 1e6 * 0.05))
    print("  Bonferroni genome-wide threshold = 0.05 / 1e6 = %.0e" % (0.05 / 1e6))


# --------------------------------------------------------------------------
# Figure 4: the unit of meaning lives on a different scale
# --------------------------------------------------------------------------
def fig_unit_length():
    from scipy.stats import gaussian_kde

    rng = np.random.default_rng(11)

    word_len = np.arange(1, 16)
    word_pmf = np.array([0.027, 0.174, 0.207, 0.157, 0.107, 0.087, 0.070,
                         0.050, 0.037, 0.028, 0.018, 0.013, 0.0085, 0.005, 0.003])
    word_pmf = word_pmf / word_pmf.sum()
    word_samples = rng.choice(word_len, size=40000, p=word_pmf).astype(float)
    word_samples += rng.uniform(-0.5, 0.5, size=word_samples.size)
    word_samples = np.clip(word_samples, 0.5, None)

    gene_samples = rng.lognormal(mean=np.log(24_000), sigma=1.1, size=40000)

    log_words = np.log10(word_samples)
    log_genes = np.log10(gene_samples)
    kde_w, kde_g = gaussian_kde(log_words), gaussian_kde(log_genes)

    xs = np.linspace(-0.2, 7.0, 1000)
    dw, dg = kde_w(xs), kde_g(xs)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.fill_between(xs, dw, color=CRIMSON, alpha=0.40)
    ax.plot(xs, dw, color=CRIMSON, lw=2, label="English word length (characters)")
    ax.fill_between(xs, dg, color=NAVY, alpha=0.40)
    ax.plot(xs, dg, color=NAVY, lw=2, label="Human gene length (bases)")

    mw, mg = np.median(word_samples), np.median(gene_samples)
    for med, c in [(mw, CRIMSON), (mg, NAVY)]:
        ax.axvline(np.log10(med), color=c, ls=":", lw=1.3)

    ax.set_xticks(range(0, 8))
    ax.set_xticklabels([f"$10^{{{t}}}$" for t in range(0, 8)])
    ax.set_xlim(-0.2, 7.0)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Length (characters for words, bases for genes), log scale")
    ax.set_ylabel("Smooth density (per decade)")
    ax.set_title("The atomic unit of meaning: a word vs a gene")
    ax.legend(fontsize=9, loc="upper right")
    fig.tight_layout()
    out = os.path.join(FIG, "unit_length_scales.png")
    fig.savefig(out)
    plt.close(fig)
    print("wrote", out)
    print(f"  median word length = {mw:.1f} characters; median gene span = {mg:,.0f} bases")


if __name__ == "__main__":
    fig_redundancy_a()
    fig_redundancy_b()
    fig_kmer()
    fig_proxy_scatter()
    fig_multiple_testing()
    fig_unit_length()
    print("done.")
