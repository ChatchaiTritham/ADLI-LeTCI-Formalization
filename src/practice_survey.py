"""Supplementary Material S13: factor-combination rules prescribed by excellence frameworks.

Input : src/data_practice_survey/survey_table.csv (17 verified documents S01-S17, 6 not-retrieved N01-N06),
        built by provenance/practice_survey/build_survey.py from the retrieved documents, whose SHA-256
        digests are listed in the CSV and in provenance/practice_survey/SOURCES_SHA256SUMS.txt. The documents
        themselves are not redistributed (third-party copyright); every row carries its URL, page and quotation.
Output: ../results/practice_survey.json (counts by rule category; the compact table of the article).
"""
import csv
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "results" if (ROOT / "results").is_dir() else HERE

# Compact table of the article: (framework row, prescribed rule, survey rows that support it)
TABLE = [
    ("Baldrige (examiner FAQ, scorebook, Excellence Builder)", "Holistic; not mean, not gate", ["S01", "S02", "S03"]),
    ("EdPEx 2024-2027", "Holistic; not mean, not gate", ["S13"]),
    ("AUN-QA v4.0 (programme verdict)", "Holistic; not mean", ["S12"]),
    ("Baldrige Award 2025 rubrics", "Not stated", ["S05"]),
    ("PMQA 4.0", "Not stated (three levels)", ["S14", "S15"]),
    ("Singapore Business Excellence", "Lower of two factor scores (gate)", ["S10", "S11"]),
    ("EFQM Model 2021 (RADAR)", "Capped at the Sound attribute", ["S06"]),
    ("CAF 2020, classical scoring", "Cumulative PDCA phases", ["S07", "S09"]),
    ("CAF 2020, fine-tuned scoring", "Mean of phase scores", ["S08", "S09"]),
]


def main():
    with open(HERE / "data_practice_survey" / "survey_table.csv", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    verified = [r for r in rows if r["id"].startswith("S")]
    ids = {r["id"] for r in verified}
    for _, _, support in TABLE:
        assert set(support) <= ids, support
    cats = Counter(r["rule_category"] for r in verified)
    out = {
        "documents_verified": len(verified),
        "documents_not_retrieved": sum(r["id"].startswith("N") for r in rows),
        "rule_category_counts": dict(sorted(cats.items())),
        "documents_prescribing_median_or_majority": sum("median" in r["rule_category"] or "majority" in r["rule_category"]
                                                        for r in verified),
        "documents_prescribing_weakest_factor_gate": [r["id"] for r in verified if r["rule_category"].startswith("weakest-factor gate")],
        "not_reverified_rows": [r["id"] for r in verified if "NOT re" in r["verification"]],
        "third_party_hosted_rows": [r["id"] for r in verified if "third-party" in r["verification"] or "hosted by" in r["verification"]],
        "article_table": [{"framework": a, "rule": b, "rows": c} for a, b, c in TABLE],
    }
    (OUT / "practice_survey.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "article_table"}, indent=1))


if __name__ == "__main__":
    main()
