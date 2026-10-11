"""Supplementary Material S8: quantities added in revision, from the committed result files and seeded replays.

1. Share of the 200 cohorts in which each planned gate-vs-alternative difference of Table V holds
   (from results/operators.json, per-replication values).
2. An ordinal-only version of R1: the share of items whose band changes when one factor is redrawn,
   replaying holistic.py exactly (same seed, same random-stream order), so no band indices are averaged.
3. Check that every order-statistic band rule R_r is a noncompensatory k-out-of-4 sorting:
   band >= j  iff  at least 5 - r factors have band >= j, over all 6^4 band vectors.
4. Check of the Lemma's two premises on all symmetric rules built from a counterexample family:
   the rounded-down mean is symmetric, idempotent and monotone but does not commute with a
   non-injective nondecreasing map of the band scale.
Output: ../results/review_extras.json
"""
import itertools
import json
from pathlib import Path

import numpy as np

import holistic as H

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" if (ROOT / "results").is_dir() else Path(__file__).resolve().parent


def table_v_shares():
    d = json.loads((ROOT / "results" / "operators.json").read_text(encoding="utf-8"))
    per = d["per_replication"]
    lower_better = {"D1", "D2"}
    out = []
    for t in d["planned_tests"]:
        k, other = t["desideratum"], t["gate_vs"]
        diff = np.array(per["EdPEx gate"][k]) - np.array(per[other][k])
        fav = (diff < 0) if k in lower_better else (diff > 0)
        out.append({"desideratum": k, "gate_vs": other, "median_difference": round(t["median_difference"], 3),
                    "share_favouring_gate": round(float(fav.mean()), 3), "share_tied": round(float((diff == 0).mean()), 3)})
    return out


def ordinal_r1():
    rng = np.random.default_rng(H.SEED)
    H.check_decisiveness()
    names = list(H.OPERATORS)
    share = {n: [] for n in names}
    r1 = {n: [] for n in names}
    for _ in range(H.REPLICATIONS):
        a, b = rng.uniform(1, 6, size=2)
        spread = rng.uniform(0, 0.25)
        base = rng.beta(a, b, size=(H.ITEMS, 1))
        x = np.clip(base + rng.normal(0, spread, size=(H.ITEMS, 4)), 0, 1)
        sub = rng.integers(0, 2**32)
        for n in names:
            r = np.random.default_rng(sub)
            w0 = np.full(4, 0.25)
            b0 = H.band(H.OPERATORS[n](x, w0))
            x2 = x.copy()
            idx = r.integers(0, 4, size=len(x))
            x2[np.arange(len(x)), idx] = r.random(len(x))
            b2 = H.band(H.OPERATORS[n](x2, w0))
            share[n].append(float((b2 != b0).mean()))
            r1[n].append(round(float(np.abs(b2 - b0).mean()), 5))
    ref = json.loads((ROOT / "results" / "holistic.json").read_text(encoding="utf-8"))
    med = {n: round(float(np.median(v)), 3) for n, v in share.items()}
    diff = np.array(share["lower median"]) - np.array(share["gate"])
    return {"median_share_band_changed": med,
            "lower_median_minus_gate_median": round(float(np.median(diff)), 3),
            "share_of_cohorts_favouring_lower_median": round(float((diff < 0).mean()), 3),
            "replay_consistent_with_holistic_json": all(
                r1[n] == ref["per_replication"][n]["R1"] for n in names)}


def sorting_check():
    vecs = np.array(list(itertools.product(range(6), repeat=4)))
    s = np.sort(vecs, axis=1)
    ok = {}
    for r in range(1, 5):
        good = True
        for j in range(6):
            lhs = s[:, r - 1] >= j
            rhs = (vecs >= j).sum(axis=1) >= 5 - r
            good &= bool((lhs == rhs).all())
        ok[f"R{r}_is_{5 - r}_of_4_sorting"] = good
    return ok


def lemma_counterexample():
    vecs = list(itertools.product(range(6), repeat=4))
    fmean = lambda v: int(np.floor(np.mean(v)))
    phi = lambda t: min(t, 2)                       # merge bands 2..5 into band 2 (nondecreasing, not injective)
    sym = all(fmean(v) == fmean(tuple(sorted(v))) for v in vecs)
    idem = all(fmean((k,) * 4) == k for k in range(6))
    violations = sum(fmean(tuple(phi(t) for t in v)) != phi(fmean(v)) for v in vecs)
    os_ok = all(np.sort(tuple(phi(t) for t in v))[r] == phi(np.sort(v)[r]) for v in vecs for r in range(4))
    return {"floor_mean_symmetric": sym, "floor_mean_idempotent": idem,
            "floor_mean_violations_under_merge": int(violations), "order_statistics_commute_with_merge": bool(os_ok)}


def main():
    out = {"table_v_shares": table_v_shares(), "ordinal_r1": ordinal_r1(),
           "order_statistic_rules_as_sorting": sorting_check(), "lemma_premises": lemma_counterexample()}
    (OUT / "review_extras.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
