# 19 Validation Report

**Generated:** 2026-08-12T11:05:51.066703+00:00  
**Commit:** `88d1a8d7b08200498eefdcde7f1e71ab2a077ba8`  
**Branch:** `simulation-only/manuscript-revision`  
**Scope:** SIMULATION ONLY. Real-data models run: 0. Real-data files modified: 0. GPU hours: 0.

Every number in this report is read back from the frozen artefacts. No value is hand-typed.

## 1. Acceptance criteria

| criterion | pass | max error | tolerance | description |
|---|---|---|---|---|
| A1 | PASS | 2.706e-15 | 1e-10 | Exact logloss identity holds to the frozen tolerance |
| A2 | PASS | 9.992e-16 | 1e-10 | Exact brier identity holds to the frozen tolerance |
| A3 | PASS | 2.220e-16 | 1e-12 | Injective encoders have zero representation gap at every Delta_eta |
| A4 | PASS | 2.220e-16 | 1e-12 | Designed merge with Delta_eta = 0 has zero representation gap |
| A5 | PASS | 1.667e-03 | 1e-06 | Designed merge with Delta_eta > 0 has strictly positive gap |
| A6 | PASS | 0.000e+00 | 0 | Representation gap nondecreasing in Delta_eta (designed merge) |
| A10 | PASS | 0.000e+00 | 0 | Column-aware hash fiber count exceeds shared-value at equal B |
| A7 | PASS | 0.000e+00 | 0 | Shared-value hash has at most M+1 reachable encodings |
| A8 | PASS |  | monotone | Shared-value loss nondecreasing in M under a position-specific target |
| A9 | PASS | 1.110e-16 | 1e-12 | Shared-value hash has zero gap under a Hamming-weight target |
| A14 | PASS | 0.000e+00 | 0 | Failed cells carry a typed status and NULL metrics |

**11 passed, 0 failed.**

No criterion, tolerance, factor or hypothesis was changed after results were observed. A failing criterion is reported as failing.

## 2. Deviations from the plan

### D0 — Approval wording

**Why:** The execution prompt requires a verbatim approval statement. The approval given was equivalent in intent but not verbatim, and additionally delegated the design-variant choice. Recorded in S1_AUTHORIZATION_AND_DECISIONS.md.

**What was done:** Phase S1 proceeded under a delegated, non-template approval.

### D1 — Ordered-CatBoost running-prior variant

**Why:** The baseline OrderedCatBoostEncoder leaks a row's own label into its own code through the global prior (magnitude ~1/n; measured 7e-5 at n=400), violating A12. The baseline repository's PC2 test covers only the target encoder, so this was never asserted there.

**What was done:** Simulation 1B uses OrderedCatBoostRunningPrior (zero self-influence). The baseline encoder is NOT modified: it produced the frozen real-data results.

### D2 — Bucket-width rule

**Why:** The baseline fixes B by a cardinality staircase because the real-data benchmark needs one value; the plan requires B to be a swept factor.

**What was done:** Staircase overridden by the factor rule 0.5x/1x/2x the total category count. Hash function, seed, token construction and unsigned counting unchanged; a property test asserts byte-identical output at matched B.

### D3 — Per-cell identification of the hash population gap

**Why:** A blanket NOT_IDENTIFIED for hash encoders was over-broad: at M=5, K=4 the full space is 1024 cells and the exact gap computes in milliseconds.

**What was done:** Identification decided per cell (K**M <= 1e6). Where unidentified, BOTH representation_loss and learner_shortfall are NULL, since both require R_Bayes(Z); only total_excess_risk survives.

### D4 — Simulation 1B active block d = min(M, 3)

**Why:** Keeps the active block enumerable. Consequence: M varies the number of pure-noise columns only, so no 1B scenario has many INFORMATIVE high-cardinality columns.

**What was done:** Disclosed in TabS1 and the FigS4 caption. Simulation 1A retains d = M, so the exact theorem check is unaffected.

### D5 — LogisticRegression penalty argument

**Why:** `penalty` is deprecated in scikit-learn 1.8 and removed in 1.10.

**What was done:** Not passed; L2 is the default and C pins the regularisation.

### D6 — LightGBM installed

**Why:** A mandatory Simulation 1B learner was absent from the S0 environment.

**What was done:** Installed at the version pinned in requirements.lock.txt (4.7.0).

### D7 — Simulation 1B design variant: Option B (fractional)

**Why:** The full factorial projects to 90.6 core-hours against an 80 core-hour ceiling that only the advisor may amend.

**What was done:** Option B executed: all 288 scenarios and all 13 encoder configurations with the oracle and logistic regression; the two expensive learners on a representative encoder subset at one bucket width. No DGP factor level dropped; all six central contrasts preserved.

### D8 — S0 resource estimate was wrong

**Why:** The S0 projection understated Simulation 1C by 3.7x (5.84 vs 30.1 measured core-hours) because the finite arm was projected from a 1B cell-cost proxy rather than measured at 1C widths, and undercounted 1B cells (360k vs 547k).

**What was done:** Disclosed in S0_RESOURCE_ESTIMATE.csv row S1_CORRECTION and re-measured. Three implementation optimisations (transform amortisation, full-space caching, coordinate-wise fiber computation) were verified to give identical output and brought the total back inside the ceiling.

