# cT2I Simulation-Only Result Package

**Release tag:** `sim-only-s1-complete` — quote this when citing the package; it is stable.  
**Built from commit:** `3a37dd30e79efa0993cfd26540ec432c5428789a` on `simulation-only/manuscript-revision`. This SHA advances by one whenever the reports are regenerated, so the tag above is the identifier to cite, not this.  
**Built:** 2026-08-13T04:19:03.270099+00:00  
**Scope:** SIMULATION ONLY — real-data models run: 0, real-data files modified: 0, GPU hours: 0.

## Start here

1. `20_RESULT_HANDOFF_MEMO.md` — what was run, what passed, where everything is, and the open decisions.
2. `19_VALIDATION_REPORT.md` — every deviation from the plan and every stated limitation.
3. `11_SIM1_TABLES/TabS2.csv` — acceptance criteria, one row each.

**Acceptance: 13 passed, 0 failed.**

## One thing that will mislead you if you skip it

Where the population Bayes-on-Z risk is not identified (hash encoders outside the enumerable cells), **both** `representation_loss` and `learner_shortfall` are NULL, because both require R_Bayes(Z). Only `total_excess_risk` survives there. **A blank is not a zero.** Those are the encoders the manuscript indicts, so reading a blank as "no loss" would invert the claim. Every row carries `theoretical_gap_status`.

## What is NOT in here

No manuscript prose. The plan assigns the abstract, Results, Discussion and Conclusions to the advisor; this package supplies validated numbers, figures and tables only.

## Contents

| file | present | sha256 (first 16) | note |
|---|---|---|---|
| `00_README.md` | yes | a09ca3394636aa33 |  |
| `01_PROTOCOL_FREEZE.yaml` | yes | f6d64fc0335d7cd3 |  |
| `02_ENVIRONMENT_AND_COMMIT.json` | yes | 3927fa9990164b6c |  |
| `03_SEED_MANIFEST.csv` | yes | 08a2bcf15fd29850 |  |
| `04_SIM1_SCENARIO_MANIFEST.csv` | n/a |  | superseded by 11_SIM1_TABLES/TabS1.csv, which reports the design as EXECUTED rather than as planned |
| `05a_SIM1A_REPLICATE_RESULTS.parquet` | yes | 648b9a5ddb70bfc2 | the plan's single 05_SIM1_REPLICATE_RESULTS.parquet is split by arm (05a/05b/05c/05d) because the arms have different schemas |
| `05b_SIM1B_REPLICATE_RESULTS.parquet` | yes | 5b5a191031be52d0 |  |
| `05c_SIM1C_EXACT_RESULTS.parquet` | yes | 1ebb5f533b0602de |  |
| `05d_SIM1C_FINITE_RESULTS.parquet` | yes | a4b69963f07ff7bd |  |
| `06_SIM1_SUMMARY.csv` | yes | 1bed7b9d26daa0c5 |  |
| `07_SIM1_ACCEPTANCE_REPORT.json` | yes | f29f873b8e349dd7 |  |
| `08_SIM1_FIGURE_DATA.csv` | yes | 8ae41eae0967d45c |  |
| `09_SIM1_TABLE_DATA.csv` | n/a |  | table data is emitted per table in 11_SIM1_TABLES/ |
| `10_SIM1_FIGURES` | yes | 274a4bdc95336075 |  |
| `11_SIM1_TABLES` | yes | 4452687e6ac7b910 |  |
| `12_SIM2_RESULTS.csv` | yes | cf3ecf180ee28f9e |  |
| `13_SIM2_SUMMARY.csv` | n/a |  | Simulation 2 summary is carried in 17_SIM2_SUMMARY_TABLE.csv |
| `14_SIM2_ACCEPTANCE_REPORT.json` | yes | 00b9c12e7644c0d1 |  |
| `15_SIM2_FIGURE_DATA.csv` | yes | 30b9db19528a3260 |  |
| `16_SIM2_FIGURE.pdf` | yes | d2d8fe27e1267525 |  |
| `17_SIM2_SUMMARY_TABLE.csv` | yes | 78731ab26aac24f7 |  |
| `18_RUNTIME_AND_RESOURCE_REPORT.csv` | yes | ca16cd4071146a48 |  |
| `19_VALIDATION_REPORT.md` | yes | 6c99400c92417b0a |  |
| `20_RESULT_HANDOFF_MEMO.md` | yes | d552d95e5f5ff6af |  |
| `S0_PROTOCOL_FREEZE_PROVENANCE` | n/a |  |  |
| `S0_IMPLEMENTATION_SPEC.md` | yes | af91e1b71597a944 |  |
| `S0_COUNCIL_REVIEW.md` | yes | 8f27ab1c251814d1 |  |
| `S0_PREFLIGHT_REPORT.md` | yes | 22207006de5fd87c |  |
| `S0_TEST_REPORT.md` | yes | b6c1481ff1a9b105 |  |
| `S0_RESOURCE_ESTIMATE.csv` | yes | 3a1062e160059eb0 |  |
| `S0_INPUT_AND_HASH_MANIFEST.csv` | yes | b46fd46aa4642ee2 |  |
| `S0_PLACEHOLDER_OUTPUT_MAP.csv` | yes | f97d5d3f5c55101d |  |
| `S1_AUTHORIZATION_AND_DECISIONS.md` | yes | b541042e54e21726 |  |
| `RAW_FREEZE_MANIFEST.json` | yes | c63534cede417893 |  |

## Reproducing every number

```bash
python3 scripts/run_sim1a_exact.py        # Simulation 1A, exact
python3 scripts/run_sim1c_hash.py both    # Simulation 1C, exact + finite
python3 scripts/run_sim1b_finite.py       # Simulation 1B (Option B)
python3 scripts/run_sim2_reproduce.py     # Simulation 2 reproduction
python3 scripts/run_sim1_summarize.py     # summary + acceptance
python3 scripts/run_sim1_figures.py       # figures
python3 scripts/run_sim1_tables.py        # tables
python3 scripts/run_s1_reports.py         # validation report + memo
```

Seeds are a deterministic function of (component, block, replicate); the block excludes the contrasted factor so both arms of every within-DGP contrast share one parameter draw.
