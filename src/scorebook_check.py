"""External check of the aggregation step against a published consensus scorebook.

The formalisation is stated on synthetic cohorts, so this script tests its aggregation and band
mapping against scores that Baldrige examiners actually recorded. The source is the Nightingale
College of Nursing Scorebook, prepared by a team of experienced examiners for the 2009 Malcolm
Baldrige National Quality Award Examiner Preparation Course and published by NIST
(https://www.nist.gov/system/files/documents/2017/05/09/2009_Nightingale_Scorebook.pdf). Its Score
Summary Worksheet records, for every item, the points possible (column A), the percentage the
consensus team assigned (column B), the item score A x B (column C) and the scoring band (column D),
together with the category totals, the two subtotals and the grand total.

The worksheet's own guidance states the assumption the formalisation is built on: "The overall score
is not intended to be a numerical average of the elements above; the Examiners select the range and
score that are most descriptive of the organization's achievement level for the Item."

This script recomputes columns C and D and the totals from columns A and B with the paper's
aggregation rule and band mapping, and reports any disagreement.

Run:  python src/scorebook_check.py      ->  results/scorebook_check.json
"""
from __future__ import annotations

import json
from pathlib import Path

import math

from adli_letci import band_index

ROOT = Path(__file__).resolve().parent.parent
SOURCE = {
    "title": "Nightingale College of Nursing Scorebook, 2009 Baldrige Examiner Preparation Course",
    "publisher": "Baldrige National Quality Program, National Institute of Standards and Technology",
    "url": "https://www.nist.gov/system/files/documents/2017/05/09/2009_Nightingale_Scorebook.pdf",
    "transcribed": "Score Summary Worksheet--All Sectors (pp. 62)",
}
# item: (points possible, percentage assigned, item score recorded, band recorded)
WORKSHEET = {
    "1.1": (70, 55, 39, "50-65"), "1.2": (50, 40, 20, "30-45"),
    "2.1": (40, 45, 18, "30-45"), "2.2": (45, 45, 20, "30-45"),
    "3.1": (40, 45, 18, "30-45"), "3.2": (45, 45, 20, "30-45"),
    "4.1": (45, 45, 20, "30-45"), "4.2": (45, 45, 20, "30-45"),
    "5.1": (45, 50, 23, "50-65"), "5.2": (40, 35, 14, "30-45"),
    "6.1": (35, 45, 16, "30-45"), "6.2": (50, 45, 23, "30-45"),
    "7.1": (100, 60, 60, "50-65"), "7.2": (70, 50, 35, "50-65"),
    "7.3": (70, 50, 35, "50-65"), "7.4": (70, 45, 32, "30-45"),
    "7.5": (70, 45, 32, "30-45"), "7.6": (70, 45, 32, "30-45"),
}
CATEGORY_TOTALS = {1: 59, 2: 38, 3: 38, 4: 40, 5: 37, 6: 39}
PROCESS_TOTAL, RESULTS_TOTAL, GRAND_TOTAL = 251, 226, 477
BAND_LABELS = ["0-5", "10-25", "30-45", "50-65", "70-85", "90-100"]


def main() -> None:
    rows, mismatches = [], []
    for item, (points, percent, recorded, band_recorded) in WORKSHEET.items():
        computed = math.floor(points * percent / 100 + 0.5)  # the worksheet rounds halves up
        band_computed = BAND_LABELS[band_index(percent)]
        ok = computed == recorded and band_computed == band_recorded
        rows.append({"item": item, "points": points, "percent": percent,
                     "score_recorded": recorded, "score_computed": computed,
                     "band_recorded": band_recorded, "band_computed": band_computed, "agrees": ok})
        if not ok:
            mismatches.append(item)

    cat = {}
    for c in range(1, 7):
        cat[c] = sum(math.floor(p * pc / 100 + 0.5) for i, (p, pc, _, _) in WORKSHEET.items()
                     if i.startswith(f"{c}.") )
    process = sum(v for c, v in cat.items())
    results = sum(math.floor(p * pc / 100 + 0.5) for i, (p, pc, _, _) in WORKSHEET.items() if i.startswith("7."))
    out = {
        "source": SOURCE,
        "guidance_quoted": ("The overall score is not intended to be a numerical average of the elements "
                            "above; the Examiners select the range and score that are most descriptive of "
                            "the organization's achievement level for the Item."),
        "items": rows,
        "items_agreeing": sum(r["agrees"] for r in rows), "items_total": len(rows),
        "category_totals_recorded": CATEGORY_TOTALS,
        "category_totals_computed": cat,
        "category_totals_agree": cat == CATEGORY_TOTALS,
        "process_total": {"recorded": PROCESS_TOTAL, "computed": process, "agrees": process == PROCESS_TOTAL},
        "results_total": {"recorded": RESULTS_TOTAL, "computed": results, "agrees": results == RESULTS_TOTAL},
        "grand_total": {"recorded": GRAND_TOTAL, "computed": process + results,
                        "agrees": process + results == GRAND_TOTAL},
        "mismatched_items": mismatches,
        "rounding": "halves rounded up, as the published worksheet does (70 x 55% = 38.5 recorded as 39)",
    }
    (ROOT / "results" / "scorebook_check.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f'items: {out["items_agreeing"]}/{out["items_total"]} agree on score and band')
    print(f'category totals agree: {out["category_totals_agree"]}  ({cat} vs {CATEGORY_TOTALS})')
    print(f'process {process} vs {PROCESS_TOTAL}; results {results} vs {RESULTS_TOTAL}; '
          f'grand {process + results} vs {GRAND_TOTAL}')
    print("wrote results/scorebook_check.json")


if __name__ == "__main__":
    main()
