# S0B Council Review — Advisor-Ruling Amendment and A1 Runner Gate (Phase A0.1)

**All four council seats were genuinely filled. The two external seats are REAL — Codex
and Gemini produced the text attributed to them below. No output in this file is a Claude
substitution for a mandated provider seat.**

**All four seats returned a negative verdict.**

**Phase:** A0.1 (advisor-ruling amendment + A1 runner gate). **Scope:** simulation only.
**Addendum cells run: 0** — by every seat, and by the host. **Real-data models run: 0.**
**GPU hours: 0.** No file under `/Users/Eric/Desktop/114/碩論/` was read or written by any
seat. No git write command was issued.

Each seat's output is reproduced **verbatim and complete** in §7–§10, together with the
exact prompt it was given and the exact dispatch command, in the same form
`S0A_ADDENDUM_COUNCIL_REVIEW.md` used at Phase A0. Line references point at the files as
they stood at review time.

This document is a **record**, not an argument. Where two seats disagree, both readings
are shown and the thing that settled the disagreement is named. Where a seat was wrong,
the evidence is given. Where a seat's finding corrects the **advisor's own binding
ruling**, that is stated plainly — §5 exists for exactly that purpose.

---

## 1. Council composition and dispatch

| Seat | Role as the ADVISOR assigned it | Provider | Model id | Dispatch | Wall-clock | Verdict |
|---|---|---|---|---|---|---|
| 1 | "Codex for implementation/numerical verification" | **Codex** (codex-cli 0.147.0) | `gpt-5.6-terra` | `codex exec --sandbox read-only --skip-git-repo-check "$(cat prompt_codex.txt)" </dev/null`, cwd `/Users/Eric/Desktop/114/ct2i-benchmark` | **159 s** (epoch 1787582491 → 1787582650), exit 0 | **NOT READY FOR A1** |
| 2 | "Gemini for independent scientific review" | **Antigravity** `agy` v1.1.19 | `gemini-3.1-pro-high` | `agy --model gemini-3.1-pro-high --sandbox --print-timeout 25m --print "$(cat prompt_agy.txt)" </dev/null`, cwd = an **empty neutral directory outside the repo** (`…/scratchpad/agy_neutral`) | **97 s** (epoch 1787582611 → 1787582708), exit 0, stderr 0 bytes | **DO NOT EXECUTE AS AMENDED** |
| 3 | Supplementary seat, retained from A0 practice — statistical validity | Claude (fresh context, no authorship of any reviewed artefact) | Claude, host model | Subagent dispatched 22:41:18, output captured 22:57:28 | ~16 min | **DO NOT EXECUTE AS AMENDED** |
| 4 | Supplementary seat, retained from A0 practice — adversarial implementation | Claude (fresh context, no authorship of any reviewed artefact) | Claude, host model | Subagent dispatched 22:41:18, output captured 23:14:38 | ~33 min | **DO NOT EXECUTE AS AMENDED** |

Host seat: Claude, orchestration, integration, write-boundary enforcement — as the advisor
mandated ("Claude as host").

### 1.1 The A0 provider premise was a mistaken assumption, not a real limitation

At Phase A0 the work order asserted that neither Codex nor Gemini was available in this
environment and planned a disclosed Claude substitution. **That was a mistaken assumption,
not a real limitation.** It was tested at A0 and found false, and it was tested again at
A0.1 and found false again: both CLIs are installed, authenticated and were probed live
before dispatch (`PROVIDER_INVOCATION.md`, both seats "Probed OK"). The error must not
recur, and this round did not repeat it.

### 1.2 The Gemini seat is STRONGER this round, not weaker

Phase A0 used `gemini-2.5-pro` via Vertex AI. Phase A0.1 used **`gemini-3.1-pro-high`**,
the strongest model offered on the sanctioned Antigravity channel. The legacy standalone
client for this provider is retired and blocked by environment policy; `agy` is the only
sanctioned route.

### 1.3 The Antigravity seat was given pasted material — a channel adaptation, not a seat-availability finding

A capability probe was run before dispatch and is recorded in full in §8. The seat
attempted to run a shell command in order to read a local file and was refused by its own
permission layer:

```
-> Error: permission check failed for command "pwd": user denied permission to run command: pwd
-> exit 1
```

Granting it the permissions it wanted (`--dangerously-skip-permissions`) would have
breached the read-only requirement that a review seat must never write. The dispatch was
therefore adapted: **176,787 bytes of review material were pasted into the prompt** and
the seat was told explicitly that it could not read the repository. It received
`01A_ADDENDUM_PROTOCOL_FREEZE.yaml` complete (52,897 B), `01B_ADDENDUM_ADVISOR_RULINGS.yaml`
complete (87,374 B), and `S0B_ADVISOR_RULING_IMPLEMENTATION_REPORT.md` complete (31,180 B),
plus a context block. **This is a channel adaptation, not a seat-availability finding.**
The seat was filled, by Gemini, and it returned a full six-part review with a verdict.

### 1.4 What each seat was given

| Seat | Material |
|---|---|
| 1 — Codex | Direct read-only access to the repository, given as PATHS not pasted text: `01B_ADDENDUM_ADVISOR_RULINGS.yaml`, `S0B_ADVISOR_RULING_IMPLEMENTATION_REPORT.md`, `S0B_RUNNER_TEST_REPORT.md`, `S0B_REFERENCE_IMPLEMENTATION_TEST_REPORT.md`, `S0B_RESOURCE_CONFIRMATION.csv`, `RAW_FREEZE_MANIFEST_ADDENDUM.json`, `scripts/run_sim1b_dense_addendum.py`, `scripts/s0b_reference_gap_check.py`, `tests/test_a0_dense_addendum_properties.py`, `tests/test_a1_runner_smoke.py`, `tests/test_a0_1_reconciliation.py`; context: `01A_ADDENDUM_PROTOCOL_FREEZE.yaml`, `S0A_ADDENDUM_PREFLIGHT_REPORT.md`, `src/ct2i_benchmark/simulations/sim1_core.py`, `scripts/run_sim1b_finite.py`. It additionally opened `scripts/_s1_parallel.py` and `scripts/s0a_addendum_microbenchmark.py` on its own initiative. Six named attack questions Q1–Q6. |
| 2 — Antigravity/Gemini | 176,787 bytes pasted: context block, 01A complete, 01B complete, S0B implementation report complete. **Not** given the runner source, the tests, the runner/reference test reports, the resource CSV, the manifest, or the A0 preflight — by design: this seat reviews SCIENCE and DESIGN, which is not the Codex seat's remit. Six named questions S1–S6. |
| 3 — Claude, statistical validity | Full repository read access. Executed exact population-algebra probes only (`draw_params` → `impose_delta_eta` → `exact_gap_report`), no learner fitted, six probe scripts in `<SCRATCHPAD>/council_sci/`. Read the frozen `05b_SIM1B_REPLICATE_RESULTS.parquet` read-only. |
| 4 — Claude, adversarial implementation | A byte-copy of the repository at `<SCRATCHPAD>/adv/repo` (heavy `raw/` symlinked read-only). Mandate: make the A0.1 gates PASS while the science is WRONG. 29 mutations executed against the copy and reverted; baseline `1027 passed in 17.8 s` reproduced before every mutation. |

### 1.5 Write-boundary verification

`git status --porcelain` in `/Users/Eric/Desktop/114/ct2i-benchmark` was captured before
and after every dispatch and is **byte-identical throughout** (21 entries: 8 modified,
13 untracked, all pre-existing A0.1 work):
`gitstatus_council_baseline.txt`, `gitstatus_after_codex.txt`, `gitstatus_after_agy.txt`,
`gitstatus_council_claude_start.txt`, `gitstatus_council_claude_end.txt`,
`gitstatus_final.txt`, `git_status_end.txt`. The Antigravity seat's neutral working
directory was still empty after the run. No reviewer wrote to the working tree.

---

## 2. Veto tally

Each seat's **own** severity labels, not re-graded and not renumbered by the host.

| Seat | CRITICAL | MAJOR | MINOR | Verdict line as the seat wrote it |
|---|---|---|---|---|
| 1 — Codex (`gpt-5.6-terra`) | **4** | 2 | 2 | `CODEX VERDICT: NOT READY FOR A1 - the real runner can silently omit attempted cells, and the D17 gate can pass without validating runner output or a wrong same-cardinality partition.` |
| 2 — Antigravity/Gemini (`gemini-3.1-pro-high`) | **3** | 3 | 0 | `GEMINI VERDICT: DO NOT EXECUTE AS AMENDED` |
| 3 — Claude, statistical validity | **3** | 5 | 6 | `# DO NOT EXECUTE AS AMENDED` |
| 4 — Claude, adversarial implementation | **6** | 7 | 4 | `**DO NOT EXECUTE AS AMENDED.**` |
| **Total across seats (not de-duplicated)** | **16** | **17** | **12** | **4 of 4 negative** |

Notes on the tally, recorded rather than resolved:
- Seat 4's own count line reads "**Counts: 6 CRITICAL, 7 MAJOR, 4 MINOR**"; a fifth MINOR
  (its MINOR-5, on the resource rationale) is introduced later in its §6, after that count
  was struck. The seat's own number is reproduced above unaltered.
- Seat 2 labelled its findings by question (S1–S6) rather than numbering them; the
  severities above are the labels it attached to each answer.
- These totals are **across seats, before de-duplication**. §4 identifies where two seats
  found the same thing independently.

**CRITICAL VETO COUNT for the required status block: 16 across seats; 4 of 4 seats vetoed.**

---

## 3. Consolidated findings

Severity is **as the originating seat assigned it**. Titles are one-line renderings of the
seat's own title; the seat's full text is in §7–§10.

Disposition key:
- **CLOSED AT A0.1** — the council examined it and it needs no further action, or A0.1 work
  already closes it and the closure was verified by a seat.
- **CLOSURE IN PROGRESS** — a concurrent A0.1 implementation pass is landing the fix; final
  status is **not** recorded here. **See `S0B_FINAL_GATE_REPORT.md`.**
- **OPEN FOR ADVISOR** — blocks A1 and requires the advisor's decision or his authorisation
  of the fix-and-recheck pass.
- **DISPUTED** — two seats, or a seat and the binding ruling, disagree. See §5.

### 3.1 Seat 1 — Codex, `gpt-5.6-terra` (implementation / numerical verification)

| # | Sev (seat's) | Title | file:line | Disposition |
|---|---|---|---|---|
| C1 | **CRITICAL** | The D17 gate can PASS without checking the A1 runner's production output (`--stored` is not mandatory) | `scripts/s0b_reference_gap_check.py:393-458` | OPEN FOR ADVISOR |
| C2 | **CRITICAL** | Worker/pool failure is converted to an empty checkpoint, silently omitting every attempted cell | `scripts/_s1_parallel.py:56,74,79,83,85` | OPEN FOR ADVISOR |
| C3 | **CRITICAL** | Typed-row coverage excludes several named setup/fatal paths (`BaseException`, pre-`try` setup, failure inside the failure handler) | `scripts/run_sim1b_dense_addendum.py:852,856,859,863,887` | OPEN FOR ADVISOR |
| C4 | **CRITICAL** | G1 + fiber-count G2 cannot detect wrong **same-cardinality** partitions | `scripts/s0b_reference_gap_check.py:392,415`; `01B…yaml:863` | **CLOSURE IN PROGRESS — see `S0B_FINAL_GATE_REPORT.md` for final status** |
| C5 | MAJOR | Existing or malformed part files are trusted as completed work | `scripts/_s1_parallel.py:50,56,103` | OPEN FOR ADVISOR |
| C6 | MAJOR | The 8.573 core-hour projection is arithmetically consistent but is not a defensible **upper bound** | `S0B_RESOURCE_CONFIRMATION.csv:4,7,8`; `run_sim1b_dense_addendum.py:1192` | DISPUTED (see §5.3) |
| C7 | MINOR | D14 mathematics is correct, but the threshold implements a different boundary rule (`den <= tol` vs the frozen `< tol`) | `run_sim1b_dense_addendum.py:680,714,719`; `01B…yaml:461` | OPEN FOR ADVISOR |
| C8 | MINOR | The seed rule is not literally single-source; the immutable A0 microbenchmark's private copy can drift outside tests | `run_sim1b_dense_addendum.py:316`; `s0a_addendum_microbenchmark.py:67,71`; `tests/test_a0_1_reconciliation.py:252` | OPEN FOR ADVISOR |

Codex also recorded, affirmatively: the substantive D14 computation checks out
(`eta_raw` is a probability at `sim1_core.py:156-162`; `R_Brier*(X)=E[eta(1-eta)]` at
`sim1_core.py:256-259`; the runner uses `Var(Y)-R_Brier*(X)`), and it found **no other
executable addendum seed-rule implementation** beyond the runner and the acknowledged
immutable microbenchmark.

### 3.2 Seat 2 — Antigravity / Gemini, `gemini-3.1-pro-high` (independent scientific review)

| # | Sev (seat's) | Title | Disposition |
|---|---|---|---|
| G-S1 | **CRITICAL** | The "DENSE-SIGNAL STRESS TEST" reframing is insufficient and actively misleading — "dense" directs the reader to dimensionality while concealing that total signal magnitude increased | OPEN FOR ADVISOR |
| G-S2 | MAJOR | "Sensitivity analysis" is the correct status; but the non-linear logistic link means the *fraction* of signal lost is not invariant to signal strength, so a ratio of risks fails to isolate the dimensionality effect | OPEN FOR ADVISOR |
| G-S3 | MAJOR | Reporting the interaction strata separately is necessary but insufficient — the `interaction_pairs=3` stratum conflates dimension, a 70% saturation drop, and a topology shift | OPEN FOR ADVISOR |
| G-S4 | **CRITICAL** | 8 blocks / 7 df mathematically cripples power; a block bootstrap on N=8 clusters is severely discrete and asymptotically invalid; BH over that base rigs the design to fail to reject | OPEN FOR ADVISOR (01B Q6; see §5) |
| G-S5 | **CRITICAL** | Data-dependent BH family size — if E1c drops out the family shrinks 3→2, violating the FDR guarantee and inflating Type I error for E1a/E1b | OPEN FOR ADVISOR (01B Q2/Q3) |
| G-S6 | MAJOR | What the paper could and could not write — a normalized "density independent of overall signal strength" claim is not available | OPEN FOR ADVISOR |

### 3.3 Seat 3 — Claude, statistical validity

| # | Sev (seat's) | Title | Disposition |
|---|---|---|---|
| S-C1 | **CRITICAL** | The D16 primary statistic is a pure population quantity, computable before A1 — and it **REVERSES** the raw result. No rule governs the reversal, and D14 and D16 contradict each other about which is the headline | OPEN FOR ADVISOR — **the single most important decision**; see §6.1 |
| S-C2 | **CRITICAL** | D16 E1c's `fiber_count < 1024` matched-non-injectivity restriction is **vacuous on the d=3 side**; the arms are compared against thresholds with different denominators | OPEN FOR ADVISOR; see §6.2 |
| S-C3 | **CRITICAL** | The D14 normalized estimand **cannot be formed for the d=3 arm** from any frozen artefact, and 01B contains no rule for obtaining it | OPEN FOR ADVISOR |
| S-M1 | MAJOR | D13's stated premise is false: 400 independent parameter draws, not 8. (And: "82% of the clustered variance is fixed-factor heterogeneity") | **DISPUTED → SETTLED, see §5.** Verdict upheld; the **82% figure NOT reproduced** |
| S-M2 | MAJOR | The design is underpowered against the effect it is testing (MDE 0.028 vs a true 0.018); the D14-mandated stratification makes it powerless (MDE 0.047 / 0.091 at 4 blocks) | OPEN FOR ADVISOR |
| S-M3 | MAJOR | Interaction saturation is not a background confound but the dominant term; stratification exposes it and cannot repair it | OPEN FOR ADVISOR |
| S-M4 | MAJOR | The BH family size is data-dependent, breaking pre-registration and creating a directional incentive; reproduced numerically | OPEN FOR ADVISOR (01B Q2/Q3) |
| S-M5 | MAJOR | At (M,K)=(5,4) `hash_shared` is not a hash — its partition is exactly the multiset-of-values partition at every frozen bucket width. **This confirms D16 E1a's collapse premise**, but for a structural reason that must be stated | OPEN FOR ADVISOR (text change) |
| S-m1 | MINOR | A1 buys nothing for the E1a/E1b primary statistic — the normalized gaps are population quantities | OPEN FOR ADVISOR (write-up) |
| S-m2 | MINOR | `fiber_count` is two different quantities under one column name (hash: `K**M`; coordinate-wise: `K**d_active`) | OPEN FOR ADVISOR |
| S-m3 | MINOR | No low-power fallback for E1a/E1b — `effective_blocks_min` exists only under E1c | OPEN FOR ADVISOR |
| S-m4 | MINOR | The "only exact arm" claim is overstated | OPEN FOR ADVISOR (text change) |
| S-m5 | MINOR | NOT_IDENTIFIED will never fire — min denominators ~4,000× the tolerance; guard correct and dormant, no change needed | **CLOSED AT A0.1** (independently corroborated by seat 4, §5 of its report, margin ≥ 5,677×) |
| S-m6 | MINOR | D14 `estimands` assigns `PRIMARY` to two different things; rename one | OPEN FOR ADVISOR (textual surface of S-C1) |

### 3.4 Seat 4 — Claude, adversarial implementation

Every row below was **executed**, not reasoned about: a mutation was applied to a repo
copy, the full 1,027-test suite was run, and the numeric effect was measured.

| # | Sev (seat's) | Title | Suite result | Disposition |
|---|---|---|---|---|
| A-C1 | **CRITICAL** | A fiber-assignment **permutation** defeats both surviving D17 gates and the whole test suite; `relative_log_gap` (the D16 primary statistic) moves 0.1564 → 0.4715 while `|prod−ref|` and `fiber_count` read clean | 1027 pass | **CLOSURE IN PROGRESS — see `S0B_FINAL_GATE_REPORT.md` for final status** |
| A-C2 | **CRITICAL** | The hash fiber cache key can collide `hash_shared` with `hash_column` (`fiber_count` 56 → 363 / 768; `pop_gap_logloss` 15× and 30× wrong) | 1027 pass | OPEN FOR ADVISOR |
| A-C3 | **CRITICAL** | The metric argument to `FIN.decompose` can be swapped; the entire finite-sample layer of every row becomes the other metric's, and no test compares a row's `representation_loss` to its `theoretical_gap` | 1027 pass | OPEN FOR ADVISOR |
| A-C4 | **CRITICAL** | 9 of 13 encoder configurations — **every supervised encoder** — are never exercised end to end; label leakage can be reintroduced into `target`/`woe` invisibly (`woe` shortfall +27%) | 1027 pass | OPEN FOR ADVISOR |
| A-C5 | **CRITICAL** | The D17 reference column can be filled from production (`ref = dict(pop)`); the D17 columns *improve* to exactly 0.0 and nothing fires, though 01B explicitly bans the derivation | 1027 pass | OPEN FOR ADVISOR |
| A-C6 | **CRITICAL** | **Defect in the shipped runner, not a mutation:** a late failure emits a DUPLICATE row for every cell already written as SUCCESS, with contradictory status. AD6's exact 182,400-row count becomes unsatisfiable | n/a — confirmed | OPEN FOR ADVISOR |
| A-M1 | MAJOR | The hash-diagnostic column-awareness flag is unpinned (`collision_count` 12→0, `occupied_buckets` 8→4) | 1027 pass | OPEN FOR ADVISOR |
| A-M2 | MAJOR | `theoretical_gap` can be written with the wrong metric (2.04× wrong on Brier rows) | 1027 pass | OPEN FOR ADVISOR |
| A-M3 | MAJOR | `roc_auc` / `pr_auc` are ungated — AUC against permuted labels passes | 1027 pass | OPEN FOR ADVISOR |
| A-M4 | MAJOR | The seed rule is single-source in **definition** only, not in **consumption** — `addendum_oof_seed(rep+1)` and `(1)` both pass | 1027 pass | OPEN FOR ADVISOR |
| A-M5 | MAJOR | The D17 harness carries its OWN hardcoded copy of the sampling rule, unpinned; `return 1` — the choice 01B declines by name — passes | 1027 pass | OPEN FOR ADVISOR |
| A-M6 | MAJOR | The D17 harness's addendum train-seed can drift, making the harness recompute a different production than the one stored | 1027 pass | OPEN FOR ADVISOR |
| A-M7 | MAJOR | The R5 status separation is convention, not a gate; and the analysis scripts A1 will reuse filter on `theoretical_gap_status`, which is a hardcoded constant | 1027 pass | OPEN FOR ADVISOR |
| A-m1 | MINOR | `den <= tolerance` → `den < tolerance` passes; no test exercises `den == tolerance` | 1027 pass | OPEN FOR ADVISOR (same line as Codex C7) |
| A-m2 | MINOR | AD4 is unfalsifiable in the addendum output — `theoretical_gap_status` is a hardcoded constant on every SUCCESS row | n/a | OPEN FOR ADVISOR |
| A-m3 | MINOR | The D17 rule whitelist does not require the rule to be a function of `scenario_id` at all; `int("0042"[-4:])` is ACCEPTED | n/a | OPEN FOR ADVISOR |
| A-m4 | MINOR | Non-SUCCESS `METRIC_UNDEFINED` rows carry `exact_or_mc="exact"` and `IDENTIFIED_EXACT` while every population value is NULL — the R4 semantic gap in a second, asymmetric form | n/a | OPEN FOR ADVISOR (backlog R4) |
| A-m5 | MINOR (§6, after the count line) | The 1.4 contention calibration and the anchor's embedded contention are the same 1.48× phenomenon; the 1.4 is applied twice | n/a | **CLOSED AT A0.1** — both directions conservative, ceiling verdict unaffected; rationale text should be corrected |

