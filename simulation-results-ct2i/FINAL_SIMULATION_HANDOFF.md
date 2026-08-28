# FINAL SIMULATION HANDOFF — cT2I simulation-only package

This is the release report for the completed simulation package. It is the
document to read before the package is opened, and the document to cite when
the package is referenced.

**SIMULATION ONLY.** Real-data models run: 0. Real-data files modified: 0.
Manuscripts modified: 0. New simulation cells run in the finalization pass: 0.
GPU hours: 0.

---

## 1. Release identifiers

| field | value |
|---|---|
| repository | https://github.com/hanmingwu1103/ct2i-benchmark |
| branch | `simulation-only/manuscript-revision` |
| final commit | `PENDING_STAMP_SEE_PACKAGE_PROVENANCE` |
| annotated tag | `ct2i-simulations-v1.0` |
| superseded Phase R tag | `sim-only-s1-complete-v2` (history, not the current release) |
| ZIP filename | `simulation-results-ct2i-final_PENDING_SHORT_SHA_SEE_PACKAGE_PROVENANCE.zip` |
| ZIP SHA-256 | `PENDING_ZIP_SHA256_SEE_SHA256SUMS` |
| ZIP size | `PENDING_ZIP_BYTES_SEE_SHA256SUMS` bytes |

```text
AUTHORITATIVE COMMIT: PENDING_STAMP_SEE_PACKAGE_PROVENANCE
```

### Why two of those values are tokens inside the archive

The archive's own SHA-256 and byte size do not exist until the archive has been
built, and this file is *inside* the archive. No file can carry the hash of a
container it is part of; a build that tried would never reach a fixed point.
This package therefore uses the Option A convention it already uses for the
commit SHA: the copy shipped **inside** `…-final_….zip` keeps the two
`PENDING_ZIP_…` placeholders that `scripts/stamp_provenance.py` defines, and
the delivered copy **beside** the archive, in the repository working tree, is
stamped with the concrete values once the archive exists. The archive's SHA-256
also travels detached, in `…-final_PENDING_SHORT_SHA_SEE_PACKAGE_PROVENANCE.zip.sha256` next to the archive.

Both copies verify against the manifest that sits beside them: the manifests
inside the archive hash the archive's payload, and the manifests on disk were
regenerated after the stamp. Neither ships stale. The two differ in exactly
three files — this one and the two package manifests — and in nothing else.

No stamp value in this package was typed by hand. Every one is written by
`scripts/stamp_provenance.py` from a command-line argument.

---

## 2. Raw row counts (verified against the frozen raw outputs)

| arm | file | rows |
|---|---|---|
| Simulation 1A | `05a_SIM1A_REPLICATE_RESULTS.parquet` | 211,200 |
| Simulation 1B | `05b_SIM1B_REPLICATE_RESULTS.parquet` | 1,094,400 |
| Simulation 1C exact | `05c_SIM1C_EXACT_RESULTS.parquet` | 14,400 |
| Simulation 1C finite | `05d_SIM1C_FINITE_RESULTS.parquet` | 91,200 |
| Simulation 2 | `12_SIM2_RESULTS.csv` | 1,263 |

The 1,094,400 Simulation 1B rows are 979,200 `SUCCESS` and 115,200
`SKIPPED_INELIGIBLE`. Both counts are reported; the skipped rows are a design
consequence (the cell was never eligible), not a failure, and they are never
represented as zero or as chance performance. `TabS1` reports `rows` and
`rows_success` in separate columns for exactly this reason.

All five raw outputs are byte-identical to the accepted repaired package;
`RAW_FREEZE_MANIFEST.json` carries their SHA-256 values and
`scripts/verify_raw_freeze_manifest_addendum.py` re-checks them.

---

## 3. Acceptance results

| suite | result |
|---|---|
| Simulation 1 acceptance criteria | **13 / 13 pass** (`07_SIM1_ACCEPTANCE_REPORT.json`, `11_SIM1_TABLES/TabS2.csv`) |
| Simulation 2 acceptance criteria | **5 / 5 pass** (`14_SIM2_ACCEPTANCE_REPORT.json`, `17_SIM2_SUMMARY_TABLE.csv`) |
| repository test suite | **1,104 passed / 1,104 collected** (`PYTHONPATH=src python3 -m pytest -q`) |
| package checksums | every shipped file verifies; 0 self-entries in any manifest |

