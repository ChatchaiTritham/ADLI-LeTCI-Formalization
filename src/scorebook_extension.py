"""Supplementary Material S12: band rules on three published NIST Baldrige consensus scorebooks.

Pre-registration: provenance/scorebooks/PREREG.md (written before the new scorebooks were searched for).
Inputs : src/data_scorebooks/passA.json (coordinate extraction, provenance/scorebooks/extract_passA.py)
         src/data_scorebooks/passB_visual.json (independent visual pass)
Sources: provenance/scorebooks/sources.csv (NIST URLs, all 13 scorebooks screened) and sha256.csv (PDF digests).
Outputs: ../results/scorebook_items.csv (one row per item), ../results/scorebook_extension.json.
Confirmatory set = 2007 Share Food + 2009 Nightingale (new). Exploratory = 2008 Novel Connect (S10).
Run: python src/scorebook_extension.py
"""
import csv
import json
from fractions import Fraction
from math import comb, sqrt
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE / "data_scorebooks"
ROOT = HERE.parent
OUT = ROOT / "results" if (ROOT / "results").is_dir() else HERE
LOW = [0, 10, 30, 50, 70, 90]
META = {"2007_Share_Food": ("Share Food (fictitious food bank)", 2007, "Nonprofit", "confirmatory"),
        "2008_Novel_Connect": ("Novel Connect (fictitious manufacturer)", 2008, "Business", "exploratory"),
        "2009_Nightingale": ("Nightingale College of Nursing (fictitious)", 2009, "Education", "confirmatory")}
POINTS = {"1.1": 70, "1.2": 50, "2.1": 40, "2.2": 45, "3.1": 40, "3.2": 45, "4.1": 45, "4.2": 45, "5.1": 45,
          "5.2": 40, "6.1": 35, "6.2": 50, "7.1": 100, "7.2": 70, "7.3": 70, "7.4": 70, "7.5": 70, "7.6": 70}
PUBLISHED_GRAND = {"2007_Share_Food": 425, "2008_Novel_Connect": 554, "2009_Nightingale": 477}
WORKSHEET_PAGE = {"2007_Share_Food": 70, "2008_Novel_Connect": 67, "2009_Nightingale": 65}


def band(pct):
    return max(k for k, lo in enumerate(LOW) if pct >= lo)


def wilson(k, n, z=1.959964):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 3), round(c + h, 3)]


def binom_two_sided(k, n):
    """Exact two-sided binomial test, p0 = 0.5 (McNemar exact on discordant pairs)."""
    if n == 0:
        return None
    pk = comb(n, k)
    return min(1.0, sum(comb(n, i) for i in range(n + 1) if comb(n, i) <= pk) / 2 ** n)


def predictions(fb):
    s = sorted(fb)
    vals, counts = np.unique(fb, return_counts=True)
    return {"gate": s[0], "lower_median": s[1], "upper_median": s[2], "max": s[3],
            "rounded_mean": int(np.floor(np.mean(fb) + 0.5)),
            "midrange": int(np.floor((s[0] + s[3]) / 2 + 0.5)),
            "mode_low": int(vals[counts == counts.max()].min())}


def load():
    a = json.loads((DATA / "passA.json").read_text(encoding="utf-8"))
    b = json.loads((DATA / "passB_visual.json").read_text(encoding="utf-8"))
    rows, cells, cell_agree, pct_agree = [], 0, 0, 0
    for case, items in a.items():
        for r in items:
            fb_b, pct_b = b[case][r["item"]]
            cells += 4
            cell_agree += sum(x == y for x, y in zip(r["factor_bands"], fb_b))
            pct_agree += int(r["consensus_pct"] == pct_b)
            ok = r["n_marks"] == 4 and r["factor_bands"] == fb_b and r["consensus_pct"] == pct_b
            rows.append({"case": case, "item": r["item"], "fb": r["factor_bands"], "pct": r["consensus_pct"],
                         "page": r["page"], "both_passes_agree": ok})
    agree = {"items": len(rows), "factor_cells": cells, "factor_cells_agree": cell_agree,
             "pct_agree": pct_agree, "items_fully_agree": sum(r["both_passes_agree"] for r in rows)}
    return rows, agree


def arithmetic(rows):
    out = {}
    for case in META:
        g = sum(int(np.floor(POINTS[r["item"]] * r["pct"] / 100 + 0.5)) for r in rows if r["case"] == case)
        out[case] = {"recomputed": g, "published": PUBLISHED_GRAND[case], "match": g == PUBLISHED_GRAND[case]}
    return out


