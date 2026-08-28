> # ⛔ TERMINAL STATUS — THE DENSE-SIGNAL ADDENDUM WAS TERMINATED BEFORE EXECUTION
>
> ```text
> addendum_run     = false
> addendum_status  = TERMINATED_BEFORE_EXECUTION
> full addendum cells run: 0        decided: 2026-08-25 by the advisor
> ```
>
> The dense-signal `M = 5, K = 4, d = 5` Simulation 1B addendum was **permanently
> discontinued before execution**. It is not pending, not planned, not paused, not awaiting
> approval and not scheduled. **Phase A1 will never run.** Nothing in this document is an
> open item, a next action, or work still to be done.
>
> **This file is retained ONLY as a methodological audit record — design-audit provenance.
> None of its projected, exploratory or measured contrasts is a study result, and none may be
> cited as one.**
>
> Authoritative decision record, with the reasons and their file:line evidence:
> [`DENSE_ADDENDUM_DECISION.md`](DENSE_ADDENDUM_DECISION.md).
> Everything below this box is the record **as it stood on 2026-08-25 before the termination**
> and is preserved unaltered for audit; read every verdict, gate, question, default and "next
> action" in it as **superseded and closed by the termination**.

---

# S0B — RUNNER TEST REPORT (Phase A0.1, decision D18 / criterion AD15)

Scope: the TEST-MIGRATION half of D18. The property tests now exercise the real
Phase A1 runner instead of a duplicated copy of its seed rule.

    interpreter   /Users/Eric/.pyenv/versions/3.11.9/bin/python3   (never conda `t2i`)
    invocation    PYTHONPATH=src python -m pytest -q
    date          2026-08-24
    FULL ADDENDUM CELLS RUN            0
    ADDENDUM OUTPUT WRITTEN OR FROZEN  0 bytes (no file matching *dense_addendum* under raw/)
    REAL-DATA MODELS RUN               0
    GPU HOURS USED                     0

Files touched by this half of D18:

