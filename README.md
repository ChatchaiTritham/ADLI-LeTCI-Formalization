# ADLI–LeTCI computational logic — reproducibility artifact

Code and data for the article *Median Band Rules for Baldrige-Based Excellence Assessment: An
Order-Statistic Analysis of the Scoring Guidance* (manuscript submitted to IEEE Access).

The artifact covers every computed result in the article:

| Article element | File | What it does |
|---|---|---|
| Continuous and gated item scores (Eqs. adli, letci, gate), point-weighted category and organizational scores (Eq. points), band classification (Eq. band), gap and priority, Integration Health Index, weight-invariance condition (Propositions 1-2) | `src/adli_letci.py` | Reference implementation of the equations; running it checks the worked example (continuous score 58.75 in band 4, gap 21.25, priority 16.256; gated score 45 in band 3, invariant to the factor weights) |
| Sensitivity analysis (Section "Sensitivity Analysis") | `src/sensitivity_analysis.py` | Monte Carlo weight perturbation, 10,000 iterations, fixed seed 20260914, 25 synthetic departments on the 17 EdPEx 2024-2027 items weighted by official points |
| Specification conformance and mutation analysis (Section "Specification Conformance and Mutation Analysis", Table II) | `src/conformance.py` -> `results/conformance.json` | Data-free validation: seven properties derived from the scoring rules checked on 20,000 random cases each (seed 20260914) for the reference implementation and seven mutants; reference passes all, 7/7 mutants killed |
| Theorem 1 (band of the gated score = band of the weakest factor) and comparison of five aggregation operators (Section "Comparison with Alternative Aggregation Operators", Table III) | `src/operators.py` -> `results/operators.json` | Exhaustive and random check of Theorem 1 (7,006,835 cases, 0 violations); 200 synthetic cohorts x 425 items, five operators, five desiderata, Wilcoxon signed-rank tests with Holm correction, rank-biserial effect sizes and bootstrap CIs (needs SciPy) |
| Theorem 2 (single-factor decisiveness of order-statistic band rules) and comparison of the median rules with the gate (Section "Median Rules Compared with the Gate", Table VI) | `src/holistic.py` -> `results/holistic.json` | Enumeration of all 6^4 band vectors; 200 synthetic cohorts x 425 items, five band rules, measures G1, G2, R1, D2-D4 with paired bootstrap CIs. Motivated by the EdPEx 2024-2027 criteria (p. 79) and Baldrige examiner guidance, which exclude averaging and single-factor gates |
| Quantities added in review: share of cohorts per Table V comparison, ordinal single-factor measure R0, order-statistic rules as k-of-4 sortings (Proposition 3), and the floor-mean counterexample to a bijection-only Lemma 1 | `src/review_extras.py` -> `results/review_extras.json` | Reads `operators.json` and `holistic.json`; replays the seeded stream of `holistic.py` and checks the replay against the stored per-replication R1 |
| Theorem 3 (n factors, k bands): t-robustness of order statistics, medians as the most robust rules, k-of-n sorting identity, and a brute-force check that k >= n is needed for the lemma | `src/general_nk.py` -> `results/general_nk.json` | Exhaustive over all band vectors for n <= 6, k <= 7; every symmetric rule enumerated for small (n, k) |
| Published NIST scorebooks as real data: per-factor ranges and consensus percentages of the 18 items of the 2008 Novel Connect Scorebook (with PDF page numbers), band rules vs the examiners' consensus band (Table VIII), and exact reproduction of the 2008 Novel Connect and 2010 NuGrain worksheets | `src/scorebook_factors.py` -> `results/scorebook_factors.json` | Data transcribed from https://www.nist.gov/document/2008novelconnectscorebookpdf and https://www.nist.gov/document/2010nugrainscorebookpdf |
| Range-null baseline for the scorebook agreement: probability that a band drawn uniformly within the four factor ranges falls between the medians in all 18 items (1/31104, about 3.2e-5) and the exact one-sided 95% lower bound for 18/18 (0.85) | `src/chance_baseline.py` -> `results/chance_baseline.json` | Uses the data transcribed in `src/scorebook_factors.py` |
| Extension to three published scorebooks (S12): factor ranges and consensus percentages of the 54 items of the 2007 Share Food, 2008 Novel Connect and 2009 Nightingale scorebooks, transcribed twice independently (216/216 factor cells and 54/54 percentages agree); band rules vs consensus band with Wilson intervals, exact McNemar tests, range-null baseline and exact reproduction of the three worksheet totals (425, 554, 477) | `src/scorebook_extension.py` -> `results/scorebook_extension.json`, `results/scorebook_items.csv` | Inputs in `src/data_scorebooks/`. Pre-registration (written before the new scorebooks were searched for), source URLs of all 13 NIST scorebooks screened (2002-2018; only 2007-2009 carry a per-factor grid), PDF SHA-256 digests and the coordinate extractor are in `provenance/scorebooks/`. The PDFs are not redistributed; download them from the URLs in `sources.csv` and check the digests |
| Practice survey (S13): factor-combination rules prescribed by 17 public excellence-framework documents (Baldrige, EdPEx, AUN-QA, PMQA 4.0, Singapore BE, EFQM 2021, CAF 2020/2024, APO), with verbatim quotations, page locators, URLs and SHA-256 digests; counts by rule category and the compact table of the article | `src/practice_survey.py` -> `results/practice_survey.json` | Input `src/data_practice_survey/survey_table.csv`, built by `provenance/practice_survey/build_survey.py`. Source documents are not redistributed (third-party copyright; three are third-party-hosted copies, flagged in the CSV); digests in `provenance/practice_survey/SOURCES_SHA256SUMS.txt` |
| Figures 2-5 of the article | `src/make_figures.py` -> `figures/fig2_band_map`, `figures/fig3_sensitivity`, `figures/fig4_operators`, `figures/fig5_holistic` | Band map of the gated score (from the equations), weight-perturbation distributions (from `results/sensitivity_iterations.csv`) and operator comparison (from `results/operators.json`, which now also stores per-replication values) and single-factor sensitivity of the band rules with a sweep over within-item imbalance (from `results/holistic.json`; the generator parameters are recovered by replaying the seeded random stream of `holistic.py`, checked against the stored lone-outlier share); requires matplotlib |
| Sensitivity results | `results/sensitivity_indicators.csv`, `results/sensitivity_iterations.csv`, `results/sensitivity_summary.json` | Synthetic indicator table, per-iteration statistics and the summary figures reported in the article |

