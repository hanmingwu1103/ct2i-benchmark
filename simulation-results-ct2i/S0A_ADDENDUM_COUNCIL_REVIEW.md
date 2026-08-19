# S0A Council Review — Dense-Signal Addendum (Phase A0)

**Both mandated provider seats were filled with the real providers. No review in this
file is a substitution, and no output is attributed to a provider that did not produce
it.**

**Phase:** A0 (preflight). **Scope:** simulation only. **Addendum cells run: 0.**
**Reviewed artefacts:** `01A_ADDENDUM_PROTOCOL_FREEZE.yaml` (as drafted before the
corrections this review prompted), `01_PROTOCOL_FREEZE.yaml`,
`tests/test_a0_dense_addendum_properties.py`, `scripts/s0a_addendum_microbenchmark.py`,
`S0A_ADDENDUM_MICROBENCHMARK_ROWS.csv`, `S0A_ADDENDUM_RESOURCE_ESTIMATE.csv`,
`sim1_core.py`, `sim1_design.py`, `sim1_finite.py`, `run_sim1b_finite.py`,
`03_SEED_MANIFEST.csv`, `RAW_FREEZE_MANIFEST.json`.

Provider notes are reproduced **verbatim** below. Line references point at the files as
they stood *at review time*; several statements in the freeze have since been corrected
**because of** these reviews, and each correction is marked in place in the YAML.

---

## 1. Council composition

| Seat | Assigned provider | Status |
|---|---|---|
| Orchestration, integration, write-boundary enforcement | Claude (host) | Filled |
| Implementation, tests, numerical verification | **Codex** | **FILLED** — `codex exec --sandbox read-only`, `gpt-5.6-terra` |
| Independent design / scientific scope | **Gemini** | **FILLED** — `gemini-2.5-pro` via Vertex AI (project `wq-alphas-prod-2607`) |
| Supplementary design review | Claude (fresh context) | Filled — retained, not substituting |
| Supplementary implementation review | Claude (fresh context) | Filled — retained, not substituting |

**On the A0 work order's premise.** The work order stated that "neither Codex nor Gemini
is available in this environment" and planned a disclosed Claude substitution (decision
D11). That premise was **tested rather than accepted, and found false**: both CLIs are
installed and authenticated, matching the S0 precedent in `S0_COUNCIL_REVIEW.md`. The
named seats were therefore filled for real and D11 is resolved without substitution. The
two Claude reviewers had already been launched and are retained as supplementary — the
same treatment the S0 round gave its Claude stand-in once Gemini became reachable.

Each reviewer was launched with no access to the orchestrator's reasoning and was given
the freeze, the parent freeze, the anchor numbers and the test list — not the preflight
report's conclusions. Each was asked to return `CRITICAL VETO: <n>`.

---

## 2. Verdict counts

| Seat | CRITICAL VETO |
|---|---|
| Codex (implementation/verification) | **2** |
| Gemini (design/scope) | **1** |
| Claude supplementary (design) | **2** |
| Claude supplementary (implementation) | **1** |
| **Distinct critical findings after de-duplication** | **4** |

**All four seats independently reached "do not execute as written."**

### The four distinct CRITICAL findings

| # | finding | raised by | host verification |
|---|---|---|---|
| C1 | **Total signal strength is not held constant when d goes 3 → 5.** `eta_raw` sums one p-centred main effect per active coordinate with no normalisation by d, so at fixed `tau` the d = 5 arm simply carries more signal. The freeze's "exactly one factor" and `nothing_else_differs: true` were false. | **Gemini, Claude-design, Claude-impl** (3 seats concurring) | **CONFIRMED.** `sd(eta)` is larger at d = 5 in **all 24** (marginal × tau × n_int × Δη) combinations — the grid is 2 × 2 × 2 × 3 = 24, corrected from an earlier miscount of 16 — ratio range **1.038–1.437**, confirmed by independent recomputation (24/24); `R_log(X)` falls correspondingly. |
| C2 | **The uncertainty scheme is anti-conservative.** The 48 scenario pairs are not 48 independent units: the block key excludes `delta_eta` and `n_train`, so they cluster into **8** parameter-draw blocks. `sd/sqrt(48)` understates the SE; one seat measured 2.4× and a conclusion that flips significance. | **Claude-design (CRITICAL), Gemini (MAJOR)** | **CONFIRMED.** `df[(df.M==5)&(df.K==4)].seed.nunique() == 400 == 8 blocks × 50 replicates`. |
| C3 | **The A1 runner does not exist, so no preflight test exercises it.** `scripts/run_sim1b_dense_addendum.py` is mandated by D3 but absent; the seed rule is reimplemented three times (freeze, test module, microbenchmark) with no shared source. | **Codex** | **CONFIRMED and inherent to A0** — A0 is forbidden to write A1's runner. Converted into gate AD13 + decision D18. |
| C4 | **AD10's raw-file clause is unsatisfiable.** It claimed `raw/*.csv` byte-identical to `RAW_FREEZE_MANIFEST.json`, but that manifest holds only the five parquet/CSV result files and no `raw/` entry; AT16 checks only a line count, so altered content with an unchanged row count would pass. | **Codex** | **CONFIRMED.** Manifest keys are the five result files; `raw/` holds five CSVs, two logs and a parts directory, none of them in the manifest. |

### Convergent MAJOR findings the host also verified

- **Simulation 1A at M = 5, K = 4 is already d = M = 5 and exact** (52,800 rows,
  `n_cells = 1024`, 100 replicates, both hash encoders). The freeze's uniqueness claim
  overstated, and the population half of E1 is already answerable from frozen data at
  zero cost. *(Claude-design; confirmed by the host.)*