**Attacks that FAILED — recorded because failed attacks are the point.** Eleven mutations
were caught: label/feature unpairing on the n=500 arm (2 failures), `d_active=3`
substituted at the draw (22), reversing the active coordinate block (1), general
OOF→full-fit substitution (4), swapping the two D14 denominators (2), unweighted `p_y`
(12), disabling the NOT_IDENTIFIED branch (3), evaluating on the training draw (2),
conflating executed with successful rows (2), removing the replicate from the OOF seed
formula (1), amending 01B to a non-scenario rule (7). Two measurement attacks also failed:
denominator instability near 1.0e-6 (margin ≥ 5,677× over all 1,200 distinct DGPs) and the
resource-ceiling breach (uncosted population layer = 0.033 core-h, 0.17% of the ceiling).

**Backlog closures verified to bite (CLOSED AT A0.1).** R1 (3 tests fire), R9 (5 tests on
`SEED_BASE_1BD`, 2 on `OOF_BASE_1BD`, including
`test_every_one_of_the_2400_seeds_agrees_with_the_runner`), R10 (2 tests). One correction
of the A0.1 record: `test_the_pin_bites_when_the_runner_rule_moves` monkeypatches
`RUN.addendum_seed` itself and so fires by construction — it is **not** evidence about the
runner; the 2,400-seed test is.

---

## 4. Convergence — findings two or more seats reached INDEPENDENTLY

Independent convergence is stronger evidence than any single finding. The seats below did
not see each other's work, ran on different providers or in different fresh contexts, were
given different material, and used different methods.

### 4.1 THE STRONGEST — fiber-construction defects evade BOTH surviving D17 gates

**Codex C4** (CRITICAL) and **seat 4's CRITICAL-1** (CRITICAL) are **the same defect
class, found independently by two seats with different methods.**

- **Codex** found it by *reading code under a read-only sandbox, executing nothing.* Its
  construction: "a defect in `group_ids`, `hash_codes`, or `ebar_coordinatewise` swaps one
  cell from fiber A with one from fiber B. The partition membership changes and usually
  changes both population gaps, but the number of fibers remains identical." Both gates
  pass while the reported gaps are wrong.
- **Seat 4** found it by *executing a mutation battery against a repo copy.* Its
  construction: `fid = fiber_cache[key]` → `np.roll(fiber_cache[key], 1)` at
  `run_sim1b_dense_addendum.py:948`. A permutation preserves the fiber count **and the
  multiset of fiber sizes exactly**. Measured through the runner: `relative_log_gap` for
  `hash_column/B0` moves **0.1564 → 0.4715** — the D16 E1a/E1b primary statistic, wrong by
  a factor of three — with `abs_production_minus_reference_log` and `log_identity_error`
  both unchanged at ~1e-16 and `fiber_count` byte-identical. Suite: **1027 passed.**
  Independently confirmed on the D17 harness itself: `defect=fiber_permute` is detected in
  **1 of 78** d=3 cells (incidental) and **0 of 6** hash configurations at d=5, while
  `fiber_merge` — the defect the harness was designed against — is detected 78/78.

Both seats prescribe the same remedy: the gate must compare something that is **not**
invariant under relabelling. Codex asks for a canonical partition fingerprint built by an
independent implementation; seat 4 points out that the harness **already computes** the
column that would catch it — `stored_abs_diff_log_mc` — and that it is simply excluded
from the pass criterion at `scripts/s0b_reference_gap_check.py:459`
(`ok = (n_out == 0) and (fc_bad == 0)`).

This defect class is the reason for the backlog's R2 amendment history: R2 added the
second gate after the advisor's named identity columns were shown not to gate at all. Two
seats have now shown the second gate is also insufficient. **A third detector is being
implemented concurrently — see `S0B_FINAL_GATE_REPORT.md` for its final status.**

### 4.2 D17's independence is not enforced anywhere

- **Codex C1**: the checker can report `RESULT=PASS` on a checker-local recomputation with
  `--stored` omitted, i.e. without ever examining a runner-produced `fiber_count` or
  population gap. "A passing D17/AD1/AD2 verdict is attributed to the runner although no
  runner-produced value was examined."
- **Seat 4 CRITICAL-5**: `ref = CORE.reference_gap_report(...)` → `ref = dict(pop)` makes
  `abs_production_minus_reference_log` go 2.22e-16 → **exactly 0.0**. The D17 columns
  *improve*. 01B `rulings.D17.persisted_columns.forbidden` explicitly bans this derivation
  and it is enforced by nothing.
- **Seat 4 MAJOR-5 / MAJOR-6**: the harness holds its own hardcoded sampling rule and its
  own train-seed reference, both unpinned. Codex's C1 remedy ("make `--stored` mandatory")
  and seat 4's MAJOR-6 ("the harness would be comparing two different experiments while
  reporting agreement as if it were a defect signal") are the same concern from two sides.

Two seats, two methods, one conclusion: **D17 currently certifies its own copy.**

### 4.3 Typed-row accounting does not guarantee one row per attempted cell

Two seats reached this from opposite directions and neither knew of the other's case.

- **Codex C2 + C3** — rows can go **MISSING**: a worker/pool failure is converted to
  `results[scenario_id] = []` and a header-only part file (`_s1_parallel.py:74-85`), so all
  3,800 rows of a scenario vanish and the restart skips it; and several setup/fatal paths
  (`BaseException`, pre-`try` setup, an exception inside `_typed_failure_rows` itself)
  escape typed accounting entirely.
- **Seat 4 CRITICAL-6** — rows can be **DUPLICATED**: the config-level `except Exception`
  at `run_sim1b_dense_addendum.py:1040-1052` re-emits a `TRAINING_FAILURE` row for every
  `lrn × metric` including those already appended as SUCCESS. Executed demonstration: 6
  rows for 4 attempted cells, the same primary key twice with contradictory status.

Both conclude the same thing: **AD6's "executed rows == 182,400 exactly" is not
guaranteed** in the presence of any failure. Seat 4 adds that `_s1_parallel.run_parallel`
does no de-duplication (verified), which is precisely Codex's C5 ("existing or malformed
part files are trusted as completed work").

### 4.4 8 blocks / 7 df cannot support the claims — reached from text and from measurement

- **Gemini S4** (CRITICAL) reached it **from the design documents alone**, with no
  repository access: "a block-resampling bootstrap on N=8 clusters is severely discrete and
  asymptotically invalid… with 7 df the cluster-robust t-distribution is exceedingly
  fat-tailed… realistic power to detect anything short of a massive effect size is near
  zero… the design is rigged to fail to reject the null."
- **Seat 3 MAJOR-2** reached it **by computing the exact population quantities**:
  `E1a normalized: n_blocks=8, between-block SD 0.02849, SE 0.01007, MDE = 0.02811` against
  a true effect of **0.018** — "the test cannot detect the effect that exists, in either
  direction." At 4 blocks (the mandatory stratified analysis) the MDE rises to 0.047 /
  0.091, larger than any effect in the design.

A model that saw only prose and a model that ran the algebra arrived at the same verdict.

### 4.5 The BH family size is data-dependent, and that breaks the correction

- **Gemini S5** (CRITICAL), from the text: "if E1c drops out… the family size dynamically
  shrinks from 3 to 2. Adjusting p-values based on a data-dependent family size violates
  the theoretical guarantees of the FDR procedure."
- **Seat 3 MAJOR-4** reproduced it numerically: `p = (0.030, 0.040, 0.600)` gives
  `m=3 → q=(0.060,0.060,0.600)`, **0 confirmed**; `m=2 → q=(0.040,0.040)`, **2 confirmed**.
  Dropping a *null* third hypothesis flips both surviving clauses. Seat 3 adds the deeper
  point: the problem is not the strictness of `effective_blocks_min` but the family size
  being data-dependent **at all**, and it is correlated with block composition because
  `marginal` is a block-key factor and drives tie frequency.

Seat 3 explicitly records that it **reproduced the other seat's coupling**.

### 4.6 Normalization does not remove the signal-strength confound

- **Gemini S2** (MAJOR), analytically: "because the DGP passes the linear predictor through
  a non-linear logistic link, increasing the signal variance pushes the probabilities into
  the compressed tails of the sigmoid. Consequently the *fraction* of signal lost by a
  fixed partition is not invariant to the total signal strength."
- **Seat 3 Q2**, by measurement: the signal-matched counterfactual (raise τ at d=3 by
  bisection until `sd(eta)` matches the d=5 arm) leaves a residual confound of
  **20–170% of the normalized estimate** depending on encoder. Verdict: "partial
  neutralisation — directionally reliable, quantitatively not."

**Both seats agree D14's "sensitivity analysis" status is the right one** and that the
"must not be described as removing confounding" wording should stay. Seat 3 recommends the
measured numbers be put into the freeze so the caveat is quantitative rather than
rhetorical.

### 4.7 Interaction saturation: stratification is necessary but not sufficient

- **Gemini S3** (MAJOR): the `interaction_pairs=3` stratum "is hopelessly confounded: it
  conflates the change in dimensionality with a 70% drop in interaction saturation and a
  structural shift in interaction placement (forcing coordinate 0 into every pair)."
- **Seat 3 MAJOR-3**, measured: `hash_column B0` pooled −0.04052, `n_int=0` stratum
  **−0.00220 (a null)**, `n_int=3` stratum **−0.07884, t=−4.39**. "The pooled number is an
  average of a null and a large effect — it describes neither."

Both prescribe the same minimum: restrict clean dimensionality claims to
`interaction_pairs = 0`. Seat 3 adds the priced alternative (`interaction_pairs = [0, 10]`
at d=5, saturation-matched, ~1.5× core-hours, still inside the 20-hour cap) and the
uncomfortable corollary that `interaction_pairs = 0` is also the stratum where E1a's effect
is least distinguishable from zero.

### 4.8 The seed rule is single-source in name only

Three independent surfaces of one claim, from two seats:
- **Codex C8** (MINOR): `scripts/s0a_addendum_microbenchmark.py:67,71` still holds a private
  `SEED_BASE_1BD` / `addendum_seed`; AD15's literal "everything else imports it" is not met.
- **Seat 4 MAJOR-4**: the rule is single-source in **definition** but not in
  **consumption** — `addendum_oof_seed(rep + 1)` and `addendum_oof_seed(1)` both pass 1027
  tests and change every supervised encoder's codes (+14% on `target`/logloss shortfall).
- **Seat 4 MAJOR-5**: `scripts/s0b_reference_gap_check.py:160` is a *second* hardcoded
  implementation of `reference_replicate`. The A0.1 implementation report's claim "there is
  no second copy of the rule to drift from" is true of the runner and **false of the
  harness**.

### 4.9 The D14 tolerance boundary

- **Codex C7** (MINOR): 01B freezes `|denominator| < 1e-6`; the code uses `den <= tolerance`.
  A denominator exactly at `1e-6` is suppressed contrary to the frozen rule.
- **Seat 4 MINOR-1**: `den <= tolerance` → `den < tolerance` passes 1027 tests; no test
  exercises `den == tolerance` exactly.

Same line, two readings: Codex says the code deviates from the frozen rule; seat 4 says
nothing pins either version. Both are true.

---

## 5. CONTRADICTION — where seats disagreed, and what settled it

### 5.1 The load-bearing contradiction: 8 independent parameter draws, or 400?

This is the most consequential item in the document, because it corrects a fact the
advisor was given and **accepted as binding ruling D13**.

**The two positions.**

| | Position | Held by | Stated evidence |
|---|---|---|---|
| **A** | The DGP parameters are drawn **once per block** and reused across that block's 50 replicates, so there are exactly **8 independent parameter draws**. Inferential unit = the block; 8 units; **7 df**; block-resampling bootstrap. | The **Phase A0 council record**, recorded as **CONFIRMED** (`S0A_ADDENDUM_COUNCIL_REVIEW.md:62`, C2 row), carried into `01A_ADDENDUM_PROTOCOL_FREEZE.yaml:362-366` and `:411-417` and the runner docstring, and **ACCEPTED by the advisor as binding D13**. Gemini S4 reasoned within this premise and attacked its consequences. | `df[(df.M==5)&(df.K==4)].seed.nunique() == 400 == 8 blocks × 50 replicates` |
| **B** | Parameters are drawn **afresh for every replicate**. There are **400 independent parameter draws per arm**. | **Seat 3 (Claude, statistical validity), MAJOR-1** | `addendum seeds rep 1/2/3 in one block: [2149762001, 2149762002, 2149762003] distinct; max\|a(rep1) − a(rep2)\| = 2.2953` |

**How it was settled: by direct investigation of the generating code, not by weighing
opinions.** The full investigation is `FACT_BLOCKS_VS_DRAWS.md` — it reads the generating
code, regenerates the parameters, and re-inspects the frozen twin. No addendum cell was
executed and nothing was written into the repository.

**VERDICT: Position B is correct on the factual question. Parameters are drawn afresh per
replicate. D13's stated premise is FALSE.**

**The deciding code path.**

| file:line | what it establishes |
|---|---|
| `scripts/run_sim1b_dense_addendum.py:316-327` `addendum_seed()` | `seed = 2_000_000_000 + 1000*(blake2b(repr(block))%1e6) + int(replicate)` — **the replicate is added into the seed.** One seed per (block, replicate). |
| `scripts/run_sim1b_dense_addendum.py:389-395` `addendum_scenarios()` | each scenario carries `seeds=[addendum_seed(blk, r) for r in 1..50]` — 50 distinct seeds per scenario. |
| `scripts/run_sim1b_dense_addendum.py:866` | `for rep, seed in enumerate(seeds, 1):` — the replicate loop. |
| **`scripts/run_sim1b_dense_addendum.py:871-872`** | `prm = CORE.draw_params(M, K, marginal, tau, n_int, de, seed, d_active=5)` — **`draw_params` is called INSIDE the replicate loop, with the replicate-varying seed. This is the decisive line.** |
| `src/ct2i_benchmark/simulations/sim1_core.py:132-153` `draw_params()` | `rng = np.random.default_rng(seed)`; `a = rng.standard_normal((d,K))`; one `rng.standard_normal((K,K))` per interaction pair. A different seed gives a different `a` and `b`. |
| `src/ct2i_benchmark/simulations/sim1_core.py:471-482` `dgp_block_seed()` | the frozen d=3 arm uses the identical construction — same conclusion for the partner arm. |
| **`tests/test_a0_dense_addendum_properties.py:437-443`** `test_replicate_still_varies_the_draw` | **the repository's OWN frozen test already asserted `not np.array_equal(p1.a, p2.a)` for replicates 1 and 2 of the same block. The codebase already knew Position A's premise was false.** |
| `tests/test_a0_dense_addendum_properties.py:415-423` `test_parameter_draw_identical_across_delta_eta` | asserts `array_equal` across the 3 `delta_eta` levels at fixed (block, replicate) — this, and only this, is what the block key's exclusions buy. |

The prose that produced Position A is a **docstring, not a computation**:
`scripts/run_sim1b_dense_addendum.py:305-313`.

**The measured evidence** (`FACT_BLOCKS_VS_DRAWS.md` §4, probe
`scratchpad/probe_params.py`, which imports the production `addendum_block` /
`addendum_seed` and asserts them equal to the transcribed rule):

```
25 within-block replicate pairs across 5 distinct blocks (both marginals, both taus,
both interaction counts), pairs (1,2), (1,3), (2,3), (1,50), (25,26):

  MIN over all within-block replicate pairs of max|da| = 1.5211429810022610
  MAX over all within-block replicate pairs of max|da| = 4.4900162000102508
  pairs with max|da| EXACTLY 0.0 : 0 / 25

distinct blocks                : 8
distinct seeds (8 x 50)        : 400
distinct (a,b) byte signatures : 400      <- 400 seeds, 400 distinct draws, no reuse
distinct scenarios             : 48

what the block key DOES buy (80 cells, all 8 blocks):
  max|a| and max|b| difference across delta_eta  : 0   (exactly 0.0: True)
  max seed difference across n_train levels      : 0   (n_train is not in the seed at all)
```

`01B_ADDENDUM_ADVISOR_RULINGS.yaml` AMENDMENT-3 records an expanded sweep over **56**
within-block replicate pairs spanning **all 8** blocks: range 1.5211429810022610 to
4.5610643088552312, **exactly 0.0 in 0 of 56 pairs**.

**D13's own cited evidence refutes D13.** The sentence offered in support of "only 8
draws" is `seed.nunique() == 400`. That is a count of **400 distinct parameter draws**. The
A0 evidence line was read backwards. Confirmed on the frozen twin
(`scratchpad/probe_twin.py`, read-only):

```
rows = 182400   seeds = 400   replicates = 1..50   scenarios = 48
distinct blocks = 8;  seeds per block = 50 for every block
max distinct seeds within (block, replicate) = 1
(seed - replicate) has exactly 1 distinct value within every block   <- seed = f(block) + replicate
recomputed dgp_block_seed('1B', (5,4,'uniform',0.5,0), r) == frozen seed for r = 1,2,3
```

**What survives, and what does not.**

| statement | true? |
|---|---|
| the block key excludes `delta_eta` and `n_train` | YES |
| therefore the 6 scenarios in a `(block, replicate)` share one parameter draw | YES, measured exactly 0.0 |
| therefore the 48 scenario-level means are not 48 independent observations | YES — **this narrow A0 finding stands** |
| therefore there are only 8 parameter draws | **NO — there are 400** |
| therefore the inferential unit is the block, with 7 df | **NO — it does not follow** |
| `seed.nunique() == 400` supports "only 8 draws" | **NO — it refutes it** |

**The correct inferential unit.** The independent random unit is the parameter draw,
indexed by `(block, replicate)`: **400 per arm**, cluster size 6. The 8 blocks are a
complete, exhaustively enumerated 2×2×2 factorial of **fixed** design factors
(`run_sim1b_dense_addendum.py:277-279`) — not a random sample from a population of blocks.
Between-block spread is designed heterogeneity, not sampling error. Treating `marginal`,
`tau`, `interaction_pairs`, `delta_eta`, `n_train` as fixed effects gives
**df ≈ 400 − 8 = 392 per arm, not 7.**

This is the A0 council's **own** argument applied consistently.
`S0A_ADDENDUM_COUNCIL_REVIEW.md:229` says, of the 48-scenario denominator: *"`sd` across a
fixed, exhaustively enumerated factorial grid is designed heterogeneity, not Monte Carlo
error; calling it MCSE mislabels it."* That sentence is correct — and it applies verbatim
to the 8 block means. **D13 rejected the mislabelled denominator at one level of the grid
and then adopted the identical mislabelled denominator one level up.**

**Direction of the error.** D13's SE is *conservative in magnitude* for the fixed-grid
estimand. But conservatism is not harmless here: D16's E1 clauses are **one-sided greater**
tests, so an inflated SE makes a **null** outcome spuriously easy, and D16's outcome
classifications turn null outcomes into reported conclusions. `SE(400 draws)` is 10–20×
smaller than `SE(8 blocks)`; D13 discards roughly 385 df of real information.

**This changes no frozen number.** It is an inference-scheme defect only. No raw result
changes, no cell needs re-running, no manifest is touched.

**Note on Gemini S4.** Gemini reasoned *within* Position A — it was given 01A and 01B,
which both state the false premise, and it could not read the code. Its conclusion (8
blocks / 7 df cannot support the claims) is therefore **not refuted** by the settlement;
it is reinforced from the opposite side. Gemini said 7 df is too few for the claims; the
investigation says 7 df was never the right number.

### 5.2 A figure inside the winning position that could NOT be reproduced

Seat 3's MAJOR-1 carried a supporting statistic alongside its verdict:

```
share of the D13 clustered variance that is condition heterogeneity = 81.7%
```

**This number could not be reproduced.** `FACT_BLOCKS_VS_DRAWS.md` §6 measured the
between-block share on the frozen twin and obtained **14.9% – 56.8%**, depending on
encoder, learner and quantity:

```
encoder/learner       quantity             between-block share   SE(8 blk)   SE(48 scen)  ratio
target /logistic      representation_loss        17.6%           1.349e-05    1.240e-05   1.09
target /logistic      total_excess_risk          56.8%           5.719e-03    2.929e-03   1.95
label  /logistic      total_excess_risk          44.8%           6.675e-03    3.847e-03   1.73
hash_shared/lightgbm  representation_loss        52.9%           7.812e-03    4.144e-03   1.89
onehot /mlp           total_excess_risk          14.9%           2.837e-03    2.835e-03   1.00
```

The seat presumably measured 81.7% on a different quantity or on its exact population
probe rather than the frozen twin; the investigation did not locate a quantity that
reproduces it.

**Recorded plainly, without disparagement: the seat's VERDICT was right — parameters are
drawn per replicate, there are 400 draws, D13's premise is false. That particular number
was not verified. The 82% figure must not be reused in the manuscript, the freeze, or a
report without provenance.** The *direction* of the argument — that a large share of the
block-clustered variance is fixed-factor heterogeneity rather than sampling error — is
confirmed by the table above.

A second number from the A0 record needs the same treatment: the claim that *"one seat
measured a 2.4× understatement"* for `sd/sqrt(48)`. The measured `SE(8 blk)/SE(48 scen)`
ratios on the frozen twin are **1.00–1.95**, and by the variance identity the same
clustering that inflates the SE 1.9× is itself inflated by the fixed-factor component. That
number also needs re-derivation under the corrected unit.

