"""Supplementary Material S6: band decomposition check and comparison of aggregation operators.

Part 1 (Theorem 1). For every convex weight vector the band of the gated score is the band of the weakest
factor, B(S^g) = beta(m), and the gated score lies in that band: l_beta(m) <= S^g <= u_beta(m). Checked
exhaustively on a grid of indicator vectors and weight vectors, and on random continuous inputs.

Part 2 (operator comparison). Five aggregation operators from the multi-criteria literature are compared on
synthetic cohorts against four desiderata taken from the scoring guidelines and from decision-aid practice:
  D1 ceiling  - share of items whose band exceeds the band of the weakest factor (the guidelines require 0);
  D2 weights  - share of items whose band changes when factor weights are perturbed by +/-0.10;
  D3 scale    - normalised entropy of the band distribution (use of the six-band scale);
  D4 credit   - Spearman correlation between the awarded score and the mean factor rating
                (how far strengths other than the weakest are still credited);
  D5 in-band  - added after Theorem 1 showed that the gate and the minimum assign identical bands: Spearman
                correlation, within each weakest-factor band, between the awarded score and the mean of the
                three stronger factors, averaged over bands weighted by their size.
Operators: weighted mean (compensatory), minimum (conjunctive, noncompensatory), pessimistic OWA,
majority sorting (a band is supported when at least three of four factors reach it) capped as the gate,
and the EdPEx gate. Paired differences over replications are tested with the Wilcoxon signed-rank test,
with Holm correction, rank-biserial effect size and 95% bootstrap confidence intervals.

Synthetic data only. Output: ../results/operators.json (or next to this script when that folder is absent)
"""
import itertools
import json
from pathlib import Path

import numpy as np
from scipy import stats

SEED = 20260915
REPLICATIONS, ITEMS, PERTURBATIONS, BOOT = 200, 425, 30, 5000
_HERE = Path(__file__).resolve().parent
OUT = _HERE.parent / "results" if (_HERE.parent / "results").is_dir() else _HERE

CHOICES = np.arange(0, 101, 5)
LOW = np.array([0, 10, 30, 50, 70, 90])
TOP = np.array([5, 25, 45, 65, 85, 100])
OWA_W = np.array([0.4, 0.3, 0.2, 0.1])          # weights on factors sorted from lowest to highest


def floor_choice(x):
    return CHOICES[np.clip(np.searchsorted(CHOICES, x + 1e-9, side="right") - 1, 0, None)]


def beta(p):
    """Band index 0..5 of a percentage (largest lower bound <= p)."""
    return np.searchsorted(LOW, p + 1e-9, side="right") - 1


def band(score):
    return beta(floor_choice(score))


def weighted(x, w):
    return 100 * x @ w


def op_gate(x, w):
    return floor_choice(np.minimum(weighted(x, w), TOP[beta(100 * x.min(axis=-1))]))


def op_mean(x, w):
    return floor_choice(weighted(x, w))


def op_min(x, w):
    return floor_choice(100 * x.min(axis=-1))


def op_owa(x, w):
    return floor_choice(100 * np.sort(x, axis=-1) @ OWA_W)


def op_majority(x, w):
    # band k is supported when at least 3 of the 4 factors reach its lower bound; third-lowest factor decides
    third = np.sort(x, axis=-1)[..., 1]
    return floor_choice(np.minimum(weighted(x, w), TOP[beta(100 * third)]))


OPERATORS = {"weighted mean": op_mean, "minimum": op_min, "pessimistic OWA": op_owa,
             "majority sorting": op_majority, "EdPEx gate": op_gate}


# --------------------------------------------------------------------------- Part 1
def check_theorem(rng):
    grid = np.arange(0, 1.0001, 0.05)
    xs = np.array(list(itertools.product(grid, repeat=4)))                      # 194,481 vectors
    steps = [v for v in itertools.product(range(5), repeat=4) if sum(v) == 4]   # 35 weight vectors
    ws = np.array(steps, dtype=float) / 4
    violations, checked = 0, 0
    lhs_band = None
    for w in ws:
        s = weighted(xs, w)
        g = op_gate(xs, w)
        wb = beta(100 * xs.min(axis=1))
        violations += int(((band(g) != wb) | (g < LOW[wb]) | (g > TOP[wb])).sum())
        checked += len(xs)
    xr = rng.random((200_000, 4))
    wr = rng.dirichlet(np.ones(4), size=200_000)
    s = np.einsum("ij,ij->i", xr, wr) * 100
    g = floor_choice(np.minimum(s, TOP[beta(100 * xr.min(axis=1))]))
    wb = beta(100 * xr.min(axis=1))
    violations += int(((band(g) != wb) | (g < LOW[wb]) | (g > TOP[wb])).sum())
    checked += len(xr)
    return {"cases_checked": checked, "violations": violations}


# --------------------------------------------------------------------------- Part 2
def perturb(w, rng):
    v = np.clip(w + rng.uniform(-0.10, 0.10, size=w.shape), 0, None)
    return v / v.sum()


