# S0B — ADVISOR RULING IMPLEMENTATION REPORT (Phase A0.1)

What was actually built for each binding ruling D13–D18, in which file, and
which test holds it in place. Written by the A0.1 **reconciliation pass**, after
four agents worked in parallel on the amendment, the runner, the test migration
and the reference harness.

    ruling source   ADVISOR_RULING_20260821 (transcribed verbatim into
                    01B_ADDENDUM_ADVISOR_RULINGS.yaml `advisor_ruling_verbatim`)
    interpreter     /Users/Eric/.pyenv/versions/3.11.9/bin/python3   (never conda `t2i`)
    invocation      PYTHONPATH=src python -m pytest -q
    date            2026-08-24, refreshed 2026-08-25 (consistency pass)

    FULL ADDENDUM CELLS RUN            0
    ADDENDUM OUTPUT WRITTEN OR FROZEN  0 bytes (no file matching *dense_addendum* under raw/)
    REAL-DATA MODELS RUN               0
    GPU HOURS USED                     0
    FULL TEST SUITE                    1,086 passed / 1,086 collected  (2026-08-25)
                                       (1,027 / 1,027 when this report was first
                                       written; +59 from tests/test_a0_2_defect_closure.py,
                                       which did not then exist, and one added
                                       reconciliation test. 0 regressions.)

**Read §2 before §1.** §1 says what is implemented; §2 says what is *not*, and
several D13–D18 clauses are A1-time claims that A0.1 can only prepare.

> **Numbering notice (2026-08-25).** The open items in §3 were originally
> numbered Q1–Q8 and **collided** with `01B_ADDENDUM_ADVISOR_RULINGS.yaml`'s own
> Q1–Q7: two different "Q6". They are renumbered **IR-1 … IR-8** here, and each
> carries its mapping into 01B.
> **`01B advisor_confirmation_requested` is the single authority for advisor
> question numbering** (now Q1–Q8); no other document defines a Qn.

---

## 1. Ruling by ruling

### D13 — block-clustered inference as ruled (8 blocks, 7 df) — **PREMISE SINCE REFUTED**

> **Status correction (2026-08-25).** This heading originally asserted the
> 8-block scheme as settled. It is not. D13's factual premise — that the DGP
> parameters are drawn once per block — was **refuted by measurement** on
> 2026-08-24: they are drawn afresh per replicate, giving **400 draws per arm**,
> not 8. `01B rulings.D13.status` is
> `PREMISE_REFUTED_ADVISOR_RULING_REQUIRED` and the question is **01B Q6**
> (`severity: BLOCKS_A1_INFERENCE`). Provenance:
> `S0B_D13_PREMISE_INVESTIGATION.md`. What is described below is what was
> BUILT against the ruling as written; the data structure it delivers (a block
> label and a draw-varying seed on every row) supports either inferential unit,
> so nothing below needs rebuilding whichever way Q6 is settled.

| | |
|---|---|
| **Frozen in** | `01B rulings.D13` — `n_blocks: 8`, `degrees_of_freedom: 7`, the block key, block-resampling bootstrap, the ban on treating 48 scenarios or 2,400 replicates as independent |
| **Implemented in** | `scripts/run_sim1b_dense_addendum.py` — `addendum_block()` (the block key **excludes** `delta_eta` and `n_train`, which is what makes the two arms of every within-DGP contrast share one parameter draw), `addendum_blocks()` (returns exactly 8), and the `block_key` column stamped on **every** emitted row by `_base_row_fields` |
| **Enforced by** | `test_a1_runner_smoke.py::TestRunnerOwnsTheSeedRule::test_block_excludes_the_contrasted_factors` (8 distinct blocks); `…::TestRunnerEndToEndProbe::test_every_row_carries_the_block_key_for_D13`; `test_a0_dense_addendum_properties.py::test_parameter_draw_identical_across_delta_eta`, `::test_seed_is_invariant_to_delta_eta_and_n_train` |
| **NOT implemented at A0.1** | **The estimator itself.** No block-clustered t interval, no block-resampling bootstrap, and no "effective number of blocks and duplicated conditions" statement exists in code. D13 is an *analysis-time* ruling; A0.1 delivers only the data structure that makes it computable (a block label on every row and a block key that is invariant to the contrasted factors). Everything downstream of that is A1. |

### D14 — dense-signal stress test; raw AND signal-normalized gaps

