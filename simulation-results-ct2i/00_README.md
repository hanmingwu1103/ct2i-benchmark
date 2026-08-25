# cT2I Simulation-Only Result Package

**Release tag:** `sim-only-s1-complete-v2` — quote this when citing the package; it is the stable identifier.  
**Repository:** https://github.com/hanmingwu1103/ct2i-benchmark.git  
AUTHORITATIVE COMMIT: `PENDING_STAMP_SEE_PACKAGE_PROVENANCE`  
**Branch:** `simulation-only/manuscript-revision`  
The repository, branch and annotated tag above are the authoritative identifiers. The commit SHA is stamped by `scripts/stamp_provenance.py` after the commit exists, because a file inside a commit cannot carry that commit's own SHA at write time.  
**Built:** 2026-08-25T01:33:19.889259+00:00  
**Scope:** SIMULATION ONLY — real-data models run: 0, real-data files modified: 0, GPU hours: 0.

## Start here

1. `20_RESULT_HANDOFF_MEMO.md` — what was run, what passed, where everything is, and the open decisions.
2. `19_VALIDATION_REPORT.md` — every deviation from the plan and every stated limitation.
3. `11_SIM1_TABLES/TabS2.csv` — acceptance criteria, one row each.

**Acceptance: 13 passed, 0 failed.**

## Phase A0.1 addendum deliverables (index)

**Phase A0.1 verdict: BLOCKED.** Complete as work, blocked as a gate. Every required A0.1 deliverable exists, and **full addendum cells run: 0** — real-data models run: 0, GPU hours: 0, nothing under `raw/` written or altered. Phase A1 must not begin until the advisor settles the three matters in `S0B_FINAL_GATE_REPORT.md` §2; the machine-readable status block is that report's §9.

Phase A0.1 is the dense-signal Simulation 1B addendum (d = M = 5, K = 4). It is a later, separate phase from the Simulation 1 / Simulation 2 package indexed under `## Contents` above, and nothing in it changes a number there. The files below are the whole of it.

### Ruling amendment

| file | purpose | status |
|---|---|---|
| `01B_ADDENDUM_ADVISOR_RULINGS.yaml` | rulings D13–D18 transcribed and amended (v5, AMENDMENT-5); amends but does not supersede `01A_ADDENDUM_PROTOCOL_FREEZE.yaml`, which stays authoritative for the design | frozen at A0.1, before any addendum cell; 8 advisor questions open (`advisor_confirmation_requested`) |

### Reports and data

| file | purpose | status |
|---|---|---|
| `S0B_FINAL_GATE_REPORT.md` | the closing document of A0.1: verdict, the three advisor decisions, what was fixed, what remains open, honest disclosures, verification log | final; verdict **BLOCKED** |
| `S0B_COUNCIL_REVIEW.md` | verbatim record of what four council seats said; all four returned a negative verdict | frozen verbatim — never edited, final status is in the gate report |
| `S0B_ADVISOR_RULING_IMPLEMENTATION_REPORT.md` | what was built for each ruling D13–D18, in which file, and which test holds it in place | current, corrected by the consistency pass |
| `S0B_RUNNER_TEST_REPORT.md` | the test-migration half of D18 / AD15: the property tests now exercise the real A1 runner | current |
| `S0B_REFERENCE_IMPLEMENTATION_TEST_REPORT.md` | D17 independent reference check: what the harness compares and what it caught | current |
| `S0B_REFERENCE_GAP_CHECK_d3_frozen.csv` | the D17 harness output, 624 cells on the frozen d = 3 arm | frozen output; **sensitivity arm only** — G4 `NOT_EVALUATED`, not reportable for AD1/AD2 |
| `S0B_D13_PREMISE_INVESTIGATION.md` | measures whether the inferential unit is the block or the draw; D13's premise is refuted | current; basis of `01B` Q6 |
| `S0B_NORMALIZED_CONTRAST_SENSITIVITY.md` | how far the normalized d = 5 minus d = 3 contrast moves under the readings D16 leaves unsaid | current; basis of `01B` Q8 |
| `S0B_RESOURCE_CONFIRMATION.csv` | A1 resource position measured rather than projected: 8.573 core-hours, 0.2026 GB | current; supersedes `S0A_ADDENDUM_RESOURCE_ESTIMATE.csv`, which is left byte-identical |
| `RAW_FREEZE_MANIFEST_ADDENDUM.json` | D15: SHA-256 coverage for every top-level `raw/*.csv`, a strict superset of `RAW_FREEZE_MANIFEST.json` | active; verifier reports `10/10 MATCH`, superset `5/5`, exit 0 |

### Scripts (repository root, outside this directory)

