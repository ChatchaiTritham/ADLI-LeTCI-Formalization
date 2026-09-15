"""Supplementary Material S7: holistic band rules that no single factor decides, compared with the gate.

The EdPEx 2024-2027 scoring guidance (criteria book, p. 79) asks assessors to choose the band from the four
factors taken together, not by averaging them, and states that no single factor is to act as a gate to a higher
band; the Baldrige examiner guidance says the same. This script formalises that guidance as band rules built on
order statistics of the factor bands and compares them with the gate and with compensatory operators.

Band rules (b_(1) <= ... <= b_(4) are the bands of the four factors):
  gate           band b_(1), score capped at the top of that band                  (institutional, stricter)
  lower median   band b_(2), score clipped into that band                          (holistic, conservative)
  upper median   band b_(3), score clipped into that band                          (holistic, lenient)
  maximum        band b_(4), score clipped into that band                          (lift by one factor)
  weighted mean  compensatory average of the factors
Within the chosen band every rule except the weighted mean places the percentage by the weighted mean of the
factors, clipped into the band and rounded down to a legal percentage.

Part 1 (Proposition 3, single-factor decisiveness). Exhaustive check over all 6^4 band vectors that
  (a) under the gate, lowering any one factor to band 0 forces band 0 whatever the other three are;
  (b) under the maximum, raising any one factor to band 5 forces band 5;
  (c) under either median, replacing any one factor by any band keeps the result within the bands spanned by
      the other three factors (between their smallest and largest band).
Part 2 (desiderata on synthetic cohorts, same generator and seed as S6):
  G1 lone-low decides - among items with exactly one factor in a band below the other three, the share whose
                        band is below the lowest band of the other three (a single factor acting as a gate);
  G2 lone-high decides- among items with exactly one factor in a band above the other three, the share whose
                        band is above the highest band of the other three (a single factor lifting the band);
  R1 single-factor    - mean absolute band change when one randomly chosen factor is redrawn uniformly;
  D2 weights, D3 scale, D4 credit as in S6.
Synthetic data only. Output: ../results/holistic.json
"""
import itertools
import json
from pathlib import Path

import numpy as np
from scipy import stats

SEED = 20260915
REPLICATIONS, ITEMS, PERTURBATIONS = 200, 425, 30
_HERE = Path(__file__).resolve().parent
OUT = _HERE.parent / "results" if (_HERE.parent / "results").is_dir() else _HERE

CHOICES = np.arange(0, 101, 5)
LOW = np.array([0, 10, 30, 50, 70, 90])
TOP = np.array([5, 25, 45, 65, 85, 100])


def floor_choice(x):
    return CHOICES[np.clip(np.searchsorted(CHOICES, x + 1e-9, side="right") - 1, 0, None)]


def beta(p):
    return np.searchsorted(LOW, p + 1e-9, side="right") - 1


def band(score):
    return beta(floor_choice(score))


def order_band_rule(k, clip_low=True):
    def op(x, w):
        fb = np.sort(beta(100 * x), axis=-1)[..., k]
        s = 100 * x @ w
        lo = LOW[fb] if clip_low else 0
        return floor_choice(np.minimum(np.maximum(s, lo), TOP[fb]))
    return op


def op_mean(x, w):
    return floor_choice(100 * x @ w)


OPERATORS = {"weighted mean": op_mean, "gate": order_band_rule(0, clip_low=False),
             "lower median": order_band_rule(1), "upper median": order_band_rule(2), "maximum": order_band_rule(3)}
BAND_RULE = {"gate": 0, "lower median": 1, "upper median": 2, "maximum": 3}


def check_decisiveness():
    vecs = np.array(list(itertools.product(range(6), repeat=4)))
    res = {}
    for name, k in BAND_RULE.items():
        forced_low = forced_high = within = True
        for v in vecs:
            for i in range(4):
                others = np.delete(v, i)
                results = [np.sort(np.insert(others, i, nb))[k] for nb in range(6)]
                forced_low &= results[0] == 0 if k == 0 else True
                forced_high &= results[5] == 5 if k == 3 else True
                within &= all(others.min() <= r <= others.max() for r in results)
        res[name] = {"low_factor_forces_band_0": bool(forced_low) if k == 0 else None,
                     "high_factor_forces_band_5": bool(forced_high) if k == 3 else None,
                     "result_within_range_of_other_three": bool(within)}
    res["band_vectors_checked"] = int(len(vecs))
    return res