| | |
|---|---|
| **Frozen in** | `01B rulings.D14` — Option 1 with narrowed interpretation, the two normalized estimands, the `NOT_IDENTIFIED` rule, the interaction-pair split, the retained confounds, the framing tokens |
| **Implemented in** | `run_sim1b_dense_addendum.py` — `population_signal_scales()` computes `H(Y)`, `R_log*(X)`, `Var{eta(X)}` and `R_Brier*(X)` exactly; `relative_gaps()` forms `relative_log_gap = (R_log*(Z) − R_log*(X)) / (H(Y) − R_log*(X))` and `relative_brier_gap = (R_Brier*(Z) − R_Brier*(X)) / Var{eta(X)}`; below the frozen tolerance the row records the token `NOT_IDENTIFIED` **and a NULL value, never 0**. Raw absolute gaps are persisted alongside (`pop_gap_logloss`, `pop_gap_brier`), so both quantities the advisor asked for are on every row. `relative_gap_tolerance()` reads `01B rulings.D14.denominator_tolerance.frozen_value` at run time and **refuses it unless the parent freeze's tolerance table already contains that number**, so a tolerance cannot be invented in either file. |
| **Enforced by** | `test_a1_runner_smoke.py::TestSignalNormalisedEstimands` — `test_var_eta_identity` (the load-bearing `Var{eta} = Var(Y) − R_Brier*(X)` identity, over the whole 24-point grid), `test_log_denominator_is_the_mutual_information`, `test_relative_gaps_are_the_ruled_ratios`, `test_degenerate_denominator_is_NOT_IDENTIFIED_never_zero`, `test_tolerance_comes_from_the_frozen_table`; `…::TestRunnerEndToEndProbe::test_relative_gaps_are_persisted_and_identified` |
| **NOT implemented at A0.1** | The **interpretation** clauses are prose obligations on the A1 write-up, not code: reporting `interaction_pairs = 0` and `= 3` separately, disclosing the total-signal-strength / interaction-saturation / interaction-placement confounds, and never calling a d=5 − d=3 result a pure dimensionality effect. `01B AD15 item 11` makes the forbidden-label check a mechanical gate, but **no lint over the A1 text outputs has been written**. It is an A1 deliverable and is listed as open in §3. |
| **Token collision (backlog R5), verified** | D14's `NOT_IDENTIFIED` (a degenerate normalizing denominator) and AD4's `NOT_IDENTIFIED` (an unidentified theoretical gap) are the same token with different meanings. The runner keeps them in **separate columns**: `relative_log_gap_status` / `relative_brier_gap_status` for D14, `theoretical_gap_status` for AD4. Confirmed still separate in `FIELDS` and in `addendum_row`. The A1 acceptance report must read `theoretical_gap_status` for AD4; reading the relative-gap status columns instead would be a wrong verdict. |

### D15 — SHA-256 manifest coverage for every protected and new raw output

| | |
|---|---|
| **Frozen in** | `01B rulings.D15` |
| **Implemented in** | `simulation-results-ct2i/RAW_FREEZE_MANIFEST_ADDENDUM.json` (a superset of the original manifest: 5 top-level raw CSVs + 5 carried-forward frozen result outputs + 3 declared pending A1 addendum outputs) and `scripts/verify_raw_freeze_manifest_addendum.py`, which re-hashes every entry and additionally checks that every entry of the OLD manifest is carried forward with a matching hash |
| **Verification run (this pass, verbatim)** | `RAW FREEZE MANIFEST ADDENDUM: 10/10 MATCH` — with `superset check: 5/5 old-manifest entries carried forward with matching hash -> PASS`, `0 mismatched, 0 missing, 0 unlisted, self-entries: 0` |
| **Enforced by** | The standalone verifier script only. `test_a0_dense_addendum_properties.py::TestOriginalRawUnchanged::test_every_frozen_raw_output_matches_its_recorded_sha256` covers the **original 5-entry** `RAW_FREEZE_MANIFEST.json`, not the addendum manifest. **No pytest test executes the addendum verifier**, so a broken addendum manifest is caught only when someone runs the script. Listed as open in §3. |
| **Disclosed coverage gap (backlog R7)** | `raw/sim1b_replicates_parts/` — 288 files, ~260 MB — is **excluded** from the addendum manifest on a literal reading of "raw/*.csv" (non-recursive). This is defensible because the downstream frozen parquet built from those parts **is** hashed, so a change to any part that reached the results would be caught. It is recorded in the manifest's `excluded_from_coverage` field, and it is recorded here so it is not visible only inside a JSON file. The advisor should be told this exclusion exists rather than discovering it. |

