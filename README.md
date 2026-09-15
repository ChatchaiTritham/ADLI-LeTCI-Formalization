# ADLI–LeTCI computational logic — reproducibility artifact

Code and data for the article *ADLI–LeTCI Computational Logic: A Mathematical Framework for
Organizational Excellence Assessment* (manuscript submitted to IEEE Access).

The artifact covers every computed result in the article:

| Article element | File | What it does |
|---|---|---|
| Continuous and gated item scores (Eqs. adli, letci, gate), point-weighted category and organizational scores (Eq. points), band classification (Eq. band), gap and priority, Integration Health Index, weight-invariance condition (Propositions 1-2) | `src/adli_letci.py` | Reference implementation of the equations; running it checks the worked example (continuous score 58.75 in band 4, gap 21.25, priority 16.256; gated score 45 in band 3, invariant to the factor weights) |
| Sensitivity analysis (Section "Sensitivity Analysis") | `src/sensitivity_analysis.py` | Monte Carlo weight perturbation, 10,000 iterations, fixed seed 20260914, 25 synthetic departments on the 17 EdPEx 2024-2027 items weighted by official points |
| Specification conformance and mutation analysis (Section "Specification Conformance and Mutation Analysis", Table II) | `src/conformance.py` -> `results/conformance.json` | Data-free validation: seven properties derived from the scoring rules checked on 20,000 random cases each (seed 20260914) for the reference implementation and seven mutants; reference passes all, 7/7 mutants killed |
| Theorem 1 (band of the gated score = band of the weakest factor) and comparison of five aggregation operators (Section "Comparison with Alternative Aggregation Operators", Table III) | `src/operators.py` -> `results/operators.json` | Exhaustive and random check of Theorem 1 (7,006,835 cases, 0 violations); 200 synthetic cohorts x 425 items, five operators, five desiderata, Wilcoxon signed-rank tests with Holm correction, rank-biserial effect sizes and bootstrap CIs (needs SciPy) |
| Theorem 2 (single-factor decisiveness of order-statistic band rules) and comparison of the median rules with the gate (Section "Median Rules Compared with the Gate", Table VI) | `src/holistic.py` -> `results/holistic.json` | Enumeration of all 6^4 band vectors; 200 synthetic cohorts x 425 items, five band rules, measures G1, G2, R1, D2-D4 with paired bootstrap CIs. Motivated by the EdPEx 2024-2027 criteria (p. 79) and Baldrige examiner guidance, which exclude averaging and single-factor gates |
| Figures 2-4 of the article | `src/make_figures.py` -> `figures/fig2_band_map`, `figures/fig3_sensitivity`, `figures/fig4_operators` | Band map of the gated score (from the equations), weight-perturbation distributions (from `results/sensitivity_iterations.csv`) and operator comparison (from `results/operators.json`, which now also stores per-replication values); requires matplotlib |
| Sensitivity results | `results/sensitivity_indicators.csv`, `results/sensitivity_iterations.csv`, `results/sensitivity_summary.json` | Synthetic indicator table, per-iteration statistics and the summary figures reported in the article |

All data are synthetic. No organizational or personal records are included.

## Reproduce

Requirements: Python 3.9 or later and NumPy.

```bash
pip install -r requirements.txt
python verify.py
```

`verify.py` runs the worked-example checks, re-runs the simulation in a temporary directory, and
compares the SHA-256 digest of every output with `results/SHA256SUMS`. It prints
`All 5 result files reproduced byte-for-byte.` and exits with status 0 when the results match.

To regenerate the results in place:

```bash
python src/sensitivity_analysis.py
```

Tested with Python 3.11.15 and NumPy 2.4.6. NumPy's `default_rng` is stable across versions for the
generators used here; if a future NumPy release changes a stream, `verify.py` will report it.

## Key results (from `results/sensitivity_summary.json`)

| Quantity | Continuous score | Gated score |
|---|---|---|
| Mean organizational score at baseline | 71.68 | 57.91 |
| Mean SD of organizational score under ±0.10 weight perturbation | 0.418 | 0.133 |
| Top-10 priority items retained (mean) | 84.1 % | 100.0 % |
| Items keeping their scoring band (mean) | 92.5 % | 100.0 % |
| Items capped by the weakest dimension at baseline | – | 77.4 % |
| Items meeting the weight-invariance condition (sampled weights / whole simplex) | – | 81.9 % / 26.1 % |

Version 1.1.0 replaces the designer-chosen defaults of 1.0.0 (unequal factor weights, equal category weights, 20-point maturity levels) with equal factor weights, the official EdPEx point values and the six official scoring bands, and adds the weight-invariance check. Version 1.2.0 adds the specification-conformance and mutation analysis. Version 1.3.0 adds Theorem 1 and the operator comparison. Version 1.4.0 adds the figure generator and per-replication operator results.

## Licence

- Code (`src/`, `verify.py`): MIT — see `LICENSE`.
- Data (`results/`): CC BY 4.0 — see `LICENSE-DATA`.

## Citation

See `CITATION.cff`. Please cite the archived release DOI once it is available.