def perturb(w, rng):
    v = np.clip(w + rng.uniform(-0.10, 0.10, size=w.shape), 0, None)
    return v / v.sum()


def metrics(op, x, rng):
    w0 = np.full(4, 0.25)
    sc = op(x, w0)
    b = band(sc)
    fb = np.sort(beta(100 * x), axis=1)
    lone_low = fb[:, 0] < fb[:, 1]
    lone_high = fb[:, 3] > fb[:, 2]
    g1 = float((b[lone_low] < fb[lone_low, 1]).mean()) if lone_low.any() else 0.0
    g2 = float((b[lone_high] > fb[lone_high, 2]).mean()) if lone_high.any() else 0.0
    x2 = x.copy()
    idx = rng.integers(0, 4, size=len(x))
    x2[np.arange(len(x)), idx] = rng.random(len(x))
    r1 = float(np.abs(band(op(x2, w0)) - b).mean())
    changed = np.zeros(len(x))
    for _ in range(PERTURBATIONS):
        changed += band(op(x, perturb(w0, rng))) != b
    d2 = float((changed / PERTURBATIONS).mean())
    counts = np.bincount(b, minlength=6) / len(b)
    nz = counts[counts > 0]
    d3 = float(-(nz * np.log(nz)).sum() / np.log(6))
    d4 = float(stats.spearmanr(sc, x.mean(axis=1)).statistic)
    return {"G1": g1, "G2": g2, "R1": r1, "D2": d2, "D3": d3, "D4": d4}


def main():
    rng = np.random.default_rng(SEED)
    decisiveness = check_decisiveness()
    names = list(OPERATORS)
    keys = ("G1", "G2", "R1", "D2", "D3", "D4")
    per = {n: {k: [] for k in keys} for n in names}
    shares = []
    for _ in range(REPLICATIONS):
        a, b = rng.uniform(1, 6, size=2)
        spread = rng.uniform(0, 0.25)
        base = rng.beta(a, b, size=(ITEMS, 1))
        x = np.clip(base + rng.normal(0, spread, size=(ITEMS, 4)), 0, 1)
        fb = np.sort(beta(100 * x), axis=1)
        shares.append(float(((fb[:, 0] < fb[:, 1]) | (fb[:, 3] > fb[:, 2])).mean()))
        sub = rng.integers(0, 2**32)
        for n in names:
            for k, v in metrics(OPERATORS[n], x, np.random.default_rng(sub)).items():
                per[n][k].append(v)
    summary = {n: {k: {"median": float(np.median(v)), "q1": float(np.percentile(v, 25)), "q3": float(np.percentile(v, 75))}
                   for k, v in per[n].items()} for n in names}
    contrasts = []
    for k, a_, b_ in (("R1", "lower median", "gate"), ("D4", "lower median", "gate"),
                      ("R1", "lower median", "weighted mean"), ("D2", "lower median", "weighted mean"),
                      ("R1", "upper median", "lower median")):
        diff = np.array(per[a_][k]) - np.array(per[b_][k])
        boots = np.median(rng.choice(diff, size=(5000, len(diff)), replace=True), axis=1)
        contrasts.append({"measure": k, "rule": a_, "versus": b_, "median_difference": float(np.median(diff)),
                          "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
                          "share_of_replications_favouring_rule": float((diff < 0).mean() if k in ("R1", "D2") else (diff > 0).mean())})
    out = {"seed": SEED, "replications": REPLICATIONS, "items_per_replication": ITEMS,
           "decisiveness": decisiveness, "contrasts": contrasts,
           "median_share_items_with_lone_outlier_factor": float(np.median(shares)),
           "operators": summary,
           "per_replication": {n: {k: [round(float(v), 5) for v in per[n][k]] for k in keys} for n in names}}
    (OUT / "holistic.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(decisiveness, indent=1))
    print("items with a lone outlier factor (median share):", out["median_share_items_with_lone_outlier_factor"])
    for n in names:
        print(f"{n:14s} " + "  ".join(f"{k} {summary[n][k]['median']:.3f}" for k in keys))


if __name__ == "__main__":
    main()
