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

# S0B — Independent reference-implementation test report (ruling D17)

Phase A0.1. **Full addendum cells run: 0.** Real-data models run: 0. GPU hours: 0.
Interpreter: `/Users/Eric/.pyenv/versions/3.11.9/bin/python3` (conda `t2i` not used).

Harness: `scripts/s0b_reference_gap_check.py` (**38,957 B** as of 2026-08-25; 23,466 B when
this report was first written, before gates G3 and G4 landed).
Output: `simulation-results-ct2i/S0B_REFERENCE_GAP_CHECK_d3_frozen.csv` (**260,631 B**, 624
data rows, 46 columns; 211,395 B before the G3/G4 columns were added).

> **Currency notice (2026-08-25).** This report was written against the
> **AMENDMENT-1 two-gate** D17 rule and predates AMENDMENT-4. **D17 now gates on FOUR
> conjunctive gates**, not two:
> **G1** `|production − reference|` on both risk scales at `exact_identity_abs = 1e-10`;
> **G2** recomputed vs stored `fiber_count`;
> **G3** stored `representation_loss` vs the recomputed exact population gap, within
> `6 × stored_mcse + 1e-9` per metric (a **second tolerance class**, MCSE-scaled, that the
> advisor never set — `01B Q7`);
> **G4** stored vs recomputed canonical partition fingerprint, exact and tolerance-free.
> §5's row counts and its PASS are correct and unchanged. §6's three injected defects are
> correct and unchanged; two further defects (`fiber_permute`, `fiber_swap`) were added
> later and are recorded in `01B a0_1_verification.V12`, not here. Sections below marked
> with a currency note were corrected on 2026-08-25; the rest is as first written.
> Authoritative current statement: `01B rulings.D17.evaluation_rule.ad1_ad2_gating_rule`.

---

## 1. What was broken

`sim1_core.exact_gap_report` (`src/ct2i_benchmark/simulations/sim1_core.py:309`) computes
`gap = R(Z) − R(X)` **and** `theoretical_gap` (the CMI / expected conditional variance) from
the *same* `fiber_posteriors` aggregation. Recomputing an identity error from those stored
columns therefore returns ~1e-16 by construction — measured 1.28e-16 on the frozen twin by the
A0 council (`S0A_ADDENDUM_COUNCIL_REVIEW.md` finding 6). AD1 and AD2 would pass whatever the
fiber algebra does. The repo already ships the dependency-free remedy,
`sim1_core.reference_gap_report` (`sim1_core.py:332`; pure-Python dict grouping, `math` rather
than numpy reductions, no `bincount`, no `fiber_posteriors`), and the A0 preflight did not use
it (`grep -c reference_gap_report tests/test_a0_dense_addendum_properties.py` → 0).

Ruling D17 (`01B_ADDENDUM_ADVISOR_RULINGS.yaml`, `rulings.D17`) makes that implementation the
mandatory evaluation route for AD1/AD2 and freezes the sample and the persisted columns.

## 2. Phase ordering — what this report does and does not cover

Production values for **addendum** cells cannot exist until Phase A1 runs, and A0.1 is
forbidden to run any addendum cell (`prohibitions.PR1`). This report therefore executes the
adopted reading in `advisor_confirmation_requested.Q1`: the harness is **built and validated
against the existing frozen d = 3 arm**, where production values are already on disk. The
≥ 624 **addendum**-cell run is an A1 gate (see §7). Nothing in this report is an addendum
result.

## 3. Sample — the frozen deterministic rule, read not re-derived

Read from `01B_ADDENDUM_ADVISOR_RULINGS.yaml:692`, key
`rulings.D17.sampling_rule.frozen_replicate_rule.rule`:

    reference_replicate(scenario) = int(scenario_id[-4:])

The harness prints this line, read from the YAML at run time, in every run header. Applied to
the frozen twin, whose scenario ids are `S1B-0001 … S1B-0048` with 50 replicates each, it
selects replicates 1 … 48 — one per scenario, all in range, no implementer discretion.