def evaluate(rows):
    n = len(rows)
    rules = ["gate", "lower_median", "upper_median", "rounded_mean", "midrange", "mode_low", "max"]
    hits = {k: 0 for k in rules}
    hits["any_median"] = 0
    disc, d_med, d_mean, d_neither = 0, 0, 0, 0
    lm_vs_rm = {"discordant": 0, "lower_median_only": 0, "rounded_mean_only": 0}
    gate_vs_any = {"any_only": 0, "gate_only": 0}
    rm_vs_any = {"any_only": 0, "rm_only": 0}
    lone, lone_over, null_prob = 0, 0, Fraction(1)
    for r in rows:
        p, c, s = r["pred"], r["c"], sorted(r["fb"])
        anym = s[1] <= c <= s[2]
        for k in rules:
            hits[k] += int(p[k] == c)
        hits["any_median"] += int(anym)
        gate_vs_any["any_only"] += int(anym and p["gate"] != c)
        gate_vs_any["gate_only"] += int(p["gate"] == c and not anym)
        rm_vs_any["any_only"] += int(anym and p["rounded_mean"] != c)
        rm_vs_any["rm_only"] += int(p["rounded_mean"] == c and not anym)
        if not (s[1] <= p["rounded_mean"] <= s[2]):                  # pre-registered discriminating subset D
            disc += 1
            d_med += int(anym)
            d_mean += int(p["rounded_mean"] == c)
            d_neither += int(not anym and p["rounded_mean"] != c)
        if p["lower_median"] != p["rounded_mean"]:                  # secondary: lower median vs rounded mean
            lm_vs_rm["discordant"] += 1
            lm_vs_rm["lower_median_only"] += int(p["lower_median"] == c)
            lm_vs_rm["rounded_mean_only"] += int(p["rounded_mean"] == c)
        if s[0] < s[1]:
            lone += 1
            lone_over += int(c > s[0])
        null_prob *= Fraction(s[2] - s[1] + 1, s[3] - s[0] + 1)
    lmo, rmo = lm_vs_rm["lower_median_only"], lm_vs_rm["rounded_mean_only"]
    return {
        "n_items": n,
        "hit_rates": {k: {"k": v, "rate": round(v / n, 3), "wilson95": wilson(v, n)} for k, v in hits.items()},
        "H1_discriminating_subset_D": {"size": disc, "consensus_in_median_band": d_med, "consensus_eq_rounded_mean": d_mean,
                                       "neither": d_neither,
                                       "exact_binomial_p": binom_two_sided(d_med, d_med + d_mean) if d_med + d_mean else None,
                                       "underpowered (|D|<10)": disc < 10},
        "secondary_lower_median_vs_rounded_mean": {**lm_vs_rm,
                                                   "mcnemar_exact_p": binom_two_sided(lmo, lmo + rmo) if lmo + rmo else None},
        "any_median_vs_rounded_mean_mcnemar": {**rm_vs_any, "exact_p": binom_two_sided(rm_vs_any["any_only"], sum(rm_vs_any.values())) if sum(rm_vs_any.values()) else None},
        "H2_gate_vs_any_median_mcnemar": {**gate_vs_any, "exact_p": binom_two_sided(gate_vs_any["any_only"], sum(gate_vs_any.values())) if sum(gate_vs_any.values()) else None},
        "H3_lone_weakest_factor": {"items": lone, "consensus_above_gate": lone_over},
        "range_null_P_all_between_medians": float(null_prob),
    }


def cluster_bootstrap(rows, reps=10000, seed=20261011):
    rng = np.random.default_rng(seed)
    cases = sorted({r["case"] for r in rows})
    by = {c: [r for r in rows if r["case"] == c] for c in cases}
    diffs = []
    for _ in range(reps):
        pick = [r for c in rng.choice(cases, len(cases)) for r in by[c]]
        a = np.mean([sorted(r["fb"])[1] <= r["c"] <= sorted(r["fb"])[2] for r in pick])
        m = np.mean([r["pred"]["rounded_mean"] == r["c"] for r in pick])
        diffs.append(a - m)
    return {"clusters": len(cases), "reps": reps, "seed": seed,
            "diff_any_median_minus_rounded_mean_95ci": [round(float(np.percentile(diffs, q)), 3) for q in (2.5, 97.5)],
            "note": "few clusters; percentile CI is descriptive only"}


def main():
    rows, agree = load()
    for r in rows:
        r["c"] = band(r["pct"])
        r["pred"] = predictions(r["fb"])
    with open(OUT / "scorebook_items.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["case", "applicant", "year", "sector", "set", "team_stage", "item", "item_type",
                    "f1", "f2", "f3", "f4", "factor_labels", "consensus_pct", "consensus_band", "pdf_page_factor_grid",
                    "pdf_page_worksheet", "passA_passB_agree"] + list(rows[0]["pred"]))
        for r in rows:
            name, yr, sec, st = META[r["case"]]
            res = r["item"].startswith("7")
            w.writerow([r["case"], name, yr, sec, st, "consensus (training scorebook team)", r["item"],
                        "results" if res else "process", *r["fb"], "Le/T/C/I" if res else "A/D/L/I", r["pct"], r["c"],
                        r["page"], WORKSHEET_PAGE[r["case"]], r["both_passes_agree"], *r["pred"].values()])
    conf = [r for r in rows if META[r["case"]][3] == "confirmatory"]
    out = {"transcription_agreement": agree, "arithmetic_check": arithmetic(rows),
           "confirmatory_2007_2009": evaluate(conf), "exploratory_2008": evaluate([r for r in rows if r["case"] == "2008_Novel_Connect"]),
           "pooled_all": evaluate(rows), "per_case": {c: evaluate([r for r in rows if r["case"] == c]) for c in META},
           "cluster_bootstrap_pooled": cluster_bootstrap(rows), "cluster_bootstrap_confirmatory": cluster_bootstrap(conf)}
    (OUT / "scorebook_extension.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for key in ["transcription_agreement", "arithmetic_check"]:
        print(key, json.dumps(out[key]))
    for s in ["confirmatory_2007_2009", "exploratory_2008", "pooled_all"]:
        e = out[s]
        print(f"\n== {s} (n={e['n_items']})")
        for k, v in e["hit_rates"].items():
            print(f"  {k:14s} {v['k']:3d}  {v['rate']:.3f}  {v['wilson95']}")
        for k in ["H1_discriminating_subset_D", "secondary_lower_median_vs_rounded_mean",
                  "any_median_vs_rounded_mean_mcnemar", "H2_gate_vs_any_median_mcnemar", "H3_lone_weakest_factor",
                  "range_null_P_all_between_medians"]:
            print(" ", k, e[k])
    print("\nbootstrap", out["cluster_bootstrap_pooled"], out["cluster_bootstrap_confirmatory"])


if __name__ == "__main__":
    main()
