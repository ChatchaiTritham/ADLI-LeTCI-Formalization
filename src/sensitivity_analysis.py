"""Supplementary Material S4: Monte Carlo weight-sensitivity analysis for ADLI--LeTCI scoring.

Illustrative simulation on synthetic data. No organisational records are used.

Design (as stated in the manuscript, Section "Sensitivity Analysis"):
  * 25 synthetic departments, 10 assessment items each. Items 1-6 are process items,
    one in each of categories 1-6 (ADLI, Eq. adli); items 7-10 are results items in
    category 7 (LeTCI, Eq. letci). Equal item weights within a category and equal
    category weights omega[c] = 1/7 (Eqs. cat, org).
  * Indicators drawn once from Beta(5, 2).
  * Targets T_item = 80; Criticality and Risk drawn once from Uniform(0, 1) (Eq. priority).
  * Baseline weights ADLI (0.30, 0.30, 0.20, 0.20), LeTCI (0.35, 0.25, 0.25, 0.15).
  * Each of 10,000 iterations adds Uniform(-0.10, 0.10) to every weight, clips at 0,
    and renormalises each weight vector to sum to 1.

Outputs (written to ../results):
  sensitivity_indicators.csv   the synthetic indicator, target, criticality and risk table
  sensitivity_iterations.csv   per-iteration summary statistics
  sensitivity_summary.json     the numbers reported in the manuscript
"""
import csv, json
from pathlib import Path

import numpy as np

SEED = 20260913
N_DEPT, N_ITER, DELTA, TARGET = 25, 10_000, 0.10, 80.0
W_ADLI = np.array([0.30, 0.30, 0.20, 0.20])
W_LETCI = np.array([0.35, 0.25, 0.25, 0.15])
PROC_ITEMS, RES_ITEMS = 6, 4          # categories 1-6 one item each; category 7 four items
OUT = Path(__file__).resolve().parent.parent / "results"


CHOICES = np.array([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100])
BAND_LOW = np.array([0, 10, 30, 50, 70, 90])
BAND_TOP = np.array([5, 25, 45, 65, 85, 100])


def gate(items, weakest):
    """Eq. gate: cap each item at the top of the band of its weakest dimension, round down to a legal choice."""
    cap = BAND_TOP[np.searchsorted(BAND_LOW, 100 * weakest, side="right") - 1]
    capped = np.minimum(items, cap)
    return CHOICES[np.searchsorted(CHOICES, capped + 1e-9, side="right") - 1]


def maturity(s):
    return np.digitize(s, [20, 40, 60, 80])   # 0 Reactive .. 4 Role Model


def score(ind_p, ind_r, w_p, w_r):
    """Item, category and organisational scores for every department."""
    item_p = 100 * ind_p @ w_p                       # (dept, 6)
    item_r = 100 * ind_r @ w_r                       # (dept, 4)
    cat = np.concatenate([item_p, item_r.mean(axis=1, keepdims=True)], axis=1)  # (dept, 7)
    org = cat.mean(axis=1)                           # omega = 1/7
    items = np.concatenate([item_p, item_r], axis=1)  # (dept, 10)
    return items, cat, org


def perturb(w, rng):
    v = np.clip(w + rng.uniform(-DELTA, DELTA, size=w.shape), 0, None)
    return v / v.sum()