| | |
|---|---|
| Arm evaluated | frozen 1B twin, M = 5, K = 4, `d_active` = 3 |
| Scenarios | 48 (`S1B-0001` … `S1B-0048`), all of them |
| Encoder configurations | 13 = 7 non-hash + 2 hash × 3 bucket widths (B0/B1/B2), all of them |
| Replicates per scenario | 1, by the frozen rule; replicate indices 1 … 48 |
| **Cells evaluated** | **624** = 48 × 13 × 1 — the D17 minimum, matched exactly |
| `n_train` coverage | both 500 and 5000 appear (they are a scenario factor) |
| Fibers per cell | 36 … 768 |
| Non-degenerate cells | 295 / 624 carry \|gap\| > 1e-6 (max log gap 0.1280) — the check is not passing on an all-zero sample |

The sample may only be enlarged, never reduced (`sampling_rule.expansion_rule`); `--limit` is
provided for smoke probes only and is not used for a real check.

## 4. Tolerance and its provenance

`exact_identity_abs = 1.0e-10`, read at run time from `01_PROTOCOL_FREEZE.yaml:525`
(`tolerances.exact_identity_abs`) — the harness parses the file rather than hardcoding the
number, and prints the file:line it read. D17 leaves it unchanged
(`rulings.D17.evaluation_rule.tolerance_ref`).

## 5. Result on the frozen d = 3 arm

Verbatim summary line:

```
D17 REFERENCE CHECK arm=d3_frozen defect=none cells=624 tol=1.0e-10 max_log_identity_error=5.447e-15 max_brier_identity_error=2.050e-15 max_prod_ref_abs_diff=5.551e-15 cells_over_tolerance=0 fiber_count_mismatches=0 RESULT=PASS
```

Exit code 0. Wall time 10 s, single process.

Distribution over the 624 cells (counts):

| statistic | max | p99 | median | < 1e-18 | [1e-18,1e-16) | [1e-16,1e-15) | [1e-15,1e-14) | ≥ 1e-10 |
|---|---|---|---|---|---|---|---|---|
| `log_identity_error` | 5.447e-15 | 5.175e-15 | 9.17e-18 | 219 | 124 | 144 | 137 | **0** |
| `brier_identity_error` | 2.050e-15 | 1.584e-15 | 1.34e-17 | 307 | 75 | 215 | 27 | **0** |
| \|production − reference\| log | 5.551e-15 | 5.107e-15 | 1.11e-16 | 236 | 0 | 262 | 126 | **0** |
| \|production − reference\| Brier | 2.054e-15 | 1.582e-15 | 2.78e-17 | 211 | 161 | 228 | 24 | **0** |

The largest errors are all in the two hash encoders (768-fiber partitions on the full
1024-cell space, so the longest summation chains); every coordinate-wise encoder stays at or
below 3.3e-16. All four statistics are five orders of magnitude inside tolerance.

Six mandated columns persisted, per `rulings.D17.persisted_columns`: `reference_log_gap`,
`reference_brier_gap`, `production_log_gap`, `production_brier_gap`, `log_identity_error`,
`brier_identity_error` — the two reference columns and both identity errors taken from
`reference_gap_report` executed on the cell, never derived from stored production columns
(`persisted_columns.forbidden`). Keying columns also persisted as required
(`scenario_id`, `replicate`, `encoder`, `bucket_width`, `width_label`, `d_active`) plus
`seed`, the DGP factors, and the diagnostics below.

**Cross-check that the harness rebuilds the production cells, not different ones:**
`fiber_count` recomputed from the rebuilt partition equals the frozen
`05b_SIM1B_REPLICATE_RESULTS.parquet` value in **624 / 624** cells. The stored
representation loss (a Monte-Carlo plug-in over 50,000 evaluation rows, not an exact
quantity) differs from the exact population gap by at most 1.07e-3, median 1.1e-16 — the
expected MC scale, reported descriptively and **not** gated.

## 6. Evidence that the check can actually fail

A check that cannot fail is worth nothing. Three defects were injected as **in-process
monkeypatches of `sim1_core`** — no source file was edited, no scratch copy of the repo was
made, and every perturbed CSV was written outside the package and deleted. The harness
refuses (`exit 2`) to write a defect-injected CSV into `simulation-results-ct2i/`.