`NOT_IDENTIFIED` is never converted to zero anywhere in the package. Where the
population Bayes-on-Z risk is not identified, `representation_loss` and
`learner_shortfall` are NULL and only `total_excess_risk` survives; every row
carries `theoretical_gap_status`, and FigS4 panel (a) omits those cells and
annotates the count of omitted rows.

---

## 4. Resource use (measured)

| component | measured CPU core-hours | rows | basis |
|---|---|---|---|
| Simulation 1B | 57.97 | 1,094,400 | `resource.getrusage` summed per worker |
| Simulation 1A | 0.038 | 211,200 | wall clock × worker count |
| Simulation 1C exact | 0.004 | 14,400 | wall clock × worker count |
| Simulation 1C finite | 30.10 | 91,200 | wall clock × worker count |
| Simulation 2 | 0.001 | 1,263 | single-threaded wall clock |
| **TOTAL** | **88.11** | 1,412,463 | 8 workers maximum |

GPU hours: 0. The 80 core-hour ceiling was exceeded (88.11); the overrun is
recorded as deviation D11 and retrospectively ratified in
`19_VALIDATION_REPORT.md` §4a. Source of record:
`18_RUNTIME_AND_RESOURCE_REPORT.csv`.

The finalization pass that produced this release ran no simulation cells and
consumed no measurable compute beyond hashing and archiving.

---

## 5. Dense addendum status

```text
addendum_run:     false
addendum_status:  TERMINATED_BEFORE_EXECUTION
addendum cells run: 0
```

The proposed dense-signal `M = 5, K = 4, d = 5` Simulation 1B addendum was
**permanently discontinued before execution** by the advisor on 2026-08-25. It
is not pending, not planned, and not awaiting approval; Phase A1 will never run.

Reasons, in the terms recorded at the time: the proposed contrast had no single
stable prespecified estimand; alternative reasonable normalizations changed the
direction of the effect; the inferential-unit premise used in the ruling was
false; and the completed 1A, 1B and 1C arms are sufficient for the paper.

The A0 and A0.1 files (`01A_ADDENDUM_PROTOCOL_FREEZE.yaml`,
`01B_ADDENDUM_ADVISOR_RULINGS.yaml`, `S0A_*`, `S0B_*`) are retained **only** as
methodological audit records showing that the addendum was stopped before
execution. None of their projected, exploratory or measured contrasts is a
study result. Full decision record: `DENSE_ADDENDUM_DECISION.md`. Integrity
coverage for those files: `A0_1_DELIVERABLES_SHA256.json`.

---

## 6. Known limitations

Carried verbatim in substance from `19_VALIDATION_REPORT.md` §3, which remains
the source of record.

1. **Simulation 1B is a sparse-signal design.** `d = 3` informative coordinates
   in **every** cell; `M` varies the number of pure-noise coordinates only. The
   arm does **not** establish a pure effect of increasing signal dimension. Two
   independent reviewers ranked this the study's most significant residual
   weakness, and it is the limitation the terminated addendum was meant to
   address. Exact dense-signal behaviour is carried by Simulation 1A and the
   binary-width mechanism by Simulation 1C.
2. The Simulation 1B design is **fractional** (Option B, deviation D7): LightGBM
   and the small MLP were run on a representative encoder subset at one bucket
   width. All DGP factor levels and all six central contrasts are retained, and
   the Bayes-on-Z oracle and logistic regression cover all 13 encoder
   configurations, but comparisons involving the two heavy learners are
   correspondingly narrower.
3. Column-aware hashing has no identified population gap in 1C, and only in the
   enumerable cells of 1B; contrasts involving it are empirical only.
4. The designed-merge result is a **construction identity**: its Brier gap is an
   exact function of `(K, marginal, Δη)` alone. H4 on that encoder verifies the
   construction, not the theory.
5. Label and one-hot are exact injective controls in **1A only**; in 1B they
   carry an UNSEEN bucket and are not zero-gap.
6. Marginal prevalence is near 0.5 in every cell; there is no class-imbalance
   factor, so PR-AUC carries little independent information.
7. A7 is brute-force verified only for `M ≤ 14`; at `M ∈ {50, 200, 1000}` it
   evaluates the closed form backed by the Stage 1 proposition.
8. The count encoder's population behaviour is a knife-edge tie phenomenon.
9. Coordinate independence is assumed throughout.
10. H6's direction was disclosed **before** the run as possibly reversed. The
    instrument was corrected for a scale confound; the hypothesis direction was
    deliberately not changed.