- **`hash_shared` representation loss is identical across B0/B1/B2** — `max|B0−B1| =
  max|B0−B2| = 0.0` — because the shared-value token space holds only K = 4 tokens. The
  bucket-width sweep carries zero information for that encoder and its three contrasts
  triple-count one piece of evidence in the BH family. *(Claude-design; confirmed.)*
- **Representation loss is exactly `n_train`-invariant** for `label`, `onehot`,
  `hash_shared` and `homals` (`max|Δ| = 0.0`), so 24 of the 48 pairs are literal
  duplicates for that quantity. *(Claude-design; confirmed.)*
- **The interaction pairs are a different SET, not just a different density.** At d = 3
  they are {(0,1), (0,2), (1,2)}; at d = 5 they are {(0,1), (0,2), (0,3)} — all on
  coordinate 0, the one `phi_D` merges, leaving coordinate 4 purely additive.
  *(Claude-design; confirmed.)*
- **"Every derived seed is disjoint" is overbroad.** The hash seed (20260810), the
  ordered-CatBoost permutation seeds (977–980) and the bootstrap seed (90210) are
  intentionally SHARED constants. *(Codex and Claude-impl, concurring; confirmed.)*
- **AD1/AD2 are self-checks as specified.** `exact_gap_report` derives both sides of the
  identity from one `fiber_posteriors` aggregation and the runner stores
  `theoretical_gap = representation_loss`, giving ~1e-16 by construction. The repo ships
  `reference_gap_report` for exactly this and the preflight did not use it.
  *(Codex and Claude-impl, concurring; confirmed.)*
- **AT coverage is narrower than labelled.** `IDENTITY_GRID` runs at `n_train = 5000`,
  replicate 1 only, so the `n_train = 500` fitted-encoder regime is never exercised at
  A0. *(Codex and Claude-design, concurring.)*
- **`run_sim1b_finite.py:151-152` silently `continue`s on a setup exception**, writing
  zero rows for that replicate — a failure with no typed row, which AD9 cannot detect.
  *(Claude-impl and Codex, concurring.)*
- **`exact_or_mc == "mc"` on all 182,400 `IDENTIFIED_EXACT` rows**, contradicting the
  "exact population computation" framing for anyone reading that column.
  *(Claude-impl; confirmed.)*
- **Three of five ratios in `S0A_ADDENDUM_RESOURCE_ESTIMATE.csv` do not reproduce to the
  fourth decimal** from the rows they cite (n500 1.0262 vs 1.0249 stated). Impact ≈ 0.1%
  on the projection; the 8.55-vs-20 verdict is unaffected. *(Claude-impl and Gemini,
  concurring.)*

**On the resource projection, all four seats agree the arithmetic is sound.** Codex
re-derived the anchor (5.9308679 core-hours), the split, the 1.0298 weighted ratio, the
6.108 raw and 8.551 calibrated hours and the 0.084 GB disk independently, and confirmed
that `cpu_seconds` is a per-cell amortised value so the row-sum does not double-count.

**On preflight side-effects, all seats agree A0 was clean.** All five frozen artefacts
re-hash identically; `01_PROTOCOL_FREEZE.yaml` contains no addendum content; the only
tracked modifications are the seven Phase R files, all with pre-session mtimes.

---

## 3. What was changed in response

Every factually false statement was corrected in `01A_ADDENDUM_PROTOCOL_FREEZE.yaml`,
with each correction marked in place so the record shows what was claimed and why it
changed: `nothing_else_differs` withdrawn; a second top-level confound block
(`disclosed_confound_signal_strength`) added with the measured magnitudes; the
uniqueness-versus-1A claim corrected and the addendum's genuine contribution narrowed;
the disjointness structural argument corrected and the intentionally shared constants
named; AD10 restated and its gap routed to a decision; the E1 count claim replaced with
the measured distribution; E3's mechanism corrected; E4 reclassified as a reporting
policy; AD3 and AD8 wording made honest about what they gate.

**The uncertainty scheme (D13) was changed to block-clustered inference on 8 blocks.**
Freezing a procedure three seats identified as anti-conservative would be a worse error
than correcting it before approval, and the correction only widens intervals. It is
flagged for override.

**Nothing was changed to make a veto disappear.** C1 and C2 are recorded as live design
issues requiring an advisor ruling (D14) or an adopted correction open to override (D13);
C3 and C4 became gates AD13/AD14 and decisions D15/D18.

**Five decisions remain UNRESOLVED and require an advisor ruling before A1: D14
(signal-strength confound), D15 (AD10 raw coverage), D16 (E1 decision rule), D17
(AD1/AD2 independence), D18 (runner-first gate).**

---

## 4. Codex — implementation and verification seat (VERBATIM)

Verdict: **veto execution as written.** The frozen originals are intact and resource arithmetic is correct, but the required addendum runner does not exist and AD10 cannot verify the raw CSV immutability it claims. The 264 preflight tests pass, but several validate helpers or tautologies rather than the eventual runner/output.

- **CRITICAL** — `scripts/run_sim1b_dense_addendum.py` is required by freeze D3 ([01A_ADDENDUM_PROTOCOL_FREEZE.yaml:438-440]) but is absent (`dense_runner_exists=0`). AT1–AT16 import/test the old runner or helpers; no test exercises the implementation that would execute A1.

- **CRITICAL** — AD10 claims byte-identical `raw/*.csv` against `RAW_FREEZE_MANIFEST.json` ([01A_ADDENDUM_PROTOCOL_FREEZE.yaml:390-393]), but that manifest contains only the five parquet/Sim2 files. AT16 merely counts `raw/sim1b_replicates.csv` lines ([tests/test_a0_dense_addendum_properties.py:762-767]); altered CSV content with unchanged row count passes.

- **MAJOR** — AT3/AT4’s “every addendum cell” claim is false: `IDENTITY_GRID` omits `n_train` and replicates, while `_reports_for_draw` defaults to `n_train=5000`, `replicate=1` ([tests/test_a0_dense_addendum_properties.py:148-170, 261-274]). It covers 24 parameter grids, not 48 realised cells and not their fitted mappings.