| file | status | bytes |
|---|---|---|
| `tests/test_a0_dense_addendum_properties.py` | MODIFIED (migration + 3 new classes) | 55,707 |
| `simulation-results-ct2i/S0B_RUNNER_TEST_REPORT.md` | CREATED (this file) | — |
| `scripts/run_sim1b_dense_addendum.py` | READ ONLY — untouched (sha256 `4da91347…3598aa`, mtime 21:43:51, written by the runner author) | 49,719 |
| `tests/test_a1_runner_smoke.py` | READ ONLY — untouched (sibling agent's file) | 23,253 |

---

## 1. What migrated

Deleted from `tests/test_a0_dense_addendum_properties.py`: the private copy of the
addendum seed rule — 16 design/seed constants (`M_ADD`, `K_ADD`, `D_ADD`,
`N_CELLS`, `MARGINALS`, `TAUS`, `N_INTS`, `DELTAS`, `N_TRAINS`, `REPS_ADD`,
`N_SCENARIOS_ADD`, `ROWS_ADD`, `SEED_BASE_1BD`, `OOF_BASE_1BD`,
`TRAIN_DRAW_OFFSET`, `EVAL_DRAW_OFFSET`) and 4 local functions
(`addendum_block`, `addendum_seed`, `addendum_oof_seed`, `addendum_scenarios`).

They are now imported from `run_sim1b_dense_addendum`, together with the two
derived-seed helpers the test module previously open-coded as `seed + 100_000` /
`seed + 200_000` (8 + 2 call sites now route through `addendum_train_seed` /
`addendum_eval_seed`).

The import is deliberately unguarded — no `try`, no fallback, no local default —
so a missing or renamed runner is a COLLECTION error and every AT test errors
loudly. `TestTheSeedRuleIsNotRedefinedHere::test_the_runner_import_has_no_fallback`
asserts that no guard is added later.

Bit-identity check performed BEFORE the deletion (old module and runner imported
side by side): 15/15 shared constants equal, 48/48 scenario ids equal, 48/48
block keys equal, 2,400/2,400 seeds equal, 50/50 OOF seeds equal, all
train/eval derivations equal. Result: **ALL BIT-IDENTICAL** — no expected value
in the AT suite had to change, and none was changed.

## 2. AT1–AT16 against the real runner

    before migration (private seed-rule copy)   264 passed / 264 collected
    after  migration (runner-imported rule)     264 passed / 264 collected
    values changed                              NONE

No seed-semantics discrepancy was found. Every AT expected value (fiber counts
240/363/768/56, bucket occupancies 8/12/16, widths B0=10/B1=20/B2=40, row total
182,400, 48 scenario ids, the 8-block seed structure) is unchanged.

New tests added by this migration: **17** (3 classes), so the module now collects
281. They are numbered outside the AT series because they test the RUNNER, not
the frozen design.

    full suite BEFORE   987 passed / 987 collected
    full suite AFTER  1,004 passed / 1,004 collected      (+17, no regression)

> **Currency note (2026-08-25).** The two figures above are the BEFORE/AFTER of
> *this migration* and are correct as such; they are not the current suite size.
> The suite is now **1,086 passed / 1,086 collected**, grown by the
> reconciliation module (`tests/test_a0_1_reconciliation.py`) and the defect
> closures (`tests/test_a0_2_defect_closure.py`), neither of which existed when
> this section was written. Nothing above §7 has been edited.
> Separately: this report describes the runner's **8-block seed structure**,
> which is a correct statement about the SEED. It is not a claim that 8 is the
> inferential unit — that premise was refuted at A0.1 and is `01B Q6`.

## 3. Proof that the gate can fail

A test that cannot fail is worth nothing. The runner's seed rule was broken
**in memory only** by a pytest plugin living in the scratchpad
(`brokenseed*.py`, outside the repo); the file on disk was never written —
confirmed after the fact by `git status --porcelain` (the runner is untracked
and unmodified), its sha256 and its unchanged mtime.

| induced break | failures in the AT module | failures across the suite |
|---|---|---|
| `+ 2*replicate` instead of `+ replicate` | 3 | 4 |
| seed stops depending on the block (8 blocks collapse to 1) | 3 | 4 |
| base offset moved back onto the completed run's namespace | 2 | 3 |

Failing tests, in all three breaks, include
`TestTheSeedRuleIsNotRedefinedHere::test_seed_semantics_are_still_the_frozen_ones`
and `::test_every_seed_name_is_the_runners_own_object`; the smoke module's
`TestRunnerOwnsTheSeedRule::test_seed_matches_the_formula_written_in_01A` also
fires. Observed weakness worth recording: AT6's seed-disjointness assertions did
NOT fire on the base-offset break, because the eight realised block digests
happened to land above the completed run's maximum seed anyway. AT6's
disjointness is therefore data-dependent; the structural test above is what
actually bites.

## 4. AD15 / D18 item → enforcing test

`SMOKE` = `tests/test_a1_runner_smoke.py` (sibling agent, not modified here).
`AT`    = `tests/test_a0_dense_addendum_properties.py`.

| AD15 item | requirement | enforcing test |
|---|---|---|
| 1 | the runner exists and is the module the tests bind to | `AT::TestTheSeedRuleIsNotRedefinedHere::test_the_imported_runner_is_the_repository_file`; `SMOKE::TestProtocolFileWiring::test_runner_reads_01A`; PARTIAL — see §5 |
| 2 | the runner is the single source of truth for the seed rule | `AT::TestTheSeedRuleIsNotRedefinedHere::test_every_seed_name_is_the_runners_own_object`, `::test_seed_semantics_are_still_the_frozen_ones`; `SMOKE::TestRunnerOwnsTheSeedRule` (5 tests) |
| 3 | the tests import that rule and MUST NOT redefine it | `AT::TestTheSeedRuleIsNotRedefinedHere::test_module_defines_no_local_seed_rule` (AST scan of this module's own source), `::test_module_never_recomputes_the_seed_construction` (bans inline `blake2b` and the literal seed bases), `::test_the_runner_import_has_no_fallback`; PARTIAL — the microbenchmark, see §5 |
| 4 | AT1–AT16 re-run against the real runner and all pass | the whole `AT` module: 264/264, §2 |
| 5 | both n_train levels; n=500 nesting exercised by the REAL runner | `AT::TestNestedNTrainThroughTheRealRunner::test_both_n_train_levels_execute_a_real_runner_path[0-500]` and `[1-5000]`, `::test_the_runner_draws_the_nest_max_and_never_redraws_at_500[0,1]`, `::test_n500_training_matrix_is_the_prefix_of_the_n5000_one`, `::test_the_slicing_is_load_bearing_for_the_labels`; design layer: `AT::TestNestedNTrainDraw` (AT8); end-to-end: `SMOKE::TestRunnerEndToEndProbe::test_both_n_train_levels_execute_a_real_code_path` |
| 6 | typed row per attempted cell; EXECUTED ≠ SUCCESSFUL | `AT::TestRunnerFailureAccountingIsTyped::test_executed_and_successful_are_distinguishable_in_the_schema` (a MIXED output: `0 < rows_success < rows_executed` in ONE result set); `SMOKE::TestTypedRowDiscipline::test_executed_and_successful_are_separately_countable` (all-success case) |
| 7 | no silent `continue` on a setup exception | `AT::TestRunnerFailureAccountingIsTyped::test_a_failed_replicate_does_not_delete_itself` (replicate 1's DGP draw raises, replicate 2 succeeds; both replicates still emit rows, the exception type and message survive); `SMOKE::TestTypedRowDiscipline::test_setup_exception_emits_typed_rows_not_a_silent_continue` |
| 8 | NULL metrics on every non-success row | `AT::TestRunnerFailureAccountingIsTyped::test_non_success_rows_carry_null_metrics_never_zero_or_a_sentinel` (all 41 metric columns `is None`, and explicitly not 0, 0.0, 0.5, −1 or any str/float sentinel, on rows produced by the REAL worker); `AT::TestTypedFailureNulls` (AT14, constructor level); `SMOKE::TestTypedRowDiscipline::test_failure_row_nulls_every_metric_column` |
| 9 | `exact_or_mc` correct: exact where IDENTIFIED_EXACT, mc only where genuinely Monte Carlo | `AT::TestRunnerFailureAccountingIsTyped::test_exact_is_backed_by_the_identity_and_mc_by_a_real_mc_error` (on a MERGING encoder, so `pop_gap_logloss > positive_gap_min` and `mcse > 0`: the `exact` label is backed by an identity error ≤ 1e-10 and the `mc` label by a strictly positive Monte Carlo error), `::test_a_row_without_a_population_quantity_may_not_claim_exact` (failure rows carry `exact_or_mc = NULL`, never `exact`); `SMOKE::TestRunnerEndToEndProbe::test_exact_or_mc_labels_the_population_layer_exact` |
| 10 | `fiber_count`, `collision_count`, `occupied_buckets` recorded | `SMOKE::TestRunnerEndToEndProbe::test_fiber_and_hash_diagnostics_are_recorded`; `AT::TestRunnerFailureAccountingIsTyped::test_exact_is_backed_by_the_identity_and_mc_by_a_real_mc_error` (asserts all three present on the hash configuration and `fiber_count < 1024`); ground truth for the values: `AT::TestCollisionsAndBucketsExact` (AT11) |
| 11 | no A1 text output carries a forbidden D14 framing label | NOT ENFORCED — see §5 |

Minor verified issues from the ruling text: "make the n=500 nesting test exercise
the real runner" → item 5; "prevent setup exceptions from disappearing" → item 7;
"correct exact_or_mc labels" → item 9; "clearly distinguish executed rows from
successful rows" → item 6. All four are closed by the tests above. The fifth,
"correct the small resource-ratio rounding discrepancies", is not a test-layer
item (see §5).

## 5. AD15 items NOT yet enforced by a test, and why

1. **Item 3, the microbenchmark half.** `scripts/s0a_addendum_microbenchmark.py`
   lines 67–74 still carry a private `SEED_BASE_1BD` and a private
   `addendum_seed`. AD15 item 3 names the microbenchmark as well as the tests.
   It was NOT migrated here because it is an S0A_* deliverable and this agent is
   prohibited from modifying S0A_* files. **Action required in reconciliation:**
   migrate it to the runner import, or record why the frozen S0A artefact keeps
   its copy. No test asserts its absence today, so this is an open AD15 gap, not
   a closed one.
2. **Item 1, the "produces every addendum row" clause.** Only the existence and
   binding half is testable at A0.1. That every retained addendum row was
   produced by this runner is a provenance claim about A1 output that does not
   exist yet (zero cells run). It becomes checkable at A1 from the row-level
   `protocol_freeze_01a` / `advisor_rulings_01b` provenance columns, which the
   schema already declares.
3. **Item 11, the D14 framing-token check.** Requires scanning A1 TEXT OUTPUT for
   the forbidden labels in `01B rulings.D14.framing_token.forbidden_labels`.
   There is no A1 text output at A0.1, so no test can fail today. This is an
   A1-evaluated item and must be wired into the acceptance report, not into the
   test suite, unless a lint over the report files is added.
4. **The resource-ratio rounding discrepancy** (`01A resources.ratio_precision_note`,
   net +0.004 core-hours) belongs to `S0B_RESOURCE_CONFIRMATION.csv`, not to the
   test layer. Not enforced here; owned by the resource-confirmation deliverable.
5. **AD15 is an A1 gate, not an A0.1 result.** Per `01B AD15.a0_1_status`, the
   run-time items are EVALUATED in A1. What §4 documents is that each item now
   has a test that will fire if the runner regresses, exercised at A0.1 on
   non-frozen probes.

## 6. Defects found in the runner (reported, NOT patched)

1. **`_typed_failure_rows` ignores `learner_filter`.** `scenario_worker`'s setup
   failure path builds rows from `DES.learners_for(enc, lab)` without applying
   the `learner_filter` keyword, while the success path applies it. A filtered
   probe therefore emits MORE failure rows than success rows for the same
   configuration. Frozen runs pass `learner_filter=None`, so the frozen row
   count and the 182,400 total are unaffected; the inconsistency is probe-only,
   and it makes probe-based row-count assertions depend on which path was taken.
   Recommendation: apply the same filter in `_typed_failure_rows`, or document
   that the failure path is deliberately unfiltered.
2. **Observation, not a defect:** `mcse` is exactly 0.0 for injective encoders
   (`label`, `onehot`) because the per-point representation loss is identically
   zero there. Any future "the mc layer must have a positive error" check must
   be written on a merging encoder, as `test_exact_is_backed_by_the_identity_and_mc_by_a_real_mc_error`
   is, or it will produce a false failure.

Nothing else in the runner was found to disagree with 01A or 01B during this
migration. The runner's 48 scenario ids, 8 block keys and 2,400 seeds are
bit-identical to the copy the tests previously carried.

---

## 7. Reconciliation pass, 2026-08-24 (appended by the A0.1 reconciliation agent)

This section is APPENDED; nothing above it was edited. It records two findings
about the strength of the A0 test suite itself, and closes item 1 of §6.

### 7.1 R11 — AT6's disjointness assertion did NOT fire when it should have

`TestAddendumSeedsDisjointFromOriginal::test_addendum_seed_set_is_disjoint_from_every_realised_seed`
compares the 2,400 addendum seeds against every seed in the completed run's
manifest ranges. During the A0.1 seed-base migration the addendum base offset
was moved, and **AT6 did not fail** — the 8 realised blake2b digests happened to
land above the old maximum seed, so the two sets stayed disjoint by accident.
What actually caught the move was the migration agent's structural assertion,
`test_disjointness_is_structural_not_accidental`, which requires
`min(addendum_seeds) > max(original_seeds) + EVAL_DRAW_OFFSET` — a margin
condition rather than a set-intersection condition.

Consequence for the reader of this package: **AT6 alone is not evidence of seed
safety.** A set-intersection test over 8 realised digests has very little power;
it passes for almost any base offset, including one that overlaps the original
namespace for a *different* block key that this design happens not to draw. The
structural test is the one that bites, because it constrains the whole namespace
rather than the eight points sampled from it.

Both tests are KEPT. AT6 is retained because it is the criterion as written and
because it is the only check that consults the realised seed manifest; the
structural test is retained because it is the one with power. Neither is a
substitute for the other, and any future report that cites AT6 as the seed-safety
evidence should cite the structural test alongside it.

### 7.2 R12 — `mcse == 0.0` on an injective encoder is CORRECT

Recorded here so that nobody later "fixes" it. At d = M = 5 the `label` encoder
is injective over all 1,024 states, so `ebar(Z) == eta(X)` pointwise, the
per-point representation loss is identically zero in every evaluation draw, and
its Monte Carlo standard error is **exactly 0.0** — a zero-variance estimator,
not a missing or defaulted number. `0.0` here is the true value; replacing it
with NULL, with a floor, or with a "recomputed" positive number would be a
falsification.

Rule that follows: **any assertion of the form "the Monte Carlo layer must carry
a positive error" must be written on a MERGING encoder.** Two tests now encode
this — the pre-existing
`test_exact_is_backed_by_the_identity_and_mc_by_a_real_mc_error` in
`tests/test_a0_dense_addendum_properties.py`, and
`TestZeroMonteCarloErrorIsLegitimate::test_injective_encoder_has_exactly_zero_mcse_and_a_merging_one_does_not`
in `tests/test_a0_1_reconciliation.py`, which asserts `label` gives exactly 0.0
AND `hash_shared` gives strictly positive `mcse` in the same probe, so the pair
cannot be "corrected" in either direction without a test failure.

### 7.3 §6 item 1 (the `learner_filter` defect) is now FIXED

`_typed_failure_rows` now takes `learner_filter` and selects learners through a
single shared helper, `_learners_for(enc, lab, learner_filter)`, which the
success path also uses — so the set of ATTEMPTED cells is a property of the
configuration and not of which path the cell took. Frozen runs pass
`learner_filter=None`, so the 182,400 total is unchanged (asserted by
`test_the_frozen_row_total_is_untouched_by_the_fix`).

One assertion in `tests/test_a1_runner_smoke.py` had encoded the defect: it
counted `DES.learners_for(...)` unfiltered while the probe passed
`learner_filter=PROBE_LEARNERS`, and so it only passed *because* the failure
path ignored the filter. It now honours the filter. Regression tests live in
`tests/test_a0_1_reconciliation.py::TestTypedFailureRowsHonourTheLearnerFilter`;
with the pre-fix behaviour restored in memory, the filtered probe emits 24
failure rows against 8 success rows and the test fails.

§6 item 2 is superseded by §7.2 above (same observation, now with a test that
pins it in both directions).
