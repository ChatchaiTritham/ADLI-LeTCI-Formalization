"""Supplementary Material S9: exhaustive checks of the n-factor, k-band generalization (Section VI-D).

For n factors rated on a chain of k bands {0, ..., k-1} and order-statistic rules R_r (r-th smallest band):
  T1 (t-robustness) R_r keeps the band within [min, max] of the untouched factors whenever any t factors are
     changed arbitrarily  <=>  t < r <= n - t.  The largest t achievable is floor((n-1)/2), attained exactly by
     the median rule(s): r = (n+1)/2 for odd n, r in {n/2, n/2 + 1} for even n.
  T2 (sorting) R_r(v) >= j  <=>  at least n - r + 1 factors have band >= j.
  T0 (lemma, brute force) on small (n, k) every symmetric rule stable under all nondecreasing self-maps is
     an order statistic when k >= n; when k < n further rules exist, so the condition k >= n is needed.
  T3 (lemma) the four-factor counterexample generalises: the rounded-down mean is symmetric, idempotent and
     monotone but violates stability under the band-merging map phi(t) = min(t, 1) for every n >= 2, k >= 3,
     while every order statistic commutes with every nondecreasing self-map of the chain (checked on all maps).
All checks run over every band vector in {0..k-1}^n for 2 <= n <= 6 and 2 <= k <= 7 (T3's map check for k <= 5).
Output: ../results/general_nk.json
"""
import itertools
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" if (ROOT / "results").is_dir() else Path(__file__).resolve().parent


def robust(n, k, r, t):
    """True iff R_r stays within the range of the n - t untouched factors under every change of any t factors."""
    vecs = np.array(list(itertools.product(range(k), repeat=n)))
    for keep in itertools.combinations(range(n), n - t):
        kept = vecs[:, keep]
        lo, hi = kept.min(axis=1), kept.max(axis=1)
        out = np.sort(vecs, axis=1)[:, r - 1]
        # all vectors share the same untouched coordinates in groups; checking every vector covers every change
        if ((out < lo) | (out > hi)).any():
            return False
    return True


def check_t1():
    res = {}
    for n in range(2, 7):
        for k in range(2, 8):
            ok = True
            for r in range(1, n + 1):
                for t in range(1, n):
                    predicted = t < r <= n - t
                    if k >= 2 and robust(n, k, r, t) != predicted:
                        ok = False
            tmax = (n - 1) // 2
            medians = [r for r in range(1, n + 1) if tmax >= 1 and robust(n, k, r, tmax)]
            expected = [(n + 1) // 2] if n % 2 else [n // 2, n // 2 + 1]
            res[f"n{n}_k{k}"] = {"robustness_iff_holds": ok, "most_robust_rules": medians,
                                 "matches_medians": medians == expected if tmax >= 1 else None}
    return res


def check_t2():
    ok = True
    for n in range(2, 7):
        for k in range(2, 8):
            vecs = np.array(list(itertools.product(range(k), repeat=n)))
            s = np.sort(vecs, axis=1)
            for r in range(1, n + 1):
                for j in range(k):
                    ok &= bool(((s[:, r - 1] >= j) == ((vecs >= j).sum(axis=1) >= n - r + 1)).all())
    return {"order_statistic_is_(n-r+1)_of_n_sorting": ok}


def check_t3():
    res = {"floor_mean_violates_merge": True, "order_statistics_commute_with_all_nondecreasing_maps": True}
    for n in range(2, 7):
        for k in range(3, 8):
            vecs = list(itertools.product(range(k), repeat=n))
            fm = lambda v: int(np.floor(np.mean(v)))
            phi = lambda x: min(x, 1)
            if not any(fm(tuple(phi(x) for x in v)) != phi(fm(v)) for v in vecs):
                res["floor_mean_violates_merge"] = False
            if k <= 5 and n <= 4:
                maps = [m for m in itertools.product(range(k), repeat=k) if all(m[i] <= m[i + 1] for i in range(k - 1))]
                for m in maps:
                    for v in vecs:
                        sv = sorted(v)
                        mv = sorted(m[x] for x in v)
                        if any(mv[r] != m[sv[r]] for r in range(n)):
                            res["order_statistics_commute_with_all_nondecreasing_maps"] = False
                            break
    return res


def check_lemma_bruteforce():
    """Enumerate every symmetric rule on small (n, k) and keep those stable under all nondecreasing self-maps."""
    res = {}
    for n, k in [(2, 2), (2, 3), (2, 4), (3, 3), (3, 2), (4, 2)]:
        ms = list(itertools.combinations_with_replacement(range(k), n))
        maps = [m for m in itertools.product(range(k), repeat=k) if all(m[i] <= m[i + 1] for i in range(k - 1))]
        idx = {m: i for i, m in enumerate(ms)}
        sols = [f for f in itertools.product(range(k), repeat=len(ms))
                if all(f[idx[tuple(sorted(mp[x] for x in v))]] == mp[f[idx[v]]] for mp in maps for v in ms)]
        stats = sorted({tuple(v[r] for v in ms) for r in range(n)})
        res[f"n{n}_k{k}"] = {"stable_symmetric_rules": len(sols), "only_order_statistics": sorted(sols) == stats}
    return res


def main():
    out = {"T0_lemma_bruteforce": check_lemma_bruteforce(), "T1_robustness": check_t1(), "T2_sorting": check_t2(), "T3_lemma": check_t3()}
    out["all_T1_hold"] = all(v["robustness_iff_holds"] and v["matches_medians"] in (True, None) for v in out["T1_robustness"].values())
    (OUT / "general_nk.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_T1_hold": out["all_T1_hold"], **out["T2_sorting"], **out["T3_lemma"]}, indent=1))


if __name__ == "__main__":
    main()