### 5.3 A secondary disagreement: is the resource projection safe?

| | Position | Held by |
|---|---|---|
| | The 8.573 core-hour projection "is arithmetically consistent but **not a defensible upper bound**" — MAJOR. No quantified bound for restart waste, full parallel I/O, or the cost tail; "a single rerun/recovery can readily invalidate a CPU budget." | **Codex C6** |
| | "I could not find an assumption that breaks the 20 core-hour ceiling." The uncosted population layer measures **0.033 core-hours = 0.17% of the ceiling**; the d-ratio would have to be wrong by **2.34×** against a 95% CI of [1.0131, 1.0364]. "42.87% is if anything pessimistic." | **Seat 4, §6** |

**These are not contradictory facts; they are different questions.** Codex objects to the
projection's **epistemic status** — a forecast presented as a ceiling guarantee, with no
failure/retry model. Seat 4 measured the **specific uncosted terms** Codex could not
measure (it was forbidden to execute) and found them immaterial. Codex itself recorded this
under "COULD NOT VERIFY": *"I could not validate real A1-scale CPU, memory, multiprocessing
reliability, or parts-file I/O because no A1 output exists and execution was prohibited."*

Both remedies are compatible and both should be taken: state the number as an **estimate**
rather than a ceiling guarantee, budget an explicit restart/failure reserve, and enforce a
CPU stop rule during A1 (Codex); and correct the rationale text so the 1.4 calibration is
described as pure retained margin worth 2.45 core-hours rather than as an independent
correction applied on top of an anchor that already contains the same 1.48× contention
(seat 4, MINOR-5). The ceiling verdict itself is unaffected.

### 5.4 Two apparent disagreements that are not disagreements

- **Is D14 correctly implemented?** Codex: "the substantive D14 computation otherwise checks
  out." Seat 3 CRITICAL-3: "the D14 normalized estimand cannot be formed for the d=3 arm."
  Both are true. Codex verified the **d=5 computation**; seat 3 found that the **d=3 side of
  the contrast** has no denominators in any frozen artefact and no rule for producing them.
  Different halves of the same estimand.
- **Is the E1a B0/B1/B2 collapse right?** Seat 3 MAJOR-5 **confirms D16 E1a's collapse
  premise** — the partitions really are identical (verified as partitions, not labels;
  relative gaps agree to 2.2e-14 over 8 blocks × 3 deltas × 4 replicates × 2 d levels) —
  while simultaneously saying the multiplicity correction around it is wrong for a different
  reason (data-dependent family size). Confirming one clause and vetoing another is not a
  contradiction.

---

## 6. What the council could NOT settle — decisions reserved to the advisor

### 6.0 The six open questions `01B_ADDENDUM_ADVISOR_RULINGS.yaml` now carries

`advisor_confirmation_requested` is marked
`status: OPEN_ADOPTED_READINGS_NOT_SETTLED_DECISIONS`, `count: 6`, `highest_priority: Q6`.

| Q | Question | Why it is open |
|---|---|---|
| **Q6** | **WHICH INFERENTIAL UNIT GOVERNS — 8 blocks / 7 df as ruled, or 400 parameter draws / df ≈ 392 as measured?** `status_of_D13: PREMISE_REFUTED_ADVISOR_RULING_REQUIRED`, `severity: BLOCKS_A1_INFERENCE` | §5.1. **The only question here that blocks A1 inference outright, and the only one about a factual premise rather than a value the advisor left blank.** Q1–Q5 can be answered after A1 without rerunning anything; Q6 cannot — it determines which numbers A1 computes. If the advisor keeps 7 df it must be re-justified as a deliberate **estimand choice** (generalizing to a population of conditions beyond the frozen grid), which is his to take, and not as a fact about the parameter draws. |
| Q1 | In which phase does the D17 624-cell reference check run? | Phase-ordering, unresolved since the A0.1 opening |
| Q2 | `effective_blocks_min = 4` — the advisor wrote "too few independent blocks" with no number | A0.1 froze a number he did not write; Gemini S5 and seat 3 MAJOR-4 both show the number is coupled to the BH family size |
| Q3 | A FOURTH outcome class (`INCONCLUSIVE_REPORTED_IN_FULL`) was added to the advisor's three | Seat 3 finds the class **sound** but notes its worked example is the mirror image of the case that will actually occur (§6.1), so as motivated it will probably never fire while the case that needs a name has none |
| Q4 | "Materially directionally inconsistent" was quantified (opposite signs AND both \|estimates\| > 1e-6) | A0.1 quantified a phrase the advisor left qualitative |
| Q5 | The two D17 columns the advisor named do not gate (AMENDMENT-1) | **This corrects the advisor's D17 as written.** Backlog R2: injected defects left `identity_error` at 5.4e-15 UNCHANGED while production was wrong by 1.083e-02. Two seats have now shown the *replacement* gate is also insufficient (§4.1) |

### 6.1 THE SINGLE MOST IMPORTANT SCIENTIFIC DECISION — which scale is the headline finding

**The two readings point OPPOSITE WAYS, and both are already determined.** Seat 3 computed
the D16 primary statistics exactly, before A1, because they are pure population quantities
requiring no simulation (`run_sim1b_dense_addendum.py:929-935, 877` — no learner, no
training sample, no evaluation sample enters them):

```
E1a hash_shared  PRIMARY normalized log        est = -0.01815  SE 0.01007  t = -1.80  blocks>0: 1/8
E1a hash_shared  supporting normalized Brier   est = -0.01967  SE 0.01037  t = -1.90  blocks>0: 1/8
E1a hash_shared  RAW log-loss contrast         est = +0.00919  SE 0.00198  t = +4.64  blocks>0: 8/8
E1b hash_column  PRIMARY normalized (mean B0,B1) est = -0.05182 SE 0.01961 t = -2.64  blocks>0: 2/8
E1b hash_column  supporting normalized Brier   est = -0.05349  SE 0.01967  t = -2.72  blocks>0: 2/8
E1b hash_column  RAW log-loss contrast         est = +0.00129  SE 0.00209  t = +0.62  blocks>0: 6/8
E1b secondary B2                               est = -0.07253  SE 0.00733  t = -9.90  blocks>0: 0/8
```

- **Raw scale:** hash_shared **+0.0092, t = +4.64, positive in 8/8 blocks** — E1's raw
  prediction confirmed and well powered (observed 0.0092 against MDE 0.0055).
- **Normalized scale:** **−0.0182** for E1a and **−0.0518 (t = −2.64)** for E1b. Under
  `01B rulings.D16.outcome_classifications`, a non-positive primary normalized log-loss
  contrast is **sufficient** for NOT_SUPPORTED. **E1a and E1b are NOT_SUPPORTED before a
  cell is run.**

**The protocol gives two contradictory instructions about which is the finding.**
`01B rulings.D14.normalized_analysis_status.label: SENSITIVITY_ANALYSIS` — the advisor's own
D14 text says the normalized analysis "is a sensitivity analysis and must not be described
as fully removing confounding". `01B rulings.D16.clauses.E1a.primary_statistic` makes that
same quantity **the sole basis of the verdict**. `D14.estimands` assigns `PRIMARY` to two
different things. **Nothing in either file resolves which one is the manuscript's headline
when they disagree — and they will disagree.**

Nor is the reversal flagged: `materially_directionally_inconsistent_definition` compares
**normalized log vs normalized Brier only**, and those two agree here (both negative). The
reversal that actually occurs — **raw positive, normalized negative** — is not a defined
inconsistency, produces no flag, and no outcome class names it.

**The scientific content of the reversal is large:** once the gap is expressed as a
fraction of the signal available in X, the dense arm loses a *smaller* fraction — i.e. the
entire raw d=5 excess representation loss is attributable to the C1 signal-strength
confound and then some. That is close to the opposite of E1's mechanism story, and it is
publishable under E4.

**What the advisor must decide, and why it cannot wait.** If A1 runs first, the acceptance
report prints "E1a NOT_SUPPORTED, E1b NOT_SUPPORTED" while the validation report separately
prints a raw contrast at t = +4.6, and the choice of headline is then made **with the
numbers in hand** — the exact failure the freeze apparatus exists to prevent.

Seat 3's recommendations, offered for decision and not as a fait accompli:
(a) pick ONE of raw / normalized as the headline and the other as the companion, and write
the choice into 01B; (b) add a fifth outcome annotation `SCALE_REVERSAL` firing when the raw
and normalized log-loss contrasts have opposite signs and both exceed `positive_gap_min`,
mandating that both be quoted in the same sentence; (c) record in 01B that these values were
computed exactly at A0.1, so the run cannot be read as having discovered them —
pre-registering a known value is more honest than pretending the run is blind.

Seat 3's own opinion, explicitly offered as opinion: the normalized reading is the more
defensible one, but it is also the one the design cannot power (MDE 0.028 against a true
0.018), **so whichever is chosen, the power statement has to go in the same sentence.**

### 6.2 E1c's `fiber_count < 1024` restriction is vacuously true on the d=3 side

`01B rulings.D16.clauses.E1c.primary_analysis_restriction` requires `fiber_count < 1024` on
**both** sides of each matched pair, sourced to `01A exactness.state_space = 4**5 = 1024`.
At d=3 the non-hash encoders' `fiber_count` is computed on the **active-block** enumeration
(`4**3 = 64` cells) — `run_sim1b_finite.py:190-192`. Measured on the frozen
`05b_SIM1B_REPLICATE_RESULTS.parquet` (M=5, K=4, SUCCESS, logloss):

```
encoder=count  fiber_count: min 24, max 64, 5 distinct values {24, 32, 36, 48, 64}, 9600 rows
  fraction with fiber_count < 1024 : 1.000     <-- the D16 restriction: 100%, VACUOUS
  fraction with fiber_count <   64 : 0.1375    <-- the CORRECT d=3 injectivity test
  by marginal x n_train (counts of fiber_count):
                    24    32    36    48    64
  uniform  500      12    24   156   744  1464
  uniform  5000      0     0    24   300  2076
  zipf     500       0     0     0    60  2340
  zipf     5000      0     0     0     0  2400
```

**No d=3 condition would ever be excluded.** Two consequences: (i) the stratum is selected
by the d=5 side alone, so the contrast is not matched on the property it claims to match on;
(ii) under the *correct* threshold (`< 64` at d=3) the **entire zipf × n_train=5000 half is
empty (0/2400)** and zipf × n_train=500 retains 60/2400. Since `marginal` is a block-key
factor, a correct restriction removes most or all of the four Zipf blocks, leaving **≈ 4
effective blocks — landing exactly on the frozen `effective_blocks_min = 4` boundary**, which
then decides the BH family size (§4.5).

The non-emptiness verification quoted in support (`01B … non_emptiness_verified`, 01A:480,
{576, 768, 1024} / {768, 1024}) is a **d=5** sweep. It establishes nothing about the d=3
arm and is presented as though it did.

Proposed replacement, for the advisor's decision: a per-arm rule — non-injective means
`fiber_count < K**d_active` on the arm's own enumeration (`< 64` at d=3, `< 1024` at d=5) —
plus an explicit statement that hash encoders' `fiber_count` is on the full `K**M` space in
both arms and is therefore on a **different denominator** from the coordinate-wise encoders'.
That column is currently two different quantities under one name (seat 3 MINOR-2, seat 3
recommends a `fiber_count_space` column). The non-emptiness check must be re-run against the
corrected rule and the surviving block count recorded **before** A1.

### 6.3 The remaining scientific decisions reserved to the advisor

| Decision | Position(s) put to him |
|---|---|
| **How the d=3 normalized denominators are produced** (seat 3 CRITICAL-3) | `05b` carries no `p_y` / `entropy_y` / `var_eta_x`; `H(Y) − R_log*(X)` and `Var{eta(X)}` are **undefined on the d=3 side**, so the primary estimand of the whole amendment does not exist for one of its two arms. Left unfrozen, an implementer will improvise at A1. Proposed: freeze an explicit d=3 population-layer recomputation from `dgp_block_seed("1B", …)` at `d_active=3`, persisted as a new sibling CSV (touches no protected raw file), plus an acceptance check that the recomputed exact d=3 representation loss agrees with the stored MC value within `max(5·mcse, 1e-4)` — a free, genuinely independent validation of the frozen arm. Cost: seconds. Also to decide: the d=5 numerator is exact while the d=3 numerator is Monte-Carlo (measured discrepancy ~1× mcse, 4.7e-5, negligible against a 1.8e-2 effect) — fixable, but it must be **decided**, not left to A1. |
| **Whether the "dense-signal stress test" licence is adequate** (Gemini S1, CRITICAL) | Gemini holds the reframing "actively misleading" because "dense" directs the reader to dimensionality while concealing the increase in total signal magnitude — "the exact same increase in representation loss could be generated by a single-coordinate signal whose variance was simply scaled up by the same factor." Seat 3 holds the *framing* honest but the *inference licence* not yet closed. |
| **Interaction saturation: demote or extend** (Gemini S3, seat 3 MAJOR-3) | (a) free: demote every `interaction_pairs = 3` comparison to descriptive and let `interaction_pairs = 0` carry the inferential weight — the only comparison in the current design that is confound-clean on C2 and C3, and also the stratum where E1a's effect is least distinguishable from zero; or (b) take the option the preflight already priced: `interaction_pairs = [0, 10]` at d=5, saturation-matched, ~1.5× core-hours, still inside the 20-hour cap. |
| **BH: fix the family or drop it** (Gemini S5, seat 3 MAJOR-4) | Fix `m = 3` unconditionally so E1c contributes its p-value even when reported descriptively; or drop BH entirely, since E1a/E1b/E1c are explicitly *not* acceptance criteria and *not* validity gates — three pre-registered expectations that gate nothing do not need FDR control. Either way, **the family size must not be a function of the data.** |
| **Whether to state the MDE beside every reported quantity** (seat 3 MAJOR-2) | D13's `mandatory_disclosure_per_reported_quantity` currently demands effective n but not what that n can detect. The mandatory stratified analysis at 4 blocks has MDE 0.047 / 0.091, larger than any effect in the design — it can by construction never support a claim, and should be declared descriptive in advance. |
| **How `hash_shared` is described** (seat 3 MAJOR-5) | At (M,K)=(5,4) it is an exact bag-of-values (exchangeability) encoder — its 56-class partition equals the multiset-of-values partition and would be B-invariant for any B ≥ 4. Describing its ~85% relative representation loss as a *hashing* result invites the referee question "what is the bucket width doing?", whose answer is "nothing, verifiably". |
| **R4 semantic gap: `METRIC_UNDEFINED` rows** (backlog R4, seat 4 MINOR-4) | 01A inherits "non-SUCCESS cell carries NULL metrics" while `run_sim1b_finite.py` stamps `METRIC_UNDEFINED` on a row that KEEPS its metrics. Seat 4 found a second, asymmetric form: on a single-class evaluation sample the SAME cell yields `METRIC_UNDEFINED` for logloss and `SUCCESS` with full metrics for brier, purely because `roc_auc` is a log-loss-row side metric. |
| **The D14 tolerance boundary** (Codex C7, seat 4 MINOR-1) | Change the code to the frozen strict `abs(den) < tolerance`, or amend 01B to `<=`. One or the other, before A1. |
| **The resource number's status** (Codex C6, seat 4 §6) | Estimate or ceiling guarantee — see §5.3. |
| **Reporting the two facts that change how A1 must be written up** (seat 3 m5, seat 4 §5) | The D14 NOT_IDENTIFIED branch **cannot fire** in this design (margin ≥ 5,677× over all 1,200 distinct DGPs), so AD4 and the NOT_IDENTIFIED apparatus are guarantees, not observations; and AD4 is unfalsifiable in the addendum output because `theoretical_gap_status` is a hardcoded constant on every SUCCESS row. Both should be stated in the A1 write-up rather than discovered later. |

### 6.4 What the council explicitly could NOT check

Recorded so that nothing is mistaken for verified.

- **Codex:** did not run the test suite, simulation, checker, addendum cells or any probe
  (read-only / no-compute instruction); could not validate real A1-scale CPU, memory,
  multiprocessing reliability or parts-file I/O because no A1 output exists; did not inspect
  the private scratchpad probe files cited by the resource CSV.
- **Gemini:** could not read the repository at all (§1.3); ruled only on the pasted design
  documents.
- **Seat 3:** whether the not-yet-written A1 analysis code will compute the d=3
  `relative_log_gap` at all ("a *specification* gap; I cannot test code that does not
  exist"); E1c's realised **d=5** fiber counts (the count encoder is fitted on training
  samples); the block-resampling bootstrap implementation (checked the t-interval arithmetic
  only); every non-statistical D15/D17/D18 item.
- **Seat 4:** ran no addendum cell; all probes were stamped
  `NON_FROZEN_PROBE_NOT_AN_ADDENDUM_RESULT`; the only non-probe execution was
  `s0b_reference_gap_check.py --arm d3_frozen` on the pre-existing frozen d=3 twin, in a
  scratchpad copy, writing to the scratchpad.

---

## 7. Seat 1 — CODEX, `gpt-5.6-terra` (implementation / numerical verification) — VERBATIM

The capture below is reproduced complete and unedited, including the seat identity block,
the exact dispatch command, the exact prompt sent, and the seat's output.

# COUNCIL SEAT 1 CAPTURE — CODEX (implementation / numerical verification)

Captured by: Claude (host seat), Phase A0.1 council dispatch
Capture date: 2026-08-24

## Seat identity

- Role assigned by advisor: "Codex for implementation/numerical verification"
- CLI: `codex exec` — codex-cli 0.147.0
- Model id: gpt-5.6-terra (the model codex-cli 0.147.0 dispatches to; see PROVIDER_INVOCATION.md)
- Sandbox: `--sandbox read-only` (reviewer cannot write)
- Working directory: /Users/Eric/Desktop/114/ct2i-benchmark
- Wall-clock: 159s (start epoch 1787582491, end epoch 1787582650)
- Exit code: 0
- ZERO addendum cells run; reviewer was explicitly forbidden to execute the simulation.

## EXACT command used

```
cd /Users/Eric/Desktop/114/ct2i-benchmark
codex exec --sandbox read-only --skip-git-repo-check "$(cat <PROMPT_FILE>)" </dev/null
```

where `<PROMPT_FILE>` is `/private/tmp/claude-501/-Users-Eric-Desktop-114----code-result/e234d5a4-799b-49a4-b4f1-9d19ec0e4653/scratchpad/prompt_codex.txt`, reproduced verbatim in the next section.

## Material the seat was given

Codex read the repository directly under `--sandbox read-only`. It was given PATHS, not pasted text:

- simulation-results-ct2i/01B_ADDENDUM_ADVISOR_RULINGS.yaml
- simulation-results-ct2i/S0B_ADVISOR_RULING_IMPLEMENTATION_REPORT.md
- simulation-results-ct2i/S0B_RUNNER_TEST_REPORT.md
- simulation-results-ct2i/S0B_REFERENCE_IMPLEMENTATION_TEST_REPORT.md
- simulation-results-ct2i/S0B_RESOURCE_CONFIRMATION.csv
- simulation-results-ct2i/RAW_FREEZE_MANIFEST_ADDENDUM.json
- scripts/run_sim1b_dense_addendum.py
- scripts/s0b_reference_gap_check.py
- tests/test_a0_dense_addendum_properties.py
- tests/test_a1_runner_smoke.py
- tests/test_a0_1_reconciliation.py
- (context) simulation-results-ct2i/01A_ADDENDUM_PROTOCOL_FREEZE.yaml
- (context) simulation-results-ct2i/S0A_ADDENDUM_PREFLIGHT_REPORT.md
- (context) src/ct2i_benchmark/simulations/sim1_core.py
- (context) scripts/run_sim1b_finite.py

It additionally opened, on its own initiative, `scripts/_s1_parallel.py` and `scripts/s0a_addendum_microbenchmark.py`.

## PROMPT SENT (verbatim)

