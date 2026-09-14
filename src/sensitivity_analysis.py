"""Supplementary Material S4: Monte Carlo weight-sensitivity analysis for ADLI--LeTCI scoring.

Illustrative simulation on synthetic data. No organisational records are used.

Design (as stated in the manuscript, Section "Sensitivity Analysis"):
  * 25 synthetic departments, each assessed on the 17 items of EdPEx 2024-2027: two process
    items in each of categories 1-6 (ADLI) and five results items in category 7 (LeTCI).
  * Item and category weights are the official point values (Eqs. cat, org):
    alpha[c,i] = item points / category points, omega[c] = category points / 1,000.
  * Indicators drawn once from Beta(5, 2).
  * Targets T_item = 80; Criticality and Risk drawn once from Uniform(0, 1) (Eq. priority).
  * Baseline factor weights: equal, (0.25, 0.25, 0.25, 0.25) for both ADLI and LeTCI.
  * Each of 10,000 iterations adds Uniform(-0.10, 0.10) to every factor weight, clips at 0,
    and renormalises each weight vector to sum to 1.
  * Bands are the EdPEx scoring bands (1-6), taken of the score rounded down to a legal choice.

Outputs (written to ../results, or next to this script when that folder is absent):
  sensitivity_indicators.csv   the synthetic indicator, target, criticality and risk table
  sensitivity_iterations.csv   per-iteration summary statistics
  sensitivity_summary.json     the numbers reported in the manuscript
"""
import csv
import json
from pathlib import Path

import numpy as np

SEED = 20260914
N_DEPT, N_ITER, DELTA, TARGET = 25, 10_000, 0.10, 80.0
W_ADLI = np.full(4, 0.25)
W_LETCI = np.full(4, 0.25)
_HERE = Path(__file__).resolve().parent
OUT = _HERE.parent / "results" if (_HERE.parent / "results").is_dir() else _HERE   # flat supplementary folder

# EdPEx 2024-2027 item points (categories 1-6: process items; category 7: results items)
ITEM_POINTS = {
    "1.1": 65, "1.2": 50, "2.1": 45, "2.2": 45, "3.1": 40, "3.2": 45,
    "4.1": 45, "4.2": 45, "5.1": 40, "5.2": 45, "6.1": 40, "6.2": 45,
    "7.1": 120, "7.2": 80, "7.3": 80, "7.4": 80, "7.5": 90,
}
CODES = list(ITEM_POINTS)
CAT = np.array([int(c.split(".")[0]) for c in CODES])
PTS = np.array([ITEM_POINTS[c] for c in CODES], dtype=float)
IS_PROC = CAT <= 6
N_ITEMS = len(CODES)
assert PTS.sum() == 1000

CHOICES = np.arange(0, 101, 5)
BAND_LOW = np.array([0, 10, 30, 50, 70, 90])
BAND_TOP = np.array([5, 25, 45, 65, 85, 100])


def floor_choice(x):
    return CHOICES[np.searchsorted(CHOICES, x + 1e-9, side="right") - 1]


def band(x):
    """Band index 0..5 of a percentage rounded down to a legal choice."""
    return np.searchsorted(BAND_LOW, floor_choice(x), side="right") - 1


def cap_of(weakest):
    """u_beta(m): top of the band that contains the weakest dimension."""
    return BAND_TOP[np.searchsorted(BAND_LOW, 100 * weakest, side="right") - 1]


def org_score(items):
    """Eqs. cat and org with official points: sum of item points x item percent / 1,000."""
    return items @ PTS / 1000


def cat_scores(items):
    return np.stack([(items[..., CAT == c] @ PTS[CAT == c]) / PTS[CAT == c].sum() for c in range(1, 8)], axis=-1)


def item_scores(ind, w_p, w_r):
    return np.where(IS_PROC, 100 * ind @ w_p, 100 * ind @ w_r)


def perturb(w, rng):
    v = np.clip(w + rng.uniform(-DELTA, DELTA, size=w.shape), 0, None)
    return v / v.sum()


def top10(items, crit, risk):
    prio = np.maximum(0, TARGET - items) * crit * risk
    return set(np.argsort(-prio.ravel(), kind="stable")[:10])