All data are synthetic, except the factor ratings and consensus percentages transcribed from the published NIST training scorebooks (S10-S12), which describe fictitious applicants, and the quotations from public framework documents (S13). No organizational or personal records are included.

## Reproduce

Requirements: Python 3.9 or later, NumPy, SciPy and Matplotlib (see `requirements.txt`).

```bash
pip install -r requirements.txt
python verify.py
```

`verify.py` runs the worked-example checks, re-runs the simulation in a temporary directory, and
compares the SHA-256 digest of every output with `results/SHA256SUMS`. It prints
`All 13 result files reproduced byte-for-byte.` and exits with status 0 when the results match.

To regenerate the results in place:

```bash
python src/sensitivity_analysis.py
```

Tested with Python 3.11.15, NumPy 2.4.6 and SciPy 1.17.1 on Windows 11. NumPy's `default_rng` is stable across versions for the
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

Version 1.1.0 replaces the designer-chosen defaults of 1.0.0 (unequal factor weights, equal category weights, 20-point maturity levels) with equal factor weights, the official EdPEx point values and the six official scoring bands, and adds the weight-invariance check. Version 1.2.0 adds the specification-conformance and mutation analysis. Version 1.3.0 adds Theorem 1 and the operator comparison. Version 1.4.0 adds the figure generator and per-replication operator results. Versions 1.5.0 and 1.6.0 add the median band rules and the scorebook check; 1.7.0 adds Fig. 5; 1.8.0 adds the review quantities (S8); 1.9.0 adds the n-factor generalization (S9) and the transcribed scorebook factor ratings (S10); 1.9.1 adds the range-null baseline (S11). Version 1.9.2 updates this README and `CITATION.cff` only; no code or result file changed. Version 1.10.0 adds the extension to three scorebooks (S12) and the practice survey (S13); the ten earlier result files are unchanged.

## Licence

- Code (`src/`, `verify.py`): MIT — see `LICENSE`.
- Data (`results/`): CC BY 4.0 — see `LICENSE-DATA`.

## Citation

See `CITATION.cff`. Please cite the archived release DOI once it is available.