### D9 — Simulation 2 asymmetric-condition convention

**Why:** An initial reproduction missed three validation targets by a consistent 1.49x. Investigation of the authoritative parameter_json showed it carries no rho key: the frozen asymmetric condition is one condition per sigma at independent errors, not crossed with rho.

**What was done:** This script's mis-specified condition was corrected; the simulation code was NOT tuned. All five targets then reproduced to four significant figures.

### D11 — CPU ceiling exceeded

**Why:** Measured total 88.1 core-hours against the advisor's 80 core-hour ceiling (1A 0.04 + 1C exact 0.004 + 1C finite 30.1 + 1B 57.97 + Sim2 0.001). Simulation 1B came in at 57.97 against a 49.8 projection, the fourth consecutive underestimate.

**What was done:** OVER BY 8.1 CORE-HOURS (10%). Reported, not concealed. No design was reduced to fit and no result was discarded. The overrun is entirely estimation error, not scope creep: the executed design is exactly the Option B design frozen at S0. The advisor may treat this as requiring retrospective ratification of the ceiling.

### D12 — Bayes-on-Z oracle recorded as a typed absence

**Why:** The oracle predicts ebar(z), which does not exist where the population gap is not identified, so 115,200 rows were initially absent from the 1B output with no explanation on the file.

**What was done:** Those rows are now emitted explicitly with status SKIPPED_INELIGIBLE and NULL metrics, so the absence is typed and countable rather than a silent hole. Row count now matches the design exactly (1,094,400).

### D10 — Run restarted after an operator error

**Why:** A healthy Simulation 1B run was killed on a false diagnosis (a pgrep pattern that cannot match spawn-based pool workers was read as 'workers died'), and the subsequent pkill orphaned 8 workers that ran ~18 minutes producing results no parent could collect.

**What was done:** Per-scenario checkpointing added so an interruption never loses completed work; the run was restarted from scratch. ~2.4 core-hours wasted, recorded here rather than absorbed.

## 3. Stated limitations

1. The Simulation 1B design is FRACTIONAL (Option B, deviation D7): LightGBM and the small MLP were run on a representative encoder subset at one bucket width, not on all 13 encoder configurations. Every DGP factor level and all six central contrasts are retained, and the Bayes-on-Z oracle and logistic regression cover all 13 configurations -- but comparisons INVOLVING THE TWO HEAVY LEARNERS are correspondingly narrower, because those learners did not meet every encoding challenge. Raised by the Gemini S1 audit as a design limitation recorded only as a deviation.
2. Simulation 1B varies M as a NOISE dimension only (d = 3 everywhere); it does not test dense high-cardinality signal. Two independent reviewers ranked this the study's most significant residual weakness.
3. Column-aware hashing has no identified population gap in 1C, and only in the enumerable cells of 1B; contrasts involving it are empirical only.
4. The designed-merge result is a CONSTRUCTION IDENTITY: its Brier gap is an exact function of (K, marginal, Delta_eta) alone. H4 on that encoder verifies the construction, not the theory; the observed-spread companion analysis is the version that can fail.
5. Label and one-hot are exact injective controls in 1A only; in 1B they carry an UNSEEN bucket and are not zero-gap.
6. Marginal prevalence is near 0.5 in every cell; there is no class-imbalance factor, so PR-AUC carries little independent information.
7. A7 is brute-force verified only for M <= 14; at M in {50, 200, 1000} it evaluates the closed form backed by the Stage 1 proposition.
8. The count encoder's population behaviour is a knife-edge tie phenomenon (total collapse under an exactly uniform marginal, injective under Zipf).
9. Coordinate independence is assumed throughout, which is what makes the exact fiber algebra tractable.
10. H6's direction was disclosed BEFORE the run as possibly reversed, based on an S0 pilot. The instrument was corrected for a scale confound; the hypothesis direction was deliberately not changed.

## 4. Resource use (measured)

| component   |   measured_cpu_core_hours |    rows | basis                                        |
|:------------|--------------------------:|--------:|:---------------------------------------------|
| 1B          |                    57.97  | 1094400 | resource.getrusage summed per worker         |
| 1A          |                     0.038 |  211200 | wall clock x worker count                    |
| 1C_exact    |                     0.004 |   14400 | wall clock x worker count                    |
| 1C_finite   |                    30.1   |   91200 | wall clock x worker count                    |
| Sim2        |                     0.001 |    1263 | single-threaded wall clock                   |
| TOTAL       |                    88.11  | 1412463 | ceiling 80; OVER; GPU hours 0; 8 workers max |

## 5. Quality gates

- [x] no real-data model was trained or rerun
- [x] historical repository and real-data result files unchanged
- [x] every factor and tolerance frozen before the full run
- [x] all seeds and package versions recorded
- [x] raw replicate-level outputs frozen before any summary was inspected
- [x] every summary value reproducible from the raw outputs by script
- [x] exact theorem checks meet the frozen tolerance
- [x] Monte Carlo errors reported
- [x] failed cells carry typed failures and null metrics
- [x] no criterion changed after observing results
- [x] all figure and table scripts run from the frozen raw outputs
- [x] Simulation 2 reproduces the validated values
- [x] the package includes the exact Git commit
- [x] this report lists every deviation