### D16 — E1 split into E1a/E1b/E1c with frozen decision rules

| | |
|---|---|
| **Frozen in** | `01B rulings.D16` — the three clauses, their primary statistics, and the CONFIRMED / PARTIALLY SUPPORTED / NOT SUPPORTED definitions, with the advisor's instruction that these are outcome summaries and not validity gates, and that null or reversed findings are retained |
| **Implemented in** | `run_sim1b_dense_addendum.py` records the **inputs** the clauses need: `fiber_count` on every row (E1c cannot identify its "both mappings non-injective, `fiber_count < 1024`" stratum without it), `bucket_width` / `width_label` distinguishing B0/B1/B2 (E1a collapses them, E1b averages B0 and B1), and the normalized + raw contrasts for both risk measures |
| **Enforced by** | `test_a1_runner_smoke.py::TestRunnerEndToEndProbe::test_fiber_and_hash_diagnostics_are_recorded` (fiber_count present and correct: 1024 for `label`, 56 for `hash_shared`); `test_a0_dense_addendum_properties.py` bucket-width and fiber-count classes |
| **NOT implemented at A0.1** | **No E1a/E1b/E1c analysis code exists, and no test enforces a decision rule.** BH adjustment, the q<0.05 threshold, the direction checks and the outcome classification are all A1-time analysis. A0.1's contribution to D16 is exactly two things: the clauses are frozen in writing before the data exist, and the runner records the columns the clauses reference. |
| **Extensions to the advisor's own text** | Three decisions were frozen that go beyond what the advisor wrote, and all three are now promoted into `01B advisor_confirmation_requested` (Q2, Q3, Q4) rather than buried: `effective_blocks_min = 4` for E1c's low-power fallback (he wrote "too few independent blocks" with no number); a **fourth** outcome class `INCONCLUSIVE_REPORTED_IN_FULL` added to his three; and "materially directionally inconsistent" quantified as opposite signs with both \|estimates\| > 1e-6. Each keeps its frozen value as the operative default; each is waiting on an answer to be *legitimate*, not to proceed. |

### D17 — independent reference check on ≥ 624 cells

| | |
|---|---|
| **Frozen in** | `01B rulings.D17`, **as amended by AMENDMENT-1 on 2026-08-24** |
| **Implemented in** | `scripts/s0b_reference_gap_check.py` (the harness, run against the frozen d=3 twin) and `run_sim1b_dense_addendum.py` (the six mandated columns written on every reference cell, from `sim1_core.reference_gap_report` executed on the cell — never derived from a production column, per `persisted_columns.forbidden`) |
| **Sampling rule** | `reference_replicate(scenario) = int(scenario_id[-4:])`, i.e. S1BD-0001 → replicate 1 … S1BD-0048 → replicate 48. 48 scenarios × 13 encoder configurations × 1 replicate = **624 cells**, the advisor's stated minimum. The runner **reads this expression out of 01B at run time** (see §2.1, reconciliation R1). |
| **Enforced by** | `tests/test_a0_1_reconciliation.py::TestD17ReferenceSampleFollows01B` (10 tests); `test_a1_runner_smoke.py::TestWorkListEnumeration::test_reference_sample_meets_the_D17_minimum`, `::test_frozen_reference_replicate_rule`; `…::TestRunnerEndToEndProbe::test_reference_columns_present_on_the_frozen_reference_replicate` |
| **Harness result (this pass)** | `D17 REFERENCE CHECK arm=d3_frozen defect=none cells=624 tol=1.0e-10 max_log_identity_error=5.447e-15 max_brier_identity_error=2.050e-15 max_prod_ref_abs_diff=5.551e-15 cells_over_tolerance=0 fiber_count_mismatches=0 RESULT=PASS`. The harness's own 624-cell sample was **re-verified against 01B's rule and matches it cell for cell**; the two independent implementations of that rule (harness and runner) were compared over all 96 scenario ids of both namespaces with zero disagreements. |
| **This CORRECTS the advisor's D17 as written** | The two identity-error columns the advisor named **do not gate**. Measured by injected defect: `ebar_bias` leaves `identity_error` at 5.4e-15 (unchanged) while \|production − reference\| moves to 5.5e-7; `mass_dropout` leaves it unchanged while \|prod − ref\| moves to 1.08e-2. `reference_gap_report` defines `ebar_f` as its own mass-weighted within-fiber mean, so the identity telescopes exactly *inside* that implementation and is blind to a production path that is wrong by 1e-2. Worse, both paths consume the **same** `fid`, so a fiber-*construction* defect (`fiber_merge`) evades \|prod − ref\| too (6.2e-15, does not fire). AMENDMENT-1 therefore gates AD1/AD2 on **G1** (\|production − reference\|) **AND G2** (recomputed vs stored `fiber_count`; 0/624 match under `fiber_merge`), and reclassifies the advisor's two named columns as **persisted and reported but DESCRIPTIVE, not gating**. They are retained because he named them. This is a correction to his ruling and is flagged as `Q5` in `01B advisor_confirmation_requested`. **Superseded in part on 2026-08-24: AMENDMENT-4 added two further co-equal gates — G3 (stored representation loss, MCSE-scaled) and G4 (canonical partition fingerprint, exact). D17 now gates on G1 ∧ G2 ∧ G3 ∧ G4, and that further correction is `01B Q7`.** |
| **Phase-ordering tension (Q1, unresolved)** | Production values for **addendum** cells cannot exist until A1, yet the advisor's A0.1 console block lists `D17 INDEPENDENT REFERENCE CHECK` as an A0.1 line item. The adopted reading is that A0.1 builds and validates the harness on the existing frozen d=3 arm (done, PASS above) and the ≥624 **addendum**-cell check becomes an A1 gate inside AD15. G2 in particular is only evaluable against production rows on disk. This is an adopted reading, not a settled decision. |