```
You are the CODEX seat on an academic review council for an MSc-thesis simulation package.
Your assigned role, set by the human advisor, is IMPLEMENTATION AND NUMERICAL VERIFICATION.
You are READ-ONLY. Do not write, create, or modify any file. Do not run the simulation.
Do NOT execute any addendum cell, any full run, or anything that would consume compute on the
real experiment. Reading files and running trivial read-only inspection is fine.

REPO ROOT: /Users/Eric/Desktop/114/ct2i-benchmark  (you are already in it)

BACKGROUND
The package is a synthetic simulation study (SIM1) supporting a paper comparing categorical
encodings. A "dense-signal addendum" extends the frozen d=3 design with a d=5 arm. A human
advisor issued a binding ruling (D13-D18). Phase A0.1 implemented that ruling and produced
the artefacts below. Phase A0.1 ran ZERO full addendum cells by design. Your job is to attack
the implementation before the advisor authorises Phase A1 (the expensive full run).

ARTEFACTS UNDER REVIEW (read these):
  simulation-results-ct2i/01B_ADDENDUM_ADVISOR_RULINGS.yaml            (frozen amendment; contains 5 open advisor questions)
  simulation-results-ct2i/S0B_ADVISOR_RULING_IMPLEMENTATION_REPORT.md
  simulation-results-ct2i/S0B_RUNNER_TEST_REPORT.md
  simulation-results-ct2i/S0B_REFERENCE_IMPLEMENTATION_TEST_REPORT.md
  simulation-results-ct2i/S0B_RESOURCE_CONFIRMATION.csv
  simulation-results-ct2i/RAW_FREEZE_MANIFEST_ADDENDUM.json
  scripts/run_sim1b_dense_addendum.py
  scripts/s0b_reference_gap_check.py
  tests/test_a0_dense_addendum_properties.py
  tests/test_a1_runner_smoke.py
  tests/test_a0_1_reconciliation.py
CONTEXT (immutable, do not propose editing):
  simulation-results-ct2i/01A_ADDENDUM_PROTOCOL_FREEZE.yaml
  simulation-results-ct2i/S0A_ADDENDUM_PREFLIGHT_REPORT.md   (the A0 preflight, returned BLOCKED)
  src/ct2i_benchmark/simulations/sim1_core.py                 (reference implementation lives here)
  scripts/run_sim1b_finite.py                                 (the inherited d=3 runner)

ATTACK THESE SIX QUESTIONS SPECIFICALLY. For each, either demonstrate a concrete failure or
state plainly that you could not construct one and why.

Q1. Can the AD15 / D18 gate be PASSED while the runner is WRONG? Find a concrete way.
    (AD15 item 3: the seed rule must live only in the runner and everything else imports it.
     D18: real-runner gate, typed row per attempted cell, no silent continue, NULL metrics on
     non-success, exact vs mc labels, fiber_count/collision_count/occupied_buckets recorded.)

Q2. Is the D17 two-gate rule sufficient? D17 evaluates AD1/AD2 with the independent
    sim1_core.reference_gap_report implementation. The A0.1 work already found that the
    advisor's NAMED identity columns evade all three injected defects:
       ebar_bias    -> identity_error 5.4e-15 UNCHANGED, |prod-ref| 5.541e-07
       mass_dropout -> identity_error 5.4e-15 UNCHANGED, |prod-ref| 1.083e-02
       fiber_merge  -> identity_error UNCHANGED, |prod-ref| 6.2e-15 ALSO UNCHANGED
    so 01B was amended to gate on |production - reference| AND the recomputed-vs-stored
    fiber_count cross-check. Find a defect class that evades BOTH of those two gates.

Q3. Are the D14 normalized estimands implemented correctly, GIVEN that
    sim1_core.eta_raw returns a PROBABILITY, not a linear predictor, so that
    Var{eta(X)} = Var(Y) - R_Brier*(X)? Check the actual code path, the denominators
    (H(Y) - R_log*(X); Var{eta(X)}), the NOT_IDENTIFIED tolerance handling, and whether the
    normalization is computed from the same quantities it claims.

Q4. Does the runner's typed-row accounting actually guarantee that EVERY attempted cell
    yields a row, including on setup exceptions (import failure, encoder construction failure,
    OOM, KeyboardInterrupt, exception inside the exception handler, worker death under
    multiprocessing)? Trace the real control flow with file:line.

Q5. Is the resource projection defensible? S0B_RESOURCE_CONFIRMATION.csv projects
    8.573 core-hours = 42.87% of a 20-hour ceiling. Is that anchored on something that will
    not hold at A1 scale (n_train=5000, d=5, 13 encoder configs, 48 scenarios, 2400 replicates,
    memory, parallel efficiency, I/O, the parts-file write path)? Show the arithmetic you
    checked and where it could be off by a factor.

Q6. Is the seed rule genuinely SINGLE-SOURCE now, or is there a surviving path that could
    diverge? Note scripts/s0a_addendum_microbenchmark.py is an immutable A0 historical record
    that still holds a private SEED_BASE_1BD / addendum_seed copy; a drift-detection test was
    added instead of editing it. Grep for every other definition or reimplementation of the
    seed rule anywhere in the repo and say whether any of them can silently diverge.

OUTPUT FORMAT
Label every finding CRITICAL, MAJOR, or MINOR. For each finding give:
  - a one-line title
  - file:line
  - the concrete failure scenario (what input / condition produces the wrong result, and what
    the wrong result looks like)
  - what would have to change to close it
End with a section "COULD NOT VERIFY" listing anything you were unable to check and why.
End with a single explicit line: CODEX VERDICT: <READY FOR A1 / NOT READY FOR A1> - <reason>.

"Looks fine" is not a useful answer. If you cannot verify something, say so plainly rather
than asserting it is correct. Be specific and adversarial. Precision matters more than volume.
```

## SEAT OUTPUT — VERBATIM AND COMPLETE (unedited, unreordered)

---

## Findings

**CRITICAL — The D17 gate can PASS without checking the A1 runner’s production output**  
`[scripts/s0b_reference_gap_check.py:393-458](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/s0b_reference_gap_check.py:393)`

- Failure scenario: run the checker for `--arm addendum` without `--stored` (the default). It rebuilds `fid`, computes both “production” (`exact_gap_report`) and reference values in the checker itself, finds agreement, has `fc=[]`, then evaluates `ok = (n_out == 0) and (fc_bad == 0)` as true. It reports `RESULT=PASS` even if the real A1 runner was never run, failed, wrote no row, or has a wrong partition.
- Wrong result: a passing D17/AD1/AD2 verdict is attributed to the runner although no runner-produced `fiber_count` or population gap was examined.
- Required change: make `--stored` mandatory for the A1/addendum gate; require exactly 624 stored successful oracle rows keyed one-to-one to the frozen sample; fail on any missing row, NULL `fiber_count`, duplicate, or mismatched key. Compute G1 from stored runner values, not a checker-local fast-path recomputation.

**CRITICAL — Worker/pool failure is converted to an empty checkpoint, silently omitting every attempted cell**  
`[scripts/_s1_parallel.py:74](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/_s1_parallel.py:74)`  
`[scripts/_s1_parallel.py:79](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/_s1_parallel.py:79)`  
`[scripts/_s1_parallel.py:83](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/_s1_parallel.py:83)`  
`[scripts/_s1_parallel.py:85](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/_s1_parallel.py:85)`  
`[scripts/_s1_parallel.py:56](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/_s1_parallel.py:56)`

- Failure scenario: an import/pickling error in a spawned worker, OOM kill, or `BrokenProcessPool` makes `fu.result()` raise. The parent catches it, sets `results[scenario_id] = []`, and writes a header-only part file. On restart, the part file exists, so that scenario is skipped.
- Wrong result: all 3,800 expected rows for that scenario (50 replicates × 76 rows) are absent; no typed failure rows exist. The runner still completes with exit code 0 and no final assertion compares merged rows to 182,400.
- Required change: the parent must synthesize typed failure rows for every expected cell when a future fails, or fail nonzero without marking the scenario checkpoint-complete. Validate each part’s schema, expected row count/key set, and final total/key set before producing a retainable output.

**CRITICAL — Typed-row coverage excludes several named setup/fatal paths**  
`[scripts/run_sim1b_dense_addendum.py:852](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/run_sim1b_dense_addendum.py:852)`  
`[scripts/run_sim1b_dense_addendum.py:856](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/run_sim1b_dense_addendum.py:856)`  
`[scripts/run_sim1b_dense_addendum.py:859](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/run_sim1b_dense_addendum.py:859)`  
`[scripts/run_sim1b_dense_addendum.py:863](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/run_sim1b_dense_addendum.py:863)`  
`[scripts/run_sim1b_dense_addendum.py:887](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/run_sim1b_dense_addendum.py:887)`

- Failure scenario: failure in `reference_replicate`, `resource.getrusage`, `encoder_configs`, `CORE.hash_gap_identified`, or `worker_tolerance` occurs before the per-replicate `try`. A `KeyboardInterrupt`/`SystemExit` inside the setup block also escapes because only `Exception`, not `BaseException`, is caught. If `_typed_failure_rows`/`addendum_row` itself raises, it also escapes.
- Wrong result: zero rows reach the parent; the parallel driver then creates the empty checkpoint described above.
- Required change: define the expected-cell manifest before work begins; use parent-side failure materialisation for all worker exceptions and fatal exits; explicitly define cancellation/KeyboardInterrupt behavior as an aborted, non-retainable run rather than pretending typed accounting is complete.

**CRITICAL — G1+fiber-count G2 cannot detect wrong same-cardinality partitions**  
`[scripts/s0b_reference_gap_check.py:392](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/s0b_reference_gap_check.py:392)`  
`[scripts/s0b_reference_gap_check.py:415](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/s0b_reference_gap_check.py:415)`  
`[simulation-results-ct2i/01B_ADDENDUM_ADVISOR_RULINGS.yaml:863](/Users/Eric/Desktop/114/ct2i-benchmark/simulation-results-ct2i/01B_ADDENDUM_ADVISOR_RULINGS.yaml:863)`

- Failure scenario: a defect in `group_ids`, `hash_codes`, or `ebar_coordinatewise` swaps one cell from fiber A with one from fiber B. The partition membership changes and usually changes both population gaps, but the number of fibers remains identical.
- Wrong result: both local production and reference paths consume the same corrupted `fid`, so G1 remains near machine precision; the independently rebuilt checker sees the same corrupted construction and G2 sees unchanged `fiber_count`. A stored A1 row also has the same count. Both gates pass while the reported gaps are wrong.
- Required change: G2 must compare a canonical partition fingerprint, not just cardinality—e.g. a deterministic digest of cell-to-fiber assignments built by an implementation independent of the production construction route. The checker must build that reference partition without calling the potentially defective production helper.

**MAJOR — Existing or malformed part files are trusted as completed work**  
`[scripts/_s1_parallel.py:50](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/_s1_parallel.py:50)`  
`[scripts/_s1_parallel.py:56](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/_s1_parallel.py:56)`  
`[scripts/_s1_parallel.py:103](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/_s1_parallel.py:103)`

- Failure scenario: an old/header-only/corrupt `sim1b_dense_addendum_replicates_parts/S1BD-0001.csv` exists. Existence alone skips recomputation; merging accepts whatever rows the CSV contains.
- Wrong result: a full A1 output can omit, duplicate, or mix rows without any final completeness check.
- Required change: use a run-specific checkpoint directory, validate provenance plus exact expected keys/count in every part, and reject pre-existing parts unless explicitly resumed from a validated manifest.

**MINOR — D14 mathematics is correct, but the threshold implements a different boundary rule**  
`[scripts/run_sim1b_dense_addendum.py:680](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/run_sim1b_dense_addendum.py:680)`  
`[scripts/run_sim1b_dense_addendum.py:714](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/run_sim1b_dense_addendum.py:714)`  
`[scripts/run_sim1b_dense_addendum.py:719](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/run_sim1b_dense_addendum.py:719)`  
`[simulation-results-ct2i/01B_ADDENDUM_ADVISOR_RULINGS.yaml:461](/Users/Eric/Desktop/114/ct2i-benchmark/simulation-results-ct2i/01B_ADDENDUM_ADVISOR_RULINGS.yaml:461)`

- Failure scenario: a denominator is exactly `1e-6`. The ruling says “below” / `|denominator| < 1e-6`; code uses `den <= tolerance`, reporting `NOT_IDENTIFIED`.
- Wrong result: an exactly-at-threshold positive normalized estimand is suppressed contrary to the frozen rule.
- Required change: use the frozen strict comparison (`abs(den) < tolerance`) or amend the ruling before A1.

The substantive D14 computation otherwise checks out: `eta_raw` is logistic/probability at [sim1_core.py:156-162](/Users/Eric/Desktop/114/ct2i-benchmark/src/ct2i_benchmark/simulations/sim1_core.py:156); `R_Brier^*(X)=E[eta(1-eta)]` at [sim1_core.py:256-259](/Users/Eric/Desktop/114/ct2i-benchmark/src/ct2i_benchmark/simulations/sim1_core.py:256); and the runner uses `Var(Y)-R_Brier^*(X)`, then divides the matching exact population gaps by the stated denominators. NULL/status handling is correctly routed through `addendum_row`.

**MAJOR — The 8.573 core-hour projection is arithmetically consistent but not a defensible upper bound**  
`[simulation-results-ct2i/S0B_RESOURCE_CONFIRMATION.csv:4](/Users/Eric/Desktop/114/ct2i-benchmark/simulation-results-ct2i/S0B_RESOURCE_CONFIRMATION.csv:4)`  
`[simulation-results-ct2i/S0B_RESOURCE_CONFIRMATION.csv:7](/Users/Eric/Desktop/114/ct2i-benchmark/simulation-results-ct2i/S0B_RESOURCE_CONFIRMATION.csv:7)`  
`[simulation-results-ct2i/S0B_RESOURCE_CONFIRMATION.csv:8](/Users/Eric/Desktop/114/ct2i-benchmark/simulation-results-ct2i/S0B_RESOURCE_CONFIRMATION.csv:8)`  
`[scripts/run_sim1b_dense_addendum.py:1192](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/run_sim1b_dense_addendum.py:1192)`

- Arithmetic checked: `5.930868 × 1.025065 × 1.0069 = 6.121474`; `× 1.4 = 8.570064`; then `+ 0.000304 + 0.000066 = 8.570434` if using the stated C2 value, while the file’s total uses `C2=0.003187`, giving `8.573317`, consistent with its own written total. `8.573316 / 20 = 42.8666%`, correctly rounded to 42.87%.
- Failure scenario: A1 encounters worker death/restart, an incomplete parts-file retry, disk pressure, or a tail configuration whose cost is materially above the 32 short probe pairs. None is bounded by the d3 aggregate anchor or the 1.025 ratio CI. The 1.4 multiplier is historical and not tied to an A1 failure/retry model.
- Wrong result: “within 20 hours” is presented as a forecast with only ~2.33× headroom, but the model has no quantified bound for restart waste, full parallel I/O, or the cost tail. A factor of 2.33 in unmodelled total overhead exhausts the cap; a single rerun/recovery can readily invalidate a CPU budget even when wall time looks acceptable.
- Required change: state it as an estimate, not a ceiling guarantee; measure a multi-worker, full-schema, full-`n_eval`, all-configuration representative batch including part writes; budget explicit restart/failure reserve; enforce CPU accounting and a stop rule during A1.

**MINOR — The seed rule is not literally single-source; the historical duplicate can drift outside tests**  
`[scripts/run_sim1b_dense_addendum.py:316](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/run_sim1b_dense_addendum.py:316)`  
`[scripts/s0a_addendum_microbenchmark.py:67](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/s0a_addendum_microbenchmark.py:67)`  
`[scripts/s0a_addendum_microbenchmark.py:71](/Users/Eric/Desktop/114/ct2i-benchmark/scripts/s0a_addendum_microbenchmark.py:71)`  
`[tests/test_a0_1_reconciliation.py:252](/Users/Eric/Desktop/114/ct2i-benchmark/tests/test_a0_1_reconciliation.py:252)`

- Failure scenario: someone changes the runner’s OOF formula or changes the microbenchmark’s direct `OOF_BASE_1BD + 17 * rep` call while retaining its base constant. The reconciliation test compares base constants and DGP `addendum_seed`, but does not compare all microbenchmark OOF/derived-seed uses against runner helpers.
- Wrong result: the immutable A0 microbenchmark can silently use a different OOF channel if it is run without the reconciliation suite; it is not an A1 runner path, but AD15’s literal “everything else imports it” is not met.
- Required change: preserve the historical file unchanged, but add AST/text-level checks covering its DGP, OOF, train, and eval expressions, and document it as a pinned historical exception rather than claiming literal single-source compliance.

I found no other executable addendum seed-rule implementation beyond the runner and the acknowledged immutable `s0a_addendum_microbenchmark.py`; `sim1_core.dgp_block_seed` is a generic, separate component rule. Tests recompute the formula only as assertions, not as runtime simulation paths.

## COULD NOT VERIFY

- I did not run the test suite, simulation, checker, addendum cells, or any probe, per the read-only/no-compute instruction. Reported A0.1 test and probe results were inspected but not independently reproduced.
- I could not validate real A1-scale CPU, memory, multiprocessing reliability, or parts-file I/O because no A1 output exists and execution was prohibited.
- I did not inspect the private scratchpad probe files cited by the resource CSV; they are outside the listed review artefacts and may not be available in this workspace.

CODEX VERDICT: NOT READY FOR A1 - the real runner can silently omit attempted cells, and the D17 gate can pass without validating runner output or a wrong same-cardinality partition.
CODEX_EXIT=0


---

## Write-check

`git status --porcelain` in /Users/Eric/Desktop/114/ct2i-benchmark before and after this dispatch: IDENTICAL (21 lines, byte-identical diff). The Codex seat wrote nothing to the working tree.


---

## 8. Seat 2 — ANTIGRAVITY / GEMINI, `gemini-3.1-pro-high` (independent scientific review) — VERBATIM

The capture below is reproduced complete and unedited, including the seat identity block,
the exact dispatch command, the recorded capability probe that changed the dispatch method,
the material inventory, the verbatim instruction head of the prompt, and the seat's output.
The full byte-exact prompt including all 176,787 bytes of pasted material is preserved at
`<SCRATCHPAD>/prompt_agy.txt`.

# COUNCIL SEAT 2 CAPTURE — ANTIGRAVITY / GEMINI (independent scientific review)

Captured by: Claude (host seat), Phase A0.1 council dispatch
Capture date: 2026-08-24

## Seat identity

- Role assigned by advisor: "Gemini for independent scientific review"
- CLI: Antigravity `agy` v1.1.19 (~/.local/bin/agy), the sanctioned route; the legacy standalone client is retired and blocked by environment policy.
- Model id: `gemini-3.1-pro-high` (strongest model on this channel; Phase A0 used 2.5-pro, so this round is a STRONGER seat, not weaker).
- Read-only enforcement: `--sandbox` flag PLUS an explicit prompt-level prohibition ("You must NOT write, create, or modify any file. Do not use any file-writing or shell tool."). Run from an EMPTY neutral working directory outside the repository: `/private/tmp/claude-501/-Users-Eric-Desktop-114----code-result/e234d5a4-799b-49a4-b4f1-9d19ec0e4653/scratchpad/agy_neutral`. That directory was still empty after the run.
- Wall-clock: 97s (start epoch 1787582611, end epoch 1787582708)
- Exit code: 0. stderr: empty (0 bytes).
- ZERO addendum cells run.

## EXACT command used

```
export PATH="$HOME/.local/bin:$PATH"
cd /private/tmp/claude-501/-Users-Eric-Desktop-114----code-result/e234d5a4-799b-49a4-b4f1-9d19ec0e4653/scratchpad/agy_neutral      # empty neutral dir, NOT the repo
agy --model gemini-3.1-pro-high --sandbox --print-timeout 25m --print "$(cat <PROMPT_FILE>)" </dev/null
```

where `<PROMPT_FILE>` is `/private/tmp/claude-501/-Users-Eric-Desktop-114----code-result/e234d5a4-799b-49a4-b4f1-9d19ec0e4653/scratchpad/prompt_agy.txt` (176,787 bytes).

## Capability probe (recorded, because it changed the dispatch method)

A first probe from a scratch directory asked whether the seat could read a local file. It attempted to run a shell command and was refused by its own permission layer:

```
agy --model gemini-3.1-pro-high --print "Without writing any file: is there a file named probe_file.txt ..." </dev/null
-> Error: permission check failed for command "pwd": user denied permission to run command: pwd
-> exit 1
```

CONCLUSION: this seat could NOT read the repository without granting it tool permissions (`--dangerously-skip-permissions`), which would have violated the read-only requirement. The dispatch was therefore adapted: **all review material was PASTED into the prompt** and the seat was told explicitly that it cannot read the repository. This is a channel adaptation, NOT a seat-availability finding — the seat was filled, by Gemini, and returned a full review.

## Material the seat was given (pasted verbatim into the prompt, in this order)

1. A CONTEXT block stating the study design, the d=3 -> d=5 addendum, the advisor ruling D13-D18, and the key technical fact that `sim1_core.eta_raw` returns a PROBABILITY (so sd(eta) is 1.038x-1.437x larger at d=5 in all 24 factor combinations, and Var{eta(X)} = Var(Y) - R_Brier*(X)).
2. MATERIAL 1/3 — `simulation-results-ct2i/01A_ADDENDUM_PROTOCOL_FREEZE.yaml`, COMPLETE (52,897 bytes).
3. MATERIAL 2/3 — `simulation-results-ct2i/01B_ADDENDUM_ADVISOR_RULINGS.yaml`, COMPLETE (87,374 bytes).
4. MATERIAL 3/3 — `simulation-results-ct2i/S0B_ADVISOR_RULING_IMPLEMENTATION_REPORT.md`, COMPLETE (31,180 bytes).

It was NOT given: the runner source, the test files, S0B_RUNNER_TEST_REPORT.md, S0B_REFERENCE_IMPLEMENTATION_TEST_REPORT.md, S0B_RESOURCE_CONFIRMATION.csv, RAW_FREEZE_MANIFEST_ADDENDUM.json, or S0A_ADDENDUM_PREFLIGHT_REPORT.md — by design, since this seat reviews SCIENCE and DESIGN, not code, and those are the Codex seat s remit.

## PROMPT SENT — instruction head, verbatim (the three pasted MATERIAL files follow it and are on disk in the repo unchanged)

