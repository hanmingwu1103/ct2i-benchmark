# 20 Result Handoff Memo

**Repository:** https://github.com/hanmingwu1103/ct2i-benchmark.git  
**Branch:** `simulation-only/manuscript-revision`  
**Annotated tag (authoritative identifier):** `ct2i-simulations-v1.0` — the final simulation release tag; quote this one. Superseded Phase R tag: `sim-only-s1-complete-v2` (the Phase R release, kept as history, not the current release).  
AUTHORITATIVE COMMIT: `PENDING_STAMP_SEE_PACKAGE_PROVENANCE`  
**Pre-repair parent commit:** `82ca32868f42cb95d2add6527b0ee57649bf7ebd`  
**Generated:** 2026-08-28T16:18:43.230721+00:00

**ADDENDUM RUN: NO. ADDENDUM STATUS: TERMINATED_BEFORE_EXECUTION.** The targeted addendum (one additional Simulation 1B configuration at M = 5, d = M = 5) was NOT executed, and will not be: the advisor permanently discontinued it before execution on 2026-08-25. Full addendum cells run: 0. It is **not** an open decision and nothing awaits the advisor on it — where "open decision 1" appears below, read it as closed by that termination. Authoritative record: `DENSE_ADDENDUM_DECISION.md`.

**Acceptance:** 13/13 criteria passed. **Raw freeze:** all five completed raw result files verified byte-identical. **CPU:** measured 88.11 core-hours against an 80 core-hour ceiling, over by 8.11 (10.1%), status RETROSPECTIVELY RATIFIED PROCESS DEVIATION (completion plan section 7).

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

*(Item 1 is CLOSED — the addendum was terminated before execution on 2026-08-25. Items 2 and 3 concern the manuscript and the release identifier, not the simulations.)*

1. ~~**The `d = min(M, 3)` arm.**~~ **CLOSED 2026-08-25 — DECIDED: DO NOT RUN.** Two independent provider organisations had ranked this the most significant residual weakness, and the proposed fix was one additional 1B configuration at M = 5, d = M = 5. The advisor **permanently discontinued it before execution**: the proposed contrast had no single stable prespecified estimand, alternative reasonable normalizations changed its direction, the inferential-unit premise behind its ruling D13 was false, and Simulations 1A, 1B and 1C are sufficient for the paper. `addendum_status = TERMINATED_BEFORE_EXECUTION`; full addendum cells run: 0; Phase A1 will never run. See `DENSE_ADDENDUM_DECISION.md`. **Nothing is required of the advisor on this item.**
2. **H1/H2 naming.** Both reviewers noted these are implementation verification rather than falsifiable hypotheses. They are named in the authoritative plan, so they were not renamed.
3. **Release tag and DOI** for the data/code availability statement (placeholder REPO-01).