### D18 — the real A1 runner gate (encoded as AD15)

> **Count notice (2026-08-25).** `01B D18.title`, `AD15.description` and
> `AD15.gate_semantics` all say **ten** items while `AD15.items:` runs **1–11**.
> Item 11 — the D14 forbidden-label check — is the one that is NOT IMPLEMENTED.
> The discrepancy is in 01B's prose, not in the item list; it is recorded in
> `S0B_FINAL_GATE_REPORT.md` §6.5 and is not silently reconciled here.

| item | implemented in | enforced by |
|---|---|---|
| 1 — the runner exists and produces every addendum row | `scripts/run_sim1b_dense_addendum.py` (NEW file; `run_sim1b_finite.py` and `sim1_core.py` stay byte-identical and are *imported*, not copied) | `test_a0_dense_addendum_properties.py::test_the_imported_runner_is_the_repository_file`; `test_a1_runner_smoke.py::TestProtocolFileWiring` |
| 2 — the runner is the single source of truth for the seed rule | `addendum_block/_seed/_oof_seed/_train_seed/_eval_seed/_scenarios` defined once, in the runner | `test_a1_runner_smoke.py::TestRunnerOwnsTheSeedRule` (recomputes the 01A formula text independently) |
| 3 — tests import that rule and do not redefine it | the property-test module's private copy (16 constants + 4 functions) was deleted and is now imported | `test_a0_dense_addendum_properties.py::TestTheSeedRuleIsNotRedefinedHere` — an **AST scan of the test module's own source**, so a reintroduced copy is a failure, plus a no-fallback-import check. **Partially closed:** see §2.2 (R9) for the microbenchmark's surviving copy. |
| 4 — AT1–AT16 rerun against the real runner, all pass | migration of `tests/test_a0_dense_addendum_properties.py` | that module: 395 tests pass across the three addendum test modules |
| 5 — both n_train = 500 and 5000 covered | `scenario_worker` draws `N_TRAIN_NEST_MAX = 5000` once and **slices** the first 500 rows | `test_a1_runner_smoke.py::TestRunnerEndToEndProbe::test_both_n_train_levels_execute_a_real_code_path`, `::test_n500_is_the_prefix_of_the_n5000_draw_as_the_runner_slices_it`; `test_a0_dense_addendum_properties.py::test_the_runner_draws_the_nest_max_and_never_redraws_at_500` (re-drawing at n=500 agrees on X but **not** on y — measured, which is why slicing is load-bearing) |
| 6 — a typed row for every attempted cell; executed ≠ successful | `row_executed` / `row_success` columns, `summarise()`, `print_summary()` | `test_a1_runner_smoke.py::TestTypedRowDiscipline::test_executed_and_successful_are_separately_countable`; `test_a0_dense_addendum_properties.py::test_executed_and_successful_are_distinguishable_in_the_schema` |
| 7 — no silent `continue` on setup exceptions | `_typed_failure_rows()` materialises the absent cells with the exception type and message | `test_a1_runner_smoke.py::TestTypedRowDiscipline::test_setup_exception_emits_typed_rows_not_a_silent_continue`; `test_a0_dense_addendum_properties.py::test_a_failed_replicate_does_not_delete_itself`; **and now** `test_a0_1_reconciliation.py::TestTypedFailureRowsHonourTheLearnerFilter` (§2.3) |
| 8 — NULL metrics on every non-SUCCESS row | `addendum_row()` routes through `sim1_finite.cell_result` and **raises** if a failure row tries to smuggle a metric | `test_a1_runner_smoke.py::TestTypedRowDiscipline::test_failure_row_nulls_every_metric_column` (5 statuses × every metric column); `test_a0_dense_addendum_properties.py::test_non_success_rows_carry_null_metrics_never_zero_or_a_sentinel` |
| 9 — correct `exact_or_mc` labels | three explicit labels instead of one ambiguous one: `population_quantity_kind` (exact), `sample_quantity_kind` (mc), `exact_or_mc` kept under the 05b name for schema continuity | `test_a1_runner_smoke.py::TestRunnerEndToEndProbe::test_exact_or_mc_labels_the_population_layer_exact`; `test_a0_dense_addendum_properties.py::test_a_row_without_a_population_quantity_may_not_claim_exact`, `::test_exact_is_backed_by_the_identity_and_mc_by_a_real_mc_error` |
| 10 — `fiber_count`, `collision_count`, `occupied_buckets` recorded | written for every configuration (hash diagnostics on the hash configurations), closing 01A known gap G1 where they were 100% NULL across 1,094,400 frozen 1B rows | `test_a1_runner_smoke.py::TestRunnerEndToEndProbe::test_fiber_and_hash_diagnostics_are_recorded` |
| 11 — no forbidden D14 framing label in A1 text output | — | **NOT IMPLEMENTED.** No lint exists. Open, §3. |

