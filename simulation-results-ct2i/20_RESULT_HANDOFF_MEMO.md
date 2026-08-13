# 20 Result Handoff Memo

**Commit:** `e638d1fb629d5d43f4c6d75a5ec5889925e5a4ba` on `simulation-only/manuscript-revision`  
**Generated:** 2026-08-13T04:18:40.454646+00:00

This memo states what was run and what passed. It contains no interpretation of what the results mean for the manuscript: the plan assigns the abstract, Results, Discussion and Conclusions to the advisor.

## What was run

| component   |   measured_cpu_core_hours |    rows | basis                                        |
|:------------|--------------------------:|--------:|:---------------------------------------------|
| 1B          |                    57.97  | 1094400 | resource.getrusage summed per worker         |
| 1A          |                     0.038 |  211200 | wall clock x worker count                    |
| 1C_exact    |                     0.004 |   14400 | wall clock x worker count                    |
| 1C_finite   |                    30.1   |   91200 | wall clock x worker count                    |
| Sim2        |                     0.001 |    1263 | single-threaded wall clock                   |
| TOTAL       |                    88.11  | 1412463 | ceiling 80; OVER; GPU hours 0; 8 workers max |

## Criteria

13 passed, 0 failed. Full detail in `19_VALIDATION_REPORT.md` and `11_SIM1_TABLES/TabS2.csv`.

## READ THIS BEFORE USING THE TABLES

For hash-encoder cells where the population Bayes-on-Z risk is not identified, **both** `representation_loss` and `learner_shortfall` are NULL, because both require R_Bayes(Z). Only `total_excess_risk` survives there. **A blank is not a zero.** These are exactly the encoders the manuscript indicts, so reading a blank as 'no loss' would invert the claim. The `theoretical_gap_status` column marks every row.

## Where the files are

| what | file |
|---|---|
| frozen protocol | `01_PROTOCOL_FREEZE.yaml` |
| environment and commit | `02_ENVIRONMENT_AND_COMMIT.json` |
| seeds | `03_SEED_MANIFEST.csv` |
| raw replicate results | `05a/05b/05c/05d_*.parquet` |
| summary | `06_SIM1_SUMMARY.csv` |
| acceptance | `07_SIM1_ACCEPTANCE_REPORT.json` |
| figure data | `08_SIM1_FIGURE_DATA.csv` |
| figures | `10_SIM1_FIGURES/` |
| tables | `11_SIM1_TABLES/` |
| Simulation 2 | `12_SIM2_RESULTS.csv` |
| resource report | `18_RUNTIME_AND_RESOURCE_REPORT.csv` |
| deviations | `19_VALIDATION_REPORT.md` |
| council review | `S0_COUNCIL_REVIEW.md` |

## Open decisions for the advisor

1. **The `d = min(M, 3)` arm.** Two independent provider organisations ranked this the most significant residual weakness. The fix is one additional 1B configuration at M = 5, d = M = 5: fully enumerable (1024 cells), negligible cost, and it gives the design one point where signal dimension and feature width move together. It is a design ADDITION, so it was not added unilaterally. **Recommended.**
2. **H1/H2 naming.** Both reviewers noted these are implementation verification rather than falsifiable hypotheses. They are named in the authoritative plan, so they were not renamed.
3. **Release tag and DOI** for the data/code availability statement (placeholder REPO-01).