- **MAJOR** — AT8’s principal nesting test never samples `n=500`; it samples 5,000 twice and compares a prefix to itself ([tests/test_a0_dense_addendum_properties.py:448-456]). It cannot detect a runner that redraws the small arm. The second test demonstrates RNG behavior, not runner behavior ([458-482]).

- **MAJOR** — AT14 validates `FIN.cell_result`, which the actual 1B runner does not use. Worse, `METRIC_UNDEFINED` rows retain calculated loss metrics after status changes ([scripts/run_sim1b_finite.py:210-236]), contrary to AD9. A copied addendum runner would violate AD9 unless explicitly corrected.

- **MAJOR** — Seed disjointness is true for DGP, train, evaluation, learner, and OOF namespaces: independent enumeration gave original range `1,952,001..995,419,050`, addendum `2,149,762,001..2,813,717,050`, and zero intersections after `+100k/+200k`; OOF `{4211+17r}` vs `{91211+17r}` is disjoint. But AT6 omits fixed stochastic channels: ordered-CatBoost permutation seeds `977..980` ([encoders/supervised.py:99-113]) and hash seed `20260810` ([sim1_core.py:72]). These are intentionally shared constants, so the freeze’s literal “every … derived seed” claim is overbroad.

- **MAJOR** — AD1/AD2/AD5 are only checkable from output as algebraic identities constructed from the same stored quantities: the runner assigns `theoretical_gap = representation_loss` ([scripts/run_sim1b_finite.py:220-227]). It does not persist an independently calculated exact-population identity error. AD7’s OOF use is likewise not auditable from rows unless the new seed manifest records it.

- **MINOR** — AD9 cannot establish that every failed *attempt* has a typed row: the current runner silently `continue`s on DGP/setup exceptions ([scripts/run_sim1b_finite.py:135-152]). AD11’s partner d=3 is protocol-inferred because current result fields do not store `d_active` ([47-55]).

- **MINOR** — Resource arithmetic checks out: frozen M=5/K=4 anchor is `182400` rows, `48` scenarios, `5.9308679` core-hours; split `{500: 2.5244783, 5000: 3.4063897}`. Reported 1.0298 weighted ratio, `6.108` raw hours, `8.551` calibrated hours, and ~0.084 GB disk follow from the CSV inputs. The e2e probe measures substantially the assumed loop, but only three 10-replicate factor points; it supports sizing, not a precise runtime guarantee.

- **MINOR** — Confirmed all frozen manifest files match: 05a, 05b, 05c, 05d, and 12_SIM2_RESULTS.csv all SHA-256 `PASS`. `01_PROTOCOL_FREEZE.yaml` has no “addendum” content. The M=5/K=4 twin is all `SUCCESS`/`IDENTIFIED_EXACT`; collision and occupied-bucket columns are all NULL.

- **MINOR** — The requested full suite initially could not start because the read-only sandbox has no writable temporary directory. With capture/cache disabled, the reviewed preflight module ran: `264 passed in 10.21s`.

- **MINOR** — Confirmed known silent-report defect: [scripts/run_sim1_tables.py:70-85] filters `SUCCESS`, truncates level lists at `[:8]`, then labels `rows=len(g)` with status `EXECUTED`. Search found no other confirmed instance of that same misleading count/truncation class; other slices are explicit CLI limits or intended algorithmic selection.

CRITICAL VETO: 2
Verdict: **veto execution as written.** The frozen originals are intact and resource arithmetic is correct, but the required addendum runner does not exist and AD10 cannot verify the raw CSV immutability it claims. The 264 preflight tests pass, but several validate helpers or tautologies rather than the eventual runner/output.

- **CRITICAL** — `scripts/run_sim1b_dense_addendum.py` is required by freeze D3 ([01A_ADDENDUM_PROTOCOL_FREEZE.yaml:438-440]) but is absent (`dense_runner_exists=0`). AT1–AT16 import/test the old runner or helpers; no test exercises the implementation that would execute A1.

- **CRITICAL** — AD10 claims byte-identical `raw/*.csv` against `RAW_FREEZE_MANIFEST.json` ([01A_ADDENDUM_PROTOCOL_FREEZE.yaml:390-393]), but that manifest contains only the five parquet/Sim2 files. AT16 merely counts `raw/sim1b_replicates.csv` lines ([tests/test_a0_dense_addendum_properties.py:762-767]); altered CSV content with unchanged row count passes.

- **MAJOR** — AT3/AT4’s “every addendum cell” claim is false: `IDENTITY_GRID` omits `n_train` and replicates, while `_reports_for_draw` defaults to `n_train=5000`, `replicate=1` ([tests/test_a0_dense_addendum_properties.py:148-170, 261-274]). It covers 24 parameter grids, not 48 realised cells and not their fitted mappings.

- **MAJOR** — AT8’s principal nesting test never samples `n=500`; it samples 5,000 twice and compares a prefix to itself ([tests/test_a0_dense_addendum_properties.py:448-456]). It cannot detect a runner that redraws the small arm. The second test demonstrates RNG behavior, not runner behavior ([458-482]).

- **MAJOR** — AT14 validates `FIN.cell_result`, which the actual 1B runner does not use. Worse, `METRIC_UNDEFINED` rows retain calculated loss metrics after status changes ([scripts/run_sim1b_finite.py:210-236]), contrary to AD9. A copied addendum runner would violate AD9 unless explicitly corrected.

