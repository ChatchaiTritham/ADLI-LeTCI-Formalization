# ADLI–LeTCI computational logic — reproducibility artifact

Code and data for the article *ADLI–LeTCI Computational Logic: A Mathematical Framework for
Organizational Excellence Assessment* (manuscript submitted to IEEE Access).

The artifact covers every computed result in the article:

| Article element | File | What it does |
|---|---|---|
| Item, category and organizational scores; maturity classification; gap and priority; Integration Health Index; weakest-dimension gated score (Eq. gate, Proposition 5) | `src/adli_letci.py` | Reference implementation of the equations; running it checks the worked example (continuous score 59.0, *Aligned*, gap 21, priority 16.065, gated score 45) |
| Sensitivity analysis (Section "Sensitivity Analysis") | `src/sensitivity_analysis.py` | Monte Carlo weight perturbation, 10,000 iterations, fixed seed 20260913 |
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
`All 3 result files reproduced byte-for-byte.` and exits with status 0 when the results match.

To regenerate the results in place:

```bash
python src/sensitivity_analysis.py
```

Tested with Python 3.11.15 and NumPy 2.4.6. NumPy's `default_rng` is stable across versions for the
generators used here; if a future NumPy release changes a stream, `verify.py` will report it.

## Key results (from `results/sensitivity_summary.json`)

| Quantity | Continuous score | Gated score |
|---|---|---|
| Mean organizational score at baseline | 71.10 | 58.77 |
| Mean SD of organizational score under ±0.10 weight perturbation | 0.550 | 0.186 |
| Top-10 priority items retained (mean) | 82.6 % | 100 % |
| Items keeping their maturity level (mean) | 93.7 % | 99.2 % |
| Items capped by the weakest dimension at baseline | – | 71.2 % |

## Licence

- Code (`src/`, `verify.py`): MIT — see `LICENSE`.
- Data (`results/`): CC BY 4.0 — see `LICENSE-DATA`.

## Citation

See `CITATION.cff`. Please cite the archived release DOI once it is available.