```
You are the INDEPENDENT SCIENTIFIC REVIEW seat on an academic review council for an MSc
statistics thesis simulation package. Your assigned role, set by the human advisor, is
INDEPENDENT SCIENTIFIC AND DESIGN REVIEW -- NOT code style, NOT software engineering.

HARD CONSTRAINT: You must NOT write, create, or modify any file. Do not use any file-writing
or shell tool. Answer purely in your reply text. If you feel you need to run a tool, do not;
say what you would have checked instead.

All material you need is pasted below. You cannot read the repository.

===================== CONTEXT =====================
A synthetic simulation study (SIM1) supports a paper on categorical-encoding effects. The
frozen study used d=3 informative coordinates. A "dense-signal addendum" adds a d=5 arm.
A human advisor issued a binding ruling (D13-D18). Phase A0.1 implemented that ruling,
writing a frozen amendment file (01B) plus a runner and tests, and running ZERO simulation
cells. Phase A1 (the expensive full run) is gated on this council's review.

Key technical fact you need: sim1_core.eta_raw returns a PROBABILITY, not a linear predictor.
eta_raw sums one main effect per active coordinate and does NOT normalise by d, so sd(eta) is
larger at d=5 than at d=3 in all 24 factor combinations (ratio 1.038x to 1.437x). That is why
the advisor reframed the addendum as a DENSE-SIGNAL STRESS TEST rather than a pure
dimensionality experiment. Consequently Var{eta(X)} = Var(Y) - R_Brier*(X).

===================== YOUR TASK =====================
Rule on the following six questions. Give reasoning, not assent.

S1. The advisor KEPT the inherited d=5 DGP unchanged (no tau/sqrt(d) rescaling, no third
    signal-matched arm) and instead reframed the addendum as a DENSE-SIGNAL STRESS TEST.
    Is that reframing scientifically honest and SUFFICIENT, or does it still license a
    conclusion the design cannot support? Be concrete about which sentences a reader would
    wrongly infer.

S2. Two normalized estimands are offered as a SENSITIVITY ANALYSIS that explicitly does NOT
    remove confounding:
       relative_log_gap   = (R_log*(Z) - R_log*(X)) / (H(Y) - R_log*(X))
       relative_brier_gap = (R_Brier*(Z) - R_Brier*(X)) / Var{eta(X)}
    Is "sensitivity analysis" the right epistemic status for them? Do these SPECIFIC
    denominators actually do what is claimed? Consider: what is being normalised away, what
    is not, whether the two denominators are on comparable footing, behaviour as the
    denominator approaches its frozen tolerance, and whether a ratio of risks is even the
    right functional form for the contrast of interest.

S3. Interaction pairs are held at 3 in both arms: 3 of 3 possible pairs at d=3 (100%
    saturation) versus 3 of 10 at d=5 (30%). Is reporting interaction_pairs=0 and
    interaction_pairs=3 SEPARATELY an adequate treatment of this second confound? If not,
    what is the minimum additional analysis or disclosure that would make it adequate?

S4. D13 moves inference to 8 independent parameter-draw blocks with 7 degrees of freedom,
    using block-clustered inference and a block-resampling bootstrap. Is 7 df adequate for
    the claims E1a / E1b / E1c are meant to support? Is the block key correct? Comment on
    the bootstrap's behaviour at 8 blocks, on the one-sided BH adjustment across the three
    E1 clauses, and on what power is realistically available.

S5. Phase A0.1 FROZE two extensions beyond the advisor's own text:
      - effective_blocks_min = 4 (he wrote only "if too few independent blocks remain")
      - a FOURTH outcome class INCONCLUSIVE_REPORTED_IN_FULL added to his three
        (CONFIRMED / PARTIALLY SUPPORTED / NOT SUPPORTED), for the case: positive primary
        normalized estimate, q >= 0.05, but a non-positive raw or Brier contrast
      - "materially directionally inconsistent" quantified as opposite signs AND both
        |estimates| > 1e-6
    Are those extensions SOUND? Is there a coupling consequence between them (e.g. between
    the blocks floor, the E1c matched-condition filter, and the outcome classes) that the
    advisor should be told about before he approves?

S6. What conclusion COULD this addendum support, and what would it NOT be able to support
    even if every gate passes and every result is positive? State both in the form of
    sentences a paper could or could not write.

===================== OUTPUT FORMAT =====================
Label every finding CRITICAL, MAJOR, or MINOR, each with concrete reasoning (not "consider
adding"). Then end with EXACTLY one line:

GEMINI VERDICT: EXECUTE AS AMENDED
   or
GEMINI VERDICT: DO NOT EXECUTE AS AMENDED

followed by one sentence giving the reason. Be adversarial and specific. "Looks reasonable"
is not a useful answer. If you cannot judge something from the pasted material, say so.

===================== MATERIAL 1/3: 01A_ADDENDUM_PROTOCOL_FREEZE.yaml (immutable design) =====================
```

The full byte-exact prompt including all pasted material is preserved at `/private/tmp/claude-501/-Users-Eric-Desktop-114----code-result/e234d5a4-799b-49a4-b4f1-9d19ec0e4653/scratchpad/prompt_agy.txt`.

## SEAT OUTPUT — VERBATIM AND COMPLETE (unedited, unreordered)

---

**S1.** CRITICAL. The reframing as a "DENSE-SIGNAL STRESS TEST" is scientifically insufficient and actively misleading. The word "dense" explicitly directs the reader to attribute performance degradation to the *distribution* of the signal across multiple coordinates (dimensionality). It completely conceals the fact that the total signal magnitude was increased. Even with the confounds disclosed, a reader would wrongly infer: "The hash encoder's increased representation loss at d=5 demonstrates that it cannot handle dense, high-dimensional signals," when in fact the exact same increase in representation loss could be generated by a single-coordinate signal whose variance was simply scaled up by the same factor. 

**S2.** MAJOR. "Sensitivity analysis" is the correct epistemic status because these normalizations do not successfully remove the confound. The specific denominators are structurally correct for their respective proper scoring rules: $H(Y) - R_{log}^*(X)$ is the mutual information (total available log-loss signal), and $Var\{\eta(X)\}$ is the total available Brier signal. However, because the DGP passes the linear predictor through a non-linear logistic link, increasing the signal variance pushes the probabilities into the compressed tails of the sigmoid. Consequently, the *fraction* of signal lost by a fixed partition is not invariant to the total signal strength. Therefore, taking a ratio of risks fails to mathematically isolate the dimensionality effect from the signal-strength confound.

**S3.** MAJOR. Reporting the strata separately is necessary but insufficient. The `interaction_pairs=0` stratum provides a clean, 0%-saturation matched comparison that isolates the dimensionality effect (modulo signal strength). However, the `interaction_pairs=3` stratum is hopelessly confounded: it conflates the change in dimensionality with a 70% drop in interaction saturation and a structural shift in interaction placement (forcing coordinate 0 into every pair). The minimum adequate disclosure is to explicitly restrict all clean claims about dimensionality to the `interaction_pairs=0` stratum, and explicitly warn that the 3-pair stratum measures a joint effect of dimension, saturation, and topology.

**S4.** CRITICAL. Moving to 8 blocks with 7 degrees of freedom mathematically cripples the addendum's statistical power. A block-resampling bootstrap on $N=8$ clusters is severely discrete and asymptotically invalid; it cannot reliably estimate the tail probabilities required for a valid p-value. With 7 df, the cluster-robust t-distribution is exceedingly fat-tailed, meaning realistic power to detect anything short of a massive effect size is near zero. Layering a Benjamini-Hochberg adjustment over this structurally underpowered foundation guarantees that the design is rigged to fail to reject the null, risking a Type II error that the reporting policy (E4) will then wrongly force to be published as a "null finding."

**S5.** CRITICAL. The individual extensions (4 blocks floor, fourth outcome class, 1e-6 inconsistency tolerance) are mechanically sound in isolation, but they create a fatal statistical coupling that invalidates the inference. E1c's inclusion depends on the realized `fiber_count`, which is a data-dependent random variable driven by sample ties. If E1c drops out because fewer than 4 independent blocks survive the filter, the Benjamini-Hochberg family size dynamically shrinks from 3 to 2. Adjusting p-values based on a data-dependent family size violates the theoretical guarantees of the FDR procedure, artificially inflating the Type I error rate for E1a and E1b.

**S6.** MAJOR. 
A paper COULD write: "In a setting with increased total signal variance and more active coordinates, non-injective encoders lose a strictly larger fraction of the available target information than they do in a sparser setting."
A paper COULD NOT write: "The signal-normalized sensitivity analysis proves that the encoders' degraded performance is driven by the density of the signal, independent of the overall signal strength."

GEMINI VERDICT: DO NOT EXECUTE AS AMENDED
The amendment must be blocked because the data-dependent shrinkage of the Benjamini-Hochberg family size invalidates the multiple-testing correction, and the 8-block cluster-robust inference lacks the statistical power to support the addendum's primary claims.


---

## Write-check

`git status --porcelain` in /Users/Eric/Desktop/114/ct2i-benchmark before and after this dispatch: IDENTICAL (21 lines, empty diff). The neutral working directory `/private/tmp/claude-501/-Users-Eric-Desktop-114----code-result/e234d5a4-799b-49a4-b4f1-9d19ec0e4653/scratchpad/agy_neutral` was empty after the run. The Antigravity seat wrote nothing.


---

## 9. Seat 3 — CLAUDE, statistical validity (supplementary) — VERBATIM

Dispatched 2026-08-24 22:41:18 as a fresh-context subagent with no authorship of any
reviewed artefact and no sight of the host's reasoning; output captured 22:57:28
(~16 min). Interpreter `/Users/Eric/.pyenv/versions/3.11.9/bin/python3`. Probe scripts in
`<SCRATCHPAD>/council_sci/`. Repository writes: zero. Addendum cells executed: zero.

Retained as a supplementary seat under the same treatment Phase A0 gave its two Claude
reviewers: **it does not substitute for either mandated provider seat**, both of which
were filled for real (§1).

# Council seat — SCIENTIFIC AND STATISTICAL VALIDITY
## Phase A0.1, cT2I dense-signal Simulation 1B addendum
Reviewer: independent seat, no authorship of any artefact reviewed.
Date: 2026-08-24. Interpreter: `/Users/Eric/.pyenv/versions/3.11.9/bin/python3`.
Repository writes: **zero** (`git status --porcelain` identical before and after; see §8).
Addendum cells executed: **zero**. All probes are exact population algebra
(`draw_params` → `impose_delta_eta` → `exact_gap_report`), no learner fitted, all
scripts in `<SCRATCHPAD>/council_sci/`.

---

## 0. One-paragraph summary

The stress-test reframing is honest as far as it goes, and the two normalized
estimands are algebraically correct and genuine analogues — I verified both
claims independently. But the amendment has three defects that a referee would
find in an afternoon. (i) The D16 primary statistic is a **pure population
quantity that requires no simulation at all**; I computed it exactly, and it
comes out **negative** for E1a and E1b while the raw contrast comes out
**strongly positive**. The package will therefore produce a raw/normalized
**reversal** that no rule in 01A or 01B anticipates, adjudicates, or flags, and
that D14 and D16 give contradictory instructions about (D14: normalized is a
*sensitivity analysis*; D16: normalized is the *primary*). (ii) D16 E1c's
matched-non-injectivity restriction, `fiber_count < 1024` on both sides, is
**vacuously true on the d = 3 side** — the frozen d = 3 `count` fiber counts are
in {24, 32, 36, 48, 64}, never near 1024. (iii) The D14 normalized estimand is
**not computable for the d = 3 arm** from any frozen artefact and 01B specifies
no rule for obtaining it. Separately, D13's stated justification ("only 8
parameter draws") is factually false — there are 400 — and the resulting
procedure is underpowered against the effect it is trying to detect.

---

## 1. CRITICAL findings

### CRITICAL-1 — The primary statistic is already determined, and it REVERSES the raw result. No rule governs the reversal, and D14 and D16 contradict each other about which one is the headline.

**Claim.** `relative_log_gap` is a function of the exact 1024-state cell law
alone. The runner computes it from `pop = CORE.exact_gap_report(fid, tab.p_cell,
tab.eta)` and `population_signal_scales(tab.p_cell, tab.eta)`
(`scripts/run_sim1b_dense_addendum.py:929-935, 877`) — no learner, no training
sample, no evaluation sample enters it. The D16 primary statistics for E1a and
E1b are therefore computable to machine precision **before A1 runs**, and I
computed them.

**Evidence** (`council_sci/p3_predict_E1.py`, 50 replicates, 8 blocks, 7 df,
d = 5 seeds from `run_sim1b_dense_addendum.addendum_seed`, d = 3 seeds from
`sim1_core.dgp_block_seed("1B", …)` — seed rule verified against the frozen
parquet: recomputed 149962001 == stored 149962001):

```
E1a hash_shared  PRIMARY normalized log   est = -0.01815  SE 0.01007  t = -1.80  blocks>0: 1/8
E1a hash_shared  supporting normalized Brier est = -0.01967  SE 0.01037 t = -1.90 blocks>0: 1/8
E1a hash_shared  RAW log-loss contrast     est = +0.00919  SE 0.00198  t = +4.64  blocks>0: 8/8
E1b hash_column  PRIMARY normalized (mean B0,B1) est = -0.05182 SE 0.01961 t = -2.64 blocks>0: 2/8
E1b hash_column  supporting normalized Brier est = -0.05349 SE 0.01967 t = -2.72 blocks>0: 2/8
E1b hash_column  RAW log-loss contrast     est = +0.00129  SE 0.00209  t = +0.62  blocks>0: 6/8
E1b secondary B2                            est = -0.07253  SE 0.00733  t = -9.90  blocks>0: 0/8
```

Under `01B rulings.D16.outcome_classifications`, "the primary NORMALIZED
log-loss contrast estimate is non-positive" is *sufficient* for NOT_SUPPORTED.
**E1a and E1b are NOT_SUPPORTED before a cell is run.** Meanwhile the raw
hash_shared contrast is positive in 8/8 blocks at t = +4.64 — E1's raw
prediction is confirmed and well powered.

**Why this is critical, not merely interesting.**
1. `01B rulings.D14.estimands` assigns `status: PRIMARY_ALWAYS_REPORTED` to the
   raw pair and `status: PRIMARY_FOR_D16_DECISION_RULES_AND_SENSITIVITY_ELSEWHERE`
   to the normalized pair. Two primaries. `D14.normalized_analysis_status.label:
   SENSITIVITY_ANALYSIS` says the normalized quantity is a sensitivity analysis;
   `D16.clauses.E1a.primary_statistic` makes the same quantity the sole basis of
   the verdict. **Nothing in either file resolves which one is the manuscript's
   headline when they disagree** — and they will disagree.
2. `D16.outcome_classifications.NOT_SUPPORTED.materially_directionally_inconsistent_definition`
   compares **normalized log vs normalized Brier only**. Those two agree here
   (both negative). The reversal that actually occurs — raw positive, normalized
   negative — is not a defined inconsistency, produces no flag, and no
   classification names it. Q3's enumeration of the "gap that was found"
   (01B:1170) explicitly instances "primary positive, q ≥ 0.05, raw non-positive"
   — the mirror image of the case that will occur.
3. The scientific content of the reversal is large and should be stated, not
   discovered in a table: **the entire raw d = 5 excess representation loss is
   attributable to the signal-strength confound C1 and then some.** Once the gap
   is expressed as a fraction of the signal available in X, the dense arm loses a
   *smaller* fraction. That is a publishable result under E4, and it is close to
   the opposite of E1's mechanism story.

**Failure scenario.** A1 runs; the acceptance report prints "E1a NOT_SUPPORTED,
E1b NOT_SUPPORTED"; the validation report separately prints a raw contrast at
t = +4.6; a reader — or the advisor — asks which is the finding, and the frozen
protocol has no answer, so the answer is chosen after the data are seen. That is
the exact failure the whole freeze apparatus exists to prevent.

**Recommendation.** Before A1: (a) the advisor picks ONE of raw / normalized as
the headline and the other as the companion, and the choice is written into 01B;
(b) add a fifth outcome annotation `SCALE_REVERSAL` that fires when the raw and
normalized log-loss contrasts have opposite signs and both exceed
`positive_gap_min`, mandating that both be quoted in the same sentence; (c)
record in 01B that the E1a/E1b primary statistics were computed exactly at A0.1
and their values, so the run cannot be read as having discovered them.
Pre-registering the known value is more honest than pretending the run is blind.

---

### CRITICAL-2 — D16 E1c's "matched non-injective" restriction is vacuous on the d = 3 side. The two arms are compared against threshold values with different denominators.

**Claim.** `01B rulings.D16.clauses.E1c.primary_analysis_restriction` requires
`fiber_count < 1024` on **both** sides of each matched pair, sourced to
"01A exactness.state_space = 4**5 = 1024". At d = 3 the non-hash encoders'
`fiber_count` is computed on the **active-block** enumeration (`4**3 = 64`
cells) — `run_sim1b_finite.py:190-192`, `fib = len(np.unique(fid_cells))` where
`fid_cells` comes from `ebar_coordinatewise(mp, tab, prm)` on `tab.cells`. So at
d = 3 the count encoder's fiber count can never exceed 64 and the restriction is
satisfied by construction.

**Evidence** (read-only, frozen `05b_SIM1B_REPLICATE_RESULTS.parquet`, M = 5,
K = 4, SUCCESS, metric = logloss):

```
encoder=count  fiber_count: min 24, max 64, 5 distinct values, 9600 rows
  fraction with fiber_count < 1024 : 1.000     <-- the D16 restriction: vacuous
  fraction with fiber_count <   64 : 0.1375    <-- the CORRECT d=3 injectivity test
  by marginal x n_train (counts of fiber_count):
                    24    32    36    48    64
  uniform  500      12    24   156   744  1464
  uniform  5000      0     0    24   300  2076
  zipf     500       0     0     0    60  2340
  zipf     5000      0     0     0     0  2400
```

Two consequences. (i) The stratum is selected by the d = 5 side alone; the
contrast is not matched on the property it claims to match on. (ii) Under the
*correct* threshold (`< 64` at d = 3) the **entire zipf × n_train = 5000 half is
empty** (0/2400) and zipf × n_train = 500 retains 60/2400. Since `marginal` is a
block-key factor, a correct restriction removes most or all of the four Zipf
blocks, leaving ≈ 4 effective blocks — i.e. it lands exactly on the frozen
`effective_blocks_min = 4` boundary, which then decides the BH family size (see
MAJOR-4).

The non-emptiness "verification" quoted in support
(`01B ... non_emptiness_verified.verified_line_quoted_from_01A`, 01A:480,
{576, 768, 1024} / {768, 1024}) is a **d = 5** sweep. It establishes nothing
about the d = 3 arm and is presented as though it did.

**Failure scenario.** E1c is reported as restricted to matched non-injective
conditions when in fact no d = 3 condition was ever excluded; a referee reads
`fiber_count` in the shipped CSV, sees 64 next to a 1024 threshold, and the
package loses credibility on a point that costs one line to fix.

**Recommendation.** Replace the frozen constant with a per-arm rule:
non-injective means `fiber_count < K**d_active` evaluated on the arm's own
enumeration, i.e. `< 64` at d = 3 and `< 1024` at d = 5. State that hash
encoders' `fiber_count` is on the full `K**M` space in both arms and is
therefore on a different denominator from the coordinate-wise encoders' — that
column is currently two different quantities under one name. Re-run the
non-emptiness check against the corrected rule and record the surviving block
count *before* A1.

---

### CRITICAL-3 — The D14 normalized estimand cannot be formed for the d = 3 arm from any frozen artefact, and 01B contains no rule for obtaining it.

**Claim.** The D16 primary statistic is a d = 5 minus d = 3 difference in
`relative_log_gap`. The d = 5 side is written by the new runner. The d = 3 side
must come from the frozen twin, which does not carry the denominators.

**Evidence** (`council_sci/p1_d3_denominators.py`):

```
05b columns matching p_y / entropy / var : []      (none exist)
columns present: risk_x, risk_z, theoretical_gap, representation_loss, mcse, fiber_count, …
```

`H(Y) − R_log*(X)` needs `p_y = E[eta]`; `Var{eta(X)}` needs `p_y(1−p_y) −
R_Brier*(X)`. Neither `p_y` nor any function of it is stored. The denominators
are therefore **undefined on the d = 3 side**, and the primary estimand of the
entire amendment does not exist for one of its two arms.

A second, independent asymmetry: the frozen d = 3 numerator is a Monte-Carlo
quantity, the d = 5 numerator is exact. Recomputing scenario S1B-0001 (uniform,
τ = 0.5, n_int = 0, Δη = 0, seed 149962001), hash_shared B0, exactly:

```
EXACT   d=3: R_log(X)=0.6844883399  gap_log=0.0073752977
STORED  d=3: risk_x  =0.6845349072  rep_loss=0.0073385525   (stored mcse 4.046e-05)
|exact - stored| : risk_x 4.657e-05,  rep_loss 3.675e-05  ~ 1 x mcse
```

`run_sim1b_finite.py:215-221` confirms the mechanism: `r_x = fn(eta_ev,
eta_ev).mean()` and `decompose(eta_ev, ebar_ev, p, metric)` are Rao-Blackwellised
averages over the 50,000-row evaluation draw, not population sums. Mixing an
exact d = 5 numerator with an MC d = 3 numerator biases nothing but adds a
one-sided noise floor of ~4e-5, which is negligible against the 1.8e-2 effect —
so this is fixable, not fatal, but it must be *decided*, not left to A1.

**Failure scenario.** A1 reaches the analysis step, discovers the missing
denominators, and an implementer improvises — most plausibly by substituting
`Var(Y)` computed from the evaluation labels, or by using the MC `risk_x` in a
denominator whose numerator is exact. Either produces an estimand nobody
pre-registered.