- **MAJOR** — Seed disjointness is true for DGP, train, evaluation, learner, and OOF namespaces: independent enumeration gave original range `1,952,001..995,419,050`, addendum `2,149,762,001..2,813,717,050`, and zero intersections after `+100k/+200k`; OOF `{4211+17r}` vs `{91211+17r}` is disjoint. But AT6 omits fixed stochastic channels: ordered-CatBoost permutation seeds `977..980` ([encoders/supervised.py:99-113]) and hash seed `20260810` ([sim1_core.py:72]). These are intentionally shared constants, so the freeze’s literal “every … derived seed” claim is overbroad.

- **MAJOR** — AD1/AD2/AD5 are only checkable from output as algebraic identities constructed from the same stored quantities: the runner assigns `theoretical_gap = representation_loss` ([scripts/run_sim1b_finite.py:220-227]). It does not persist an independently calculated exact-population identity error. AD7’s OOF use is likewise not auditable from rows unless the new seed manifest records it.

- **MINOR** — AD9 cannot establish that every failed *attempt* has a typed row: the current runner silently `continue`s on DGP/setup exceptions ([scripts/run_sim1b_finite.py:135-152]). AD11’s partner d=3 is protocol-inferred because current result fields do not store `d_active` ([47-55]).

- **MINOR** — Resource arithmetic checks out: frozen M=5/K=4 anchor is `182400` rows, `48` scenarios, `5.9308679` core-hours; split `{500: 2.5244783, 5000: 3.4063897}`. Reported 1.0298 weighted ratio, `6.108` raw hours, `8.551` calibrated hours, and ~0.084 GB disk follow from the CSV inputs. The e2e probe measures substantially the assumed loop, but only three 10-replicate factor points; it supports sizing, not a precise runtime guarantee.

- **MINOR** — Confirmed all frozen manifest files match: 05a, 05b, 05c, 05d, and 12_SIM2_RESULTS.csv all SHA-256 `PASS`. `01_PROTOCOL_FREEZE.yaml` has no “addendum” content. The M=5/K=4 twin is all `SUCCESS`/`IDENTIFIED_EXACT`; collision and occupied-bucket columns are all NULL.

- **MINOR** — The requested full suite initially could not start because the read-only sandbox has no writable temporary directory. With capture/cache disabled, the reviewed preflight module ran: `264 passed in 10.21s`.

- **MINOR** — Confirmed known silent-report defect: [scripts/run_sim1_tables.py:70-85] filters `SUCCESS`, truncates level lists at `[:8]`, then labels `rows=len(g)` with status `EXECUTED`. Search found no other confirmed instance of that same misleading count/truncation class; other slices are explicit CLI limits or intended algorithmic selection.

CRITICAL VETO: 2

---

## 5. Gemini — design and scientific-scope seat (VERBATIM)

The proposed addendum is a methodologically sound and impressively well-verified extension that directly addresses the standing objection regarding sparse signal. The pre-flight tests are exhaustive and provide strong confidence in the technical implementation. However, the experimental design introduces a critical, unnamed confound, and the statistical analysis plan overstates the effective sample size, which undermines the validity of the planned uncertainty quantification for the primary contrast.

- **CRITICAL:** The total signal strength is not held constant. The linear predictor `g(x)` in `src/ct2i_benchmark/simulations/sim1_core.py` sums `d` main effect terms. As `d` increases from 3 to 5, with `tau` fixed, the variance of `g(x)` increases, creating a stronger signal in the d=5 arm. This is a powerful confound that is NOT disclosed in the protocol, and any observed differences between the arms could be attributed to this change in signal strength rather than the intended contrast of signal density.

- **MAJOR:** The stated effective sample size of n=48 is misleading. The 48 scenarios for the addendum are generated from only 8 unique parameter draws, with factors `delta_eta` and `n_train` varied within each draw. This creates clusters of dependent observations. Treating the 48 scenario-pair differences as independent for uncertainty calculations (e.g., `sd/sqrt(48)`) is statistically invalid and will likely lead to underestimated standard errors and over-confident conclusions. The degrees of freedom are closer to 7 than 47. Evidence is in `01A_ADDENDUM_PROTOCOL_FREEZE.yaml` under `seeds.block_key` and `design.scenario_enumeration_order`, which reveals that the number of distinct blocks is 2 (marginal) * 2 (tau) * 2 (interaction_pairs) = 8.

- **MAJOR:** The interaction saturation confound, while commendably disclosed in `01A_ADDENDUM_PROTOCOL_FREEZE.yaml`, remains a significant limitation. The d=3 arm has 100% interaction saturation while the d=5 arm has 30%. This means the contrast is between a fully interactive sparse signal and a partially interactive dense signal, complicating interpretation. While the freeze is transparent about this, its impact on the conclusions that can be drawn should not be understated.

- **MINOR:** Expectation E1 (`representation loss ... expected to be STRICTLY LARGER at d=5`) may not hold. While moving from pure-noise to signal columns should increase loss for merging encoders, the simultaneous (and undeclared) increase in total signal strength could push posteriors further apart, potentially increasing the information that even a non-injective encoder can preserve, complicating the expected outcome.

CRITICAL VETO: 1

---

## 6. Claude — supplementary design / scientific-scope review (VERBATIM)

*Fresh context, no access to the orchestrator's reasoning. Retained as supplementary;
does not substitute for the Gemini seat, which was filled.*

**VERDICT**

The addendum is competently engineered and unusually honest about several of its own weaknesses — the interaction-saturation confound, the condition-level pairing cost, the NULL diagnostic columns, and the D11 reviewer substitution are all disclosed rather than buried. But it must not execute as written. Two defects are frozen into the protocol and cannot be repaired after the A1 run without breaking the freeze: (1) the pre-registered uncertainty procedure treats 48 scenario pairs as 48 independent units when the seed scheme yields only 8 independent parameter-draw blocks, and when 24 of the 48 pairs are exact duplicates for the headline quantity; (2) the freeze asserts `nothing_else_differs: true` while raising d from 3 to 5 at fixed tau materially increases total signal, so the AC-D difference cannot support the mechanism E1 attributes it to. Separately, the population half of E1 is already answered by frozen Simulation 1A output at this exact cell, at zero cost, and the freeze does not acknowledge it. Neither critical requires a redesign; both require an A0-gate amendment before any cell runs.

