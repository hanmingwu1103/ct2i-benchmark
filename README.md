# ct2i-benchmark

Fold-safe, selection-valid, encoding-aware benchmark of tabular-to-image (T2I)
learning on categorical data. Companion code repository for the manuscript
"Benchmarking tabular-to-image learning on categorical data: Encoding, model
selection, and tabular baselines".

The repository carries two separate things, and they are not interchangeable:

1. **the frozen simulation-only result package**, in `simulation-results-ct2i/` —
   the release described on this page, and the only part of this repository that
   supplies numbers to the manuscript;
2. **the Stage 2 real-data pilot infrastructure** (`src/`, `configs/`, `tests/`),
   which validates pipeline correctness, leakage safety, typed failure handling
   and artifact lineage on a four-dataset CPU pilot. No Stage 2 output is a
   final benchmark result.

This release ran 0 real-data models, modified 0 manuscript files, and used 0 GPU
hours.

## Release identity

| field | value |
|---|---|
| repository | https://github.com/hanmingwu1103/ct2i-benchmark |
| branch | `simulation-only/manuscript-revision` |
| annotated tag | `ct2i-simulations-v1.0` |

AUTHORITATIVE COMMIT: `PENDING_STAMP_SEE_PACKAGE_PROVENANCE`

The annotated tag is the stable identifier — quote `ct2i-simulations-v1.0` when
citing this package. The commit SHA on the line above is written in by
`scripts/stamp_provenance.py` once the commit exists, because a file that lives
inside a commit cannot carry that commit's own SHA at write time. The same token
and the same mechanism are used in `simulation-results-ct2i/00_README.md`,
`19_VALIDATION_REPORT.md`, `20_RESULT_HANDOFF_MEMO.md`,
`02_ENVIRONMENT_AND_COMMIT.json` and the repository-root `REPAIR_REPORT.md`, so
that after stamping every one of those files names exactly one commit.

## Simulation scope

Four completed, frozen components. Nothing else in this repository is a
simulation result.

| component | design | executed rows | raw file |
|---|---|---|---|
| Simulation 1A | exact enumeration; `d = M`; verifies the exact log-loss and Brier-risk identities | 211,200 | `raw/sim1a_replicates.csv` |
| Simulation 1B | finite-sample sparse-signal design; `d = 3` in every cell; studies representation loss and learner shortfall as sample size, cardinality, marginal distribution, encoder and learner vary | 1,094,400 (979,200 successful) | `raw/sim1b_replicates.csv` |
| Simulation 1C (exact) | binary-width mechanism with five named signal coordinates; position-specific and Hamming-weight targets; shared-value versus column-aware hashing | 14,400 | `raw/sim1c_exact.csv` |
| Simulation 1C (finite) | the same mechanism at finite sample size | 91,200 | `raw/sim1c_finite.csv` |
| Simulation 2 | candidate-set size and model-selection optimism | 1,263 | `raw/sim2_results.csv` |

Acceptance: **Simulation 1, 13 of 13 criteria pass**
(`simulation-results-ct2i/07_SIM1_ACCEPTANCE_REPORT.json`); **Simulation 2, 5 of
5** (`simulation-results-ct2i/14_SIM2_ACCEPTANCE_REPORT.json`). Every deviation
from the plan and every stated limitation is listed in
`simulation-results-ct2i/19_VALIDATION_REPORT.md`.

### The sparse-signal `d = 3` limitation of Simulation 1B

Simulation 1B was deliberately a sparse-signal finite-sample experiment with
three informative coordinates. Exact dense-signal behavior was examined in
Simulation 1A, while Simulation 1C isolated the binary-width mechanism under
position-specific and Hamming-weight targets.

Inside Simulation 1B, `M` varies the number of pure-noise coordinates, not the
signal dimension: `d = 3` in every cell of the executed design. The arm
therefore does not test dense high-cardinality signal, and no dense-signal or
pure-dimensionality claim may be drawn from it. The disclosure is carried by the
artefacts themselves, not only by this page:
`11_SIM1_TABLES/TabS1.csv` states it in the Simulation 1B row, and `FigS4`
repeats it on the rendered figure and in
`10_SIM1_FIGURES/FIGURE_CAPTIONS.md`.

### One more thing that will mislead you if you skip it