def main():
    rng = np.random.default_rng(SEED)
    ind_p = rng.beta(5, 2, size=(N_DEPT, PROC_ITEMS, 4))
    ind_r = rng.beta(5, 2, size=(N_DEPT, RES_ITEMS, 4))
    crit = rng.uniform(0, 1, size=(N_DEPT, 10))
    risk = rng.uniform(0, 1, size=(N_DEPT, 10))

    weakest = np.concatenate([ind_p.min(axis=2), ind_r.min(axis=2)], axis=1)   # (dept, 10)
    items0, cat0, org0 = score(ind_p, ind_r, W_ADLI, W_LETCI)
    g_items0 = gate(items0, weakest)
    g_org0 = (np.concatenate([g_items0[:, :PROC_ITEMS], g_items0[:, PROC_ITEMS:].mean(axis=1, keepdims=True)], axis=1)).mean(axis=1)
    g_prio0 = np.maximum(0, TARGET - g_items0) * crit * risk
    g_top0 = set(np.argsort(-g_prio0.ravel(), kind="stable")[:10])
    prio0 = np.maximum(0, TARGET - items0) * crit * risk
    top0 = set(np.argsort(-prio0.ravel(), kind="stable")[:10])
    mat0 = maturity(items0)

    orgs = np.empty((N_ITER, N_DEPT))
    cats = np.empty((N_ITER, N_DEPT, 7))
    overlap = np.empty(N_ITER)
    same_mat = np.empty(N_ITER)
    g_orgs = np.empty((N_ITER, N_DEPT))
    g_overlap = np.empty(N_ITER)
    g_same_mat = np.empty(N_ITER)
    g_unchanged_items = np.empty(N_ITER)
    for k in range(N_ITER):
        items, cat, org = score(ind_p, ind_r, perturb(W_ADLI, rng), perturb(W_LETCI, rng))
        prio = np.maximum(0, TARGET - items) * crit * risk
        overlap[k] = len(top0 & set(np.argsort(-prio.ravel(), kind="stable")[:10])) / 10
        same_mat[k] = (maturity(items) == mat0).mean()
        orgs[k], cats[k] = org, cat
        g_items = gate(items, weakest)
        g_orgs[k] = np.concatenate([g_items[:, :PROC_ITEMS], g_items[:, PROC_ITEMS:].mean(axis=1, keepdims=True)], axis=1).mean(axis=1)
        g_prio = np.maximum(0, TARGET - g_items) * crit * risk
        g_overlap[k] = len(g_top0 & set(np.argsort(-g_prio.ravel(), kind="stable")[:10])) / 10
        g_same_mat[k] = (maturity(g_items) == maturity(g_items0)).mean()
        g_unchanged_items[k] = (g_items == g_items0).mean()

    sd_org = orgs.std(axis=0, ddof=1)          # per department, across perturbations
    sd_cat = cats.std(axis=0, ddof=1)          # per department x category
    summary = {
        "seed": SEED, "iterations": N_ITER, "departments": N_DEPT, "items_per_department": 10,
        "indicator_distribution": "Beta(5,2)", "perturbation": "Uniform(-0.10,0.10), clip at 0, renormalise",
        "baseline_org_score_mean": round(float(org0.mean()), 2),
        "org_score_sd_mean_across_departments": round(float(sd_org.mean()), 3),
        "org_score_sd_max_across_departments": round(float(sd_org.max()), 3),
        "category_score_sd_mean": round(float(sd_cat.mean()), 3),
        "org_score_mean_percentile_2_5": round(float(np.percentile(orgs.mean(axis=1), 2.5)), 2),
        "org_score_mean_percentile_97_5": round(float(np.percentile(orgs.mean(axis=1), 97.5)), 2),
        "top10_priority_overlap_mean": round(float(overlap.mean()), 4),
        "maturity_level_unchanged_mean": round(float(same_mat.mean()), 4),
        "gated_baseline_org_score_mean": round(float(g_org0.mean()), 2),
        "gated_share_of_items_capped_at_baseline": round(float((g_items0 < np.floor(items0 / 5) * 5).mean()), 4),
        "gated_org_score_sd_mean_across_departments": round(float(g_orgs.std(axis=0, ddof=1).mean()), 3),
        "gated_item_score_unchanged_mean": round(float(g_unchanged_items.mean()), 4),
        "gated_top10_priority_overlap_mean": round(float(g_overlap.mean()), 4),
        "gated_maturity_level_unchanged_mean": round(float(g_same_mat.mean()), 4),
    }

    with open(OUT / "sensitivity_indicators.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["department", "item", "category", "type", "ind1", "ind2", "ind3", "ind4",
                     "target", "criticality", "risk", "baseline_item_score"])
        for d in range(N_DEPT):
            for i in range(10):
                ind = ind_p[d, i] if i < PROC_ITEMS else ind_r[d, i - PROC_ITEMS]
                wr.writerow([d + 1, i + 1, min(i + 1, 7), "ADLI" if i < PROC_ITEMS else "LeTCI",
                             *np.round(ind, 6), TARGET, round(crit[d, i], 6), round(risk[d, i], 6),
                             round(items0[d, i], 4)])
    with open(OUT / "sensitivity_iterations.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["iteration", "org_score_mean", "top10_overlap", "maturity_unchanged"])
        for k in range(N_ITER):
            wr.writerow([k + 1, round(orgs[k].mean(), 4), overlap[k], round(same_mat[k], 4)])
    (OUT / "sensitivity_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