**Recommendation.** Freeze, in 01B, an explicit d = 3 population-layer
recomputation: for each (block, replicate, delta_eta) rebuild the d = 3 cell law
from `dgp_block_seed("1B", (5,4,marginal,tau,n_int), replicate)` with
`d_active = 3`, compute `pop_gap_logloss`, `pop_gap_brier`, `p_y`, `entropy_y`,
`var_eta_x` exactly, and persist them as a new sibling CSV (this modifies no
protected raw file). Add an acceptance check that the recomputed exact d = 3
representation loss agrees with the stored MC value within `max(5*mcse, 1e-4)`
— a free and genuinely independent validation of the frozen arm. The cost is
seconds; my probe did 2,400 d = 3 laws in ~10 s.

---

## 2. MAJOR findings

### MAJOR-1 — D13's stated premise is false: the addendum contains 400 independent parameter draws, not 8. And 82% of the "cluster-robust" variance is fixed-factor heterogeneity, not sampling error.

**Claim.** `01B rulings.D13` says "the 48 scenarios span only 8 parameter draws"
and derives 7 df from it. That is wrong. `addendum_seed(block, replicate) =
2_000_000_000 + 1000*(h(block) % 1e6) + replicate` gives a distinct seed per
replicate, and `draw_params` re-draws `a` and `b` from `default_rng(seed)`.

**Evidence** (`council_sci/p5_variance_decomp.py`):

```
addendum seeds rep 1/2/3 in one block: [2149762001, 2149762002, 2149762003]  distinct
max |a(rep1) - a(rep2)| = 2.2953      -> the main-effect draw CHANGES with replicate
=> independent parameter draws = 8 blocks x 50 replicates = 400, NOT 8
```

01B's own V1/V2 checks record "400 distinct addendum seeds" and then conclude
"=> 8 blocks". What the block key actually buys is that the 6 scenarios of a
block **at a fixed replicate** share one draw — i.e. it removes dependence
across `delta_eta` and `n_train`, not across replicates.

Variance decomposition of the E1a block-mean contrast:

```
between-block SD of the 8 block means         = 0.02849
mean within-block DRAW SE of a block mean     = 0.01218   (from 50 reps per arm per delta)
implied FIXED-FACTOR (condition) SD           = 0.02576
share of the D13 clustered variance that is condition heterogeneity = 81.7%
block means: [+0.0249 -0.0120 -0.0164 -0.0184 -0.0050 -0.0129 -0.0772 -0.0283]
```

So the D13 standard error is overwhelmingly a measure of *how much the effect
varies across the frozen 2 × 2 × 2 grid*, not of *how precisely the effect is
estimated*. This is not anti-conservative — it is the opposite — but the
justification given is factually wrong, and the estimand is left unnamed. The
target of a t-test over 8 condition means is "the equally-weighted average
effect over this arbitrary grid", which does not generalize to other τ or
marginals.

**Recommendation.** Correct the sentence. Name the estimand explicitly
("equally-weighted mean over the frozen 2 × 2 × 2 condition grid"). Report, next
to the clustered SE, the draw-level SE from the 400 draws, and state that the
gap between them is condition heterogeneity. Nothing about the procedure needs
to change; the claim about why it is used does. Keeping a false premise in an
immutable ruling file is the kind of thing that gets quoted back.

### MAJOR-2 — The design is underpowered against the effect it is testing, and the D14-mandated stratification makes it powerless.

**Evidence** (`council_sci/p4_power_strata_bh.py`, one-sided α = 0.05, 80% power):

```
E1a normalized: n_blocks=8, between-block SD 0.02849, SE 0.01007, MDE = 0.02811
E1a normalized: n_blocks=4, SE 0.01425,                            MDE = 0.04747
E1b normalized: n_blocks=8, between-block SD 0.05451, SE 0.01927,  MDE = 0.05378
E1b normalized: n_blocks=4, SE 0.02725,                            MDE = 0.09080
E1a RAW:        n_blocks=8, between-block SD 0.00559,              MDE = 0.00552, observed +0.00919
```

The true |E1a normalized effect| is 0.018 against an MDE of 0.028: **the test
cannot detect the effect that exists, in either direction.** Only the RAW
statistic is adequately powered (observed 0.0092 vs MDE 0.0055). Under
`D14.stratified_reporting`, every quantity must also be reported separately by
`interaction_pairs`, which halves the blocks to 4 (3 df) and raises the MDE to
0.047 / 0.091 — larger than any effect in the design. So the mandatory
stratified analysis can, by construction, never support a claim.

**Recommendation.** State the MDE next to every reported quantity (this follows
naturally from D13's `mandatory_disclosure_per_reported_quantity`, which
currently demands effective n but not what that n can detect). Declare in
advance that the stratified analysis is descriptive only. If the advisor wants
E1 to be testable at all on the normalized scale, the honest options are more
blocks (more marginal / τ levels) or inference at the draw level (400 units),
not the current 8.

### MAJOR-3 — Interaction saturation is not a background confound; it is the dominant term. Stratification exposes it but cannot repair it.

**Evidence** (same script):

```
E1a hash_shared     pooled(8)  -0.01815 | n_int=0 (4): -0.01841 t=-0.86 | n_int=3 (4): -0.01788 t=-4.76
E1b hash_column B0  pooled(8)  -0.04052 | n_int=0 (4): -0.00220 t=-0.11 | n_int=3 (4): -0.07884 t=-4.39
E1b hash_column B1  pooled(8)  -0.06312 | n_int=0 (4): -0.02274 t=-1.03 | n_int=3 (4): -0.10351 t=-6.06
```

For hash_column the `interaction_pairs = 0` stratum is a null (−0.002) and the
`= 3` stratum carries essentially the whole effect (−0.079). The pooled number
is an average of a null and a large effect — it describes neither. Combined with
C3 (interaction *placement*: at d = 5 all three lexicographic pairs are
(0,1), (0,2), (0,3), so every interaction touches coordinate 0, the coordinate
`phi_D` collapses, and coordinate 4 is purely additive; at d = 3 the pairs are
(0,1), (0,2), (1,2) and the block is fully interactive), the `n_int = 3` arms of
the two d levels are not the same experiment in any useful sense.

So the answer to the question as posed: **reporting the two strata separately is
necessary but not adequate.** Stratification fixes the *pooling* problem; it
cannot fix the fact that within the `n_int = 3` stratum the two arms differ in
saturation (100% vs 30%) *and* in placement, and that this stratum is where the
entire effect lives. With 4 blocks per stratum nothing can be concluded from
either.

**Recommendation.** Either (a) demote every `interaction_pairs = 3` comparison
to descriptive and let `interaction_pairs = 0` — where saturation and placement
are both trivially matched, since there are no pairs — carry the inferential
weight; or (b) take the option the preflight already priced (`interaction_pairs
= [0, 10]` at d = 5, saturation-matched, ~1.5× core-hours, still inside the
20-hour cap). Option (a) is free and is the only comparison in the current
design that is confound-clean on C2 and C3. It is worth noting that it is also
the stratum where E1a's effect is least distinguishable from zero.

### MAJOR-4 — The BH family size is data-dependent, which breaks the pre-registration and creates a directional incentive. Q2 discloses the coupling but understates it.

**The coupling is real.** Demonstrated (`council_sci/p4_power_strata_bh.py`):

```
p = (0.030, 0.040, 0.600)  m=3 -> q=(0.0600,0.0600,0.6000)  confirmed 0
                           m=2 -> q=(0.0400,0.0400)          confirmed 2
p = (0.030, 0.040, 0.200)  m=3 -> q=(0.0600,0.0600,0.2000)  confirmed 0
                           m=2 -> q=(0.0400,0.0400)          confirmed 2
p = (0.012, 0.045, 0.900)  m=3 -> q=(0.0360,0.0675,0.9000)  confirmed 1
                           m=2 -> q=(0.0240,0.0450)          confirmed 2
```

Dropping a *null* third hypothesis flips both surviving clauses from
not-confirmed to confirmed. `advisor_confirmation_requested.Q2` states this
("this is not a neutral change to the other two clauses") — correctly, but only
as a consequence of the advisor choosing a *stricter threshold*. The deeper
problem survives any threshold he picks: **under the frozen value of 4, whether
E1c is in the family is decided by the data.** The count encoder's merges are
random sampling ties (01A's own `measured_caveat_recorded_at_A0`), so
`effective_n_blocks` for E1c is a random variable; and it is correlated with
block composition, because `marginal` is a block-key factor and drives tie
frequency (my C2 table: zipf/n=5000 has zero ties at d = 3). A BH family whose
size depends on the realised data is not a pre-registered family.

**Other couplings I checked.**
- `D14.denominator_tolerance` says NOT_IDENTIFIED counts are "subtracted from
  the effective n of every quantity that uses them" — a second data-dependent
  path into the same `effective_blocks_min` gate. Measured headroom says it will
  never fire (min denominators 0.00786 / 0.00390 vs 1e-6; my independent value
  on one draw: 0.00866 / 0.00430), so this path is dormant. No action needed.
- `effective_blocks_min = 4` has **no counterpart for E1a or E1b**. If
  duplication or NOT_IDENTIFIED ever reduced their effective blocks below 4,
  D16 gives no rule at all. Asymmetric, and worth one line.
- Q3 (the fourth class) and Q4 (materiality) interact, as 01B itself notes. They
  do not interact with the family size.

**Recommendation.** Fix `m = 3` unconditionally: E1c stays a family member and
contributes its p-value even when reported descriptively, or — cleaner — drop
BH entirely. E1a/E1b/E1c are explicitly *not* acceptance criteria and *not*
validity gates (`e1_remains_not_an_acceptance_criterion`); three pre-registered
expectations that gate nothing do not need FDR control, and reporting three
unadjusted one-sided p-values with the family stated is both simpler and
immune to this failure. Whatever is chosen, the family size must not be a
function of the data.

### MAJOR-5 — At (M, K) = (5, 4) `hash_shared` is not a hash. Its partition is exactly the multiset-of-values partition, at every frozen bucket width.

**Evidence** (canonical partition comparison, not label comparison):

```
hash_shared PARTITION identical B10/B20: True   B10/B40: True   fibers 56/56/56
hash_shared B10 partition == multiset-of-values partition: True  (56 = C(4+5-1,5))
hash_column PARTITION identical B10/B20: False                  fibers 240 / 363 / 768
max |rel_log(B0) - rel_log(B1 or B2)| over 8 blocks x 3 deltas x 4 reps x 2 d = 2.209e-14
```

**This confirms D16 E1a's collapse premise** — B0/B1/B2 really are one piece of
evidence, and entering them as three BH members would triple-count one
partition. That part of the amendment is right. But the reason is structural,
not incidental: with only K = 4 shared tokens the bucket-count vector is a
sufficient statistic for the multiset of coordinate values, so `hash_shared` at
this configuration is an exact bag-of-values (exchangeability) encoder that
destroys column identity and nothing else, and the B-invariance would hold for
any B ≥ 4. It also explains, without appeal to hashing, why the partition cannot
depend on d.

**Recommendation.** Say this in the freeze and in the caption. Describing an
exchangeability encoder's ~85% relative representation loss (measured: 0.85 at
d = 3, S1B-0001) as a *hashing* result invites a referee to ask what the bucket
width is doing, and the answer is "nothing, verifiably". Corollary for E1b:
`hash_column`'s widths are genuinely distinct partitions (240 / 363 / 768
fibers), so averaging B0 and B1 mixes two different encoders — defensible as the
advisor's narrow-width statistic, but the B2 secondary is the one carrying the
strongest signal (−0.073, t = −9.9) and must not read as an afterthought.

---

## 3. Answers to the seven questions, stated plainly

**Q1 — is the stress-test reframing honest?** The *framing* is honest; the
*inference licence* is not yet closed. What can be concluded if every gate
passes: that at (M, K) = (5, 4), under this specific DGP, an arm in which all
five coordinates carry signal and total signal is 3–44% larger produces a
larger/smaller absolute (respectively relative) representation loss for these
encoders, averaged over one arbitrary 2 × 2 × 2 factor grid. What cannot be
concluded: anything about dimensionality per se (C1/C2/C3), anything about
`hash_shared`'s *mechanism* (its partition is identical in both arms — the
freeze says this itself), anything generalizing beyond the frozen grid (MAJOR-1),
and — given MAJOR-2 — any negative claim from a non-significant normalized
result, because the design cannot detect the effect that exists. The one gap in
the framing is CRITICAL-1: "stress test" does not tell a reader what to do when
the stress test's raw and normalized readings point opposite ways.

**Q2 — the algebra.** Verified, both parts.
`eta_raw` (sim1_core.py:156-162) returns `1/(1+exp(-tau*g))`; the realised
posterior is `impose_delta_eta(...) = 0.20 + 0.60*m(f) + (Δ/2)*s`, still a
probability in [0.05, 0.95]; `bayes_risks_x` (sim1_core.py:256-259) defines
`R_Brier*(X) = E[eta(1-eta)]`. Hence, with `Y | X ~ Bern(eta)`,
`Var(Y) = E[Var(Y|X)] + Var(E[Y|X]) = E[eta(1-eta)] + Var(eta) = R_Brier*(X) +
Var{eta(X)}`, so **`Var{eta(X)} = Var(Y) − R_Brier*(X)`. CONFIRMED**, residual
1.11e-16 in 01B's own check and **2.60e-18** in mine (`p1`, independent
recomputation `p(1−p) − E[eta(1−eta)]` vs `E[(eta−p)²]`). D14's
`do_not_correct` warning is right and should stay.
**The two denominators are genuine analogues**: both equal
`R*(best constant) − R*(X)`. For log loss the best constant is `p = E[Y]` with
risk `H(Y)`, so the denominator is `I(X;Y)`; for Brier the best constant is `p`
with risk `Var(Y)`, so the denominator is `Var{eta(X)}`. Same object on two
scales.
**Do they neutralise the signal-strength difference? Substantially, but not
fully, and the residual is the same size as the effect.**
- At fixed d, sweeping τ over a 16-fold range (0.25 → 4.0) moves the RAW gap by
  up to **17.4×** and the NORMALIZED gap by only **0.5%–5.9%** (`p2`, 8 factor
  cells, hash_shared B0). So normalization removes the first-order scale effect.
- But the C1 confound is small (sd(eta) ratio 1.03–1.44), and so is the effect.
  The direct signal-matched counterfactual (`p2b`: raise τ at d = 3 by bisection
  until sd(eta) matches the d = 5 arm, then recompute the normalized gap) gives,
  averaged over 24 conditions: hash_shared normalized contrast −0.0311, of which
  **+0.0063 (20%) is the residual signal-strength part**; hash_column B0
  −0.0149 of which **+0.0258 — larger than the contrast itself**; B20 −0.0353 of
  which +0.0228 (65%); B40 −0.0777 of which +0.0260 (34%). Sign agreement
  between the normalized and the signal-matched contrast: 24/24 (hash_shared,
  B40), 22/24 (B20), 19/24 (B10).
**Verdict on Q2: partial neutralisation.** Directionally reliable, quantitatively
not — the residual confound is 20–170% of the normalized estimate depending on
encoder. D14's insistence that this is a sensitivity analysis and "must not be
described as removing … confounding" is exactly right and is supported by these
numbers. I recommend putting these numbers into the freeze so the caveat is
quantitative rather than rhetorical.

**Q3 — interaction saturation.** Not adequate. See MAJOR-3: stratification fixes
pooling but leaves saturation *and* placement confounded inside the stratum that
carries the whole effect, at 4 blocks / 3 df.

**Q4 — 7 df and the block key.** 7 df is not adequate (MAJOR-2: MDE 0.028
against a true effect of 0.018). The block key is wrong in its *stated
rationale*, not in its construction: excluding `delta_eta` and `n_train` is
correct and necessary — it is what makes the within-DGP contrasts paired, and
the frozen twin confirms it (400 seeds = 8 × 50). What it does **not** do is
reduce the number of independent draws to 8 (MAJOR-1: 400). And two further
dependencies the clustering does not capture: (i) the population quantities are
*exactly* invariant to `n_train` for `hash_shared`, `label`, `onehot`, `homals`,
so within each block the 6 scenarios are 3 distinct values duplicated — 01B
discloses this for representation loss; (ii) the d = 5 and d = 3 arms use
**disjoint** seeds, so the contrast is unpaired at the draw level and carries
between-draw variance from both arms. Measured: draw-level SE of a block mean
0.0122, i.e. the unpaired component is ~18% of the clustered variance.

**Q5 — the two extensions.** `effective_blocks_min = 4` is sound as a *number*
(3 or fewer gives ≤ 2 df) and freezing some number before the run is correct.
The coupling the other agent observed is **real and I reproduced it** (MAJOR-4):
dropping a null E1c from m = 3 to m = 2 flips both E1a and E1b from q = 0.060 to
q = 0.040. But the coupling is not a property of the threshold's strictness — it
is a property of the family size being data-dependent at all. Fix m.
`INCONCLUSIVE_REPORTED_IN_FULL` is **sound**: the advisor's three classes are
genuinely non-exhaustive (a positive normalized estimate with q ≥ 0.05 and a
non-positive raw contrast satisfies none of them), and absorbing that case into
one of the three would be a reporting decision made by omission. Two caveats:
(a) it is *less* conservative than folding the residual into NOT_SUPPORTED, so
the headline count must never be reported as "n not refuted"; (b) Q3's worked
example is the mirror image of the case that will actually occur (CRITICAL-1),
so the class as motivated will probably never fire while the case that needs a
name has none.

**Q6 — the BH family and the E1a collapse.** The partitions **are** identical —
verified as partitions, not labels: `hash_shared` at B ∈ {10, 20, 40} gives the
same 56-class partition, equal to the multiset-of-values partition, and the
relative gaps agree to 2.2e-14 over 8 blocks × 3 deltas × 4 replicates × 2 d
levels. Collapsing B0/B1/B2 to one member is **correct**. The multiplicity
correction is nonetheless **not right**, for a different reason: the family size
is data-dependent (MAJOR-4), and the family is applied to three hypotheses that
are declared not to gate anything, which is FDR control without a decision to
control.

**Q7 — anything else.** See §4.

---

## 4. MINOR findings

- **MINOR-1 — A1 buys nothing for the E1a/E1b primary statistic.** The
  normalized gaps are population quantities; the ~8.555 calibrated core-hours
  purchase learner shortfall, ROC/PR-AUC and finite-sample behaviour only. The
  resource memo should say so, and the acceptance report should not present the
  primary E1 numbers as an outcome of the run.
- **MINOR-2 — `fiber_count` is two different quantities under one column name.**
  Hash encoders: cardinality on the full `K**M` space (both arms). Coordinate-wise
  encoders: cardinality on the `K**d_active` active block (64 at d = 3, 1024 at
  d = 5). Any threshold, filter or figure that reads `fiber_count` across
  encoders is comparing incommensurable numbers. Add an explicit
  `fiber_count_space` column.
- **MINOR-3 — no low-power fallback for E1a/E1b.** `effective_blocks_min` exists
  only under E1c.
- **MINOR-4 — the "only exact arm" claim is overstated.** The preflight (§3)
  says the dense arm is "the only 1B configuration in which every reported
  quantity … is an exact population quantity". The d = 3 twin at (M, K) = (5, 4)
  satisfies `hash_gap_identified` identically (`4**5 = 1024 ≤ ENUM_CAP`), and in
  both arms the *risks actually stored by the finite runner* are Rao-Blackwellised
  MC over 50,000 evaluation rows (`run_sim1b_finite.py:215-221`), not population
  sums. What is new in the d = 5 arm is that the runner *additionally* persists an
  exact population layer (`pop_*` columns). Worth restating precisely.
- **MINOR-5 — NOT_IDENTIFIED will never fire.** Independently confirmed: min
  observed denominators 0.0087 (log) and 0.0043 (Brier) on my probe, consistent
  with 01B's 0.00786 / 0.00390 — ~4,000× the 1e-6 tolerance. The guard is
  correct and dormant; no change needed.
- **MINOR-6 — D14 `estimands` assigns `PRIMARY` to two different things.**
  Rename one. This is the textual surface of CRITICAL-1.

---

## 5. What I could NOT verify

- Whether the A1 analysis code (not yet written) will compute the d = 3
  `relative_log_gap` at all, and how — CRITICAL-3 is a *specification* gap; I
  cannot test code that does not exist.
- E1c's realised d = 5 fiber counts. The count encoder is fitted on training
  samples, so its merges depend on draws I would have to simulate; I verified
  the d = 3 side from the frozen parquet only and inferred the d = 5 side from
  01A's recorded sweep.
- The block-resampling bootstrap (B = 2000, seed 90210) implementation — I
  checked the t-interval arithmetic only.
- Every non-statistical D15/D17/D18 item (manifest coverage, typed failure rows,
  `exact_or_mc` labels, runner tests). Other seats own those; I read D17's
  AMENDMENT-1 and found its reasoning about G1's structural blindness to fiber
  *construction* defects correct, but I did not re-run the injected-defect
  harness.

---

## 6. Verdict

# DO NOT EXECUTE AS AMENDED

Not because the science is unsalvageable — it is not, and the honesty of the
disclosure apparatus is well above what I usually see — but because three things
must be fixed first, and two of them cost minutes:

1. **CRITICAL-2**: `fiber_count < 1024` is vacuous at d = 3. One-line rule change
   plus a re-run of the non-emptiness check. Blocking, because E1c's stratum
   definition currently determines the BH family size.
2. **CRITICAL-3**: freeze how the d = 3 arm's normalized denominators are
   produced. Blocking, because the primary estimand is otherwise undefined for
   half the contrast and will be improvised at A1.
