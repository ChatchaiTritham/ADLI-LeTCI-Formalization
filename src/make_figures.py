"""Data figures for the IEEE Access article, drawn only from the equations and the committed result files.

Figure 2  band map of the gated score: weakest factor m against continuous score S (Eq. gate, Theorem 1)
Figure 4  operator comparison: distribution of D1 and D5 over synthetic cohorts (results/operators.json)
Figure 3  weight perturbation: top-10 priorities retained and items keeping their band, continuous vs gated
          (results/sensitivity_iterations.csv)

Single IEEE column width (3.5 in), 8 pt type floor, Okabe-Ito palette. Output: ../figures/*.pdf and *.png (600 dpi).
"""
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import BoundaryNorm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures"
W = 3.5
OKABE = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
                     "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8, "pdf.fonttype": 42,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6})
CHOICES = np.arange(0, 101, 5)
LOW = np.array([0, 10, 30, 50, 70, 90])
TOP = np.array([5, 25, 45, 65, 85, 100])


def save(fig, name):
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.png", dpi=600)
    plt.close(fig)


def gated(m, s):
    cap = TOP[np.searchsorted(LOW, m + 1e-9, side="right") - 1]
    v = np.minimum(s, cap)
    return CHOICES[np.searchsorted(CHOICES, v + 1e-9, side="right") - 1]


def band_map():
    m = np.linspace(0, 100, 801)
    s = np.linspace(0, 100, 801)
    M, S = np.meshgrid(m, s)
    G = gated(M, S).astype(float)
    G[S < M] = np.nan                      # a convex combination cannot fall below its weakest factor
    fig, ax = plt.subplots(figsize=(W, W * 0.82))
    cmap = plt.get_cmap("viridis", 21)
    im = ax.pcolormesh(M, S, G, cmap=cmap, norm=BoundaryNorm(np.arange(-2.5, 103, 5), cmap.N), shading="auto", rasterized=True)
    for x in np.concatenate([LOW[1:], TOP[:-1]]):
        ax.axvline(x, color="#555555", lw=0.35, ls=":")
    ax.plot([0, 100], [0, 100], color="black", lw=0.6)
    ax.annotate("infeasible: $S < m$", (72, 22), fontsize=8, ha="center")
    ax.plot([45], [58.75], marker="o", ms=4, mfc="white", mec="red", mew=1.0)
    ax.annotate("worked example\n$m=45$, $S=58.75$, $S^g=45$", (45, 58.75), xytext=(8, 80), fontsize=8,
                color="white", arrowprops=dict(arrowstyle="-", lw=0.6, color="white"))
    ax.set_xlabel("Weakest factor $m$ (%)")
    ax.set_ylabel("Continuous score $S_{item}$ (%)")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    cb = fig.colorbar(im, ax=ax, ticks=[0, 25, 45, 65, 85, 100], pad=0.02)
    cb.set_label("Gated score (%)")
    fig.subplots_adjust(left=0.15, right=0.9, bottom=0.14, top=0.97)
    save(fig, "fig2_band_map")


def operators():
    data = json.loads((ROOT / "results" / "operators.json").read_text(encoding="utf-8"))
    per = data["per_replication"]
    names = ["weighted mean", "pessimistic OWA", "majority sorting", "minimum", "EdPEx gate"]
    short = ["Mean", "OWA", "Majority", "Min", "Gate"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, W * 0.62))
    for ax, key, title in ((a1, "D1", "(a) D1"), (a2, "D5", "(b) D5")):
        vals = [per[n][key] for n in names]
        bp = ax.boxplot(vals, widths=0.6, patch_artist=True, showfliers=False, medianprops=dict(color="black", lw=0.8))
        for patch, col in zip(bp["boxes"], [OKABE[1], OKABE[4], OKABE[3], OKABE[2], OKABE[0]]):
            patch.set_facecolor(col)
            patch.set_alpha(0.8)
            patch.set_linewidth(0.5)
        ax.set_xticks(range(1, 6))
        ax.set_xticklabels(short, rotation=45, ha="right")
        ax.set_title(title, loc="left")
    a1.set_ylabel("Share of items")
    a2.set_ylabel("Spearman correlation")
    fig.subplots_adjust(left=0.13, right=0.98, bottom=0.24, top=0.9, wspace=0.45)
    save(fig, "fig4_operators")


def sensitivity():
    rows = list(csv.DictReader(open(ROOT / "results" / "sensitivity_iterations.csv", encoding="utf-8")))
    top10 = np.array([float(r["top10_overlap"]) for r in rows])
    band = np.array([float(r["band_unchanged"]) for r in rows])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, W * 0.5))
    a1.hist(top10, bins=np.arange(0.35, 1.06, 0.1), color=OKABE[1], edgecolor="white", lw=0.4)
    a1.axvline(1.0, color=OKABE[0], lw=1.2)
    a1.legend(["Gated", "Continuous"], frameon=False, loc="upper left", fontsize=8)
    a1.set_ylim(0, 7200)
    a1.set_xlabel("Top-10 priorities retained")
    a1.set_ylabel("Iterations")
    a1.set_title("(a)", loc="left")
    a2.hist(band, bins=30, color=OKABE[1], edgecolor="white", lw=0.3)
    a2.axvline(1.0, color=OKABE[0], lw=1.2)
    a2.set_xlabel("Items keeping band")
    a2.set_title("(b)", loc="left")
    fig.subplots_adjust(left=0.18, right=0.96, bottom=0.26, top=0.9, wspace=0.4)
    save(fig, "fig3_sensitivity")
    return {"top10_mean": round(float(top10.mean()), 4), "band_unchanged_mean": round(float(band.mean()), 4),
            "top10_min": round(float(top10.min()), 2), "band_unchanged_min": round(float(band.min()), 4)}


if __name__ == "__main__":
    band_map()
    operators()
    print(json.dumps(sensitivity()))