def metrics(op, x, rng):
    w0 = np.full(4, 0.25)
    sc = op(x, w0)
    b = band(sc)
    wb = beta(100 * x.min(axis=1))
    d1 = float((b > wb).mean())
    changed = np.zeros(len(x))
    for _ in range(PERTURBATIONS):
        changed += band(op(x, perturb(w0, rng))) != b
    d2 = float((changed / PERTURBATIONS).mean())
    counts = np.bincount(b, minlength=6) / len(b)
    nz = counts[counts > 0]
    d3 = float(-(nz * np.log(nz)).sum() / np.log(6))
    d4 = float(stats.spearmanr(sc, x.mean(axis=1)).statistic)
    stronger = np.sort(x, axis=1)[:, 1:].mean(axis=1)
    num = den = 0.0
    for k in range(6):
        sel = wb == k
        if sel.sum() >= 10 and np.ptp(sc[sel]) > 0:
            num += sel.sum() * stats.spearmanr(sc[sel], stronger[sel]).statistic
            den += sel.sum()
        elif sel.sum() >= 10:
            den += sel.sum()          # constant scores within the band credit nothing
    d5 = float(num / den) if den else 0.0
    return d1, d2, d3, d4, d5


def paired(a, b, rng):
    diff = np.asarray(a) - np.asarray(b)
    if np.allclose(diff, 0):
        return {"median_difference": 0.0, "ci95": [0.0, 0.0], "wilcoxon_p": 1.0, "rank_biserial": 0.0}
    res = stats.wilcoxon(a, b, zero_method="wilcox")
    nz = diff[diff != 0]
    ranks = stats.rankdata(np.abs(nz))
    rbc = float((ranks[nz > 0].sum() - ranks[nz < 0].sum()) / ranks.sum())
    boots = np.median(rng.choice(diff, size=(BOOT, len(diff)), replace=True), axis=1)
    return {"median_difference": float(np.median(diff)), "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
            "wilcoxon_p": float(res.pvalue), "rank_biserial": rbc}


def main():
    rng = np.random.default_rng(SEED)
    theorem = check_theorem(rng)

    names = list(OPERATORS)
    per = {n: {k: [] for k in ("D1", "D2", "D3", "D4", "D5")} for n in names}
    for _ in range(REPLICATIONS):
        a, b = rng.uniform(1, 6, size=2)                        # cohort-level factor distribution
        spread = rng.uniform(0, 0.25)                           # within-item imbalance between factors
        base = rng.beta(a, b, size=(ITEMS, 1))
        x = np.clip(base + rng.normal(0, spread, size=(ITEMS, 4)), 0, 1)
        sub = rng.integers(0, 2**32)
        for n in names:
            vals = metrics(OPERATORS[n], x, np.random.default_rng(sub))
            for k, v in zip(("D1", "D2", "D3", "D4", "D5"), vals):
                per[n][k].append(v)

    summary = {n: {k: {"median": float(np.median(v)), "q1": float(np.percentile(v, 25)), "q3": float(np.percentile(v, 75))}
                   for k, v in per[n].items()} for n in names}
    # planned comparisons: the gate against each alternative on the desideratum that alternative is weakest on
    plan = [("D1", "weighted mean"), ("D1", "pessimistic OWA"), ("D1", "majority sorting"),
            ("D2", "weighted mean"), ("D2", "majority sorting"),
            ("D3", "minimum"), ("D4", "minimum"), ("D4", "pessimistic OWA"), ("D5", "minimum")]
    tests = []
    for k, other in plan:
        r = paired(per["EdPEx gate"][k], per[other][k], rng)
        tests.append({"desideratum": k, "gate_vs": other, **r})
    ps = [t["wilcoxon_p"] for t in tests]
    order = np.argsort(ps)
    adj = np.empty(len(ps))
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    for t, a_ in zip(tests, adj):
        t["holm_p"] = float(a_)

    out = {"seed": SEED, "replications": REPLICATIONS, "items_per_replication": ITEMS,
           "perturbations_per_item_set": PERTURBATIONS, "theorem1": theorem,
           "operators": summary, "planned_tests": tests,
           "per_replication": {n: {k: [round(float(x), 5) for x in v] for k, v in per[n].items()} for n in names}}
    (OUT / "operators.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("Theorem 1:", theorem)
    for n in names:
        print(f"{n:18s} " + "  ".join(f"{k} {summary[n][k]['median']:.3f}" for k in ("D1", "D2", "D3", "D4", "D5")))
    for t in tests:
        print(f"gate vs {t['gate_vs']:17s} {t['desideratum']}: median diff {t['median_difference']:+.3f} "
              f"CI [{t['ci95'][0]:+.3f},{t['ci95'][1]:+.3f}] Holm p {t['holm_p']:.2e} r {t['rank_biserial']:+.2f}")


if __name__ == "__main__":
    main()