3. **CRITICAL-1**: the raw/normalized reversal. Blocking, because it is not a
   risk — it is the determined outcome, and the protocol currently gives two
   contradictory instructions about which reading is the finding.

MAJOR-1 (correct the "8 draws" premise) and MAJOR-4 (fix the BH family size)
should ride along; both are text changes. MAJOR-2 and MAJOR-3 are honest
limitations that must be stated, not fixed — unless the advisor takes the
saturation-matched `interaction_pairs = [0, 10]` option the preflight already
priced.

## 7. The single most important thing the advisor must decide

**Which scale is the finding.** At the exact population level the raw d = 5
minus d = 3 representation-loss contrast is **positive and well powered**
(hash_shared +0.0092, t = +4.64, 8/8 blocks), while the signal-normalized
contrast — the one D16 makes primary — is **negative** (−0.0182, 1/8 blocks
positive; hash_column −0.0518, t = −2.64). D14 calls the normalized quantity a
sensitivity analysis; D16 makes it the sole basis of the verdict. He must choose
one as the headline before A1, because after A1 the choice is made with the
numbers in hand. My own reading, offered as opinion and not as a
recommendation he is obliged to take: the normalized reading is the more
defensible one — it says the entire raw dense-signal effect, and more, is the
C1 confound — but it is also the one his own design cannot power (MDE 0.028
against a true 0.018), so whichever he picks, the power statement has to go in
the same sentence.

---

## 8. Provenance

Scripts (all in `<SCRATCHPAD>/council_sci/`, nothing written to the repository):

| script | what it establishes |
|---|---|
| `p1_d3_denominators.py` | 05b carries no `p_y`/`entropy_y`/`var_eta_x`; stored d = 3 risks are MC (Δ ≈ 1×mcse vs exact); `Var{eta} = Var(Y) − R_Brier(X)` residual 2.6e-18 |
| `p2_normalization.py` | τ-sweep at fixed d: raw gap moves up to 17.4×, normalized gap 0.5–5.9% |
| `p2b_signalmatched.py` | signal-matched counterfactual; residual confound 20–170% of the normalized contrast |
| `p3_predict_E1.py` | exact block-clustered E1a/E1b primary statistics; hash_shared width identity 2.2e-14 |
| `p4_power_strata_bh.py` | strata split, MDE at 8 and 4 blocks, BH m = 3 vs m = 2 flip |
| `p5_variance_decomp.py` | 400 draws not 8; 81.7% of clustered variance is condition heterogeneity |

Read-only repository probes: `05b_SIM1B_REPLICATE_RESULTS.parquet` (schema,
`fiber_count` by encoder, count-encoder tie table), `sim1_core.py`,
`run_sim1b_finite.py`, `run_sim1b_dense_addendum.py`,
`01A_ADDENDUM_PROTOCOL_FREEZE.yaml`, `01B_ADDENDUM_ADVISOR_RULINGS.yaml`,
`S0A_ADDENDUM_PREFLIGHT_REPORT.md`.

`git status --porcelain` before this review and after: byte-identical
(8 modified + 13 untracked, all pre-existing A0.1 work). No git write command
was run. No file under `/Users/Eric/Desktop/114/碩論/` was touched.
Addendum cells executed: 0. Real-data models: 0. GPU hours: 0.


---

## 10. Seat 4 — CLAUDE, adversarial implementation (supplementary) — VERBATIM

Dispatched 2026-08-24 22:41:18 as a fresh-context subagent with no authorship of any
reviewed artefact and no sight of the host's reasoning; output captured 23:14:38
(~33 min). Mandate: make the A0.1 gates PASS while the science is WRONG. All mutation work
was done in `<SCRATCHPAD>/adv/repo`, a byte-copy of the repository. Repository writes: zero.
Addendum cells executed: zero.

Retained as a supplementary seat under the same treatment Phase A0 gave its two Claude
reviewers: **it does not substitute for either mandated provider seat**, both of which
were filled for real (§1).

# Supplementary council seat — ADVERSARIAL IMPLEMENTATION review of Phase A0.1

Seat: council-Claude (adversarial implementation).
Date: 2026-08-24.
Mandate: make the A0.1 gates PASS while the science is WRONG. Every claim below was
executed, not reasoned about.

## Method

A byte-copy of the repository was made at
`<SCRATCHPAD>/adv/repo` (heavy `raw/` and `08_SIM1_FIGURE_DATA.csv` symlinked read-only).
Every mutation was applied to that copy and reverted; the harnesses are
`<SCRATCHPAD>/adv/mutate.py`, `atk.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk7.py`,
`atk8.py`, `quant*.py`. Interpreter `/Users/Eric/.pyenv/versions/3.11.9/bin/python3`,
`PYTHONPATH=src`. Baseline: **1027 passed in 17.8 s**, reproduced before every mutation.

Prohibitions honoured: zero addendum cells run (all probes used
`n_eval` / `replicates` / `encoder_filter` / `learner_filter`, which the runner stamps
`NON_FROZEN_PROBE_NOT_AN_ADDENDUM_RESULT`); nothing written into the repository;
nothing under `碩論/` touched; no git write command; repo verified unchanged at the end.

---

# 1. Attack table

`SUCCEEDED` = the mutation produced materially wrong addendum numbers (or nullified a
gate) **and** the full 1,027-test suite still passed.

| # | Attack | Mutation | Suite | Result |
|---|---|---|---|---|
| A1a | wrong fiber assignment — hash cache key collision | `key = (Bw, enc=="hash_column")` → `key = (Bw,)` | 1027 pass | **SUCCEEDED — CRITICAL-2** |
| A1b | wrong hash diagnostics flag | `hash_diagnostics(..., enc=="hash_column")` → `enc=="hash_shared"` | 1027 pass | **SUCCEEDED — MAJOR-1** |
| A1c | unpair labels from features (n=500 tail slice) | `Xbig.iloc[:n_tr]` → `Xbig.iloc[-n_tr:]` | 2 failed | failed (gate holds) |
| A1d | wrong metric on `theoretical_gap` | `pop[f"theoretical_gap_{metric}"]` → `pop["theoretical_gap_logloss"]` | 1027 pass | **SUCCEEDED — MAJOR-2** |
| A1e | swapped d | `d_active=D_ADD` → `d_active=3` | 22 failed | failed (gate holds) |
| A1f | off-by-one / reversal of the active coordinate block | `Xev.iloc[:, :d_active]` → reversed columns | 1 failed | failed (gate holds) |
| A1h | encoder applied without OOF (all encoders) | `oof_train_codes` → `full_fit_mapping().transform` | 4 failed | failed (gate holds) |
| A1i | metric computed on the wrong column | `FIN.decompose(..., metric)` → swapped logloss/brier | 1027 pass | **SUCCEEDED — CRITICAL-3** |
| A1j | AUC computed against permuted labels | `roc_auc_score(yev, p)` → `roc_auc_score(yev[::-1], p)` | 1027 pass | **SUCCEEDED — MAJOR-3** |
| A1k | relative gaps built from the theoretical gap | `pop["gap_*"]` → `pop["theoretical_gap_*"]` | 1027 pass | failed — numerically a no-op (identity error 1e-16) |
| A2a | leakage confined to `target` / `woe` | OOF codes → full-fit codes for those two encoders only | 1027 pass | **SUCCEEDED — CRITICAL-4** |
| A2b | OOF seed off-by-one | `addendum_oof_seed(rep)` → `(rep+1)` | 1027 pass | **SUCCEEDED — MAJOR-4** |
| A2c | coordinate-wise fibers from the wrong mapping | substituted a `label` mapping | 1027 pass | failed — no numeric change |
| A2d | swap the two D14 denominators | `den_log` ↔ `den_bri` | 2 failed | failed (gate holds) |
| A2e | `p_y` as an unweighted mean of eta | `(p_cell*eta).sum()` → `eta.mean()` | 12 failed | failed (gate holds) |
| A2f | NOT_IDENTIFIED branch made unreachable | `den <= tol` → `den < 0` | 3 failed | failed (gate holds) |
| A2g | evaluation sample drawn on the training seed | `addendum_eval_seed` → `addendum_train_seed` | 2 failed | failed (gate holds) |
| A2i | D17 reference column filled from production | `reference_gap_report(...)` → `dict(pop)` | 1027 pass | **SUCCEEDED — CRITICAL-5** |
| A3a | **fiber-assignment permutation (hash)** | `fid = fiber_cache[key]` → `np.roll(fiber_cache[key], 1)` | 1027 pass | **SUCCEEDED — CRITICAL-1** |
| A3b | fiber-assignment permutation (coordinate-wise) | `np.roll(fid, 7)` + recomputed ebar | 1027 pass | SUCCEEDED (numerically inert at d=5: those encoders are injective) |
| A4a | the D17 harness's own hardcoded sampling rule | `s0b:160 return int(scenario_id[-4:])` → `return 1` | 1027 pass | **SUCCEEDED — MAJOR-5** |
| A4b | the D17 harness's addendum train-seed | `train_seed=ADD.addendum_train_seed` → `lambda s: s+100_001` | 1027 pass | **SUCCEEDED — MAJOR-6** |
| A4c | 01B rule replaced by a constant | `int(scenario_id[-4:])` → `int("0042"[-4:])` | 7 failed | failed (gate holds) |
| A4d | OOF seed loses its replicate dependence | `OOF_BASE+17*replicate` → `OOF_BASE+17` | 1 failed | failed (gate holds) |
| A4e | OOF seed *consumption* pinned to replicate 1 | `addendum_oof_seed(rep)` → `(1)` | 1027 pass | **SUCCEEDED — MAJOR-4** |
| A4f | conflate executed with successful rows | `executed = len(rows)` → count of successes | 2 failed | failed (gate holds) |
| A5a | AD4 status column fed D14's token | `theoretical_gap_status=IDENTIFIED_EXACT` → `rel[...]` | 1027 pass | **SUCCEEDED — MAJOR-7** |
| A5b | tolerance comparison at the cliff | `den <= tol` → `den < tol` | 1027 pass | SUCCEEDED — MINOR-1 |
| — | **duplicate typed rows on a late failure** | *no mutation — defect in the shipped runner* | n/a | **CONFIRMED — CRITICAL-6** |
| — | denominator instability near 1.0e-6 | measured all 1,200 distinct DGPs | n/a | failed — margin ≥ 5,676× (see §5) |
| — | resource ceiling breach | measured the uncosted population layer | n/a | failed — 0.033 core-h, 0.17% of ceiling (see §6) |
| R1 | backlog closure bite | revert to `REFERENCE_REPLICATES = (1,)` | 3 failed | **closure reproduces** |
| R9 | backlog closure bite | move `SEED_BASE_1BD` / `OOF_BASE_1BD` | 5 / 2 failed | **closure reproduces** |
| R10 | backlog closure bite | `_typed_failure_rows` ignores `learner_filter` | 2 failed | **closure reproduces** |

Counts: **6 CRITICAL, 7 MAJOR, 4 MINOR.**

---

# 2. CRITICAL findings

## CRITICAL-1 — A fiber-assignment PERMUTATION defeats both surviving D17 gates and the whole test suite

This is the fourth defect class the mandate asked for.

**Attack.** R2 established that `reference_gap_report` consumes the same `fid` as
production, so fiber-construction defects evade `|production − reference|`; the answer
was to add a second gate on recomputed-vs-stored `fiber_count`. A permutation of the
cell→fiber assignment preserves the number of fibers **and the multiset of fiber sizes
exactly**, so it evades the count gate as well.

**Mutation.** `scripts/run_sim1b_dense_addendum.py:948`
`fid = fiber_cache[key]` → `fid = np.roll(fiber_cache[key], 1)`

**Test suite.** `1027 passed`.

**Measured effect** (S1BD-0001, replicate 1, all six hash configurations, computed
directly from `sim1_core`):

| config | fiber_count true | fiber_count permuted | gap_logloss true | gap_logloss permuted | \|prod−ref\| permuted |
|---|---|---|---|---|---|
| hash_column/B0 | 240 | **240** | 0.00209971 | **0.00632796** (3.01×) | 1.11e-16 |
| hash_column/B1 | 363 | **363** | 0.00075091 | **0.00333397** (4.44×) | 9.99e-16 |
| hash_column/B2 | 768 | **768** | 0.000379244 | 0.000443197 | 2.22e-16 |
| hash_shared/B0–B2 | 56 | **56** | 0.0114325 | 0.0124225 | ≤1.11e-16 |

Through the runner, `relative_log_gap` for hash_column/B0 moves 0.1564 → **0.4715** —
the D16 E1a/E1b **primary statistic**, wrong by a factor of three, with
`abs_production_minus_reference_log` and `log_identity_error` both unchanged at ~1e-16
and `fiber_count` byte-identical.

**Independent confirmation on the D17 harness itself.** I added a `fiber_permute`
defect kind to a scratchpad copy of `scripts/s0b_reference_gap_check.py` and ran the
frozen d=3 arm (no addendum cell):

```
defect=none           prod_ref 3.442e-15   fiber_count matches 78/78   RESULT=PASS
defect=fiber_permute  prod_ref 3.997e-15   fiber_count matches 77/78   RESULT=FAIL  (1/78, incidental)
defect=fiber_merge    prod_ref 2.998e-15   fiber_count matches  0/78   RESULT=FAIL  (78/78)
```

The permutation is detected in **1 of 78 cells** at d=3, and by the table above in
**0 of 6** hash configurations at d=5. `fiber_merge` — the defect the harness was
designed against — is detected in 78 of 78. The gate discriminates size-changing
defects, not assignment-changing ones.

**Aggravating factor.** The harness already computes the one column that *would* catch
this — `stored_abs_diff_log_mc = |stored representation_loss − recomputed population
gap|` on the `bayes_z_oracle` rows — but it is **excluded from the pass criterion**:
`scripts/s0b_reference_gap_check.py:459` reads
`ok = (n_out == 0) and (fc_bad == 0)`, and `n_out` at line 449 is built from
`worst = max(log_identity_error, brier_identity_error, dlog, dbri)` only.

**Recommended fix (blocking).** Add a THIRD D17 gate on the stored-vs-recomputed
representation loss, which is already computed:

* include `stored_abs_diff_log_mc` / `stored_abs_diff_brier_mc` in the pass criterion at
  `s0b_reference_gap_check.py:459`, tolerance `mcse`-scaled (e.g. `≤ 6·stored_mcse_log`
  plus a floor), not `exact_identity_abs`; and
* add a property test that permutes `fid` and asserts the gaps move — the structural
  claim "the fiber partition is what carries the signal" must be testable.

Amend 01B `rulings.D17.evaluation_rule` to name three gates, and record that
`fiber_count` alone is invariant under fiber relabelling.

## CRITICAL-2 — The hash fiber cache key can collide `hash_shared` with `hash_column`

**Attack.** Wrong fiber assignment via a plausible refactor of the memo key.

**Mutation.** `scripts/run_sim1b_dense_addendum.py:945`
`key = (Bw, enc == "hash_column")` → `key = (Bw,)`

**Test suite.** `1027 passed`.

**Measured effect.** `hash_shared` at B1/B2 silently receives `hash_column`'s partition:
`fiber_count` 56 → 363 and 56 → 768; `pop_gap_logloss` 0.011433 → 0.000751 and
0.000379 (**15× and 30× wrong, in the conservative direction**); `relative_log_gap`
0.8518 → 0.0559 and 0.0283. `abs_production_minus_reference_log` stays at 1.1e-16.

**Why the suite is blind.** The only end-to-end fiber assertion is
`tests/test_a1_runner_smoke.py:396-398`, which probes `label` and `hash_shared` at the
DEFAULT width only and asserts `fc["hash_shared"] == 56` — the mutation leaves B0 (the
first-inserted key) correct, so the assertion passes on the value it happens to read.

This one *is* caught by the D17 `fiber_count` gate — but only if the addendum arm is
run with `--stored`, which is an A1-stage action, and only after 182,400 rows exist.

**Recommended fix.** Assert `fiber_count` per (encoder, width_label) across all six hash
configurations, not per encoder; and assert the six values are the frozen
`{56,56,56,240,363,768}` set.

## CRITICAL-3 — The metric argument to the decomposition can be swapped

**Attack.** "A metric computed on the wrong column."

**Mutation.** `scripts/run_sim1b_dense_addendum.py:999`
`dd = FIN.decompose(eta_ev, ebar_ev, p, metric)` →
`FIN.decompose(eta_ev, ebar_ev, p, "brier" if metric=="logloss" else "logloss")`

**Test suite.** `1027 passed`.

**Measured effect** (hash_shared/B1, logistic): the row labelled `metric = "logloss"`
carries `risk_x 0.6803 → 0.2436`, `risk_z 0.6915 → 0.2492`,
`representation_loss 0.011206 → 0.005534`, `learner_shortfall 0.009875 → 0.004749`,
`total_excess_risk 0.021081 → 0.010284`, `mcse 3.12e-4 → 1.53e-4` — i.e. the entire
finite-sample layer of every row is the other metric's. `theoretical_gap` is unaffected
(it is keyed on the true metric from `pop`), so the row becomes **internally
contradictory**: `representation_loss = 0.005534` against `theoretical_gap = 0.011433`.

**Why the suite is blind.** `test_decomposition_identity_on_the_probe` asserts only
`total_excess_risk = representation_loss + learner_shortfall`, which is metric-agnostic.
**No test anywhere compares a row's `representation_loss` against that row's
`theoretical_gap`** — grep of `tests/test_a0_dense_addendum_properties.py` finds
`theoretical_gap` used only as `theoretical_gap_status` at lines 572, 1104, 1108. That
comparison IS acceptance criteria AD1/AD2, and it exists in A0.1 as prose only.

**Recommended fix (blocking).** Add the AD1/AD2 pre-check as a runner-level property
test: for every probe row, `|representation_loss − theoretical_gap| ≤ k·mcse + floor`,
separately per metric. This single test kills A1i, and is the criterion the A1 gate will
have to apply anyway.

## CRITICAL-4 — Nine of the thirteen encoder configurations are never exercised end to end; label leakage can be reintroduced into `target`/`woe` invisibly

**Attack.** Wrong encoder application, confined to the encoders where it matters.

**Mutation.** `scripts/run_sim1b_dense_addendum.py:934` — replace the OOF code path with
full-fit codes **for `target` and `woe` only**.

**Test suite.** `1027 passed`.

**Measured effect** (S1BD-0001, replicate 1, logistic):

| cell | pristine `learner_shortfall` | leaky |
|---|---|---|
| target / logloss | 0.018156 | 0.020239 |
| woe / logloss | 0.015933 | **0.020291 (+27%)** |
| woe / brier | 0.007699 | **0.009329 (+21%)** |

**Root cause.** Every end-to-end probe in the A0.1 suite uses
`PROBE_ENCODERS = ("label", "hash_shared")` (`test_a1_runner_smoke.py:61`,
`test_a0_1_reconciliation.py:57`). `onehot`, `count`, `hash_column`(×3), `target`,
`woe`, `ordered_catboost_sim`, `homals` — **9 of 13 configurations, and every supervised
encoder** — never execute a runner path in any test. `label` is injective at d=5, so its
OOF and full-fit codes coincide, which is precisely why the general form of this
mutation (A1h) was caught and the targeted form was not.

**Recommended fix (blocking).** Add one end-to-end probe covering all 13 configurations
at a small `n_eval`, asserting per-encoder `fiber_count` and, for `target`/`woe`, that
the OOF path was taken (e.g. assert `Ztr` differs from `mp.transform(Xtr)`). This is
cheap: the label/hash_shared probe already runs in well under a second.

## CRITICAL-5 — The D17 reference column can be filled from production, and nothing fires

**Attack.** Defeat D17 by removing the independence it rests on.

**Mutation.** `scripts/run_sim1b_dense_addendum.py:963`
`ref = CORE.reference_gap_report(fid, tab.p_cell, tab.eta)` → `ref = dict(pop)`

**Test suite.** `1027 passed`.

**Measured effect.** `abs_production_minus_reference_log` 2.22e-16 → **exactly 0.0**;
`log_identity_error` 1.98e-16 → 1.73e-17. The D17 columns *improve*. Every AD1/AD2 check
passes perfectly, forever, on a reference that is a copy of the thing it certifies.

01B `rulings.D17.persisted_columns.forbidden` explicitly bans this derivation. It is
enforced by nothing — `test_reference_columns_present_on_the_frozen_reference_replicate`
asserts only that the columns are non-NULL and agree to tolerance, which is exactly what
the forbidden derivation guarantees.

**Recommended fix.** A test that monkeypatches `CORE.reference_gap_report` to a sentinel
and asserts the runner's `reference_log_gap` changes; plus a static check that
`reference_gap_report` is called on the reference-checked path.

## CRITICAL-6 — A late failure emits a DUPLICATE row for every cell already written as SUCCESS (defect in the shipped runner, not a mutation)

**Attack.** Typed-row accounting: find a path where one attempted cell yields more than
one row, with contradictory status.

**No mutation.** The config-level `except Exception` at
`scripts/run_sim1b_dense_addendum.py:1040-1052` re-emits a `TRAINING_FAILURE` row for
**every** `lrn × metric` of the configuration, including those for which SUCCESS rows
were already appended inside the `for lrn: for metric:` loop at lines 995-1039.

**Executed demonstration** (injected `ValueError` on the third `FIN.decompose` call;
encoder `label`, learners `bayes_z_oracle` + `logistic`):