11. CPU ceiling exceeded (88.11 of 80 core-hours), deviation D11.

---

## 7. Exact files intended for manuscript insertion

Every path is relative to `simulation-results-ct2i/`. All were confirmed present
at release time and are covered by `PACKAGE_SHA256.json`.

### Figures (insert the PDF; the SVG is the editable source)

| file | what it shows |
|---|---|
| `10_SIM1_FIGURES/FigS1.pdf` / `.svg` | estimated versus theoretical representation gap |
| `10_SIM1_FIGURES/FigS2.pdf` / `.svg` | representation loss versus within-fiber posterior spread (1A, exact) |
| `10_SIM1_FIGURES/FigS3.pdf` / `.svg` | shared-value versus column-aware hashing as binary width M grows |
| `10_SIM1_FIGURES/FigS3_auc.pdf` / `.svg` | finite-sample ROC-AUC, shared-value versus column-aware hashing |
| `10_SIM1_FIGURES/FigS4.pdf` / `.svg` | representation loss and learner shortfall (1B); 6.90 × 3.15 in canvas |
| `16_SIM2_FIGURE.pdf` / `16_SIM2_FIGURE.svg` | Simulation 2 |

`10_SIM1_FIGURES/FIGURE_CAPTIONS.md` carries the final caption text for every
figure above. **Insert those captions as written.** FigS4's two mandated
clarifications — `d = 3` in every Simulation 1B cell, and `NOT_IDENTIFIED`
population gaps omitted rather than set to zero — live in that caption because
they are too long for the graphics canvas; a figure inserted without them is
missing a required disclosure.

### Tables (insert the `.tex`; the `.csv` is the same table as data)

| file | what it is |
|---|---|
| `11_SIM1_TABLES/TabS1.tex` / `.csv` | the executed design, one row per arm; 1B row includes `woe` and reports 1,094,400 rows with 979,200 successes, `d = 3` stated |
| `11_SIM1_TABLES/TabS2.tex` / `.csv` | acceptance criteria, one row each |
| `11_SIM1_TABLES/TabS3.tex` / `.csv` | hypothesis results |

### Summary CSVs (numbers quoted in prose)

| file | what it is |
|---|---|
| `06_SIM1_SUMMARY.csv` | Simulation 1 per-cell summary — every Simulation 1 number quoted in the text |
| `17_SIM2_SUMMARY_TABLE.csv` | Simulation 2 criteria, observed value against bound |
| `18_RUNTIME_AND_RESOURCE_REPORT.csv` | the resource paragraph |
| `08_SIM1_FIGURE_DATA.csv` | the per-point data behind the Simulation 1 figures |
| `15_SIM2_FIGURE_DATA.csv` | the per-point data behind the Simulation 2 figure |

### Statements that must accompany the insertion

* Simulation 1B is a **sparse-signal** design, `d = 3` in every cell; `M` varies
  pure-noise coordinates only (limitation 1 above).
* `NOT_IDENTIFIED` is an absence, not a zero.
* The dense-signal addendum was `TERMINATED_BEFORE_EXECUTION`; 0 cells run.

### Not for insertion

No manuscript prose is in this package. The abstract, Results, Discussion and
Conclusions are the advisor's. Nothing under `raw/`, no `S0*`/`S0A_*`/`S0B_*`
audit record, and no A0/A0.1 file is a study result.

---

## 8. Reproducing every number

```bash
python3 scripts/run_sim1a_exact.py        # Simulation 1A, exact
python3 scripts/run_sim1c_hash.py both    # Simulation 1C, exact + finite
python3 scripts/run_sim1b_finite.py       # Simulation 1B (Option B)
python3 scripts/run_sim2_reproduce.py     # Simulation 2 reproduction
python3 scripts/run_sim1_summarize.py     # summary + acceptance
python3 scripts/run_sim1_figures.py       # figures
python3 scripts/run_sim1_tables.py        # tables
python3 scripts/run_s1_reports.py         # validation report + memo
python3 scripts/verify_package_checksums.py            # both manifests
python3 scripts/verify_raw_freeze_manifest_addendum.py # raw freeze
```

Seeds are a deterministic function of `(component, block, replicate)`; the block
excludes the contrasted factor, so both arms of every within-DGP contrast share
one parameter draw.

---

## 9. Next action

Return this package for one-pass manuscript integration.
