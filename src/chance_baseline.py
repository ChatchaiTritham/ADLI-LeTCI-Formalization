"""Supplementary Material S11: range-null baseline for the scorebook agreement reported in S10.

Uses the 18 transcribed items of the 2008 Novel Connect Scorebook (data in scorebook_factors.py).
  1. Range null: if the team had picked a band uniformly among those spanned by the four factor ranges,
     the consensus band would lie between the two medians with probability
     (b(3) - b(2) + 1) / (b(4) - b(1) + 1) per item; the product over the 18 items is reported.
  2. Exact (Clopper-Pearson) one-sided 95% lower confidence bound for a rate observed as k of n
     (k = n = 18): alpha ** (1 / n).
Both figures are descriptive (one team scored every item). Output: ../results/chance_baseline.json
"""
import json
from fractions import Fraction

from scorebook_factors import NOVEL_CONNECT_2008, OUT, band


def main():
    items, prob = [], Fraction(1)
    for item, (fb, pct, page) in NOVEL_CONNECT_2008.items():
        s = sorted(fb)
        p = Fraction(s[2] - s[1] + 1, s[3] - s[0] + 1)
        prob *= p
        items.append({"item": item, "sorted_factor_bands": s, "consensus_band": band(pct),
                      "between_medians": s[1] <= band(pct) <= s[2], "p_between_under_range_null": str(p)})
    n = len(items)
    k = sum(r["between_medians"] for r in items)
    lower = 0.05 ** (1 / n) if k == n else None
    out = {"items": n, "consensus_between_medians": k,
           "items_with_p_below_one": sum(Fraction(r["p_between_under_range_null"]) < 1 for r in items),
           "range_null_probability_all_between": {"exact": str(prob), "float": float(prob)},
           "clopper_pearson_one_sided_95_lower_bound": round(lower, 4) if lower is not None else None,
           "per_item": items}
    (OUT / "chance_baseline.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: v for key, v in out.items() if key != "per_item"}, indent=1))


if __name__ == "__main__":
    main()