| injected defect | what it corrupts | max \|prod − ref\| log | reference identity error | `fiber_count` match | verdict / exit |
|---|---|---|---|---|---|
| none | — | 5.551e-15 | 5.447e-15 | 624/624 | PASS, exit 0 |
| `ebar_bias` — `fiber_posteriors` returns `ebar × (1 + 1e-6)` | conditional means | **5.541e-07** (5.5e4 × tolerance) | 5.447e-15 (unchanged) | 624/624 | FAIL, exit 1, 624/624 cells over tolerance |
| `mass_dropout` — the lightest positive-mass fiber's mass is zeroed | fiber masses | **1.083e-02** (1.1e8 × tolerance) | 5.447e-15 (unchanged) | 624/624 | FAIL, exit 1, 624/624 cells over tolerance |
| `fiber_merge` — `group_ids` returns `fid // 2` | fiber **grouping** | 6.217e-15 (**does not fire**) | 6.214e-15 (does not fire) | **0/624** | FAIL, exit 1, caught only by `fiber_count` |

Two findings follow, and both matter for how AD1/AD2 should be worded.

**(a) The discriminating statistic is `|production − reference|`, not the identity errors.**
Under `ebar_bias` and `mass_dropout` the production result is wrong by 5.5e-7 and 1.1e-2
respectively, and the reference comparison fires by four to eight orders of magnitude — but
`log_identity_error` and `brier_identity_error`, the two columns D17 names, are *unchanged at
5.4e-15*. The reason is algebraic: `reference_gap_report` defines `ebar_f` as its own
mass-weighted within-fiber mean, and with that definition `R_log(Z) − R_log(X) = CMI` telescopes
exactly (likewise Brier and E[Var]). The reference implementation's internal identity error is
therefore a self-check of the *same class* as the production one — persisting it satisfies D17
literally but detects nothing on its own. What has teeth is
`rulings.D17.evaluation_rule.also_required`: the production-versus-reference comparison. The
harness gates on **all four** statistics, so this is a wording issue in D17, not a gap in the
implementation — but AD1/AD2 must not be reported as "passed" on the identity-error columns
alone. *(Currency note, 2026-08-25: AMENDMENT-1 acted on this finding and reclassified the two
identity-error columns as persisted-but-**descriptive, not gating** — `01B Q5`.)*