Both protocol files are referenced by the runner, as the ruling requires:
`load_freeze_01a()` (01A) and `load_rulings_01b()` (01B), the latter naming all
18 keys it expects and **refusing to substitute a default for a binding
quantity** — `--execute` raises with the missing key names rather than running.

Dry run, this pass: `PROJECTED CELL COUNT: 182,400 EXECUTED rows (01A
design.row_count.total = 182,400) -> MATCH`, `D17 reference cells (48 x 13 x 1)
624 (01B minimum 624)`, `No cell executed.`

**Minor verified issues** named in the ruling text: the n=500 nesting test now
exercises the real runner (item 5); setup exceptions no longer disappear
(item 7); `exact_or_mc` is corrected (item 9); executed and successful rows are
distinguished (item 6). The **resource-ratio rounding discrepancy** (net +0.004
core-hours, cap verdict unchanged) is owned by `S0B_RESOURCE_CONFIRMATION.csv`
and is not enforced by any test.

---

## 2. Reconciliation — drift and defects between the parallel agents

Four agents produced the amendment, the runner, the test migration and the
reference harness concurrently. Every item below is a disagreement *between*
artefacts, which no single agent's own suite could catch.

### 2.1 R1 — the runner's D17 sample disagreed with 01B — **RESOLVED**

`run_sim1b_dense_addendum.py` set `REFERENCE_REPLICATES = (1,)`: replicate 1 for
all 48 scenarios. `01B rulings.D17.sampling_rule.frozen_replicate_rule` freezes
`int(scenario_id[-4:])`, and 01B carries a `why_not_replicate_1_for_all` clause
**declining the runner's choice by name**. Both samples contain exactly 624
cells, so every count-based assertion in the package passed while the two files
pointed at different replicates — the drift was invisible to arithmetic.

**Resolution: 01B wins; the runner was changed.** And it was changed so the
conflict cannot recur: the runner no longer contains a copy of the rule at all.
`_d17_rule_text()` reads
`rulings.D17.sampling_rule.frozen_replicate_rule.rule` from 01B at run time,
`_d17_compile()` parses the right-hand side and **whitelists** it (only the name
`scenario_id`/`scenario`, only the call `int`, only subscript/slice/constant
nodes — the rule is data from a frozen protocol file, so anything that is not a
pure function of the scenario id is refused rather than executed), and
`reference_replicate()` evaluates it and range-checks the result against
`1..REPS_ADD`. The result is cached per (path, mtime, size), so an amended 01B
takes effect immediately. `d17_reference_cells()` likewise reads
`sampling_rule.cell_count` from 01B. If 01B is absent, `reference_replicate`
raises `FileNotFoundError` — it does **not** fall back to a sample of the
runner's own choosing.

This is the intended reading of D18: the runner is the single source of truth
for the **seed** rule, 01B is the single source of truth for the **sampling**
rule, and each side reads the other instead of restating it.

