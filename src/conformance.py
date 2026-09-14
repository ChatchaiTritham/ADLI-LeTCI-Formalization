"""Supplementary Material S5: specification-conformance and mutation analysis of the gated score.

Data-free validation. Each rule of the scoring guidelines that the formalization claims to encode is
written as an executable property (P1-P7). The properties are checked on randomly generated indicator
vectors and weight vectors (fixed seed) for the reference implementation, and then for seven mutants,
each a plausible mis-implementation of one rule. A property suite that passes on the reference and fails
on every mutant shows both that the implementation conforms and that the suite can detect a violation.

Output: ../results/conformance.json (or next to this script when that folder is absent)
"""
import json
import random
from pathlib import Path

import adli_letci as ref

SEED, N_CASES = 20260914, 20_000
_HERE = Path(__file__).resolve().parent
OUT = _HERE.parent / "results" if (_HERE.parent / "results").is_dir() else _HERE
CHOICES = ref.CHOICES
LOW = [ch[0] for ch in ref.BAND_CHOICES]
TOP = [ch[-1] for ch in ref.BAND_CHOICES]


# --------------------------------------------------------------------------- mutants
def m1_average(x, w):
    """Averages the factors and ignores the weakest-factor cap."""
    return ref.floor_choice(ref.item_score(x, w))


def m2_cap_at_band_floor(x, w):
    """Caps at the lower bound of the weakest factor's band instead of its top."""
    return ref.floor_choice(min(ref.item_score(x, w), LOW[ref.band_index(100 * min(x))]))


def m3_round_nearest(x, w):
    """Rounds to the nearest 5 instead of down to a legal choice."""
    v = min(ref.item_score(x, w), ref.cap(x))
    return min(CHOICES, key=lambda c: (abs(c - v), c))


def m4_cap_from_strongest(x, w):
    """Takes the cap from the strongest factor instead of the weakest."""
    return ref.floor_choice(min(ref.item_score(x, w), TOP[ref.band_index(100 * max(x))]))


def m5_cap_next_band(x, w):
    """Off-by-one: caps at the top of the band above the weakest factor's band."""
    return ref.floor_choice(min(ref.item_score(x, w), TOP[min(ref.band_index(100 * min(x)) + 1, 5)]))


def m6_no_rounding(x, w):
    """Returns the capped continuous value without restricting it to legal choices."""
    return min(ref.item_score(x, w), ref.cap(x))


def m7_equal_category_weights(x, w):
    """Correct item rule; the mutation is in aggregation (checked by P7)."""
    return ref.gated_item_score(x, w)


def org_equal_categories(item_scores):
    return sum(ref.category_score(item_scores, c) for c in range(1, 8)) / 7


MUTANTS = {
    "M1 no weakest-factor cap": (m1_average, ref.organisational_score),
    "M2 cap at band lower bound": (m2_cap_at_band_floor, ref.organisational_score),
    "M3 round to nearest": (m3_round_nearest, ref.organisational_score),
    "M4 cap from strongest factor": (m4_cap_from_strongest, ref.organisational_score),
    "M5 cap one band too high": (m5_cap_next_band, ref.organisational_score),
    "M6 no restriction to legal choices": (m6_no_rounding, ref.organisational_score),
    "M7 equal category weights": (m7_equal_category_weights, org_equal_categories),
}


# --------------------------------------------------------------------------- generators
def indicators(rng):
    # mix of continuous values and values placed exactly on band edges, where mistakes show
    edges = [b / 100 for b in LOW + TOP] + [0.0, 1.0]
    return tuple(rng.choice(edges) if rng.random() < 0.3 else round(rng.random(), 3) for _ in range(4))


def weights(rng):
    v = [rng.random() for _ in range(4)]
    return tuple(a / sum(v) for a in v)


# --------------------------------------------------------------------------- properties
def violations(score, org, rng):
    """Return {property: counterexample or None} for one implementation."""
    found = {f"P{i}": None for i in range(1, 8)}

    def fail(p, case):
        if found[p] is None:
            found[p] = case

    for _ in range(N_CASES):
        x, w, w2 = indicators(rng), weights(rng), weights(rng)
        s = score(x, w)
        m = 100 * min(x)
        cap = TOP[ref.band_index(m)]
        # P1 the awarded score is a legal percentage choice
        if s not in CHOICES:
            fail("P1", (x, w, s))
        # P2 no score above the top of the band that contains the weakest factor
        if s > cap:
            fail("P2", (x, w, s))
        # P3 the weakest factor alone is enough to reach its band top when all factors are at least that strong
        if all(100 * xi >= cap for xi in x) and s != cap and m < TOP[-1] and ref.band_index(m) == ref.band_index(cap):
            fail("P3", (x, w, s))
        # P4 raising one factor never lowers the awarded score
        k = rng.randrange(4)
        x_up = tuple(min(1.0, xi + rng.random() * 0.3) if i == k else xi for i, xi in enumerate(x))
        if score(x_up, w) < s:
            fail("P4", (x, x_up, w))
        # P5 the awarded score never exceeds what the factors themselves support
        if s > ref.item_score(x, w) + 1e-9:
            fail("P5", (x, w, s))
        # P6 weight invariance (Proposition 2) when the weakest factor is at a band top or in a gap
        if m >= cap and score(x, w2) != s:
            fail("P6", (x, w, w2))
    # P7 aggregation by official points: org score moves by points/1000 per percentage point of an item
    for _ in range(2000):
        items = {c: rng.choice(CHOICES) for c in ref.ITEM_POINTS}
        code = rng.choice(list(ref.ITEM_POINTS))
        bumped = dict(items, **{code: items[code] + 5})
        delta = org(bumped) - org(items)
        if abs(delta - 5 * ref.ITEM_POINTS[code] / 1000) > 1e-9:
            fail("P7", (code, delta))
            break
    return found


def main():
    impls = {"reference": (ref.gated_item_score, ref.organisational_score), **MUTANTS}
    result = {"seed": SEED, "cases_per_property": N_CASES, "properties": {
        "P1": "awarded score is a legal percentage choice",
        "P2": "score does not exceed the top of the weakest factor's band",
        "P3": "score reaches the weakest factor's band top when every factor supports it",
        "P4": "raising a factor never lowers the score",
        "P5": "score does not exceed the continuous factor score",
        "P6": "score is invariant to factor weights when Proposition 2's condition holds",
        "P7": "organizational score aggregates by official points",
    }, "implementations": {}}
    for name, (score, org) in impls.items():
        found = violations(score, org, random.Random(SEED))
        failed = sorted(p for p, case in found.items() if case is not None)
        result["implementations"][name] = {"failed_properties": failed,
                                           "first_counterexample": {p: repr(found[p]) for p in failed}}
    mutants = [n for n in impls if n != "reference"]
    result["reference_passes_all"] = not result["implementations"]["reference"]["failed_properties"]
    result["mutants_killed"] = sum(bool(result["implementations"][n]["failed_properties"]) for n in mutants)
    result["mutants_total"] = len(mutants)
    (OUT / "conformance.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    for n in impls:
        print(f"{n:38s} failed: {', '.join(result['implementations'][n]['failed_properties']) or '-'}")
    print(f"reference passes all: {result['reference_passes_all']}; mutants killed {result['mutants_killed']}/{result['mutants_total']}")


if __name__ == "__main__":
    main()
