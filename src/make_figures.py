"""Data figures for the IEEE Access article, drawn only from the equations and the committed result files.

Figure 2  band map of the gated score: weakest factor m against continuous score S (Eq. gate, Theorem 1)
Figure 3  weight perturbation: top-10 priorities retained and items keeping their band, continuous vs gated
          (results/sensitivity_iterations.csv)
Figure 4  operator comparison: distribution of D1 and D5 over synthetic cohorts (results/operators.json)
Figure 5  median rules vs gate: single-factor sensitivity R1 per rule (results/holistic.json) and the paired
          R1 difference as a function of the within-item imbalance of the generator. The generator parameters
          are not stored in holistic.json; they are recovered by replaying the random stream of holistic.py
          (same seed, same call order), and the replay is checked against the stored lone-outlier share.

Single IEEE column width (3.5 in), Times at 8 pt to match the journal body, Okabe-Ito palette,
whiskers span the full range. Output: ../figures/*.pdf and *.png (600 dpi).
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
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
                     "mathtext.fontset": "stix", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
                     "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 7.5, "pdf.fonttype": 42,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
                     "xtick.major.width": 0.6, "ytick.major.width": 0.6})
CHOICES = np.arange(0, 101, 5)
LOW = np.array([0, 10, 30, 50, 70, 90])
TOP = np.array([5, 25, 45, 65, 85, 100])
FULL_RANGE = dict(whis=(0, 100), widths=0.6, patch_artist=True, showfliers=False,
                  medianprops=dict(color="black", lw=0.9), whiskerprops=dict(lw=0.6), capprops=dict(lw=0.6))


def save(fig, name):
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.png", dpi=600)
    plt.close(fig)


def gated(m, s):
    cap = TOP[np.searchsorted(LOW, m + 1e-9, side="right") - 1]
    v = np.minimum(s, cap)
    return CHOICES[np.searchsorted(CHOICES, v + 1e-9, side="right") - 1]


def colour_boxes(bp, cols):
    for patch, col in zip(bp["boxes"], cols):
        patch.set_facecolor(col)
        patch.set_alpha(0.85)
        patch.set_linewidth(0.6)


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
    ax.annotate("infeasible: $S_{item} < m$", (72, 22), ha="center")
    ax.plot([45], [58.75], marker="o", ms=4, mfc="white", mec="#D55E00", mew=1.0)
    ax.annotate("worked example\n$m=45$, $S_{item}=58.75$, $S^{g}_{item}=45$", (45, 58.75), xytext=(6, 80),
                color="white", arrowprops=dict(arrowstyle="-", lw=0.6, color="white"))
    ax.set_xlabel("Weakest factor $m$ (%)")
    ax.set_ylabel("Continuous score $S_{item}$ (%)")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    cb = fig.colorbar(im, ax=ax, ticks=[0, 5, 25, 45, 65, 85, 100], pad=0.02)
    cb.set_label("Gated score $S^{g}_{item}$ (%)")
    cb.outline.set_linewidth(0.6)
    fig.subplots_adjust(left=0.14, right=0.9, bottom=0.13, top=0.97)
    save(fig, "fig2_band_map")


def sensitivity():
    rows = list(csv.DictReader(open(ROOT / "results" / "sensitivity_iterations.csv", encoding="utf-8")))
    top10 = np.array([float(r["top10_overlap"]) for r in rows])
    band = np.array([float(r["band_unchanged"]) for r in rows])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, W * 0.6))
    vals, counts = np.unique(np.round(top10, 1), return_counts=True)
    a1.bar(vals, counts / len(top10), width=0.07, color=OKABE[1], edgecolor="white", lw=0.4, label="Continuous score")
    a1.axvline(1.0, color=OKABE[0], lw=1.4, label="Gated score (every iteration)")
    a1.set_xlim(0.55, 1.05)
    a1.set_xticks([0.6, 0.7, 0.8, 0.9, 1.0])
    a1.set_xlabel("Top-10 priorities retained")
    a1.set_ylabel("Share of iterations")
    a1.set_title(f"(a) mean {top10.mean():.2f}", loc="left")
    edges = np.linspace(band.min() - 0.0025, 1.0025, 31)
    a2.hist(band, bins=edges, weights=np.full(len(band), 1 / len(band)), color=OKABE[1], edgecolor="white", lw=0.3)
    a2.axvline(1.0, color=OKABE[0], lw=1.4)
    a2.set_xticks([0.9, 0.95, 1.0])
    a2.set_xlabel("Items keeping their band")
    a2.set_title(f"(b) mean {band.mean():.2f}", loc="left")
    h, l = a1.get_legend_handles_labels()
    fig.legend(h, l, frameon=False, loc="upper center", ncol=2, handlelength=1.2, bbox_to_anchor=(0.5, 1.0))
    fig.subplots_adjust(left=0.15, right=0.97, bottom=0.2, top=0.8, wspace=0.35)
    save(fig, "fig3_sensitivity")
    return {"top10_mean": round(float(top10.mean()), 4), "band_unchanged_mean": round(float(band.mean()), 4)}


def operators():
    data = json.loads((ROOT / "results" / "operators.json").read_text(encoding="utf-8"))
    per = data["per_replication"]
    names = ["weighted mean", "pessimistic OWA", "majority sorting", "minimum", "EdPEx gate"]
    short = ["Mean", "OWA", "Majority", "Min", "Gate"]
    cols = [OKABE[1], OKABE[4], OKABE[3], OKABE[2], OKABE[0]]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, W * 0.62))
    for ax, key, title, ylab in ((a1, "D1", "(a) D1, above weakest band", "Share of items"),
                                 (a2, "D5", "(b) D5, within-band credit", "Spearman correlation")):
        colour_boxes(ax.boxplot([per[n][key] for n in names], **FULL_RANGE), cols)
        ax.set_xticks(range(1, 6))
        ax.set_xticklabels(short, rotation=40, ha="right")
        ax.set_title(title, loc="left")
        ax.set_ylabel(ylab)
    a1.set_ylim(-0.03, 1.0)
    a2.set_ylim(0, 1.03)
    fig.subplots_adjust(left=0.13, right=0.98, bottom=0.22, top=0.9, wspace=0.45)
    save(fig, "fig4_operators")


def replay_holistic_parameters(seed, reps, items):
    """Recover (a, b, spread) of each replication of holistic.py by replaying its random stream."""
    rng = np.random.default_rng(seed)
    params, shares = [], []
    for _ in range(reps):
        a, b = rng.uniform(1, 6, size=2)
        spread = rng.uniform(0, 0.25)
        base = rng.beta(a, b, size=(items, 1))
        x = np.clip(base + rng.normal(0, spread, size=(items, 4)), 0, 1)
        fb = np.sort(np.searchsorted(LOW, 100 * x + 1e-9, side="right") - 1, axis=1)
        shares.append(float(((fb[:, 0] < fb[:, 1]) | (fb[:, 3] > fb[:, 2])).mean()))
        rng.integers(0, 2**32)
        params.append((a, b, spread))
    return np.array(params), float(np.median(shares))


def holistic():
    data = json.loads((ROOT / "results" / "holistic.json").read_text(encoding="utf-8"))
    per = data["per_replication"]
    params, share = replay_holistic_parameters(data["seed"], data["replications"], data["items_per_replication"])
    if abs(share - data["median_share_items_with_lone_outlier_factor"]) > 1e-12:
        raise SystemExit("replay of holistic.py random stream does not match holistic.json")
    names = ["weighted mean", "gate", "lower median", "upper median", "maximum"]
    short = ["Mean", "Gate $R_1$", "Median $R_2$", "Median $R_3$", "Max $R_4$"]
    cols = [OKABE[1], OKABE[0], OKABE[2], OKABE[4], OKABE[5]]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, W * 0.64), gridspec_kw=dict(width_ratios=[1, 1.15]))
    colour_boxes(a1.boxplot([per[n]["R1"] for n in names], **FULL_RANGE), cols)
    a1.set_xticks(range(1, 6))
    a1.set_xticklabels(short, rotation=40, ha="right")
    a1.set_ylabel("R1, mean band change")
    a1.set_title("(a) one factor redrawn", loc="left")
    spread = params[:, 2]
    diff = np.array(per["lower median"]["R1"]) - np.array(per["gate"]["R1"])
    a2.axhline(0, color="#555555", lw=0.5)
    a2.scatter(spread, diff, s=5, color=OKABE[2], edgecolor="none", alpha=0.8)
    order = np.argsort(spread)
    k = 25
    smooth = np.convolve(diff[order], np.ones(k) / k, mode="valid")
    a2.plot(spread[order][k // 2: k // 2 + len(smooth)], smooth, color="black", lw=0.9, label=f"running mean ({k})")
    a2.set_xlabel("Within-item imbalance (SD)")
    a2.set_ylabel("R1: $R_2$ minus gate")
    a2.set_title("(b) sweep over generator", loc="left")
    a2.legend(frameon=False, loc="lower left", handlelength=1.2)
    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.27, top=0.9, wspace=0.5)
    save(fig, "fig5_holistic")
    lo, hi = spread < 0.05, spread >= 0.15
    return {"replay_share": share, "diff_median_spread_lt_0.05": round(float(np.median(diff[lo])), 3),
            "diff_median_spread_ge_0.15": round(float(np.median(diff[hi])), 3),
            "share_favouring_R2_spread_ge_0.05": round(float((diff[spread >= 0.05] < 0).mean()), 3),
            "n_lt_0.05": int(lo.sum()), "n_ge_0.15": int(hi.sum())}


if __name__ == "__main__":
    band_map()
    operators()
    print(json.dumps(sensitivity()))
    print(json.dumps(holistic()))