Enforced by `tests/test_a0_1_reconciliation.py::TestD17ReferenceSampleFollows01B`
(12 tests) — the runner's expression must be the RHS of 01B's rule text; all 48 scenarios
must match a value re-derived here from that text by an independent parse; the
sample must not collapse to a single replicate; a module-level
`REFERENCE_REPLICATES` constant is banned by an AST scan of the runner's source;
amending 01B in a temp file must move the runner's sample; an out-of-range rule
and a non-pure-function rule must both raise; and, end to end, a two-replicate
probe of S1BD-0002 must stamp `reference_checked` on replicate **2 only**.

**Proof the tests bite:** with the superseded `(1,)` behaviour restored in
memory (no file changed), **7 of the 12 D17 tests fail**, including the
end-to-end worker test.

### 2.2 R9 — AD15 item 3 vs. the immutable A0 record — **CLOSED BY DETECTION**

`scripts/s0a_addendum_microbenchmark.py:67–74` still holds a private
`SEED_BASE_1BD`, `OOF_BASE_1BD` and `addendum_seed`. AD15 item 3 requires the
seed rule to live only in the runner, with everything else importing it. But
that file is an `S0A_*` A0 record and the advisor ruled: *"Do not overwrite or
erase the A0 freeze or council record."* Deleting the duplicate would satisfy
one binding instruction by violating another.

**AD15 item 3 is therefore closed by DETECTION, not by removal.** The A0 record
stays byte-identical — `sha256 00fbe65472347bdd837e62e08eed8f45fb37c2499835af399e921d1174848f56`,
16,779 bytes, unchanged before and after this pass — and
`tests/test_a0_1_reconciliation.py::TestS0AMicrobenchmarkSeedRuleHasNotDrifted`
imports **both** modules and compares them across **all 48 scenarios × all 50
replicates = 2,400 seeds**, plus both base constants, plus a check that the
imported module is the repository file and not a stub.

Why detection is the right trade here: the harm AD15 item 3 guards against is
*silent divergence* between two copies of the seed rule, not duplication as
such. A pinned duplicate cannot diverge silently — it diverges loudly, at the
next test run. Deleting it would additionally destroy the provenance of the A0
resource projections, which were measured with that exact code.

**Proof the test bites:** shifting the runner's rule by +1 **in memory only**
(`monkeypatch`, nothing on disk touched) produces **2,400 / 2,400 mismatches**
and the assertion fires.

**What is NOT closed:** the duplication itself. Two copies of the seed rule
still exist in the repository. If the advisor prefers literal compliance with
item 3, the microbenchmark must be edited — which requires him to lift the A0
immutability instruction for that file. Recorded as open in §3.

### 2.3 R10 — `_typed_failure_rows` ignored `learner_filter` — **FIXED**

The success path applied `learner_filter`; the typed-failure path did not. A
filtered probe therefore emitted **more failure rows than success rows for the
same configuration** — the number of ATTEMPTED cells depended on which path the
cell took. Frozen runs pass `learner_filter=None`, so the 182,400 total was
never affected; what was affected is every probe-level row-count assertion.

Fixed by routing both paths through one helper,
`_learners_for(enc, lab, learner_filter)`. Enforced by
`tests/test_a0_1_reconciliation.py::TestTypedFailureRowsHonourTheLearnerFilter`:
the clean probe and the injected-failure probe must produce the same row count
*and the same (encoder, width, learner, metric) key set*; the unfiltered failure
path must still cover every learner; and the full-arm projection must still be
182,400.

**Proof the test bites:** with the pre-fix behaviour restored in memory, the
filtered probe emits **24 failure rows against 8 success rows** and the test
fails.

One existing assertion had **encoded** the defect:
`test_a1_runner_smoke.py::…::test_setup_exception_emits_typed_rows_not_a_silent_continue`
counted every learner while its probe passed `learner_filter=PROBE_LEARNERS`, so
it passed *only because* the failure path ignored the filter. It now honours the
filter. This is the whole cost of the defect made concrete: a test that looked
green was green for the wrong reason.

### 2.4 R11 — an A0 test that did not fire — **DOCUMENTED, both tests kept**

AT6's set-intersection disjointness assertion did **not** fail when the seed base
offset was moved: the 8 realised blake2b digests happened to land above the old
maximum seed. What caught the move was the migration agent's structural test,
`test_disjointness_is_structural_not_accidental`
(`min(addendum) > max(original) + EVAL_DRAW_OFFSET`). Both are kept — AT6 is the
criterion as written and the only check that consults the realised seed manifest;
the structural test is the one with power. Recorded in
`S0B_RUNNER_TEST_REPORT.md` §7.1. **AT6 alone is not evidence of seed safety and
must not be cited as such.**

