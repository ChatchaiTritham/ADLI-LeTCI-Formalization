"""Supplementary Material S10: published NIST consensus scorebooks as real assessment data.

Data (transcribed from the published PDFs; page numbers refer to the PDF files):
  * 2008 Novel Connect Scorebook (Baldrige Examiner Preparation Course), NIST.
    For each of the 18 items the "Evaluation Factor Score Summary" marks one scoring range per factor
    (Approach, Deployment, Learning, Integration; or Levels, Trends, Comparisons, Integration) and gives
    the consensus item percentage. Ranges are recorded as zero-based band indices 0..5 of the six ranges.
  * 2010 NuGrain Laboratories Scorebook, NIST: Score Summary Worksheet (points and percentages).

Checks:
  1. Arithmetic layer (Eq. points, halves rounded up) reproduces both worksheets' subtotals and totals.
  2. Band rules against the consensus band of each Novel Connect item: exact agreement of R1..R4 and of
     the rounded mean factor band; whether the consensus band lies between the two medians; how often the
     consensus band exceeds the weakest factor's band (the gate's ceiling breached by the examiners).
Output: ../results/scorebook_factors.json
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" if (ROOT / "results").is_dir() else Path(__file__).resolve().parent
LOW = np.array([0, 10, 30, 50, 70, 90])

POINTS = {"1.1": 70, "1.2": 50, "2.1": 40, "2.2": 45, "3.1": 40, "3.2": 45, "4.1": 45, "4.2": 45, "5.1": 45,
          "5.2": 40, "6.1": 35, "6.2": 50, "7.1": 100, "7.2": 70, "7.3": 70, "7.4": 70, "7.5": 70, "7.6": 70}

# item: (factor bands in printed row order, consensus percentage, PDF page)
NOVEL_CONNECT_2008 = {
    "1.1": ([4, 3, 3, 3], 60, 14), "1.2": ([4, 3, 3, 3], 60, 17), "2.1": ([2, 3, 2, 3], 50, 20),
    "2.2": ([2, 3, 2, 3], 45, 23), "3.1": ([2, 3, 2, 4], 50, 26), "3.2": ([3, 4, 2, 3], 60, 29),
    "4.1": ([3, 4, 3, 3], 60, 32), "4.2": ([3, 2, 2, 2], 45, 35), "5.1": ([3, 3, 2, 2], 50, 39),
    "5.2": ([3, 3, 2, 3], 50, 42), "6.1": ([3, 3, 3, 4], 55, 45), "6.2": ([4, 3, 2, 3], 55, 48),
    "7.1": ([4, 4, 3, 3], 65, 51), "7.2": ([4, 4, 3, 3], 70, 54), "7.3": ([3, 4, 2, 3], 60, 57),
    "7.4": ([3, 3, 3, 2], 50, 60), "7.5": ([3, 3, 3, 2], 50, 63), "7.6": ([3, 2, 1, 2], 45, 66),
}
NOVEL_CONNECT_TOTALS = {"process": 296, "results": 258, "grand": 554}          # worksheet, PDF p. 67

NUGRAIN_2010 = {"1.1": 70, "1.2": 60, "2.1": 65, "2.2": 50, "3.1": 60, "3.2": 60, "4.1": 60, "4.2": 50,
                "5.1": 60, "5.2": 65, "6.1": 65, "6.2": 65, "7.1": 50, "7.2": 50, "7.3": 60, "7.4": 60,
                "7.5": 65, "7.6": 60}
NUGRAIN_TOTALS = {"process": 338, "results": 257, "grand": 595}                # worksheet, PDF p. 54


def item_points(points, pct):
    return int(np.floor(points * pct / 100 + 0.5))                             # halves rounded up


def totals(pcts):
    s = {i: item_points(POINTS[i], p) for i, p in pcts.items()}
    proc = sum(v for i, v in s.items() if not i.startswith("7"))
    res = sum(v for i, v in s.items() if i.startswith("7"))
    return {"process": proc, "results": res, "grand": proc + res}


def band(pct):
    return int(np.searchsorted(LOW, pct + 1e-9, side="right") - 1)


def rules():
    rows, agree = [], {"R1 (gate)": 0, "R2 (lower median)": 0, "R3 (upper median)": 0, "R4 (maximum)": 0,
                       "rounded mean band": 0}
    between, above_gate, lone_low, lone_low_overruled = 0, 0, 0, 0
    for item, (fb, pct, page) in NOVEL_CONNECT_2008.items():
        s = sorted(fb)
        c = band(pct)
        pred = {"R1 (gate)": s[0], "R2 (lower median)": s[1], "R3 (upper median)": s[2], "R4 (maximum)": s[3],
                "rounded mean band": int(np.floor(np.mean(fb) + 0.5))}
        for k, v in pred.items():
            agree[k] += int(v == c)
        between += int(s[1] <= c <= s[2])
        above_gate += int(c > s[0])
        if s[0] < s[1]:
            lone_low += 1
            lone_low_overruled += int(c > s[0])
        rows.append({"item": item, "page": page, "factor_bands": fb, "consensus_pct": pct, "consensus_band": c, **pred})
    n = len(rows)
    return rows, {"items": n, "exact_agreement": agree,
                  "consensus_between_medians": between,
                  "consensus_above_weakest_factor_band": above_gate,
                  "items_with_a_lone_weakest_factor": lone_low,
                  "of_which_consensus_above_it": lone_low_overruled}


def main():
    nc_pct = {i: v[1] for i, v in NOVEL_CONNECT_2008.items()}
    rows, summary = rules()
    out = {"novel_connect_2008": {"recomputed": totals(nc_pct), "published": NOVEL_CONNECT_TOTALS},
           "nugrain_2010": {"recomputed": totals(NUGRAIN_2010), "published": NUGRAIN_TOTALS},
           "band_rules_vs_consensus": summary, "items": rows}
    out["arithmetic_reproduced"] = (out["novel_connect_2008"]["recomputed"] == NOVEL_CONNECT_TOTALS and
                                    out["nugrain_2010"]["recomputed"] == NUGRAIN_TOTALS)
    (OUT / "scorebook_factors.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "items"}, indent=1))


if __name__ == "__main__":
    main()