| file | purpose | status |
|---|---|---|
| `scripts/run_sim1b_dense_addendum.py` | the Phase A1 runner for the addendum | ready; **not run** — 0 cells executed |
| `scripts/s0b_reference_gap_check.py` | the D17 reference harness, gates G1–G4 | run on the d = 3 frozen arm (sensitivity); the gate arm needs production rows and cannot run at A0.1 |
| `scripts/s0b_g4_fingerprint_bite.py` | proves G4 bites, using synthetic stored fingerprints because `05b` predates the column | run; cited by `01B` V12 |
| `scripts/s0b_d13_premise_probe.py` | regenerates every number in `S0B_D13_PREMISE_INVESTIGATION.md` | run; regenerates parameters only, no cell |
| `scripts/s0b_normalized_contrast_sensitivity.py` | regenerates every number in `S0B_NORMALIZED_CONTRAST_SENSITIVITY.md` | run |
| `scripts/verify_raw_freeze_manifest_addendum.py` | independent verifier for the D15 addendum manifest; shares no code with its generator | run; exit 0 |

### Tests (repository root, outside this directory)

| file | purpose | status |
|---|---|---|
| `tests/test_a0_1_reconciliation.py` | reconciliation items R1, R9, R10 — disagreements between artefacts rather than defects inside one | 24 tests, all pass |
| `tests/test_a0_2_defect_closure.py` | executable closure of the council's confirmed defects, plus gates G3 and G4 | 58 tests, all pass |
| `tests/test_a1_runner_smoke.py` | smoke and property tests against the real A1 runner, on non-frozen probes only | 91 tests, all pass |

Full suite: **1,086 passed / 1,086 collected** (`PYTHONPATH=src python -m pytest -q`).

`scripts/_s1_parallel.py`, `src/ct2i_benchmark/simulations/sim1_core.py` and `tests/test_a0_dense_addendum_properties.py` were modified by this phase rather than added; `S0B_FINAL_GATE_REPORT.md` §6.4 says why.

### Checksums for the above

The eleven package files in this directory are covered by `PACKAGE_SHA256.json` and `PACKAGE_SHA256SUMS.txt` alongside the rest of the package. The scripts and tests live outside this directory and are covered by `A0_1_DELIVERABLES_SHA256.json`, which enumerates them explicitly and hashes neither itself nor any other manifest. `python3 scripts/verify_package_checksums.py` verifies both manifests and exits non-zero if either disagrees with disk.

## One thing that will mislead you if you skip it

Where the population Bayes-on-Z risk is not identified (hash encoders outside the enumerable cells), **both** `representation_loss` and `learner_shortfall` are NULL, because both require R_Bayes(Z). Only `total_excess_risk` survives there. **A blank is not a zero.** Those are the encoders the manuscript indicts, so reading a blank as "no loss" would invert the claim. Every row carries `theoretical_gap_status`.

## What is NOT in here

No manuscript prose. The plan assigns the abstract, Results, Discussion and Conclusions to the advisor; this package supplies validated numbers, figures and tables only.

## Contents

| file | present | sha256 (first 16) | note |
|---|---|---|---|
| `00_README.md` | yes | (self — see PACKAGE_SHA256SUMS.txt) |  |
| `01_PROTOCOL_FREEZE.yaml` | yes | f6d64fc0335d7cd3 |  |
| `02_ENVIRONMENT_AND_COMMIT.json` | yes | a98ba9d8f0975e84 |  |
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
| `10_SIM1_FIGURES` | yes | b40c096811ad5573 |  |
| `10_SIM1_FIGURES/FIGURE_CAPTIONS.md` | yes | feefbe380bda33cb | final caption text for every publication figure, added in Phase R |
| `11_SIM1_TABLES` | yes | 3808824eeb2911ab |  |
| `12_SIM2_RESULTS.csv` | yes | cf3ecf180ee28f9e |  |
| `13_SIM2_SUMMARY.csv` | n/a |  | Simulation 2 summary is carried in 17_SIM2_SUMMARY_TABLE.csv |
| `14_SIM2_ACCEPTANCE_REPORT.json` | yes | 00b9c12e7644c0d1 |  |
| `15_SIM2_FIGURE_DATA.csv` | yes | 30b9db19528a3260 |  |
| `16_SIM2_FIGURE.pdf` | yes | 69d477c41ef7a30e |  |
| `17_SIM2_SUMMARY_TABLE.csv` | yes | 78731ab26aac24f7 |  |
| `18_RUNTIME_AND_RESOURCE_REPORT.csv` | yes | ca16cd4071146a48 |  |
| `19_VALIDATION_REPORT.md` | yes | 9048336c489d0565 |  |
| `20_RESULT_HANDOFF_MEMO.md` | yes | 4f435cfc6d6fb6df |  |
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
