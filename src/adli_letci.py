"""Supplementary Material S2: reference implementation of the ADLI--LeTCI scoring equations.

Executable form of the item, category and organisational scoring functions, the weakest-dimension
gated score, band classification, gap and priority ranking, the weight-invariance condition and the
Integration Health Index, exactly as defined in the manuscript (Eqs. adli, letci, gate, cat, org,
band, gap, priority, coherence, ihi; Propositions 1-2).
Indicator estimation (Algorithms 1-2) depends on institution-configured rubric thresholds and is not
reproduced here.

Run this file to check the implementation against the manuscript's worked example.
"""
from typing import Dict, List, Sequence, Tuple

EQUAL_WEIGHTS = (0.25, 0.25, 0.25, 0.25)     # default for (A, D, L, I) and (Lv, Tr, Cp, I)
EDGES = [(1, 2), (2, 5), (2, 6), (5, 4), (6, 4), (4, 7)]
BAND_CHOICES = [(0, 5), (10, 15, 20, 25), (30, 35, 40, 45), (50, 55, 60, 65), (70, 75, 80, 85), (90, 95, 100)]
CHOICES = [c for ch in BAND_CHOICES for c in ch]
# EdPEx 2024-2027 item points; category points are their sums (115, 90, 85, 90, 85, 85, 450)
ITEM_POINTS = {
    "1.1": 65, "1.2": 50, "2.1": 45, "2.2": 45, "3.1": 40, "3.2": 45,
    "4.1": 45, "4.2": 45, "5.1": 40, "5.2": 45, "6.1": 40, "6.2": 45,
    "7.1": 120, "7.2": 80, "7.3": 80, "7.4": 80, "7.5": 90,
}


def _check_weights(w: Sequence[float]) -> None:
    if any(x < 0 for x in w) or abs(sum(w) - 1) > 1e-9:
        raise ValueError("weights must be non-negative and sum to 1")


def item_score(indicators: Sequence[float], weights: Sequence[float] = EQUAL_WEIGHTS) -> float:
    """Eqs. adli / letci: S_item = 100 * sum_k w_k * indicator_k, indicators in [0, 1]."""
    _check_weights(weights)
    if len(indicators) != len(weights) or any(not 0 <= x <= 1 for x in indicators):
        raise ValueError("four indicators in [0, 1] expected")
    return 100 * sum(w * x for w, x in zip(weights, indicators))


def floor_choice(percent: float) -> int:
    """Round a percentage down to the nearest legal choice in C = {0, 5, ..., 100}."""
    return max(c for c in CHOICES if c <= percent + 1e-9)


def band_index(percent: float) -> int:
    """beta(p): index (0-5) of the EdPEx scoring band whose lower bound is the largest one <= p."""
    return max(j for j, ch in enumerate(BAND_CHOICES) if percent >= ch[0])


def cap(indicators: Sequence[float]) -> int:
    """u_beta(m): top of the band containing the weakest dimension m = 100 * min_k indicator_k."""
    return BAND_CHOICES[band_index(100 * min(indicators))][-1]


def gated_item_score(indicators: Sequence[float], weights: Sequence[float] = EQUAL_WEIGHTS) -> int:
    """Eq. gate: cap the continuous score at u_beta(m), then round down to a legal choice."""
    return floor_choice(min(item_score(indicators, weights), cap(indicators)))


def band(score: float) -> int:
    """Eq. band: scoring band 1-6 of a score rounded down to a legal choice."""
    return band_index(floor_choice(score)) + 1


def weight_invariant_everywhere(indicators: Sequence[float]) -> bool:
    """Sufficient condition of Proposition 2 over the whole weight simplex (min_w S_item = m): m >= u_beta(m)."""
    return 100 * min(indicators) >= cap(indicators)


def category_score(item_scores: Dict[str, float], category: int) -> float:
    """Eq. cat with alpha[c,i] = item points / category points."""
    codes = [c for c in ITEM_POINTS if int(c.split(".")[0]) == category]
    return sum(ITEM_POINTS[c] * item_scores[c] for c in codes) / sum(ITEM_POINTS[c] for c in codes)


def organisational_score(item_scores: Dict[str, float]) -> float:
    """Eq. org with omega[c] = category points / 1,000 (equivalently item points / 1,000)."""
    return sum(ITEM_POINTS[c] * item_scores[c] for c in ITEM_POINTS) / 1000


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
    x = (0.75, 0.45, 0.60, 0.55)
    s = item_score(x)
    assert abs(s - 58.75) < 1e-9, s
    assert band(s) == 4                       # 58.75 -> 55 -> band 50-65
    assert abs(gap(80, s) - 21.25) < 1e-9
    p = priority(80, s, 0.90, 0.85)
    assert abs(p - 16.25625) < 1e-9, p
    g = gated_item_score(x)
    assert g == 45 and band(g) == 3, g        # weakest dimension 0.45 -> band 30-45%
    assert abs(priority(80, g, 0.90, 0.85) - 26.775) < 1e-9
    assert weight_invariant_everywhere(x)     # m = 45 equals the band top, so no weights can change it
    assert gated_item_score(x, (0.0, 1.0, 0.0, 0.0)) == 45 and gated_item_score(x, (1.0, 0.0, 0.0, 0.0)) == 45
    assert not weight_invariant_everywhere((0.75, 0.40, 0.60, 0.55))
    assert gated_item_score((0.9, 0.9, 0.9, 0.9)) == 90
    assert sum(ITEM_POINTS.values()) == 1000
    assert [sum(v for k, v in ITEM_POINTS.items() if k.startswith(f"{c}.")) for c in range(1, 8)] == [115, 90, 85, 90, 85, 85, 450]
    assert organisational_score({c: 60.0 for c in ITEM_POINTS}) == 60.0
    assert ihi({c: 50.0 for c in range(1, 8)}) == 1.0
    print("worked example reproduced: S_item = %.2f (band %d), Gap = %.2f, Priority = %.3f; gated = %d (band %d), invariant to weights"
          % (s, band(s), gap(80, s), p, g, band(g)))