**(b) The reference comparison is blind to defects in fiber *construction*.** Both
implementations are handed the same `fid`, so a bug in `group_ids`, `hash_codes` or
`ebar_coordinatewise` makes both consistently wrong: `fiber_merge` halves every partition and
`|production − reference|` stays at 6.2e-15. This is precisely the failure class
`sim1_core.py:332-346` warns about ("a defect in fiber grouping … could make both sides agree
incorrectly") and D17's remedy as specified does **not** cover it. The harness therefore adds a
second, structurally independent detector for any arm whose production output is on disk:
recomputed `fiber_count` versus the stored `fiber_count` (plus the stored MC representation
loss, reported not gated). It caught `fiber_merge` in 624/624 cells. At A1 this detector is
available for the addendum as soon as the runner has written its rows, and the check should be
run **after** the runner, against its output, for exactly this reason.

*(Currency note, 2026-08-25.* This paragraph describes the two-gate scheme. It was
subsequently defeated: a fiber-**assignment** defect — a permutation, or a swap of one cell
between two fibers — preserves the fiber count **and** the entire multiset of fiber sizes, so
both G1 and G2 read clean while the D16 primary statistic moves by up to 3.01×. AMENDMENT-4
added **G3** and **G4** for exactly that class. Measured on this arm: `fiber_permute` fires G3
on 166 of 624 cells and `fiber_swap` on only 6 of 624, which is why G4 — exact and
tolerance-free — is required in addition. Full table: `01B a0_1_verification.V12`; the G4
driver is `scripts/s0b_g4_fingerprint_bite.py`.*)

Cleanup: `S0B_REFERENCE_GAP_CHECK_d3_frozen.csv` (defect `none`) is the only artefact retained.

## 7. The A1 interface

At A1, after `scripts/run_sim1b_dense_addendum.py` has written its rows, the ≥ 624
addendum-cell check is a single parameter change:

```
python3 scripts/s0b_reference_gap_check.py --arm addendum --stored
```

with, for a non-default output location, `--out <path>`. Programmatic entry point:

```python
s0b_reference_gap_check.run(arm_name="addendum", out_path=Path(...),
                            defect="none", use_stored=True, limit=None) -> int   # 0 == PASS
```

`--arm addendum` lazily imports `run_sim1b_dense_addendum` and takes `addendum_scenarios()`,
`encoder_configs()`, `addendum_train_seed`, `N_TRAIN_NEST_MAX`, `D_ADD` and `DEFAULT_OUT` from
it, so the runner remains the single source of truth for the seed rule (AD15 item 2). No code
in the harness changes between arms. Wire the exit code into the AD15 gate; on the d = 3 arm
it costs 10 s and the addendum arm is the same size.

**Interface the A1 runner must expose (already present at the time of writing, no change
requested):** `addendum_scenarios()` returning objects with `.scenario_id`, `.factors`
(`M`, `K`, `marginal`, `tau`, `n_int`, `delta_eta`, `n_train`) and `.seeds`; `encoder_configs()`
returning `(encoder, bucket_width, width_label)` triples; `addendum_train_seed(seed)`;
`N_TRAIN_NEST_MAX`; `D_ADD`; `COMPONENT`; `N_SCENARIOS_ADD`; `DEFAULT_OUT`. For `--stored` the
runner's CSV must carry `scenario_id, replicate, encoder, width_label, learner, metric, status,
fiber_count, representation_loss, mcse` — it does.

## 8. Discrepancy to resolve before A1 — **RESOLVED 2026-08-24 (reconciliation R1)**

**Status: CLOSED.** `REFERENCE_REPLICATES = (1,)` no longer exists in the runner. The constant
was removed; `scripts/run_sim1b_dense_addendum.py` now **reads the rule expression out of 01B
at run time** (`D17_RULE_KEY = "rulings.D17.sampling_rule.frozen_replicate_rule.rule"`, parsed
under a whitelist), so there is no second copy of the sampling rule to drift from. D18 makes
the runner the single source of truth for the **seed** rule; D17 makes 01B the single source of
truth for the **sampling** rule, and each side reads the other rather than restating it. Held
in place by `tests/test_a0_1_reconciliation.py` (R1 ×12). Recorded in
`S0B_ADVISOR_RULING_IMPLEMENTATION_REPORT.md` §2.1.

*What the discrepancy was, retained so the resolution is auditable:* an earlier draft of the
runner fixed replicate 1 for every scenario. That is the rule D17 explicitly declined
(`frozen_replicate_rule.why_not_replicate_1_for_all`: "Fixing one replicate index across all
scenarios would probe a single slice of the replicate axis"). The frozen rule is
`int(scenario_id[-4:])` → replicates 1 … 48. Both give 624 cells, so the count in `work_list()`
was never affected; only the *sample* differed.

## 9. Prohibitions honoured

Zero addendum cells executed; no real data, model, image or manuscript touched; no file under
`/Users/Eric/Desktop/114/碩論/` read or written. `01_PROTOCOL_FREEZE.yaml`,
`01A_ADDENDUM_PROTOCOL_FREEZE.yaml`, `01B_ADDENDUM_ADVISOR_RULINGS.yaml`, every `S0A_*` record,
`RAW_FREEZE_MANIFEST.json` and `RAW_FREEZE_MANIFEST_ADDENDUM.json` unmodified;
`scripts/run_sim1b_dense_addendum.py` and `tests/test_a0_dense_addendum_properties.py` untouched.
No git write command was issued; the Phase R provenance stamping in the working tree was
neither committed nor reverted.

`scripts/verify_raw_freeze_manifest_addendum.py` → `RAW FREEZE MANIFEST ADDENDUM: 10/10 MATCH`,
0 mismatched, 0 missing, 0 unlisted, 0 self-entries, and the superset check confirms all five
protected raw outputs (05a/05b/05c/05d parquet + `12_SIM2_RESULTS.csv`) carry forward with
matching SHA-256. Exit code 0.