Where the population Bayes-on-Z risk is not identified — hash encoders outside
the enumerable cells — both `representation_loss` and `learner_shortfall` are
NULL, because both require R_Bayes(Z). Those `NOT_IDENTIFIED` population gaps
are omitted from the figures, not drawn as zero, and no failed cell is
represented as zero or chance performance. **A blank is not a zero.** Every row
carries `theoretical_gap_status`.

### Dense-signal addendum — `TERMINATED_BEFORE_EXECUTION`

```text
addendum_run     = false
addendum_status  = TERMINATED_BEFORE_EXECUTION
full addendum cells run: 0
decision_date    = 2026-08-25
```

The proposed dense-signal `M = 5, K = 4, d = 5` Simulation 1B addendum was
permanently discontinued **before execution**. It is not pending, not planned,
not paused and not awaiting approval; it will not be run. The reasons were
design and estimand defects, not computation: the proposed contrast did not have
one stable prespecified estimand; alternative reasonable normalizations changed
the direction; the inferential-unit premise used in the advisor ruling was
false; and the completed Simulation 1A, 1B and 1C arms are sufficient for the
paper.

The authoritative record, with the file-and-line evidence for each reason, is
`simulation-results-ct2i/DENSE_ADDENDUM_DECISION.md`. Every A0 and A0.1 file in
the package is retained **only** as a methodological audit record showing what
was designed and why it was stopped; none of their projected, exploratory or
measured contrasts is a study result, and none may be cited as one.
`scripts/run_sim1b_dense_addendum.py` is retained as design-audit provenance and
its `--execute` mode refuses and exits non-zero.

## Final result locations

Start at **`simulation-results-ct2i/00_README.md`** — the package-level readme,
with the full file index, per-file hashes and the arm-by-arm notes. This page
does not repeat it.

| what | where |
|---|---|
| package readme and file index | `simulation-results-ct2i/00_README.md` |
| what was run, what passed, open decisions | `simulation-results-ct2i/20_RESULT_HANDOFF_MEMO.md` |
| deviations and limitations | `simulation-results-ct2i/19_VALIDATION_REPORT.md` |
| frozen protocol (immutable) | `simulation-results-ct2i/01_PROTOCOL_FREEZE.yaml` |
| environment and commit | `simulation-results-ct2i/02_ENVIRONMENT_AND_COMMIT.json` |
| frozen replicate-level results | `simulation-results-ct2i/05a_SIM1A_REPLICATE_RESULTS.parquet`, `05b_SIM1B_REPLICATE_RESULTS.parquet`, `05c_SIM1C_EXACT_RESULTS.parquet`, `05d_SIM1C_FINITE_RESULTS.parquet` |
| raw outputs behind them | `simulation-results-ct2i/raw/` |
| Simulation 1 summary and acceptance | `simulation-results-ct2i/06_SIM1_SUMMARY.csv`, `07_SIM1_ACCEPTANCE_REPORT.json` |
| Simulation 1 figures and captions | `simulation-results-ct2i/10_SIM1_FIGURES/` (`FigS1`, `FigS2`, `FigS3`, `FigS3_auc`, `FigS4`, each as `.pdf` and `.svg`; `FIGURE_CAPTIONS.md`) |
| Simulation 1 tables | `simulation-results-ct2i/11_SIM1_TABLES/` (`TabS1` executed design, `TabS2` acceptance criteria, `TabS3` prespecified contrasts; each as `.csv` and `.tex`) |
| Simulation 2 results, acceptance, figure, summary | `simulation-results-ct2i/12_SIM2_RESULTS.csv`, `14_SIM2_ACCEPTANCE_REPORT.json`, `16_SIM2_FIGURE.pdf`, `17_SIM2_SUMMARY_TABLE.csv` |
| runtime and resource report | `simulation-results-ct2i/18_RUNTIME_AND_RESOURCE_REPORT.csv` |
| addendum termination record | `simulation-results-ct2i/DENSE_ADDENDUM_DECISION.md` |
| checksum manifests | `simulation-results-ct2i/PACKAGE_SHA256.json`, `PACKAGE_SHA256SUMS.txt`, `A0_1_DELIVERABLES_SHA256.json`, `RAW_FREEZE_MANIFEST.json`, `RAW_FREEZE_MANIFEST_ADDENDUM.json` |

