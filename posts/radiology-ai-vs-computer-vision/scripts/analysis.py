"""
Analysis for: "Radiology AI Is Not Computer Vision"
Generates the three figures used in main.md. All numbers are either physical
(voxel geometry) or illustrative stratification fractions anchored to the
published size of MIMIC-CXR (377,110 images). Nothing here requires the raw
images; the point is the arithmetic of subtlety and statistical power.

Run:  python analysis.py   (writes PNGs into figures/)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator
from scipy.stats import norm

FIG = os.path.join(os.path.dirname(__file__), "figures")
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

NAVY, CRIMSON, STEEL, AMBER = "#1f3b57", "#9b1d20", "#3d7ca6", "#d99a00"


# --------------------------------------------------------------------------
# Figure 1: the needle in the haystack -- fraction of voxels that are lesion
# --------------------------------------------------------------------------
def sphere_volume(diameter_mm):
    r = diameter_mm / 2.0
    return (4.0 / 3.0) * np.pi * r ** 3  # mm^3


def fig_needle():
    # Chest CT acquisition geometry (typical).
    ct_dims = (512, 512, 320)
    ct_voxel_mm = (0.7, 0.7, 1.0)
    ct_total_vox = np.prod(ct_dims)
    ct_voxel_vol = np.prod(ct_voxel_mm)

    # Brain MRI (1 mm isotropic).
    mri_total_vox = 240 * 240 * 160
    mri_voxel_vol = 1.0

    def ct_frac(d):
        return sphere_volume(d) / ct_voxel_vol / ct_total_vox

    def mri_frac(d):
        return sphere_volume(d) / mri_voxel_vol / mri_total_vox

    items = [
        ("Natural image:\nobject of interest", 0.20, STEEL, "natural"),
        ("COCO 'small'\nobject", 0.003, STEEL, "natural"),
        ("Lung nodule 10 mm\n(chest CT)", ct_frac(10), CRIMSON, "med"),
        ("Lung nodule 5 mm\n(chest CT)", ct_frac(5), CRIMSON, "med"),
        ("Lung nodule 3 mm\n(chest CT)", ct_frac(3), CRIMSON, "med"),
        ("Lacunar infarct 5 mm\n(brain MRI)", mri_frac(5), NAVY, "med"),
        ("Microcalcification\n~0.4 mm (mammo)", (0.4 / 0.07) ** 2 / (3000.0 * 3800.0), NAVY, "med"),
    ]

    labels = [i[0] for i in items]
    fracs = np.array([i[1] for i in items])
    colors = [i[2] for i in items]

    fig, ax = plt.subplots(figsize=(9, 4.8))
    y = np.arange(len(items))[::-1]
    ax.barh(y, fracs, color=colors, alpha=0.9)
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Fraction of pixels / voxels belonging to the finding (log scale)")
    ax.set_xlim(1e-7, 1.5)
    for yi, f in zip(y, fracs):
        ax.text(f * 1.5, yi, f"{f:.1e}", va="center", ha="left", fontsize=9)
    ax.axvspan(1e-7, 1e-4, color="grey", alpha=0.06)
    ax.set_title("The needle in the haystack: how much of the image is the disease?")
    fig.tight_layout()
    out = os.path.join(FIG, "needle_in_haystack.png")
    fig.savefig(out)
    plt.close(fig)
    print("wrote", out)
    print("  3mm nodule fraction = %.2e (1 in %0.0f voxels)" % (ct_frac(3), 1 / ct_frac(3)))
    return ct_frac, mri_frac


# --------------------------------------------------------------------------
# Figure 2: the stratification waterfall
# --------------------------------------------------------------------------
# Anchored to MIMIC-CXR (Johnson et al. 2019): 377,110 images.
WATERFALL = [
    ("All images in MIMIC-CXR", 377_110, None),
    ("Frontal view only", 0.65, "view"),
    ("Positive for the target finding\n(pneumothorax, prev. ~3%)", 0.03, "disease"),
    ("Female patients", 0.47, "sex"),
    ("Age 18-40", 0.16, "age"),
    ("Acquired on scanner make B", 0.30, "scanner"),
    ("Moderate-large (actionable) subtype", 0.40, "severity"),
]


def waterfall_counts():
    counts, labels = [], []
    n = WATERFALL[0][1]
    counts.append(n)
    labels.append(WATERFALL[0][0])
    for label, frac, _ in WATERFALL[1:]:
        n = n * frac
        counts.append(n)
        labels.append(label)
    return labels, np.array(counts)


def fig_waterfall():
    labels, counts = waterfall_counts()
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    x = np.arange(len(counts))
    colors = [STEEL] + [CRIMSON] * (len(counts) - 1)
    ax.bar(x, counts, color=colors, alpha=0.9)
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8.5)
    ax.set_ylabel("Evaluable cases remaining (log scale)")
    ax.set_title("From 377,110 images to 66 evaluable cases: the stratification waterfall")
    for xi, c in zip(x, counts):
        ax.text(xi, c * 1.25, f"{int(round(c)):,}", ha="center", va="bottom", fontsize=8.5)
    ax.set_ylim(10, 1e6)
    fig.tight_layout()
    out = os.path.join(FIG, "stratification_waterfall.png")
    fig.savefig(out)
    plt.close(fig)
    print("wrote", out)
    print("  final evaluable positives = %.0f" % counts[-1])
    return counts


# --------------------------------------------------------------------------
# Figure 3: what those counts buy you in statistical precision / power
# --------------------------------------------------------------------------
def ci_halfwidth(p, n, z=1.96):
    return z * np.sqrt(p * (1 - p) / n)


def power_two_prop(p1, p2, n, alpha=0.05):
    """Two-sided power to detect a difference in two proportions, n per group."""
    pbar = (p1 + p2) / 2.0
    z = norm.ppf(1 - alpha / 2.0)
    se0 = np.sqrt(2 * pbar * (1 - pbar) / n)
    se1 = np.sqrt(p1 * (1 - p1) / n + p2 * (1 - p2) / n)
    return norm.cdf((abs(p1 - p2) - z * se0) / se1)


def required_n(p1, p2, alpha=0.05, power=0.80):
    pbar = (p1 + p2) / 2.0
    za = norm.ppf(1 - alpha / 2.0)
    zb = norm.ppf(power)
    num = (za * np.sqrt(2 * pbar * (1 - pbar)) +
           zb * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return num / (p1 - p2) ** 2


def fig_power(subgroup_counts):
    p = 0.85           # assumed true sensitivity
    p_drop = 0.75      # degraded subgroup sensitivity we want to be able to detect
    marks = [(c, name) for c, name in zip(
        subgroup_counts[2:], ["disease+", "+age", "+scanner", "+severity"])]
    # keep only the positive-case strata (index 2 onward are positives)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))

    # Panel A: CI half-width for a sensitivity estimate.
    n = np.logspace(1, 4, 300)
    axes[0].plot(n, ci_halfwidth(p, n), color=NAVY, lw=2)
    axes[0].axhline(0.05, color=AMBER, ls="--", lw=1.5, label="±0.05 target precision")
    axes[0].set_xscale("log")
    axes[0].set_xlabel("Number of positive (diseased) cases")
    axes[0].set_ylabel("95% CI half-width on sensitivity")
    axes[0].set_title("(a) Precision of a subgroup sensitivity estimate")
    for c, name in marks:
        hw = ci_halfwidth(p, c)
        axes[0].plot([c], [hw], "o", color=CRIMSON)
        axes[0].annotate(f"n={int(round(c))}\n±{hw:.2f}", (c, hw),
                         textcoords="offset points", xytext=(6, 6), fontsize=8)
    axes[0].legend(fontsize=9)
    axes[0].set_ylim(0, 0.25)

    # Panel B: power to detect a 0.85 -> 0.75 subgroup gap.
    npg = np.logspace(1, 3.2, 300)
    axes[1].plot(npg, [power_two_prop(p, p_drop, k) for k in npg], color=NAVY, lw=2)
    axes[1].axhline(0.80, color=AMBER, ls="--", lw=1.5, label="80% power")
    nreq = required_n(p, p_drop)
    axes[1].axvline(nreq, color="grey", ls=":", lw=1.2)
    axes[1].annotate(f"need ~{nreq:.0f}/group", (nreq, 0.3),
                     textcoords="offset points", xytext=(6, 0), fontsize=8, color="grey")
    axes[1].set_xscale("log")
    axes[1].set_xlabel("Positive cases per group")
    axes[1].set_ylabel("Power to detect sens. 0.85 -> 0.75")
    axes[1].set_title("(b) Power to catch a subgroup performance gap")
    for c, name in marks:
        if c < 1100:
            pw = power_two_prop(p, p_drop, c)
            axes[1].plot([c], [pw], "o", color=CRIMSON)
            axes[1].annotate(f"n={int(round(c))}\n{pw:.0%}", (c, pw),
                             textcoords="offset points", xytext=(6, -2), fontsize=8)
    axes[1].legend(fontsize=9)
    axes[1].set_ylim(0, 1.02)

    fig.tight_layout()
    out = os.path.join(FIG, "power_and_precision.png")
    fig.savefig(out)
    plt.close(fig)
    print("wrote", out)
    print("  required n/group for 80%% power = %.1f" % nreq)
    print("  power at n=66 = %.3f" % power_two_prop(p, p_drop, 66))
    print("  CI half-width at n=66 = %.3f" % ci_halfwidth(p, 66))


if __name__ == "__main__":
    fig_needle()
    counts = fig_waterfall()
    fig_power(counts)
    print("done.")