### 2.5 R12 — `mcse == 0.0` is legitimate — **DOCUMENTED, pinned in both directions**

For an injective encoder at d = M = 5 (`label` separates all 1,024 states),
`ebar(Z) == eta(X)` pointwise, the per-point representation loss is identically
zero, and its Monte Carlo standard error is **exactly 0.0** — a zero-variance
estimator, not a missing number. Any "the mc layer must carry a positive error"
assertion must be written on a **merging** encoder.
`TestZeroMonteCarloErrorIsLegitimate` asserts `label → mcse == 0.0` **and**
`hash_shared → mcse > 0.0` in the same probe, so it cannot be "fixed" in either
direction without a failure. Recorded in `S0B_RUNNER_TEST_REPORT.md` §7.2.

### 2.6 Found during this pass

- **`d17_reference_cells()` added.** The 624 cell count was a runner literal
  while 01B also freezes it. It is now read from
  `01B rulings.D17.sampling_rule.cell_count`, with the literal retained only as
  the fallback used when 01B is absent (dry runs).
- **R5 (token collision) re-verified as still correct** — see D14 above.
- **The `--dry-run` path never touches `reference_replicate`**, so the runner
  still enumerates the work list while 01B is being authored. Confirmed by
  running it.

### 2.7 Backlog items owned by other agents (recorded, not acted on here)

- **R2** — the D17 identity columns do not gate. Amended into 01B by the
  amendment agent (AMENDMENT-1) and reported under D17 above.
- **R3** — Q2/Q3/Q4/Q5 promoted into `01B advisor_confirmation_requested`
  (AMENDMENT-2). Confirmed present: `count: 5`.
- **R4** — a semantic gap requiring an advisor ruling; see §3.
- **R6** — two defects in **01A**, which is immutable: `AD8` says "about 9 of
  2,400 cells" for a 3×3×13 spot check, which is 117 cells (9 counts only
  (scenario, replicate) pairs); and `design.row_count.independently_confirmed`
  cites the frozen d=3 twin as *confirmation* of the addendum's row count when
  it is a **projection**. Reported, not fixed — 01A cannot be edited.
- **R7** — see D15 above.
- **R8** — council seat status is owned by `S0B_COUNCIL_REVIEW.md`. This pass
  did not fill or claim any council seat. **That file did not exist at the time
  of writing** (see §3).

---

## 3. What is NOT enforced, and what remains open for the advisor

**Not enforced by any test (stated plainly so nobody reads §1 as more than it is):**

1. **D13's estimator.** No block-clustered interval, no block-resampling
   bootstrap, no effective-blocks statement in code. A1-time.
2. **D16's decision rules.** No E1a/E1b/E1c analysis, no BH adjustment, no
   outcome classification. A1-time.
3. **D14's framing obligations** and **AD15 item 11**. No lint over A1 text
   output for the forbidden labels. A1-time, and currently unwritten.
4. **D15's addendum manifest** is verified only by running
   `scripts/verify_raw_freeze_manifest_addendum.py` by hand; no pytest test
   invokes it.
5. **The resource-ratio rounding correction** lives in
   `S0B_RESOURCE_CONFIRMATION.csv` and has no test.
6. **AD15 as a whole is an A1 gate**, per `01B AD15.a0_1_status`. What A0.1
   delivers is that each item has a test that will fire if the runner regresses,
   exercised on non-frozen probes. It is not a passed AD15.

**Open for the advisor** — this report's own item labels, **renumbered IR-n on
2026-08-25** so they cannot be mistaken for 01B's Qn. Read **01B** for the
advisor's question list; the `01B ref` column is the authoritative label.