```
rows emitted             : 6
distinct attempted cells : 4
DUPLICATED cells         : (S1BD-0001,1,label,'',bayes_z_oracle,logloss) x2
                           (S1BD-0001,1,label,'',bayes_z_oracle,brier)   x2
status counts            : SUCCESS 2, TRAINING_FAILURE 4
summarise(): rows_executed=6  rows_success=2  rows_failed=4
expected attempted cells : 4
```

The same primary key appears twice with contradictory status — once SUCCESS carrying
metrics, once TRAINING_FAILURE carrying NULLs. Consequences:

* AD6 (`executed rows == 182,400 exactly`) becomes **unsatisfiable** in the presence of
  any late failure; the arm silently exceeds its own frozen row count.
* `scripts/_s1_parallel.py:run_parallel` does no de-duplication (verified), so both rows
  reach the CSV and the parquet.
* Any downstream group-by on (scenario, replicate, encoder, width, learner, metric)
  silently double-counts the affected cells.
* This is exactly the D18-e / decision-D12 defect ("executed is not successful") in a new
  form: the count of ATTEMPTED cells again depends on which path the cell took — the same
  disease R10 fixed on the `learner_filter` axis.

The existing test `test_encoder_stage_exception_emits_typed_rows` injects at
`FIN.full_fit_mapping`, i.e. **before any row is appended**, and therefore cannot see it.

**Recommended fix (blocking).** Buffer the configuration's rows in a local list and
commit them to `rows` only on clean completion of the configuration; on exception,
discard the buffer and emit exactly one typed row per attempted cell. Add
(a) a test injecting a failure *after* the first metric row, and (b) a primary-key
uniqueness assertion over the emitted rows, promoted to an AD6 sub-criterion.

---

# 3. MAJOR findings

**MAJOR-1 (A1b) — the hash-diagnostic column-awareness flag is unpinned.**
`run_sim1b_dense_addendum.py:958` `hash_diagnostics(M, K, Bw, enc == "hash_column")` →
`enc == "hash_shared"` passes 1027 tests and turns `hash_column`'s diagnostics into
`hash_shared`'s: `collision_count` 12→0, 8→0, 4→0 and `occupied_buckets` 8→4, 12→4,
16→4 across B0/B1/B2. These are D18-d mandated columns closing known gap G1;
`test_fiber_and_hash_diagnostics_are_recorded` asserts only `is not None` and `> 0`.
*Fix:* assert the frozen `(collision_count, occupied_buckets)` pairs for all six hash
configurations against `TestCollisionsAndBucketsExact` (AT11) ground truth.

**MAJOR-2 (A1d) — `theoretical_gap` can be written with the wrong metric.**
`pop[f"theoretical_gap_{metric}"]` → `pop["theoretical_gap_logloss"]` passes 1027 tests;
every Brier row's `theoretical_gap` becomes the log-loss CMI (e.g. 0.0010286 →
0.0020997, 2.04×). Subsumed by the AD1/AD2 row-level check recommended in CRITICAL-3.

**MAJOR-3 (A1j) — `roc_auc` / `pr_auc` are ungated.** Computing the AUC against
permuted labels (0.5109 → 0.4831) passes 1027 tests. Not a D16 primary statistic, but
these columns are persisted and will be read.

**MAJOR-4 (A2b, A4e) — the seed rule is single-source in DEFINITION only, not in
CONSUMPTION.** `addendum_oof_seed(rep)` → `addendum_oof_seed(rep + 1)` and
→ `addendum_oof_seed(1)` both pass 1027 tests, and change every supervised encoder's
codes (target/logloss `learner_shortfall` 0.018156 → 0.020734, +14%). The suite pins the
seed FORMULAS exhaustively (2,400 seeds, R9) but never checks that a runner path
consumes the right argument. Contrast A4d — changing the formula itself — which fires
immediately. *Fix:* assert, on a two-replicate probe, that replicate r's OOF codes equal
`oof_train_codes(..., addendum_oof_seed(r))`.

**MAJOR-5 (A4a) — the D17 harness carries its OWN hardcoded copy of the sampling rule,
and it is unpinned.** `scripts/s0b_reference_gap_check.py:160` is a second
implementation of `reference_replicate`, hardcoded, not read from 01B. Setting it to
`return 1` — the very choice 01B's `why_not_replicate_1_for_all` declines by name —
passes 1027 tests. `read_frozen_replicate_rule()` (line 138) reads 01B only to PRINT the
rule; it never compares it to the function that is used. R1's implementation report
claims "there is no second copy of the rule … to drift from"; that is true of the runner
and false of the harness. `test_no_fixed_reference_replicate_constant_survives_in_the_runner`
inspects `run_sim1b_dense_addendum.py` only. *Fix:* have the harness import
`run_sim1b_dense_addendum.reference_replicate`, and extend the structural test to the
harness file.

**MAJOR-6 (A4b) — the D17 harness's addendum arm can silently rebuild a different
production.** `arm_addendum().train_seed = ADD.addendum_train_seed` →
`lambda s: s + 100_001` passes 1027 tests. For the seven coordinate-wise configurations
the harness's `fid` comes from `full_fit_mapping(Xtr, ytr, enc)`, so a drifted training
draw makes the harness's recomputed `fiber_count` refer to a different fit than the
stored production — the second D17 gate would then be comparing two different
experiments while reporting agreement or disagreement as if it were a defect signal.
*Fix:* a test asserting `arm_addendum().train_seed is ADD.addendum_train_seed` and
`arm_addendum().n_train_nest_max == ADD.N_TRAIN_NEST_MAX`.

**MAJOR-7 (A5a) — the R5 status separation is convention, not a gate.** Feeding the AD4
column D14's token (`theoretical_gap_status=rel["relative_log_gap_status"]`) passes 1027
tests. R5 says "the acceptance report MUST read the former for AD4. Verify this
survives." It survives in the current code but is unprotected. Worse, the *existing*
analysis code the A1 stage will reuse — `scripts/run_sim1_summarize.py:182`,
`scripts/run_sim1_figures.py:99, 244, 256` — filters on `theoretical_gap_status`, which
the addendum runner sets to the constant `IDENTIFIED_EXACT` on every SUCCESS row
(`run_sim1b_dense_addendum.py:1025`). Those scripts have no knowledge of
`relative_log_gap_status` / `relative_brier_gap_status`, so a D14-unidentified relative
gap would be plotted as identified. Unreachable today (see §5) but structurally live.
*Fix:* a test asserting the two token families never occupy each other's column, and an
explicit note in 01B that any addendum analysis must read `relative_*_gap_status` for
D14 and `theoretical_gap_status` for AD4.

---

# 4. MINOR findings

* **MINOR-1 (A5b).** `den <= tolerance` → `den < tolerance` passes 1027 tests. No test
  exercises `den == tolerance` exactly. Cosmetic today; pin it.
* **MINOR-2.** AD4 ("zero NOT_IDENTIFIED rows") is **unfalsifiable in the addendum
  output**: `theoretical_gap_status` is a hardcoded constant on every SUCCESS row
  (`:1025`, `:1038`), so a checker counting NOT_IDENTIFIED in that column can never
  fail. The underlying guarantee (`hash_gap_identified(5,4)`) is real; the *column* is
  not evidence. 01A's own hygiene note on AD3 says the same thing about AD3 — AD4
  deserves the same note.
* **MINOR-3.** The D17 rule whitelist does not enforce that the rule is a function of
  `scenario_id` at all. `RUN._d17_compile('int("0042"[-4:])')` is **ACCEPTED** and
  evaluates to the constant 42 for every scenario. The claim
  `frozen_replicate_rule.no_discretion` / "pure function of the scenario id" is enforced
  by `test_every_scenarios_reference_replicate_matches_01B` reading the on-disk 01B
  (which correctly fires: amending 01B to the constant rule fails 7 tests), not by the
  parser. *Fix:* require `scenario_id` (or `scenario`) to appear in the AST.
* **MINOR-4.** Non-SUCCESS `METRIC_UNDEFINED` rows carry `exact_or_mc="exact"` and
  `theoretical_gap_status="IDENTIFIED_EXACT"` (`:1036-1038`) while every population value
  on the row is NULL — a row asserting the exactness of numbers it does not contain.
  Related: on a single-class evaluation sample the SAME cell yields
  `METRIC_UNDEFINED` for `metric="logloss"` and `SUCCESS` with full metrics for
  `metric="brier"`, purely because `roc_auc` is a log-loss-row side metric. That is the
  R4 semantic gap in a second, asymmetric form and belongs in the advisor question.

---

# 5. Attack 5b — denominator instability near 1.0e-6: FAILED, with numbers

I evaluated both D14 denominators over **all 1,200 distinct DGP draws** of the frozen
design (24 distinct scenarios once `n_train` — which is not in the block key — is
deduplicated, × 50 replicates):

```
I(Y;X)      min = 0.0114824  p1 = 0.0138874  median = 0.0708036  max = 0.198603
Var{eta(X)} min = 0.0056766  p1 = 0.0068455  median = 0.0335951  max = 0.0855902
```

Minimum margins over the 1.0e-6 tolerance: **11,482×** (log) and **5,677×** (Brier).
The worst case is S1BD-0025 replicate 25 (zipf, tau=0.5, interaction_pairs=0,
delta_eta=0.0), `Var{eta} = 5.68e-3`.

Conclusions for the advisor: (a) there is **no cliff instability** — the NOT_IDENTIFIED
branch cannot fire in the frozen addendum, and the normalised estimands are numerically
well conditioned everywhere; (b) consequently the D14 NOT_IDENTIFIED machinery is
**dead code in this arm**, tested only synthetically, and AD4's "zero NOT_IDENTIFIED
rows" is satisfied by design rather than by observation. Both facts should be stated in
the A1 write-up rather than discovered later.

---

# 6. Attack 6 — resource projection: FAILED, and the projection is conservative twice over

I could not find an assumption that breaks the 20 core-hour ceiling.

**What is genuinely uncosted.** The 1.025065 d5/d3 ratio was measured on
`s0a_addendum_microbenchmark.probe_scenario`, which does **not** call
`CORE.exact_gap_report`, `hash_diagnostics` or `reference_gap_report` (verified by
reading `scripts/s0a_addendum_microbenchmark.py:225-305`). Those enter only through the
1.0069 runner-overhead factor, which the CSV itself concedes is "NOT resolved at n=2".
I measured them directly at d=5, 13 configurations, S1BD-0002 replicate 1:

```
exact_gap_report x13          0.0358 s
ebar_coordinatewise x7        0.0137 s
hash_diagnostics x6           0.0001 s   (uncached across the 50 replicates; immaterial)
population_signal_scales x1   0.0000 s
--------------------------------------------------
population layer per replicate 0.0498 s
  -> whole arm (2,400 replicate cells)  0.033 core-hours = 0.17% of the ceiling
reference_gap_report x13      0.0228 s per reference replicate
  -> whole arm (48 scenarios)           0.000304 core-hours
```

So the unmeasured middle term is worth ~0.03 core-hours. To breach 20 core-hours the
d-ratio would have to be wrong by **2.34×** against a 95% CI of [1.0131, 1.0364].

**Independent corroboration of the anchor.** From `S0B_RATIO_PROBE_ROWS.csv`,
`probe_scenario` at d=3 costs 5.10 s/replicate (n=500) and 6.92 s (n=5000)
single-process; the frozen twin's measured cost is 7.573 s and 10.219 s/replicate under
8 workers. Ratios 1.484 and 1.477.

**MINOR-5 (rationale, not arithmetic).** That 1.48 is numerically the same phenomenon as
the 1.4 "calibration". The CSV asserts both that "the ~1.4x 8-worker contention factor
is already inside [the anchor]" and that the 1.4 calibration is carried on top. Those
two statements cannot both be load-bearing; the 1.4 is being applied twice. Since both
directions are conservative and the uncalibrated figure (6.12 core-h, 30.6%) also passes,
the ceiling verdict is unaffected — but the rationale text should say "the anchor already
contains contention; the 1.4 is retained as pure margin, worth 2.45 core-hours", rather
than presenting it as an independent correction.

Verdict on Attack 6: the ceiling claim survives. 42.87% is if anything pessimistic.

---

# 7. Attack 7 — do the three backlog closures actually bite?

All three reproduce. Executed, not asserted.

| item | mutation | tests that fired |
|---|---|---|
| **R1** | reinstate `REFERENCE_REPLICATES = (1,)` in `scenario_worker` | **3**: `test_no_fixed_reference_replicate_constant_survives_in_the_runner`, `test_the_worker_marks_the_01B_replicate_and_not_replicate_one`, `test_reference_columns_present_on_the_frozen_reference_replicate` |
| **R9** | `SEED_BASE_1BD` 2_000_000_000 → 2_000_001_000 | **5**, including `TestS0AMicrobenchmarkSeedRuleHasNotDrifted::test_every_one_of_the_2400_seeds_agrees_with_the_runner` |
| **R9** | `OOF_BASE_1BD` 91_211 → 91_213 | **2**: `test_the_two_seed_bases_agree`, `test_oof_and_derived_channels` |
| **R10** | `_typed_failure_rows` iterates `DES.learners_for` instead of `_learners_for` | **2**: `test_failure_rows_are_filtered_exactly_as_success_rows_are`, `test_setup_exception_emits_typed_rows_not_a_silent_continue` |

One observation on R9's advertised bite: `test_the_pin_bites_when_the_runner_rule_moves`
monkeypatches `RUN.addendum_seed` itself, so it fires by construction and is not evidence
about the runner. The test that actually detects a real seed-base move is
`test_every_one_of_the_2400_seeds_agrees_with_the_runner`. Both were verified; the report
should credit the latter.

Also confirmed: amending the on-disk 01B rule to a constant fires **7** tests, so the
runner's "read the sampling rule from 01B" wiring is genuinely load-bearing (A4c).

---

# 8. What the gates DID stop — evidence of strength

Reported because failed attacks are the point. Eleven mutations were caught, several of
them subtle:

* label/feature unpairing on the n=500 arm (2 failures) — the nested-slice discipline is
  real, contrary to my expectation from reading
  `test_n500_is_the_prefix_of_the_n5000_draw_as_the_runner_slices_it`, which does not in
  fact exercise the runner path;
* `d_active=3` substituted at the draw (22 failures) — `verify_against_freeze` is
  effective;
* reversing the active coordinate block (1 failure);
* general OOF→full-fit substitution across all encoders (4 failures);
* swapping the two D14 denominators (2), unweighted `p_y` (12), disabling the
  NOT_IDENTIFIED branch (3), evaluating on the training draw (2), conflating executed
  with successful rows (2), removing the replicate from the OOF seed formula (1),
  amending 01B to a non-scenario rule (7).

The D14 estimand layer, the freeze-constant layer and the seed-formula layer are all
genuinely well defended. The weaknesses are concentrated in exactly three places: **the
fiber-construction layer, the finite-sample metric layer, and the nine encoder
configurations that no probe touches.**

---

# 9. Verdict

**DO NOT EXECUTE AS AMENDED.**

Not because the science is wrong — I found no defect in the shipped numbers except
CRITICAL-6 — but because the mandate was to test whether the gate is worth what it is
about to certify, and it is not yet. Six mutations that corrupt the D16 primary statistic
by factors of 3 to 30 pass all 1,027 tests, one of them (CRITICAL-1) while both surviving
D17 gates read clean, and one genuine defect (CRITICAL-6) makes AD6's exact row count
unsatisfiable the moment any cell fails late. A 182,400-row arm certified by this gate
would be certified against defects it cannot see.

The remedy is small and entirely pre-A1:

1. **CRITICAL-1** — add the stored-representation-loss gate to
   `s0b_reference_gap_check.py:459` and a fiber-permutation property test; amend 01B D17
   to a three-gate rule and record that `fiber_count` is invariant under relabelling.
2. **CRITICAL-3 / MAJOR-2** — add the AD1/AD2 row-level check
   `|representation_loss − theoretical_gap| ≤ k·mcse` per metric.
3. **CRITICAL-4** — one end-to-end probe over all 13 encoder configurations.
4. **CRITICAL-6** — buffer-and-commit the configuration's rows; add a primary-key
   uniqueness assertion and a late-failure injection test.
5. **CRITICAL-2 / MAJOR-1** — assert the frozen `fiber_count`, `collision_count`,
   `occupied_buckets` triples for all six hash configurations.
6. **CRITICAL-5, MAJOR-5, MAJOR-6, MAJOR-7** — pin the reference implementation, the
   harness's sampling rule, the harness's train seed, and the status-column separation.

None of these requires running an addendum cell; the whole suite runs in 18 seconds. I
would authorise A1 after a second A0.1 pass that lands items 1–4 and re-runs this
mutation battery, which is scripted and reusable at
`<SCRATCHPAD>/adv/`.

Two things the advisor should be told regardless of the fix list, because they change how
the A1 results must be written up:

* the D14 NOT_IDENTIFIED branch **cannot fire** in this design (margin ≥ 5,677×), so AD4
  and the NOT_IDENTIFIED apparatus are guarantees, not observations (§5);
* the resource ceiling is not at risk and is doubly conservative (§6); the 1.4
  calibration and the anchor's embedded contention are the same 1.48× phenomenon.

---

## Repository state

Baseline captured before work:
`<SCRATCHPAD>/gitstatus_council_claude_start.txt`, HEAD `02855025`.
All mutation work was done in `<SCRATCHPAD>/adv/repo`, a copy. No file under
`/Users/Eric/Desktop/114/ct2i-benchmark` and no file under
`/Users/Eric/Desktop/114/碩論` was written. No git write command was issued. Zero
addendum cells were run; the only non-probe execution was
`s0b_reference_gap_check.py --arm d3_frozen` on the pre-existing frozen d=3 twin, in the
scratchpad copy, writing to the scratchpad.


---

## 11. Provenance and integrity

**Source captures.** Each seat's text above is a byte-exact copy of its capture file:

| Seat | Capture file | Bytes |
|---|---|---|
| 1 — Codex | `<SCRATCHPAD>/COUNCIL_CODEX_RAW.md` | 20,251 |
| 2 — Antigravity / Gemini | `<SCRATCHPAD>/COUNCIL_ANTIGRAVITY_RAW.md` | 13,720 |
| 3 — Claude, statistical validity | `<SCRATCHPAD>/COUNCIL_CLAUDE_SCIENCE.md` | 36,410 |
| 4 — Claude, adversarial implementation | `<SCRATCHPAD>/COUNCIL_CLAUDE_ADVERSARIAL.md` | 33,030 |

Nothing was edited, trimmed, paraphrased or reordered. Each capture appears in §7–§10 as a
contiguous substring, verified byte-for-byte against its source after assembly.

**Supporting records.**
- `<SCRATCHPAD>/FACT_BLOCKS_VS_DRAWS.md` — the investigation that settled §5.1, with the
  probe scripts (`probe_params.py`, `probe_ntrain.py`, `probe_twin.py`) and a one-line
  reproduction of the decisive fact that needs no probe file.
- `<SCRATCHPAD>/ADVISOR_RULING_20260821.txt` — the binding ruling D13–D18 under review.
- `<SCRATCHPAD>/RECONCILIATION_BACKLOG.md` — the twelve pre-council items R1–R12.
- `<SCRATCHPAD>/PROVIDER_INVOCATION.md` — the live provider probes and the recording
  requirement this document satisfies.
- `<SCRATCHPAD>/prompt_codex.txt`, `<SCRATCHPAD>/prompt_agy.txt` — the byte-exact prompts.

**Write boundary.** `git status --porcelain` in `/Users/Eric/Desktop/114/ct2i-benchmark`
was captured before and after every seat and is byte-identical throughout (21 entries).
No seat wrote to the working tree. No git write command was issued by any seat or by the
host. Zero addendum cells were run. Zero real-data models were run. Zero GPU hours were
used. No file under `/Users/Eric/Desktop/114/碩論/` was read or written.

**Concurrency note.** A separate A0.1 implementation pass was running while this document
was assembled, amending `01B_ADDENDUM_ADVISOR_RULINGS.yaml`,
`scripts/s0b_reference_gap_check.py` and the test files — in particular landing the third
D17 detector that closes the fiber-permutation class (§4.1). This document does not record
the outcome of that work and does not guess at it. **The final status of Codex C4 and
seat 4's CRITICAL-1 is in `S0B_FINAL_GATE_REPORT.md`.**

---

## 12. Bottom line

**Four seats. Four negative verdicts. 16 CRITICAL findings across seats.**

No seat found the shipped *numbers* wrong — seat 4 states this explicitly: "I found no
defect in the shipped numbers except CRITICAL-6." The vetoes are about two things:

1. **The gate is not yet worth what it is about to certify.** Six mutations that corrupt
   the D16 primary statistic by factors of 3 to 30 pass all 1,027 tests, one of them while
   both surviving D17 gates read clean; and one genuine shipped defect makes AD6's exact
   row count unsatisfiable the moment any cell fails late. Codex reached the same class of
   conclusion by reading alone.
2. **The inference scheme rests on a premise that is false, and the primary statistic is
   already determined and points the opposite way from the raw one.** D13's "8 independent
   parameter draws" is refuted by the generating code and by the repository's own frozen
   test; and the D16 primary normalized contrast is negative while the raw contrast is
   positive at t = +4.64 in 8/8 blocks, with D14 and D16 giving contradictory instructions
   about which is the headline.

The first is an engineering pass measured in hours and requires no addendum cell. The
second is the advisor's to rule on, and **must be ruled on before A1**, because after A1
the choice is made with the numbers in hand.

`NEXT ACTION: WAIT FOR ADVISOR APPROVAL BEFORE FULL A1 EXECUTION`
