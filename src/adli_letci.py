"""Supplementary Material S2: reference implementation of the ADLI--LeTCI scoring equations.

Executable form of the item, category and organisational scoring functions, maturity
classification, gap and priority ranking, and the Integration Health Index, exactly as
defined in the manuscript (Eqs. adli, letci, cat, org, gap, priority, coherence, ihi).
Indicator estimation (Algorithms 1-2) depends on institution-configured rubric
thresholds and is not reproduced here.

Run this file to check the implementation against the manuscript's worked example.
"""
from typing import Dict, List, Sequence, Tuple

ADLI_WEIGHTS = (0.30, 0.30, 0.20, 0.20)      # (A, D, L, I)
LETCI_WEIGHTS = (0.35, 0.25, 0.25, 0.15)     # (Lv, Tr, Cp, I)
EDGES = [(1, 2), (2, 5), (2, 6), (5, 4), (6, 4), (4, 7)]
BAND_CHOICES = [(0, 5), (10, 15, 20, 25), (30, 35, 40, 45), (50, 55, 60, 65), (70, 75, 80, 85), (90, 95, 100)]
LEVELS = ["Reactive", "Early Systematic", "Aligned", "Integrated", "Role Model"]


def _check_weights(w: Sequence[float]) -> None:
    if any(x < 0 for x in w) or abs(sum(w) - 1) > 1e-9:
        raise ValueError("weights must be non-negative and sum to 1")


def item_score(indicators: Sequence[float], weights: Sequence[float]) -> float:
    """Eqs. adli / letci: S_item = 100 * sum_k w_k * indicator_k, indicators in [0, 1]."""
    _check_weights(weights)
    if len(indicators) != len(weights) or any(not 0 <= x <= 1 for x in indicators):
        raise ValueError("four indicators in [0, 1] expected")
    return 100 * sum(w * x for w, x in zip(weights, indicators))


def band_index(percent: float) -> int:
    """beta(p): index of the EdPEx scoring band whose lower bound is the largest one <= p."""
    return max(j for j, ch in enumerate(BAND_CHOICES) if percent >= ch[0])


def gated_item_score(indicators: Sequence[float], weights: Sequence[float]) -> int:
    """Eq. gate: cap the continuous score at the top of the band supported by the weakest
    dimension, then round down to the nearest legal percent choice."""
    s = item_score(indicators, weights)
    cap = BAND_CHOICES[band_index(100 * min(indicators))][-1]
    capped = min(s, cap)
    return max(c for ch in BAND_CHOICES for c in ch if c <= capped + 1e-9)


def weighted_mean(scores: Sequence[float], weights: Sequence[float] = None) -> float:
    """Eqs. cat / org: convex combination; equal weights when none are given."""
    weights = weights or [1 / len(scores)] * len(scores)
    _check_weights(weights)
    return sum(w * s for w, s in zip(weights, scores))


def maturity(score: float) -> str:
    """Maturity classification M(s) with 20-point bands."""
    return LEVELS[min(int(score // 20), 4)] if score >= 0 else LEVELS[0]


def gap(target: float, score: float) -> float:
    """Eq. gap."""
    return max(0.0, target - score)


def priority(target: float, score: float, criticality: float, risk: float) -> float:
    """Eq. priority."""
    return gap(target, score) * criticality * risk


def ihi(category_scores: Dict[int, float], edges: List[Tuple[int, int]] = EDGES) -> float:
    """Eqs. coherence / ihi."""
    return sum(1 - abs(category_scores[u] - category_scores[v]) / 100 for u, v in edges) / len(edges)


if __name__ == "__main__":
    s = item_score((0.75, 0.45, 0.60, 0.55), ADLI_WEIGHTS)
    assert abs(s - 59.0) < 1e-9, s
    assert maturity(s) == "Aligned"
    assert abs(gap(80, s) - 21.0) < 1e-9
    p = priority(80, s, 0.90, 0.85)
    assert abs(p - 16.065) < 1e-9, p
    g = gated_item_score((0.75, 0.45, 0.60, 0.55), ADLI_WEIGHTS)
    assert g == 45, g          # weakest dimension 0.45 -> band 30-45%, so 59.0 is capped at 45
    assert gated_item_score((0.9, 0.9, 0.9, 0.9), ADLI_WEIGHTS) == 90
    assert ihi({c: 50.0 for c in range(1, 8)}) == 1.0
    print("worked example reproduced: S_item = %.1f (%s), Gap = %.0f, Priority = %.3f; gated = %d"
          % (s, maturity(s), gap(80, s), p, g))