| # | 01B ref | question |
|---|---|---|
| IR-1 | **Q1** | In which phase does the D17 624-cell reference check run? Adopted reading: harness validated at A0.1 against the frozen d=3 arm (PASS, 624/624); the addendum-cell check becomes an A1 gate. G2 in particular requires production rows on disk. |
| IR-2 | **Q2** | `effective_blocks_min = 4` — he wrote "too few independent blocks" with no number. |
| IR-3 | **Q3** | A **fourth** outcome class, `INCONCLUSIVE_REPORTED_IN_FULL`, was added to his three. |
| IR-4 | **Q4** | "Materially directionally inconsistent" quantified as opposite signs with both \|estimates\| > 1e-6. |
| IR-5 | **Q5** | **His D17 columns do not gate.** AMENDMENT-1 moved the AD1/AD2 verdict onto G1 + G2 and reclassified `log_identity_error` / `brier_identity_error` as descriptive. This corrects his ruling as written. |
| IR-6 | *(no 01B Q; recorded at `01B AD15` and in the gate report)* | **AD15 item 3 (R9).** Closed by detection, not removal, because the file holding the duplicate is an `S0A_*` A0 record he ruled immutable. Literal compliance requires him to lift that immutability for `scripts/s0a_addendum_microbenchmark.py`. **This was the colliding label:** it was "Q6" here while 01B's Q6 is the D13 inferential unit, the highest-severity item in the package. |
| IR-7 | `01B deferred_semantic_questions.DQ1` | **R4 semantic gap.** 01A inherits "a non-SUCCESS cell carries NULL metrics", but `run_sim1b_finite.py` stamps `METRIC_UNDEFINED` on a row that **keeps** its metrics. The new runner takes the strict reading (NULL), which discards an otherwise valid log-loss when the evaluation sample is single-class. Unreachable at n_eval = 50,000 with eta ∈ [0.05, 0.95], so nothing turns on it in this arm — but the semantics should be ruled on rather than settled by an implementer. |
| IR-8 | *(erratum question; recorded in the gate report §7)* | **R6.** Two defects in the immutable 01A (the AD8 "9 cells" miscount; `row_count.independently_confirmed` is a projection). They cannot be fixed in place. Does he want an erratum entry, or is the record in this report sufficient? |

**Raised in 01B but not by this report, and both outrank every IR item above:**

| 01B ref | question |
|---|---|
| **Q6** | **Which inferential unit governs — 8 blocks / 7 df as ruled, or 400 parameter draws / df ≈ 392 as measured?** D13's premise is refuted. `BLOCKS_A1_INFERENCE`. **Answer first.** |
| **Q7** | D17 gains two further gates (G3, G4) and a second, MCSE-scaled tolerance class; a D17 PASS no longer certifies what it certified when the ruling was written (AMENDMENT-4). |
| **Q8** | **How does the normalized contrast aggregate** — per-arm ratios differenced, or the raw contrast over one common denominator? Measured at A0.1: the two readings have **opposite signs** (AMENDMENT-5). `BLOCKS_A1_INFERENCE`. |

**Deliverables from the ruling's required-outputs list that did not exist when
this report was written:** `S0B_COUNCIL_REVIEW.md` and `S0B_FINAL_GATE_REPORT.md`
(the A0 council record, `S0A_ADDENDUM_COUNCIL_REVIEW.md`, is a different
document and does not satisfy the A0.1 requirement).
The gate report cannot be closed until they land, and per backlog R8 the council
review must state exactly which seats were filled by which provider and by what
dispatch, and must **not** claim a seat was filled when a Claude stand-in was
used.

---

## 4. Files changed by the reconciliation pass

| file | status | bytes |
|---|---|---|
| `scripts/run_sim1b_dense_addendum.py` | MODIFIED — D17 rule read from 01B (R1); `_learners_for` helper + `learner_filter` on the failure path (R10); `d17_reference_cells()` | 56,469 |
| `tests/test_a0_1_reconciliation.py` | CREATED — 23 tests (R1 ×12, R9 ×4, R10 ×6, R12 ×1, counting parametrizations) | 18,827 |
| `tests/test_a1_runner_smoke.py` | MODIFIED — one assertion that had encoded the R10 defect | 23,772 |
| `simulation-results-ct2i/S0B_RUNNER_TEST_REPORT.md` | APPENDED §7 (R11, R12, R10 closure) — nothing above §7 edited | 16,311 |
| `simulation-results-ct2i/S0B_ADVISOR_RULING_IMPLEMENTATION_REPORT.md` | CREATED (this file) | — |

**Untouched, verified:** `01_PROTOCOL_FREEZE.yaml`, `01A_ADDENDUM_PROTOCOL_FREEZE.yaml`,
`01B_ADDENDUM_ADVISOR_RULINGS.yaml` (owned by the amendment agent — no change was
required by this pass), every `S0A_*` file including
`scripts/s0a_addendum_microbenchmark.py` (`sha256 00fbe654…848f56`, byte-identical),
`scripts/s0b_reference_gap_check.py`, all frozen raw outputs and both raw-freeze
manifests. No git write command was run. No file was created under `raw/`.