**FINDINGS**

1. **CRITICAL — the pre-registered uncertainty scheme is anti-conservative and is frozen as such.** `contrast.uncertainty` fixes "MCSE = sd/sqrt(48), normal 95% CI" and an i.i.d. paired bootstrap over 48 scenario pairs; `seeds.pairing_consequence` insists "the A1 uncertainty calculation must use n = 48 and must say so." Verified against the frozen parquet: the block key excludes `delta_eta` and `n_train`, so `df[(df.M==5)&(df.K==4)].seed.nunique() == 400`, i.e. **8 blocks × 50 replicates, not 2,400** — the 48 scenarios cluster into 8 draw-groups of 6. The freeze itself states between-draw variance is *not* differenced out by condition-level pairing, which is exactly the component that is clustered. On an exact population probe I ran (8 blocks × 50 reps × 3 Δη, d=3 via `dgp_block_seed` and d=5 via the addendum's own formula), the block-clustered SE of the paired hash gap difference is 0.00198 against sd/sqrt(48) = 0.00082 — a 2.4× understatement. It flips a conclusion: hash_column@B0 reads t=+3.3 (significant) naively and t=+1.31 (null) clustered. Compounding this, representation loss is *exactly* invariant to `n_train` for label, onehot, hash_column, hash_shared and homals (verified: `max|rep_loss(n=500) − rep_loss(n=5000)| == 0.0` over 15,600 matched rows in the frozen 1B output), so 24 of the 48 pairs are literal duplicates for that quantity. Also, `sd` across a *fixed, exhaustively enumerated* factorial grid is designed heterogeneity, not Monte Carlo error; calling it MCSE mislabels it and yields a CI that narrows as you add heterogeneous conditions. Required before A1: cluster on the 8 blocks (or bootstrap block-level differences), and state the effective n per quantity.

2. **CRITICAL — an undisclosed confound larger than the disclosed one; `nothing_else_differs: true` is false.** `draw_params` draws one p-centred main-effect vector per active coordinate, so d=3→5 at fixed tau adds two main effects to g(x). Computed over 20 draws per cell at M=5,K=4: Var(eta) rises by 1.10×–1.63× and R_log(X) falls by 0.007–0.025 nats in **every one of the 16 (marginal × tau × nint × Δη) combinations**. The d=5 arm simply has more signal. This matters directly because the hash fiber partition is built on the full K^M=1024 space and is *independent of d* (verified in `exact_full_space_gap` / `hash_codes`; the microbenchmark's own note says "full space = K**M = 1024, independent of d"). For the hash encoders the partition is bit-for-bit identical across arms, so the entire d5−d3 difference is "the same fixed merge destroys more of a *larger-variance* eta" — which is not E1's stated mechanism ("a non-injective encoder can no longer merge only pure-noise columns"). `intentional_differences` names only DIFF1/DIFF2 and `mandatory_reporting` names only the interaction confound. Also under-described: at d=3 the 3 lexicographic pairs are {(0,1),(0,2),(1,2)}; at d=5 they are {(0,1),(0,2),(0,3)} — the interactions concentrate entirely on coordinate 0, the coordinate phi_D merges, and coordinate 4 becomes purely additive. That is a structural change, not just "saturation 100%→30%". Fixable at no compute cost (`risk_x` is recorded, so signal-normalised gaps are computable), but the freeze's disclosure list must be amended now.

3. **MAJOR — Simulation 1A already contains the dense-signal cell; the uniqueness claims are false and E1 is pre-computable.** `05a_SIM1A_REPLICATE_RESULTS.parquet` at M=5, K=4 is d = M = 5 (parent freeze `dgp.active_block.simulation_1a`), 52,800 rows, 100 replicates, exact, with hash_column, hash_shared × 3 widths, count_pop, label, onehot. So `purpose.why_M5_K4` ("the only 1B configuration where the whole arm is an exact population computation") and `exactness.statement_for_the_manuscript` overstate: 1A is exact at this same cell. Joining 1A (d=5) to 1B (d=3) at nint=0 on (marginal, tau, Δη, encoder, B) already answers E1's population half — 24/24 conditions positive for hash_shared (mean +0.0136), positive for hash_column at B0/B1, and **reversed in 24/24 for hash_column at B2** (mean −0.0025). E1's text hedges to "hash_column at the narrow widths", which is precisely the carve-out that the already-frozen data requires. The parent freeze set the standard here itself (`multiplicity.H6_direction_disclosure`, a pilot direction disclosed before the run). The addendum should do the same, state what it adds beyond 1A (the finite-sample layer, the fitted supervised encoders, the nint=3 stratum, E3), and stop billing the population half as new.

4. **MAJOR — three of the 13 configurations are degenerate.** In the frozen 1B output at M=5, K=4, hash_shared representation loss is *identical* across B0/B1/B2 (`max|B0−B1| == max|B0−B2| == 0.0`); the shared-value token space is 4 values, so B ∈ {10,20,40} never changes the partition. Reproduced in 1A at d=5. So the "bucket-width sweep" carries zero information for hash_shared, `exactness`'s "collision counts and occupied buckets are exact and predictable at B ∈ {10,20,40}" is vacuous for that encoder, and the AC-D family entered into BH FDR contains three exact duplicate tests, which triple-counts one piece of evidence.

5. **MAJOR — E1's count clause is under-specified and largely untestable.** The freeze records "1024 fibers zipf / 768 uniform (measured at A0)" as if it were a property. I measured it over 10 addendum-seeded draws: uniform/n=500 gives {1024, 1024, 576, 1024, 576, 576, 768, 768, 768, 1024}; uniform/n=5000 gives 1024 in 9 of 10; zipf gives 1024 in all 20. The fitted count encoder's merge is a random sampling-tie event, replicate- *and* n_train-dependent. E1 is therefore testable on count only in the uniform × n_train=500 stratum (12 of 48 conditions), and even there the estimand is a mixture over whether ties occurred. The freeze says only "report per marginal".

6. **MAJOR — E1 has no decision rule.** It compounds three encoder clauses (hash_shared, hash_column-at-narrow-widths, count-where-counts-tie) with no test statistic, no stratum-combination rule, and no statement of what counts as confirmation versus partial confirmation. As written it is not falsifiable as a single proposition, only as three loose ones. E3 is better: it states a direction and an interaction, both testable. E4 is not an expectation at all — it is a reporting policy ("a null is publishable"), and cannot be falsified by any run; it belongs under reporting rules, not under `expectations`. E2 is correctly identified as a gate and routed to AD3.

7. **MAJOR — the two design-authority documents do not exist in the repo.** `meta.design_authority` (CT2I_STUDENT_SIMULATION_COMPLETION_PLAN.md §12) and `meta.execution_authority` (CT2I_STUDENT_SIMULATION_COMPLETION_EXECUTION_PROMPT.md, Phase A0) are referenced nowhere else in the tree (`find` + `grep -rl` return only the freeze itself). Every appeal to "execution-prompt step 3" — which is the sole justification for D2, the decision that costs the design its replicate-level pairing — and to "execution prompt A0 step 8" for the 20 core-hour cap is unverifiable here.

8. **MINOR — the seed disjointness *argument* is false as stated, though the conclusion holds.** `seeds.disjointness.structural_argument` says "Every addendum seed is at least 2,000,000,001". The derived OOF seed is `91_211 + 17·replicate` ∈ [91,228, 92,061], far below that bound. It is in fact disjoint (manifest `seed_start` min = 1,952,001; original OOF is 4211+17r), and AT6 checks it by a separate narrower assertion, but the stated structural argument does not cover the seed it claims to.

9. **MINOR — the parent CPU ceiling is never mentioned.** Parent `resources.cpu_core_hours_max: 80`; `18_RUNTIME_AND_RESOURCE_REPORT.csv` records TOTAL 88.11 core-hours, "OVER". The addendum inherits only `parallel_workers_max` from parent resources and substitutes a 20 core-hour cap from an unverifiable source, taking the package to ~96.7 against a frozen 80. Probably intentional; it should be said.

10. **MINOR — E3's stated mechanism is wrong.** "the effective hypothesis class is larger (K^5 = 1024 against K^3 = 64)". The learner sees all M=5 columns at both d, encoded to the same width (M·K = 20 for one-hot); the hypothesis class is unchanged. What grows is the target's complexity, hence the estimation problem. Note also that E3's *second* clause (n=500 vs n=5000) is a within-block contrast — `n_train` is excluded from the block key, so both arms share one parameter draw — and is therefore much better powered than the d contrast. Power for E3 looks adequate: scenario-mean SEM of learner_shortfall in the d=3 arm is 0.0002–0.0043 against shortfall levels of 0.007–0.13.

11. **MINOR — acceptance-criteria hygiene.** AD3 cannot fail: label/onehot are deterministic injections, AT5 already verified it exhaustively over all 1024 states with the same code path, and unseen-level collapse is impossible at K=4, n≥500. AD8 says "Every addendum cell replays bitwise" but gates on a spot-check of ~9 of 2,400 — the description should match the gate. AD1/AD2/AD5 are "pre-verified" on `IDENTITY_GRID`, which is 24 draws at replicate 1 and **n_train=5000 only** (`_reports_for_draw` default); the n_train=500 fitted-encoder regime is never exercised at A0. AD4 is deterministic given K**M ≤ ENUM_CAP (verified: `hash_gap_identified(M, K)` reads M and K only) — a fine regression gate, but "falsifiable prediction" oversells it. AD11's exclusion of collision_count/occupied_buckets is correct and well-evidenced: both are NULL for all 1,094,400 rows (verified).

12. **MINOR — resource evidence is sound but one figure does not reconcile.** The anchor 5.9309 core-hours reproduces exactly (`cpu_seconds` is written as per-cell CPU ÷ row count in `run_sim1b_finite.py:249`, so the row-sum is the true total, and it matches the 57.97 in `18_RUNTIME_AND_RESOURCE_REPORT.csv` for the full arm). `ratio_d5_over_d3_n5000 = 1.0335` and the weighted 1.0298 both reproduce from the microbenchmark rows. But `ratio_d5_over_d3_n500 = 1.0249` does not: the CSV's own columns give 53.52/52.156 = 1.0261 (cpu_s) or 54.359/53.404 = 1.0179 (elapsed). Immaterial to the 8.55 vs 20 verdict — headroom is ample either way, and the 1.4× calibration factor against four disclosed prior underestimates is the right instinct.

13. **MINOR — no `d_active` column exists in the frozen schema.** Neither 05a nor 05b carries one. The addendum lands in a separate file (05e), so the arms are separable by path, but `08A_..._FIGURE_DATA.csv` merges both and the freeze does not name the discriminating column.

**WHAT THE CONTRAST CAN AND CANNOT SUPPORT.** It *can* support: the encoders indicted at d=3 are still indicted when every coordinate carries signal (an absolute statement about the d=5 arm, which needs no d=3 twin at all and is the actual answer to the standing objection); and the learner-shortfall / n_train interaction of E3, which is properly within-draw paired. It *cannot* support: that the d5−d3 *difference* is a dimensionality or noise-column effect (confounded with total signal and with interaction structure, finding 2); any population claim that 1A does not already provide more cheaply and with 100 replicates (finding 3); or any bucket-width claim for hash_shared (finding 4).

CRITICAL VETO: 2

---

## 7. Claude — supplementary implementation / verification review (VERBATIM)

*Fresh context, no access to the orchestrator's reasoning. Retained as supplementary;
does not substitute for the Codex seat, which was filled.*

**VERDICT.** The preflight is unusually good by the standards of this class of work: the seed arithmetic checks out under independent re-derivation, the five frozen raw artefacts are byte-identical, the resource projection reproduces from a genuinely measured anchor, and the design correctly refuses to gate on `collision_count`/`occupied_buckets` (which I confirm are 100% NULL). But it is a preflight of a *design document and a library*, not of the code that will run: the A1 runner does not exist, the seed rule is reimplemented three times (freeze YAML, test module, microbenchmark) with no shared source, and several AT criteria — notably AT15, and AD1/AD2 downstream — are algebraically incapable of failing. One design defect blocks signature: the freeze claims "exactly one factor" changes and discloses exactly one confound, and I measure a second, undisclosed one of the same kind that points in the same direction as E1's prediction. It is a documentation fix, free now and impossible after A1 begins.

**FINDINGS**

1. **CRITICAL — undisclosed second confound: effective signal strength moves with d.** `eta_raw` (`src/ct2i_benchmark/simulations/sim1_core.py:156-162`) is `logistic(tau * sum of d main effects + interactions)` with **no normalisation by d**, so `g` has ~5/3 the variance at d=5. `impose_delta_eta` (`sim1_core.py:224`) then maps the *fiber mean* `m` affinely, which preserves that extra spread. Measured over 10 draws per block: `sd(eta)` d5/d3 = 1.105 / 1.065 / 1.090 / 1.040 and `R_Bayes` falls (0.6350→0.6214, 0.5766→0.5520, …). Representation loss scales with within-fiber eta variance, so a merging encoder will show a larger gap at d=5 **partly for this reason alone**. E1 predicts exactly that increase and attributes it to "every coordinate carries signal". `01A_ADDENDUM_PROTOCOL_FREEZE.yaml:88-90` ("Exactly one factor … Every other factor … held at its frozen value") and the `disclosed_confound_interaction_saturation` block are therefore incomplete. Fix before freezing: add this to the confound block and to `mandatory_reporting`, or normalise `tau` by `sqrt(d)` as an `intentional_difference`.

2. **MAJOR — the disjointness claim is false as written; two derived-seed channels are unenumerated.** `derived_seeds` (`01A…yaml:200-204`) lists train/eval/oof/learner only. Missing: (a) `perm_seed = 977` for `ordered_catboost_sim`'s 4 permutations (`src/ct2i_benchmark/encoders/supervised.py:99`, used at `sim1_finite.py:110`) — a constant, so the addendum uses seeds 977-980 *identical* to the completed run; (b) `bootstrap seed 90210` — the addendum reuses it (`01A…yaml:269`) and it is the completed run's own bootstrap seed (`01_PROTOCOL_FREEZE.yaml:514`). AT6 tests neither. Sharing them is *correct*, but "every addendum seed … disjoint from every seed realised in the completed run, including derived seeds" is then simply untrue and AD7 is unfalsifiable against these channels. State them as intentionally shared constants alongside `hash_seed`.

3. **MAJOR — AT6 validates the manifest, but the manifest is not "every realised seed".** `03_SEED_MANIFEST.csv` covers components 1A/1B/1C_finite/1C_exact only; `12_SIM2_RESULTS.csv` carries seeds 1001-9900 that appear nowhere in it, contradicting `01_PROTOCOL_FREEZE.yaml:518`. Disjointness still holds (addendum DGP ≥ 2,149,762,001; addendum OOF 91,228-92,061 vs sim2 max 9,900), but the test's evidence base is incomplete by luck, not by construction.

4. **MAJOR — the preflight verifies a test-local reimplementation, not the runner.** `scripts/run_sim1b_dense_addendum.py` (mandated by D3) does not exist. `SEED_BASE_1BD`/`addendum_seed` are duplicated in `tests/test_a0_dense_addendum_properties.py:66-96` and again in `scripts/s0a_addendum_microbenchmark.py:67-73`. No AT test imports the addendum runner, so AT6/AT7/AT8/AT13 constrain nothing the A1 run will execute. AT8's own docstring ("asserted so the addendum runner cannot regress it", line 466) is false today. Fix: have the A1 runner own the seed function and have the tests import it.

5. **MAJOR — AT15 / AD5 cannot fail.** `FIN.decompose` (`sim1_finite.py:391-399`) sets `total_excess_risk = r_l - r_x` and `rep + short = (r_z-r_x)+(r_l-r_z)`, which telescopes exactly, *and* raises `AssertionError` internally if the residual exceeds 1e-9 (line 393). The test then re-asserts the same bound (`tests/…:717-719`). It is the same guard twice on an algebraic identity.

6. **MAJOR — AD1/AD2 are self-checks, and the preflight declines the available independent implementation.** `exact_gap_report` (`sim1_core.py:309-329`) computes `gap = rl_z - rl_x` and `theoretical_gap = cmi` from the same `fiber_posteriors` aggregation — a circularity the repo itself documents at `sim1_core.py:332-346` and mitigates with `reference_gap_report`. `grep -c reference_gap_report tests/test_a0_dense_addendum_properties.py` → **0**; only the pre-existing `tests/test_s0_sim1_properties.py:132` uses it. Confirmed empirically on the frozen partner arm: max |(risk_z − risk_x) − theoretical_gap| = **1.28e-16** against a 1e-10 tolerance. AD1/AD2 will pass whatever the fiber algebra does.

7. **MAJOR — E1's "measured at A0" fiber claim is a single-draw anecdote and is wrong as stated.** `01A…yaml:322-327` asserts the fitted count encoder is "injective … under the Zipf marginal (1024 fibers)" and "merges under the uniform marginal (768)". Sweeping 8 blocks × {500,5000} × 3 replicates I get uniform ∈ {576, 768, 1024} and **zipf ∈ {768, 1024}** — the marginal does not determine it. The per-marginal reporting rule E1 prescribes rests on a false premise, and after A1 begins it cannot be amended.

8. **MAJOR — bug-class instance: silent replicate drop with no typed row.** `scripts/run_sim1b_finite.py:151-152` — `except Exception: continue` around the DGP draw / sampling block writes **zero** rows for that replicate. A failed cell then has no typed status at all, which AD9 ("every failed cell carries a typed status") cannot detect; only AD6's aggregate count would. If the A1 runner is derived from this file (D3 says a new file, mirroring it), it inherits the defect, directly against AD6's "`rows` means EXECUTED rows, *including any typed-absence row*".

9. **MAJOR — bug-class instances: counts that do not mean their label.** Beyond the known `run_sim1_tables.py:74` (`sorted(...)[:8]`) and line 85 (`rows=len(g)` from a SUCCESS-filtered frame labelled status EXECUTED): `run_sim1_tables.py:84` `replicate_count=int(g.replicate.max())` is a max index, not a count, and is SUCCESS-filtered; `run_sim1_tables.py:83` `scenarios=g.scenario_id.nunique()` silently omits any wholly-failed scenario; `run_sim1_tables.py:249` `.dropna()` on the H6 CV difference silently shrinks the paired n with no record; `run_sim1_summarize.py:248` `n_scenarios` has the same SUCCESS-filter issue. Also `run_sim1b_finite.py:160` hardcodes `exact_or_mc="mc"` for **all** 1B rows — I confirm all 182,400 M=5,K=4 rows carry `exact_or_mc == "mc"` while `theoretical_gap_status == "IDENTIFIED_EXACT"`, which contradicts the addendum's headline "only 1B configuration that is an exact population computation" for anyone reading that column.

10. **MINOR — tautological assertions.** `tests/…:690` `assert row["roc_auc"] != 0.5 and row["representation_loss"] != 0.0` runs *after* asserting every `METRIC_FIELDS` entry (which includes both, `sim1_finite.py:408-410`) is `None` — `None != 0.5` is always true. `tests/…:596` `assert n_tokens - len(buckets) == n_tokens - occupied` is implied by line 595's `len(buckets) == occupied`.

11. **MINOR — coverage narrower than the "structurally complete grid" label.** `IDENTITY_GRID` (`tests/…:161`) is 24 tuples over (marginal, tau, n_int, delta); `_reports_for_draw` defaults `n_train=5000, replicate=1`, so AT3/AT4/AT5/AT11 never see `n_train=500` — half the frozen grid — for the sample-dependent encoders (count/target/woe/homals/ordered_catboost). `AT12`'s `test_other_rows_do_influence_the_code` (`tests/…:640`) flips *all* labels including the row's own, and silently omits `ordered_catboost_sim` from the parametrisation.

12. **MINOR — three of five ratios in `S0A_ADDENDUM_RESOURCE_ESTIMATE.csv` do not reproduce from the rows they cite.** From `S0A_ADDENDUM_MICROBENCHMARK_ROWS.csv:81-86`: n500 = 53.520/52.156 = **1.026152** (claimed 1.0249); min = **1.016900** (claimed 1.0164); max = **1.050005** (claimed 1.0505). Only `ratio_d5_over_d3_n5000` = 1.033453 → 1.0335 reproduces. Impact ≈ 0.1% on the projection. Also `append_rows` opens `OUT` in `"a"` mode (`s0a_addendum_microbenchmark.py:88`), so a re-run silently appends duplicates.

13. **MINOR — the calibration band is not an uncertainty band.** `[8.439, 8.723]` propagates only the ±1.7% ratio spread; the 1.4 calibration (itself a 40% correction, and here applied on top of a *directly measured* anchor rather than a proxy composition) contributes no width. Everything else reconciles exactly, which I verified independently: anchor `df[(M==5)&(K==4)].cpu_seconds.sum()/3600` = **5.930868**, n_train split 2.524478/3.406390, weighted ratio (2.524·1.0249 + 3.406·1.0335)/5.930 = 1.02984, raw 5.9309·1.0298 = 6.1076, calibrated ×1.4 = 8.5512, headroom 11.449, wall 8.551/8 = 1.069, disk 182400·(294.7+54.8·3) B = 83.8 MB = 0.084 GB. `cpu_seconds` is `cpu/len(rows)` per worker (`run_sim1b_finite.py:249`), so summing over rows does **not** double-count. The extrapolation method is sound; the probe (`probe_scenario`) runs the real scenario loop with `d_active` as a parameter, so it measures what the projection assumes.

**AD1-AD12 checkability.** All twelve are evaluable from what the 1B schema writes, with three caveats. AD1/AD2 have no persisted `identity_error_*` column and must be computed as |(risk_z − risk_x) − theoretical_gap| — feasible (all 182,400 partner rows carry a non-null `theoretical_gap`) but vacuous per finding 6. AD9 is not falsifiable against the silent-skip path of finding 8. AD11 has no `d_active` column in `05b` (confirmed absent), so "d=3 partner" is established by file provenance only, not by a key in the data — add `d_active` to the addendum schema.

**Preflight side-effects: clean.** All five `RAW_FREEZE_MANIFEST.json` entries re-hash identically (05a/05b/05c/05d parquet + `12_SIM2_RESULTS.csv`). `grep -ic addendum 01_PROTOCOL_FREEZE.yaml` → **0**. `git status --porcelain` shows seven modified tracked files, all with mtime `Aug 19 11:31` (Phase R), versus every A0 artefact at 14:29-14:43 — A0 added only. Full suite: **896 passed** (264 addendum + 632 pre-existing), matching the freeze's claim.

CRITICAL VETO: 1