## Reproduction

### Environment

The pinned interpreter is **Python 3.11.9 under `pyenv`**, with
`requirements.lock.txt`. `pyproject.toml` requires `>=3.11`. Any other
interpreter — including any conda environment on the same machine — is not the
pinned environment and is not covered by the lock file; do not use one to
reproduce these numbers.

```bash
pyenv install -s 3.11.9
~/.pyenv/versions/3.11.9/bin/python3 -m pip install -r requirements.lock.txt
```

Run everything below from the repository root.

### Verifiers and tests (cheap; safe to run at any time)

```bash
python3 scripts/verify_package_checksums.py              # package + A0.1 manifests vs disk
python3 scripts/verify_raw_freeze_manifest_addendum.py   # raw freeze coverage, 10/10 MATCH
python3 scripts/stamp_provenance.py --check              # report what commit is stamped where
PYTHONPATH=src python3 -m pytest -q                      # full suite
```

`verify_package_checksums.py` is expected to disagree with disk until the
checksum manifests are regenerated, which is deliberately the **last** step of a
release: the manifests are rebuilt after the provenance stamp so that they hash
the stamped tree. On the released tag it must report `ALL CHECKSUMS: ... MATCH`.

### Regenerating every summary, table and figure from the frozen raw outputs

These read `simulation-results-ct2i/raw/` and the frozen protocol and recompute
every reported number; they fit no model and run no simulation cell.

```bash
PYTHONPATH=src python3 scripts/run_sim1_summarize.py   # 06 summary + 07 acceptance + 08 figure data
PYTHONPATH=src python3 scripts/run_sim1_tables.py      # 11_SIM1_TABLES/TabS1-TabS3, .csv and .tex
PYTHONPATH=src python3 scripts/run_sim1_figures.py     # 10_SIM1_FIGURES/FigS1-FigS4, .pdf and .svg
PYTHONPATH=src python3 scripts/run_s1_reports.py       # 02, 03, 18, 19_VALIDATION_REPORT, 20 memo
```

The CSV, JSON and LaTeX outputs regenerate byte-identically. The figure `.pdf`
and `.svg` files do not: matplotlib embeds a generation timestamp and per-run
element identifiers, so the vector geometry is reproduced while the bytes are
not. Compare figures after normalising those, or compare
`08_SIM1_FIGURE_DATA.csv`, which is exact.

### Re-executing the simulations themselves (expensive)

These are the only commands that run simulation cells. The measured cost of the
full set is 88.11 CPU core-hours
(`simulation-results-ct2i/18_RUNTIME_AND_RESOURCE_REPORT.csv`); they overwrite
the frozen raw outputs, so run them on a copy.

```bash
PYTHONPATH=src python3 scripts/run_sim1a_exact.py      # Simulation 1A, exact
PYTHONPATH=src python3 scripts/run_sim1c_hash.py both  # Simulation 1C, exact + finite
PYTHONPATH=src python3 scripts/run_sim1b_finite.py     # Simulation 1B
PYTHONPATH=src python3 scripts/run_sim2_reproduce.py   # Simulation 2
```

Seeds are a deterministic function of (component, block, replicate); the block
excludes the contrasted factor, so both arms of every within-DGP contrast share
one parameter draw.

## Layout

- `simulation-results-ct2i/` — the frozen simulation result package (start at its
  `00_README.md`)
- `src/ct2i_benchmark/` — package (data, splitting, encoders, layouts, readers,
  models, evaluation, simulations, artifacts)
- `scripts/` — CLI entry points: simulation runners, summary/table/figure
  generators, provenance stamping, checksum verifiers
- `tests/` — typed-failure (P-B), leakage-invariant (P-C), unit and
  simulation-property tests
- `configs/` — validated run configurations, including the frozen CPU pilot
  matrix and `simulation_protocols.yaml`
- `manuscript_reference/` — read-only manuscript sources kept for cross-checking;
  nothing here is generated by this repository
- `REPAIR_REPORT.md` — the full repair and finalization record

## License

Project code: BSD-3-Clause (see `LICENSE`). Third-party datasets and model
weights retain their own licenses — see `DATA_LICENSES.md` and
`MODEL_LICENSES.md`; nothing there is relicensed under BSD-3-Clause.