def main():
    rng = np.random.default_rng(SEED)
    ind = rng.beta(5, 2, size=(N_DEPT, N_ITEMS, 4))
    crit = rng.uniform(0, 1, size=(N_DEPT, N_ITEMS))
    risk = rng.uniform(0, 1, size=(N_DEPT, N_ITEMS))
    cap = cap_of(ind.min(axis=2))                                  # (dept, items), weight-free

    items0 = item_scores(ind, W_ADLI, W_LETCI)
    g0 = np.minimum(floor_choice(np.minimum(items0, cap)), cap)
    top0, g_top0 = top10(items0, crit, risk), top10(g0, crit, risk)
    band0, g_band0 = band(items0), band(g0)

    orgs, g_orgs = np.empty((N_ITER, N_DEPT)), np.empty((N_ITER, N_DEPT))
    cats = np.empty((N_ITER, N_DEPT, 7))
    overlap, g_overlap = np.empty(N_ITER), np.empty(N_ITER)
    same_band, g_same_band, g_unchanged = np.empty(N_ITER), np.empty(N_ITER), np.empty(N_ITER)
    s_min = items0.copy()                                          # smallest continuous score seen per item
    g_changed = np.zeros_like(g0, dtype=bool)
    for k in range(N_ITER):
        items = item_scores(ind, perturb(W_ADLI, rng), perturb(W_LETCI, rng))
        g = np.minimum(floor_choice(np.minimum(items, cap)), cap)
        s_min = np.minimum(s_min, items)
        g_changed |= g != g0
        orgs[k], g_orgs[k], cats[k] = org_score(items), org_score(g), cat_scores(items)
        overlap[k] = len(top0 & top10(items, crit, risk)) / 10
        g_overlap[k] = len(g_top0 & top10(g, crit, risk)) / 10
        same_band[k] = (band(items) == band0).mean()
        g_same_band[k] = (band(g) == g_band0).mean()
        g_unchanged[k] = (g == g0).mean()

    # Proposition 2 (weight invariance): the gated score is weight-invariant on W when min_{w in W} S_item(w) >= cap.
    cond_sampled = s_min >= cap                                     # W = the sampled weight vectors
    cond_all = 100 * ind.min(axis=2) >= cap                         # W = the whole simplex (s_min = m)
    assert not (cond_sampled & g_changed).any()                     # the condition is sufficient

    summary = {
        "seed": SEED, "iterations": N_ITER, "departments": N_DEPT, "items_per_department": N_ITEMS,
        "item_and_category_weights": "EdPEx 2024-2027 official points (1,000)",
        "baseline_factor_weights": "equal (0.25 each)",
        "indicator_distribution": "Beta(5,2)", "perturbation": "Uniform(-0.10,0.10), clip at 0, renormalise",
        "baseline_org_score_mean": round(float(org_score(items0).mean()), 2),
        "org_score_sd_mean_across_departments": round(float(orgs.std(axis=0, ddof=1).mean()), 3),
        "org_score_sd_max_across_departments": round(float(orgs.std(axis=0, ddof=1).max()), 3),
        "category_score_sd_mean": round(float(cats.std(axis=0, ddof=1).mean()), 3),
        "top10_priority_overlap_mean": round(float(overlap.mean()), 4),
        "band_unchanged_mean": round(float(same_band.mean()), 4),
        "gated_baseline_org_score_mean": round(float(org_score(g0).mean()), 2),
        "gated_share_of_items_capped_at_baseline": round(float((g0 < floor_choice(items0)).mean()), 4),
        "gated_org_score_sd_mean_across_departments": round(float(g_orgs.std(axis=0, ddof=1).mean()), 3),
        "gated_item_score_unchanged_mean": round(float(g_unchanged.mean()), 4),
        "gated_items_never_changed_share": round(float((~g_changed).mean()), 4),
        "gated_top10_priority_overlap_mean": round(float(g_overlap.mean()), 4),
        "gated_band_unchanged_mean": round(float(g_same_band.mean()), 4),
        "prop2_condition_share_sampled_weights": round(float(cond_sampled.mean()), 4),
        "prop2_condition_share_all_weights": round(float(cond_all.mean()), 4),
    }

    with open(OUT / "sensitivity_indicators.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["department", "item", "category", "points", "type", "ind1", "ind2", "ind3", "ind4",
                     "target", "criticality", "risk", "baseline_item_score", "baseline_gated_score"])
        for d in range(N_DEPT):
            for i, code in enumerate(CODES):
                wr.writerow([d + 1, code, CAT[i], int(PTS[i]), "ADLI" if IS_PROC[i] else "LeTCI",
                             *np.round(ind[d, i], 6), TARGET, round(crit[d, i], 6), round(risk[d, i], 6),
                             round(float(items0[d, i]), 4), int(g0[d, i])])
    with open(OUT / "sensitivity_iterations.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["iteration", "org_score_mean", "top10_overlap", "band_unchanged", "gated_org_score_mean"])
        for k in range(N_ITER):
            wr.writerow([k + 1, round(orgs[k].mean(), 4), overlap[k], round(same_band[k], 4), round(g_orgs[k].mean(), 4)])
    (OUT / "sensitivity_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
