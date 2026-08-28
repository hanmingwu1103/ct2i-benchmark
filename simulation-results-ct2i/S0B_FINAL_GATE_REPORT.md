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

# S0B — FINAL GATE REPORT (Phase A0.1)

The closing document of Phase A0.1. Written 2026-08-25, **revised the same day by
the whole-package consistency pass** (which corrected §6.3's framing of the
"82%" figure, added ERRATUM E-1 and the §3 DISPOSITION UPDATE, and closed all
six contradictions in §10). Interpreter
`/Users/Eric/.pyenv/versions/3.11.9/bin/python3` (never conda `t2i`).
Every number below was observed by running the command named beside it; §10
lists the commands and their raw output.

---

## 1. VERDICT

**A0.1 is COMPLETE as work and BLOCKED as a gate.**

All eight required A0.1 deliverables exist. Zero full addendum cells were run —
`find simulation-results-ct2i -iname '*dense_addendum*'` returns nothing, no file
under `raw/` has an mtime later than 2026-08-12 19:55, and the runner's
`--dry-run` ends `No cell executed.` Zero real-data models, zero GPU hours.

**Phase A1 must not begin.** *(Terminal update 2026-08-25: Phase A1 will never begin. The
advisor discontinued the addendum permanently rather than settle the three matters below;
they are closed by termination, not by ruling.)* The block is not a defect in the runner and not a
missing artefact. It is three substantive matters that only the advisor can
settle, listed in §2. Two of them determine *which numbers A1 computes*; one
determines whether a pre-registered stratum exists at all. Running A1 before
they are settled produces numbers that would have to be discarded.

All four council seats returned a negative verdict (§3). Sixteen CRITICAL
findings stand across seats. Nine of them were closed at A0.1 by implementation
(§4); the rest are design and inference questions that no implementation can
close (§5).

---

## 2. THE THREE THINGS THE ADVISOR MUST DECIDE FIRST

Ranked. Nothing below §2 changes the decision as much as these three.

### 2(a) — D13's premise is FALSE, and the error came from the A0 report, not from the ruling

**The advisor ruled correctly on what he was given. What he was given was wrong.**

D13 ACCEPTED block-clustered inference on "8 independent parameter-draw blocks"
with 7 degrees of freedom. That premise was delivered to him by the Phase A0
council record as **CONFIRMED**:

> `S0A_ADDENDUM_COUNCIL_REVIEW.md:62` — "The 48 scenario pairs are not 48
> independent units: the block key excludes `delta_eta` and `n_train`, so they
> cluster into **8** parameter-draw blocks. … **CONFIRMED.**
> `df[(df.M==5)&(df.K==4)].seed.nunique() == 400`"

The premise is false. **Parameters are drawn afresh for every replicate.**

**Deciding code path.** `scripts/run_sim1b_dense_addendum.py:871-872` calls
`CORE.draw_params(..., seed, d_active=5)` **inside** the replicate loop opened at
`:866`, with a seed that contains the replicate
(`addendum_seed()`, `:316-327`: `seed = base + 1000*(blake2b(block)%1e6) + replicate`).
`src/ct2i_benchmark/simulations/sim1_core.py:132-153` reseeds
`np.random.default_rng(seed)` on entry, so a different seed is a different `a`
and a different `b`. The frozen d=3 partner uses the identical construction at
`sim1_core.py:471-482`.

**Measured in this session** (regenerating parameters only; no cell executed):

| observation | value |
|---|---|
| distinct blocks over the frozen 48-scenario grid | 8 |
| distinct (block, replicate) seeds | **400** |
| distinct `(a,b)` byte signatures over those 400 seeds | **400** (zero collisions) |
| `max abs(a(r1) − a(r2))`, block `('uniform',0.5,0)`, replicates 1 vs 2 | **2.2952915731512284** — never 0.0 |
| `max abs(da)` across the 3 `delta_eta` levels at fixed (block, replicate) | **exactly 0.0** |
| frozen twin `05b` at M=5,K=4: rows / `seed.nunique()` / scenarios | 182,400 / **400** / 48 |

**D13's own cited evidence refutes it.** `seed.nunique() == 400` is a count of
*distinct DGP seeds*, and `draw_params` reseeds on every call, so 400 seeds are
400 parameter draws. The line was read backwards. 01B now records this
withdrawal at `rulings.D13.corroborating_frozen_twin_MISREAD_CORRECTED_BY_AMENDMENT_3`
(01B:490-498).

**The repository already asserted the truth.** `tests/test_a0_dense_addendum_properties.py::TestAddendumBlockPairingPreserved::test_replicate_still_varies_the_draw`
asserts `not array_equal(p1.a, p2.a)` for replicates 1 and 2 of one block. It
passes (verified: 5 passed, 276 deselected). It sat one file away from the
`addendum_block` docstring, which stated the opposite as fact, while the runner
printed `parameter-draw blocks (D13)     8  (7 df)` on every `--dry-run`.
**Both were corrected on 2026-08-25** (`scripts/run_sim1b_dense_addendum.py`):
the docstring now states the block structure factually, records what the
exclusions actually buy, and points at 01B Q6; the dry run now prints
`design blocks … 8`, `parameter draws per arm … 400` and
`inferential unit … OPEN -- 01B Q6`. The runner asserts no premise this phase
refuted. Its return values, the 182,400 projection and the seed rule are
unchanged.

**The correct unit.** The cluster is `(block, replicate)` — 400 per arm, cluster
size 6 (the 3 `delta_eta` × 2 `n_train` scenarios that share one draw). The 8
blocks are a complete, exhaustively enumerated 2×2×2 factorial of *fixed* design
factors (`run_sim1b_dense_addendum.py:277-279`); between-block spread is designed
heterogeneity, not sampling error. With block as a fixed effect, df ≈ 392 per
arm. This is the A0 council's own argument
(`S0A_ADDENDUM_COUNCIL_REVIEW.md:229`: "`sd` across a fixed, exhaustively
enumerated factorial grid is designed heterogeneity, not Monte Carlo error")
applied one level up, where it holds verbatim.

**The consequence that matters — conservatism is NOT the safe choice here.**
D16's E1 clauses are **one-sided greater** tests
(`01B rulings.D16.common_statistic.directionality: "one-sided, greater"`). An
inflated standard error does not buy caution; it manufactures null conclusions,
and `D16.outcome_classifications` converts null outcomes into reported findings
(`NOT_SUPPORTED`). D13 as written discards roughly 385 degrees of freedom on the
side of a design that is already underpowered. Measured on the E1a exact
contrast, **55.1%** of the variance of the 8 block means is fixed-factor
heterogeneity rather than draw noise (`s0b_d13_premise_probe.py --section
variance`; see §6.3 for why 55.1% and not the earlier 81.7%). On the frozen twin
the parallel method-B share is 14.9%–56.8% with `SE(8 blocks)/SE(48 scenarios)`
ratios 1.00–1.95. Either way, a substantial part of the SE D13 mandates is
fixed-factor heterogeneity being priced as noise.

Secondly, E1c's restriction is defined per (block, replicate, scenario). Under a
collapse to 8 block means it cannot be applied coherently, and its
`effective_blocks_min = 4` fallback can fire for a purely artefactual reason.
Fixing the unit fixes E1c's arithmetic too.

**Status.** 01B `rulings.D13.status` is now
`PREMISE_REFUTED_ADVISOR_RULING_REQUIRED`, and it is the **only** open item in
the package with no operative default: `01B:1782-1788` states
`NEITHER SCHEME IS OPERATIVE … A1 inference is BLOCKED on this question.`
*(Terminal update: neither scheme ever became operative, and neither ever will — no A1
inference exists to govern. Closed by termination.)*
It is raised as **Q6**, `severity: BLOCKS_A1_INFERENCE`, `highest_priority: Q6`.

**What the advisor is being asked.** Not to accept the correction — to choose the
estimand. If the target is the frozen grid, the unit is the draw (400, df ≈ 392,
bootstrap resampling draws stratified within block). If he deliberately wants the
estimand to generalize to a *population of conditions* beyond this grid, blocks
become the random unit and 7 df is defensible — but that is an estimand choice
and must be stated as one. D13 currently states it as a fact about parameter
draws, and that fact is false.

### 2(b) — D14 and D16 point OPPOSITE WAYS on the same data, and the data already exist

The E1 primary statistic is a **pure population quantity**. It needs no learner,
no training sample, and no addendum cell. It is computable today, and it has been
computed. Reproduced independently in this session (4.6 s, zero cells run,
`scratchpad/council_sci/p3_predict_E1.py`, exact 1024-state algebra):

```
E1a hash_shared  PRIMARY normalized log          est = -0.01815  SE 0.01007  t = -1.80  blocks>0: 1/8
E1a hash_shared  supporting normalized Brier     est = -0.01967  SE 0.01037  t = -1.90  blocks>0: 1/8
E1a hash_shared  RAW log-loss contrast           est = +0.00919  SE 0.00198  t = +4.64  blocks>0: 8/8
E1b hash_column  PRIMARY normalized (mean B0,B1) est = -0.05182  SE 0.01961  t = -2.64  blocks>0: 2/8
E1b hash_column  supporting normalized Brier     est = -0.05349  SE 0.01967  t = -2.72  blocks>0: 2/8
E1b hash_column  RAW log-loss contrast           est = +0.00129  SE 0.00209  t = +0.62  blocks>0: 6/8
E1b secondary B2                                 est = -0.07253  SE 0.00733  t = -9.90  blocks>0: 0/8
```

**On the raw scale E1 is confirmed and well powered: +0.0092, t = +4.64, positive
in 8 of 8 blocks. On the normalized scale it is negative: −0.0182 for E1a,
−0.0518 (t = −2.64) for E1b.**

The two rulings give opposite instructions about which of these is the finding:

- **D14** stamps the normalized analysis `label: SENSITIVITY_ANALYSIS`
  (01B:884-890) and marks the raw gaps `PRIMARY_ALWAYS_REPORTED` (01B:790).
  The advisor's own ruling text: *"The normalized analysis is a sensitivity
  analysis and must not be described as fully removing confounding."*
- **D16** makes the normalized log-loss gap the **verdict**: E1a's
  `primary_statistic` is "the contrast in `relative_log_gap`" (01B:989), and
  `CONFIRMED` requires "the primary NORMALIZED log-loss contrast estimate is
  POSITIVE" (01B:1099). A non-positive primary normalized contrast is
  **sufficient** for `NOT_SUPPORTED`.

01B's internal reconciliation is the compound token
`status: PRIMARY_FOR_D16_DECISION_RULES_AND_SENSITIVITY_ELSEWHERE` (01B:804).
That token is not a decision; it is the conflict written down.

**Read literally today, E1a and E1b are `NOT_SUPPORTED` before a single cell has
been run, while the quantity the hypothesis was originally about is positive at
t = +4.64 in 8 of 8 blocks.**

Which scale is the headline is the advisor's call and nobody else's. It is not
an implementation question. It was not in the question list when this was
written — **it is now `01B Q8`**, added 2026-08-25 (AMENDMENT-5) after the
contrast was measured across eleven per-arm aggregations and two
common-denominator readings. The measurement sharpens the problem: the reversal
survives every choice *inside* D14's per-arm formula (E1a −0.0179 to −0.0196,
1 of 8 blocks positive) and **disappears entirely** under either
common-denominator reading (A4 **+0.34759**, t = +5.57, 8/8; A5 **+0.19357**,
t = +6.01, 8/8), which D14's formula excludes but D16's wording never forbids.
Note also that E1b's raw contrast is only **+0.00129** (t = +0.62), so the
reversal claim rests on **E1a alone**. Both readings are defensible; what is not
defensible is running A1 with a protocol that contains both.

### 2(c) — E1c's `fiber_count < 1024` restriction is VACUOUS on the d=3 side

D16 E1c restricts the primary analysis to *matched* conditions "in which BOTH the
d=3 mapping and the d=5 mapping are non-injective, i.e. `fiber_count < 1024` on
BOTH sides of the pair" (01B:1034-1037; the advisor's own wording at 01B:293-294).
The threshold 1024 is `01A exactness.state_space = 4**5`, i.e. the **d=5** state
space.

Measured on the frozen d=3 arm this session (`05b_SIM1B_REPLICATE_RESULTS.parquet`,
M=5, K=4, read-only):

```
encoder=count   fiber_count distinct = {24, 32, 36, 48, 64}   max = 64   n = 19,200 rows
                fraction with fiber_count < 1024 = 1.0000
```

and the same holds for **every** encoder on that arm — `label`, `onehot`,
`homals` are pinned at exactly 64 = 4**3, the whole d=3 state space; the largest
`fiber_count` anywhere on the arm is 768 (`hash_column`/B2). **100% of all
182,400 d=3 rows satisfy `fiber_count < 1024`.**

**The restriction restricts nothing.** Worse than nothing: at d=3 the reachable
state space is 4**3 = 64, so a mapping with `fiber_count == 64` is *fully
injective* on the d=3 state space, and the restriction admits it as
"non-injective". The stratum is therefore selected by the d=5 side alone, and the
contrast is not matched on the property it claims to match on.

The consequence is not cosmetic. Under the correct per-arm rule
(`fiber_count < K**d_active`, i.e. `< 64` at d=3), the `count` encoder retains
only 13.75% of its d=3 rows, the entire zipf × n_train=5000 half is **empty
(0/2400)** and zipf × n_train=500 retains 60/2400. Since `marginal` is a
block-key factor, a correct restriction removes most or all four Zipf blocks,
leaving ≈ 4 effective blocks — landing exactly on the frozen
`effective_blocks_min = 4` boundary, which then decides the BH family size (3 vs 2)
and therefore the q-values of E1a and E1b.

01B's own non-emptiness verification for E1c (01B:1040-1051, quoting 01A:480,
`{576, 768, 1024}` and `{768, 1024}`) is a **d=5** sweep. It establishes nothing
about the d=3 arm and is presented as though it did.

---

## 3. COUNCIL RESULT — four seats, four negative verdicts

Full record: `S0B_COUNCIL_REVIEW.md` (168,137 B, four seats verbatim).
The advisor's role assignment was "Claude Octopus with Claude as host, Codex for
implementation/numerical verification, and Gemini for independent scientific
review." Both mandated provider seats were filled by their sanctioned providers.
**No seat was filled by a Claude stand-in for a mandated provider** — the A0-round
error (a disclosed Claude substitution on a mistaken availability assumption) was
not repeated.

| seat | advisor's role assignment | provider / model / dispatch | verdict |
|---|---|---|---|
| 1 | Codex — implementation / numerical verification | codex-cli 0.147.0, `gpt-5.6-terra`, `codex exec --sandbox read-only`, 159 s, exit 0 | `NOT READY FOR A1` |
| 2 | Gemini — independent scientific review | Antigravity `agy` v1.1.19, `gemini-3.1-pro-high`, `agy --model … --sandbox --print`, run from a neutral directory outside the repo, 97 s, exit 0 | `DO NOT EXECUTE AS AMENDED` |
| 3 | supplementary (retained from A0) — statistical validity | Claude, fresh context, no authorship of any reviewed artefact | `DO NOT EXECUTE AS AMENDED` |
| 4 | supplementary (retained from A0) — adversarial implementation | Claude, fresh context; executed a mutation battery against a repo copy | `DO NOT EXECUTE AS AMENDED` |

Host seat: Claude — orchestration, integration, write-boundary enforcement.

One channel adaptation is disclosed and must be read as such: the Gemini seat's
sandbox refused its own capability probe, so 176,787 bytes of review material
were pasted into the prompt rather than granting repo access. The review record
states this is *"a channel adaptation, not a seat-availability finding."* The
seat was filled, by Gemini, and returned a full six-part review with a verdict.

**Findings: 16 CRITICAL / 17 MAJOR / 12 MINOR, across seats, NOT de-duplicated**
(`S0B_COUNCIL_REVIEW.md:105`, and :113 — "These totals are across seats, before
de-duplication"). Per seat: Codex 4/2/2 · Gemini 3/3/0 · seat 3 3/5/6 ·
seat 4 6/7/4.

**The strongest single piece of evidence is a convergence.** Codex, reading code
under a read-only sandbox and *executing nothing*, and the adversarial seat,
*executing mutations* against a repo copy, independently identified the same
defect class: a fiber-**assignment** defect that preserves fiber cardinality.

- Codex (C4): "a defect in `group_ids`, `hash_codes`, or `ebar_coordinatewise`
  swaps one cell from fiber A with one from fiber B. The partition membership
  changes and usually changes both population gaps, but the number of fibers
  remains identical."
- Seat 4 (A-C1): executed `fid = fiber_cache[key]` → `np.roll(fiber_cache[key], 1)`
  at `run_sim1b_dense_addendum.py:948`. Measured through the runner:
  `relative_log_gap` for `hash_column`/B0 moved **0.1564 → 0.4715** — the D16
  primary statistic, wrong by a factor of three — while
  `abs_production_minus_reference_log` and `log_identity_error` stayed at ~1e-16,
  `fiber_count` was byte-identical, and **the entire 1,027-test suite passed.**

Two methods, two providers, no shared context, same defect, same prescribed
remedy (a detector that is not invariant under relabelling). That is what a
council is for, and it is the reason gates G3 and G4 exist (§4).

A second convergence is worth naming because it is *not* closed for the inherited
runners (§6.1): Codex C2/C3 (rows can go **missing**) and seat 4 CRITICAL-6 (rows
can be **duplicated**) reached the same conclusion from opposite directions —
AD6's "executed rows == 182,400 exactly" is not guaranteed in the presence of any
failure.

#### DISPOSITION UPDATE — the two findings the council record left open

`S0B_COUNCIL_REVIEW.md` is a **frozen verbatim record of what four seats said**
and is **not edited**. It predates G3/G4 and marks two findings **"CLOSURE IN
PROGRESS — see `S0B_FINAL_GATE_REPORT.md` for final status"**. This is that
final status, stated here so no reader has to infer it from §4:

| council finding | site in the frozen record | **FINAL STATUS** |
|---|---|---|
| **Codex C4** — CRITICAL: G1 + fiber-count G2 cannot detect a wrong **same-cardinality** partition | `S0B_COUNCIL_REVIEW.md:141` | **CLOSED at A0.1 by AMENDMENT-4.** Two co-equal gates added: **G3** (stored MC representation loss vs the recomputed exact gap, `6·mcse + 1e-9`) and **G4** (canonical partition fingerprint, exact). Measured on the 624-cell frozen sample: `fiber_permute` → G3 166/624, G4 297/624; `fiber_swap` → G3 6/624, G4 295/624; `fiber_merge` → G3 610/624 (and G2 0/624). Both gates are conjunctive in the AD1/AD2 verdict. **Ratification pending as `01B Q7`** — the gates are operative, the advisor has not yet ratified the second tolerance class. |
| **Adversarial seat CRITICAL-1 (A-C1)** — the executed permutation attack: `relative_log_gap` 0.1564 → 0.4715 while `\|prod−ref\|` and `fiber_count` read clean and 1,027 tests passed | `S0B_COUNCIL_REVIEW.md:190` | **CLOSED at A0.1 by the same amendment**, and the attack is now a **regression test**: `tests/test_a0_2_defect_closure.py::TestFiberAssignmentDefectsAreDetectable`, `::TestGate3StoredRepresentationLoss` (6), `::TestGate4CanonicalPartitionFingerprint` (8). The suite that passed under the attack is now 1,086 tests and **fails** under it. |

**Both closures carry one qualification, stated rather than buried:** G3 is
evidenced end-to-end on the frozen d=3 arm, but **G4 is not**. The 05b parquet
predates the `fiber_fingerprint` column, so G4 reads `NOT_EVALUATED` there and
its 297/295 counts come from a published driver that supplies synthetic stored
fingerprints — `scripts/s0b_g4_fingerprint_bite.py`. See §6.2. G4's first real
evaluation is on A1's own rows.

The council record's own §12 discloses this concurrency. Nothing in it is
withdrawn; only these two statuses have moved on.

---

## 4. WHAT WAS FIXED AT A0.1

**These are implementation closures, not design resolutions.** Not one of them
answers a question in §2. They close code defects that would have corrupted A1
output silently. The nine closures live in `tests/test_a0_2_defect_closure.py`
(58 tests, all passing, verified this session), plus the reconciliation module
`tests/test_a0_1_reconciliation.py` (24 tests).

"Induced-failure count" below means: tests in the closure's own class that fail
when the defect is put back **in memory only** (a pytest plugin in the
scratchpad; no file on disk was modified, `git status --porcelain` unchanged).
Where I did not construct an on-disk-equivalent revert, the row says so — no
number is stated that I did not observe.

| # | council finding | what was fixed | class (tests, all pass) | induced-failure count |
|---|---|---|---|---|
| 1 | A-C6 | a late failure re-emitted a DUPLICATE row for every cell already written SUCCESS, with contradictory status; AD6's exact 182,400 became unsatisfiable | `TestOneRowPerAttemptedCell` (3) | **not measured** — no monkeypatch-equivalent revert exists; bite evidence is in-test (mixed success/failure probes assert primary-key uniqueness) |
| 2 | Codex C3 | typed-row coverage did not reach `BaseException`, pre-`try` setup, or a failure *inside* the failure-row builder | `TestTypedRowCoverageHasNoUncoveredPath` (9) | **not measured** — the fix is `except BaseException` control flow, not monkeypatchable; 9 tests execute the uncovered paths (KeyboardInterrupt / SystemExit / unbuildable manifest) |
| 3 | Codex C2 | a dead worker became `results[sid] = []` and a header-only part file: every attempted cell vanished, exit 0, and a restart SKIPPED the scenario | `TestWorkerDeathIsAccountedFor` (6) | **3 of 6 fail** with `failure_rows=None` restored |
| 4 | A-C4 | 9 of 13 encoder configurations were never exercised end to end, so label leakage could be reintroduced into `target`/`woe` invisibly | `TestEveryEncoderConfigurationExecutes` (3) + `TestSupervisedEncodersDoNotLeakLabels` (8) | **4 of 11 fail** with `oof_train_codes` replaced by a full-sample fit |
| 5 | A-C3 | the metric argument to `FIN.decompose` could be swapped: the whole finite-sample layer becomes the other metric's, and nothing compared a row's `representation_loss` to its own `theoretical_gap` | `TestRepresentationLossAgreesWithItsOwnTheoreticalGap` (6) | **5 of 6 fail** with the metric swapped |
| 6 | A-C5 | the D17 reference column could be filled from production (`ref = dict(pop)`), improving the D17 columns to exactly 0.0 while 01B explicitly bans the derivation | `TestTheReferenceColumnIsIndependentOfProduction` (3) | **0 of 3** — see the caveat below; the **harness** catches it: exit 1, `REFERENCE_NOT_INDEPENDENT`, 78/78 cells |
| 7 | Codex C1 | the D17 gate could PASS without ever checking runner output, because `--stored` was not mandatory | `TestTheA1GateRequiresStoredProduction` (4) | **2 of 4 fail** with `GATE_ARMS = ()` restored |

**Caveat on closure 6, stated because a hostile reader will find it.** The three
pytest assertions are a static AST scan plus a call-spy. I substituted
`CORE.reference_gap_report` at import time with `dict(exact_gap_report(...))` —
a *derived* reference by any reasonable definition — and **all three tests stayed
green**, because the runner still calls the name. The closure is real, but it
lives in the harness, not in the test class: running the harness under that
substitution gives
`!! REFERENCE_NOT_INDEPENDENT: |production - reference| is EXACTLY 0.0 in every
one of the 78 cells for BOTH metrics`, `RESULT=FAIL`, exit code 1. The test class
alone is not evidence for closure 6; the harness is.

### The two new D17 gates (AMENDMENT-4)

D17 as the advisor wrote it did not gate (AMENDMENT-1: the two identity-error
columns he named are blind to a production path wrong by 1e-2). D17 as
AMENDMENT-1 amended it still did not gate against the fiber-assignment class
found by the convergence in §3. Two further co-equal gates were added:

| gate | what it compares | tolerance | injected defect → cells caught (measured this session, 624-cell frozen sample) |
|---|---|---|---|
| **G3** `stored_repr_loss` | stored Monte-Carlo representation loss vs the recomputed exact population gap | `6*mcse + 1e-9` (a **new** tolerance class the advisor never set — Q7) | `fiber_permute` **166/624** · `fiber_swap` **6/624** · `fiber_merge` **610/624** |
| **G4** `partition_fingerprint` | stored canonical partition digest vs recomputed (`sim1_core.partition_fingerprint`, sharing no code with `group_ids`/`hash_codes`/`quantize`/`np.unique`) | exact string equality | `fiber_permute` **297/624** · `fiber_swap` **295/624** |

Enforced by `TestGate3StoredRepresentationLoss` (6 tests) and
`TestGate4CanonicalPartitionFingerprint` (8 tests), plus
`TestFiberAssignmentDefectsAreDetectable` (2), all passing. Under both assignment
defects **G1 and G2 read completely clean** — `max|prod−ref|` 5.44e-15 and
`fiber_count` 624/624 matching — which is exactly the council's point.

**G4's numbers required a synthetic stand-in and did not come from the command
01B says produces them.** See §6.2 — this is a contradiction, not a footnote.

Also closed at A0.1, from the reconciliation pass: **R1** (the runner's D17
sample silently disagreed with 01B's frozen rule; both gave 624 cells so every
count-based assertion passed — 7 of 12 tests fail with the superseded behaviour
restored), **R9** (the S0A microbenchmark's duplicate seed rule, closed by
detection over 2,400 seeds rather than by removal, because the file is an
immutable A0 record), **R10** (`_typed_failure_rows` ignored `learner_filter`;
pre-fix the filtered probe emitted 24 failure rows against 8 success rows).

---

## 5. WHAT REMAINS OPEN — ALL OF IT CLOSED BY TERMINATION (2026-08-25)

*Nothing in this section is outstanding. Every item below was open at the close of A0.1; the
advisor closed all of them at once by discontinuing the addendum before execution. They are
kept for the audit trail, not as work. See `DENSE_ADDENDUM_DECISION.md`.*

### 5.1 The eight advisor questions in 01B (`advisor_confirmation_requested`, `count: 8`)

**`01B advisor_confirmation_requested` is the single authority for advisor
question numbering.** No other document defines a `Qn`; the implementation
report's own items are `IR-1 … IR-8`.

Priority order as the file itself sets it. Q1–Q5 and Q7 can be answered after A1
without rerunning anything. **Q6 and Q8 cannot: Q6 determines which numbers A1
computes, Q8 determines which quantity is the primary — and its two candidate
readings have opposite signs.**

| id | question | operative default |
|---|---|---|
| **Q6** | Which inferential unit governs — 8 blocks / 7 df as D13 ruled, or 400 parameter draws / df ≈ 392 as the code and the measurements show? `severity: BLOCKS_A1_INFERENCE` | **NONE. Neither scheme is operative.** The runner may be built and gated; it may not compute an SE, a p-value or a q-value until this is answered. |
| Q1 | In which phase does the D17 624-cell reference check run, given that addendum production values cannot exist until A1 but the console block lists it as an A0.1 item? | adopted reading: harness validated at A0.1 on the frozen d=3 arm; the addendum-cell check is an A1 gate |
| Q2 | Is `effective_blocks_min = 4` the right threshold for E1c's low-power fallback? He wrote "too few independent blocks" with no number. | 4 |
| Q3 | Should the author-added FOURTH outcome class `INCONCLUSIVE_REPORTED_IN_FULL` stand? He specified exactly three, and a clause can satisfy none of them. | the fourth class stands |
| Q4 | Is "materially directionally inconsistent" = opposite signs AND both abs(estimates) > 1.0e-6 the definition he intended? | that definition |
| Q5 | Should the two D17 identity-error columns he named be reclassified descriptive rather than gating? Measured: blind to a 1e-2 production defect. | G1 AND G2 gate; the named columns are persisted but descriptive |
| Q7 | Should D17 gain gates G3 and G4 and a second, MCSE-scaled tolerance class he never set — changing what a D17 PASS certifies? | G1 AND G2 AND G3 AND G4, conjunctively |
| **Q8** | How does the normalized contrast aggregate — the DIFFERENCE OF THE TWO ARMS' PER-ARM RATIOS (D14's formula as written), or the RAW CONTRAST OVER ONE COMMON DENOMINATOR (which D16 never forbids)? Measured: per-arm gives E1a −0.0182 (t = −1.80, 1/8 blocks); common-denominator gives +0.348 (t = +5.57, 8/8) and +0.194 (t = +6.01, 8/8). **Opposite signs; the second removes the raw/normalized reversal entirely.** Also open: is the primary pooled over the three `delta_eta` levels or reported per level (a factor-of-2 swing)? `severity: BLOCKS_A1_INFERENCE` | reading (a)-PER-ARM, pooled over `delta_eta`, with the per-stratum `interaction_pairs` disclosure D14 mandates — operative so the package has a default, **not** because the question is settled |

Plus one deferred semantic question, `DQ1` (`count: 1`,
`status: RECORDED_NOT_DECIDED`): is `METRIC_UNDEFINED` a non-SUCCESS status
subject to the NULL-metrics rule (the strict reading, currently implemented,
which discards an otherwise valid log-loss) or a per-column annotation?
Unreachable in this arm (numeric bound ≤ 10^-1113.5) — but it is a semantics
question and an implementer should not settle it.

### 5.2 Design findings no implementation can close

**Gemini's three** (independent scientific review):

- **G-S1 (CRITICAL)** — the "DENSE-SIGNAL STRESS TEST" reframing is insufficient
  and *actively misleading*: "dense" points the reader at dimensionality while
  concealing that total signal magnitude increased. No code change removes this.
- **G-S3 (MAJOR)** — the `interaction_pairs = 3` stratum is hopelessly
  confounded, conflating dimension, a 70% saturation drop and a topology shift.
  Separate reporting is necessary but insufficient.
- **G-S5 (CRITICAL)** — the BH family size is **data-dependent** (3 → 2 if E1c
  drops out), which violates the FDR guarantee and inflates Type I error for E1a
  and E1b. The design must change, not the implementation.

(Its **G-S4 (CRITICAL)** — 8 blocks / 7 df cripples power, a block bootstrap over
8 clusters is severely discrete and asymptotically invalid — is a fourth
design-level item, and it converges on §2(a) from the opposite side.)

**The statistical seat's three**, its own blocking list:

- **S-C1** — the raw/normalized reversal (§2(b)). Blocking "because it is not a
  risk — it is the determined outcome, and the protocol currently gives two
  contradictory instructions about which reading is the finding."
- **S-C2** — E1c's vacuous restriction (§2(c)). Blocking "because E1c's stratum
  definition currently determines the BH family size."
- **S-C3** — the D14 normalized estimand **cannot be formed for the d=3 arm from
  any frozen artefact**, and 01B contains no rule for obtaining it. Blocking
  "because the primary estimand is otherwise undefined for half the contrast and
  will be improvised at A1."

The seat also flags two MAJORs as honest limitations to be *stated, not fixed*:
the design is underpowered on the normalized scale (MDE 0.028 against a true
effect near 0.018), and interaction saturation is the dominant term — unless the
advisor takes the saturation-matched `interaction_pairs = [0, 10]` option the A0
preflight already priced.

Two D14/D16/D18 obligations remain unenforced by any test and are A1-time work:
D13's estimator (no block-clustered interval, no bootstrap, no effective-blocks
statement exists in code), D16's decision rules (no E1a/E1b/E1c analysis, no BH
adjustment, no outcome classification), and **AD15 item 11** — the lint over A1
text output for D14's forbidden framing labels — which is **NOT IMPLEMENTED**.

---

## 6. HONEST DISCLOSURES

Stated without softening. Each of these weakens the package.

### 6.1 The inherited d=3 / 1C runners still carry Codex C2

The C2 fix in `scripts/_s1_parallel.py` is **opt-in**. `run_parallel` gained a
`failure_rows` provider; when it is `None` the inherited path is preserved byte
for byte:

> `failure_rows=None` keeps the inherited behaviour byte for byte, so the two
> existing callers (`run_sim1b_finite.py`, `run_sim1c_hash.py`, whose frozen
> output is already on disk) are unaffected.

Both legacy callers pass no provider. A worker death in either still yields
`results[scenario_id] = []`, a header-only part file, exit 0, and a restart that
**skips the scenario because its part file exists**. This is deliberate — the
frozen 1B/1C output is on disk and must not be perturbed — but it means the
defect is closed for the *addendum* runner only. A test,
`TestWorkerDeathIsAccountedFor::test_existing_callers_are_unchanged_without_a_provider`,
*asserts that the silent path survives*. If either legacy runner is ever re-run,
Codex C2 is live.

### 6.2 Gate 4 is NOT_EVALUATED on the frozen d=3 arm, and 01B's own reproduction command does not reproduce its recorded G4 numbers

`05b_SIM1B_REPLICATE_RESULTS.parquet` predates the `fiber_fingerprint` column, so
G4 has nothing to compare against on the only arm that exists. Running exactly
the commands 01B `a0_1_verification.V12.command_to_reproduce` prescribes, I
observe:

```
defect=fiber_permute … fingerprint_checked=0 fingerprint_mismatches=0
                       gates=…,G4_partition_fingerprint:NOT_EVALUATED
defect=fiber_swap     … fingerprint_checked=0 fingerprint_mismatches=0
                       gates=…,G4_partition_fingerprint:NOT_EVALUATED
```

**01B V12's `result` originally stated "G4 on 297 of 624" and "G4 on 295 of 624"
under those same commands. Those numbers do not come from those commands.** They
came from an unpublished scratchpad driver that monkeypatches `load_stored` to
inject 624 fingerprints built from the *clean recomputed digests* — "exactly
what a conforming runner would have written".

**RESOLVED 2026-08-25.** A recorded command must reproduce its recorded number,
and this defect sat in the file that corrects the advisor, so it could not ship
as-is. The driver is now **published in the repository** as
`scripts/s0b_g4_fingerprint_bite.py` (an out-of-package `--out-dir` is
mandatory; it refuses to write into the package), and `01B V12` now carries two
labelled command blocks — `command_to_reproduce_G1_G2_G3` for the plain
commands, `command_to_reproduce_G4` for the driver — plus an
`exact_conditions_under_which_the_G4_numbers_arise` field and a
`provenance_correction` record. Re-run this session:

```
defect=none           … fingerprint_checked=624 fingerprint_mismatches=0   G4:PASS
defect=fiber_permute  … fingerprint_checked=624 fingerprint_mismatches=297 G4:FAIL
defect=fiber_swap     … fingerprint_checked=624 fingerprint_mismatches=295 G4:FAIL
```

297, 295, and G3's 166 and 6, all reproduce exactly. The numbers were always
correct; the instruction was not, and now is. The advisor should read G4's
evidence as: correct, measured, and obtained through a synthetic stand-in for a
column no existing arm carries.

G4 therefore has **no end-to-end evidence on real production output**. Its first
real evaluation is on A1's own rows. `S0B_REFERENCE_GAP_CHECK_d3_frozen.csv`
carries `G4_partition_fingerprint:NOT_EVALUATED` and
`reportable_for_AD1_AD2=N/A_NOT_THE_GATE_ARM`. Nothing in this package is a
passed AD1/AD2.

### 6.3 The "82% of clustered variance" figure IS reproducible; its defect is a shared-draw error, not irreproducibility

**This section replaces an earlier reading that said the 82% figure "could not
be reproduced". That reading was wrong and is retracted here.** It compared a
method-A figure against a method-B measurement and called the mismatch a
reproduction failure. Three numbers are on the record, all three are correct
computations, and they are computations of **three different quantities**.

Measured this session with
`PYTHONPATH=src python3 scripts/s0b_d13_premise_probe.py --section variance --reps 50`
(about 5 s, fits no learner, executes zero addendum cells):

| quantity | value | what it is |
|---|---|---|
| **81.7%** | as first published by the statistical-validity seat (MAJOR-1) | **reproduces exactly** under that seat's own formula: the E1a exact-population block-mean contrast, with the within-block draw variance divided by the 3 `delta_eta` levels |
| **55.1%** | the corrected figure on the **same data, same estimand, same script** | collapses `delta_eta` **within a draw first**, then varies the draw |
| **14.9%–56.8%** | also reproduces exactly | a **different estimand**: method B — frozen d=3 twin, 48 scenario means of a Monte-Carlo outcome column, between ÷ total, **no draw-noise subtraction**, varying by encoder/learner/quantity |

**The real defect in the 82% figure is more interesting than a reproduction
failure.** Its draw-variance formula divides by the number of `delta_eta`
levels, i.e. it treats the three levels as three independent replicates.
`S0B_D13_PREMISE_INVESTIGATION.md` §4.2 measures those three levels to **share
one parameter draw bit for bit** (`max|Δa| = max|Δb| = exactly 0.0` over 80
comparisons), so that division is not available. It understates draw noise and
inflates the fixed-factor share. Correct the one line and the same script
returns **55.1%** — the honest answer to the question D13 actually turns on
(*how much of the between-block spread is designed heterogeneity rather than
sampling error?*): **roughly half.**

**Rules for reuse.**
- Quote **55.1%** for the fixed-factor share, citing the command above.
- Quote **81.7%** only as "the earlier figure, under a draw-variance formula
  refuted by the shared-draw measurement" — never as the share itself.
- Quote **14.9%–56.8%** only as method B, naming its estimand. It is neither
  evidence for nor against the method-A number, and the two must never be
  presented as competing measurements of one quantity. Its two
  `representation_loss` rows at ~1e-19 are numerical dust (label and one-hot are
  injective) and must not be quoted at all.

The seat's *verdict* was right — parameters are drawn per replicate, there are
400 draws, D13's premise is false — and the *direction* of its argument (a large
share of the block-clustered variance is fixed-factor heterogeneity) is
confirmed at 55.1%.

#### ERRATUM E-1 — sites carrying the retracted "unreproduced" reading

`S0B_COUNCIL_REVIEW.md` is a **frozen verbatim record of what four seats said**
and is **not edited**. Its affected sites are named here instead:

- `S0B_COUNCIL_REVIEW.md` — the **S-M1 row** and **§5**, which record the 82%
  figure as *not reproduced*. **Correction:** it reproduces at 81.7%; the
  objection to it is the shared-draw division, and the corrected figure is
  55.1%. What the seat said stands as said; only this reading of it is amended.
- This report's own §6.3 as first written, and §10's contradiction 6 — both
  corrected in place.
- `01B rulings.D13.…c2_between_block_variance_share.disputed_number_82_percent`
  — carried `status: UNREPRODUCED`; corrected in 01B to
  `REPRODUCED_BUT_SUPERSEDED_BY_A_CORRECTED_FORMULA`.

A second number still needs re-derivation: the A0 record's claim that "one seat
measured a 2.4× understatement" of `sd/sqrt(48)`. The measured
`SE(8 blk)/SE(48 scen)` ratios on the frozen twin are **1.00–1.95**, and the
claim was derived under the refuted premise. Re-derive before reuse. This one is
genuinely unsupported as stated — unlike the 82% figure.

### 6.4 `src/ct2i_benchmark/simulations/sim1_core.py` is modified in the working tree

`git diff --stat` gives **39 insertions, 0 deletions**. The diff adds exactly one
new pure function, `partition_fingerprint`, and changes no existing behaviour;
the full suite passes 1,086/1,086 and every frozen raw output still matches its
recorded SHA-256 (`10/10 MATCH`, superset check 5/5, exit 0).

What it means for provenance, stated plainly: **the module that produced the
frozen d=3 results is no longer byte-identical to the module on disk.** The
change is additive and provably behaviour-preserving for the frozen entry points,
`sim1_core.py` appears in no SHA manifest, and nothing in `PACKAGE_SHA256.json`
or `RAW_FREEZE_MANIFEST*.json` is invalidated. But anyone reconstructing the d=3
run from HEAD plus this working tree will not get a byte-identical source tree,
and the A0.1 change is **uncommitted** (prohibition PR8 forbids any git write at
A0.1). `02_ENVIRONMENT_AND_COMMIT.json` still names Phase R's
`c7ac3611aa1e9ff1c9d6db902624b40a279615c5`, while local HEAD is `02855025`. The
orchestrator, not A0.1, must commit.

### 6.5 Other things a hostile reader would raise

- **`raw/sim1b_replicates_parts/` — 288 files, ~260 MB — is excluded from the
  D15 addendum manifest** on a literal reading of "raw/*.csv" (non-recursive).
  Defensible: the downstream frozen parquet built from those parts *is* hashed,
  so a change to any part that reached the results would be caught. It is
  recorded in the manifest's `excluded_from_coverage` field. It is disclosed here
  so it is not visible only inside a JSON file. D15 says the manifest must cover
  "every protected raw CSV"; 288 raw CSVs are not in it.
- **`S0B_ADVISOR_RULING_IMPLEMENTATION_REPORT.md` was stale in three ways that
  mattered — all three CORRECTED 2026-08-25.** (i) Its headline read `FULL TEST
  SUITE 1,027 passed / 1,027 collected`; it now reads **1,086 passed / 1,086
  collected** with the +59 accounted for (`tests/test_a0_2_defect_closure.py`
  had not been written when that report was authored, and the reconciliation
  module gained one test) and the original figure retained for audit.
  (ii) Its §3 enumerated open questions **Q1–Q8** whose numbering did **not**
  match 01B's Q1–Q7 — its Q6 was the microbenchmark seed-rule duplication while
  01B's Q6 is the D13 inferential unit, the highest-severity item in the
  package. Two different Q6s. Its items are now **IR-1 … IR-8**, each carrying
  its mapping into 01B, and **`01B advisor_confirmation_requested` is declared
  the single authority for advisor question numbering** (`01B AMENDMENT-5`).
  Q6/Q7/Q8 are listed there separately as 01B-raised and outranking every IR
  item. (iii) Its §1 heading "D13 — block-clustered inference on 8 blocks, 7 df"
  — named in 01B's retraction list — now carries a status correction stating
  that D13's premise is refuted and that the question is 01B Q6.
- **`S0B_REFERENCE_IMPLEMENTATION_TEST_REPORT.md` described a superseded
  two-gate scheme — CORRECTED 2026-08-25.** It was written against AMENDMENT-1
  and knew nothing of G3 or G4; it now carries a **currency notice** naming all
  four gates and their tolerances, plus in-place currency notes at the two
  paragraphs that argued the two-gate case. Its §1 stated the output CSV is
  `211,395 B, 624 rows`; it now states **260,631 B**, 624 data rows, 46 columns
  (and the harness's own 23,466 B → **38,957 B**), with the earlier figures
  retained as "before the G3/G4 columns landed". Its §8 listed the
  `REFERENCE_REPLICATES = (1,)` drift as unresolved; it is now marked
  **RESOLVED (reconciliation R1)** — the constant no longer exists and the
  runner reads the sampling rule out of 01B at run time — with the original
  discrepancy retained so the resolution is auditable. Its row counts and its
  PASS were always correct.
- **`S0B_RESOURCE_CONFIRMATION.csv` priced the D17 reference CSV from the stale
  size — CORRECTED 2026-08-25.** Row `C5_DISK/d17_reference_csv` used
  `211,395 B / 624 rows = 338.8 B/row`; it now uses the observed 260,631 B →
  **417.7 B/row = 0.000261 GB**. The `TOTAL_DISK` rows were resummed:
  0.202572 → **0.202622 GB** (+0.00005 GB), re-verified by summing the C5 rows
  from the file. The **0.2026 GB headline and the 1.01% ceiling fraction are
  unchanged** at the stated precision, and §8's resource position stands.
- **AD15 is described as a ten-item gate and lists eleven items** (01B D18
  `title`, `AD15.description`, `gate_semantics` all say ten; `items:` runs 1–11).
  Item 11 — the D14 forbidden-label check — is the one that is NOT IMPLEMENTED.
- **AD15 item 3 is closed by DETECTION, not by removal.** Two copies of the seed
  rule still exist in the repository. The duplicate lives in
  `scripts/s0a_addendum_microbenchmark.py:67-74`, an S0A record the advisor ruled
  immutable; a test compares both copies over all 2,400 seeds so drift is loud,
  but the duplication itself is not closed. Literal compliance requires him to
  lift the immutability for that one file.
- **AT6 is not evidence of seed safety.** Its set-intersection disjointness
  assertion did **not** fire when the seed base offset was moved — the 8 realised
  blake2b digests happened to land above the old maximum. The structural test
  (`min(addendum) > max(original) + EVAL_DRAW_OFFSET`) is what bites. Both are
  kept. Any report citing AT6 must cite the structural test alongside it.
- **`mcse == 0.0` on an injective encoder is the true value, not a defect.**
  202 of the 624 clean D17 cells have `mcse` exactly 0. Any future "the Monte
  Carlo layer must carry a positive error" assertion must be written on a
  *merging* encoder or it will produce a false failure.
- **The council review is itself behind the code — and is FROZEN, so it stays
  that way.** It says "a third detector is being implemented concurrently" and
  contains no mention of `partition_fingerprint`, gate 4, or `NOT_EVALUATED`. It
  discloses this at its own §12. Its two open findings, **Codex C4** (`:141`) and
  **adversarial CRITICAL-1 / A-C1** (`:190`), are marked "CLOSURE IN PROGRESS —
  see `S0B_FINAL_GATE_REPORT.md` for final status"; that final status is now
  stated explicitly in **§3, DISPOSITION UPDATE** (both CLOSED by AMENDMENT-4;
  G4 not yet evidenced end-to-end; ratification pending as 01B Q7). Its S-M1 row
  and §5 also record the 82% figure as "not reproduced" — corrected by
  **ERRATUM E-1** in §6.3. **No line of `S0B_COUNCIL_REVIEW.md` was edited.**
- **No seat found the shipped numbers wrong.** Seat 4 states it explicitly:
  "I found no defect in the shipped numbers except CRITICAL-6." The four vetoes
  are about gate adequacy, the inference scheme, and the design — not about the
  completed arm's results. The completed arm's 13/13 statement is untouched.

---

## 7. RETRACTIONS FROM PHASE A0

One Phase A0 finding delivered to the advisor as **CONFIRMED** is **partially
retracted**: criterion **C2**.

**Retracted:**
1. the premise — that there are 8 independent parameter draws. There are 400,
   one per (block, replicate); parameters are drawn afresh for every replicate;
2. the evidence line — `seed.nunique() == 400` was cited as confirming 8 draws.
   It measures 400 distinct parameter draws and therefore **refutes** the premise
   it was cited for;
3. the remedy that followed from the premise — collapse to 8 block means, 7 df.

**NOT retracted:**
- the narrow conclusion that `sd/sqrt(48)`, and any per-scenario denominator,
  **understates** the standard error. The 48 scenario means *are* clustered —
  6 scenarios share every parameter draw. That finding stands;
- the finding that the block key's exclusion of `delta_eta` and `n_train` is
  correct and load-bearing. Confirmed by measurement at **exactly 0.0**;
- any other A0 criterion. This retraction is scoped to C2's premise and to the
  inference drawn from it.

**Exact sites carrying the retracted premise** (line numbers as of 2026-08-24;
each verified present and unchanged this session):

*Immutable A0 record — NOT EDITED:*
- `S0A_ADDENDUM_COUNCIL_REVIEW.md:62` — the C2 row: "they cluster into **8**
  parameter-draw blocks" + "**CONFIRMED.** `seed.nunique() == 400`"
- `S0A_ADDENDUM_COUNCIL_REVIEW.md:229` — the long C2 paragraph, whose own closing
  argument about fixed, exhaustively enumerated grids refutes its own remedy
- `S0A_ADDENDUM_PREFLIGHT_REPORT.md:43` — the C2 statement
- `S0A_ADDENDUM_PREFLIGHT_REPORT.md:47` — "corrected to block-clustered inference
  on 8 blocks (7 df)"
- `S0A_ADDENDUM_PREFLIGHT_REPORT.md:317` — the `seed.nunique() == 400` evidence line
- `S0A_ADDENDUM_PREFLIGHT_REPORT.md:333` — "**Adopted correction (D13):**
  cluster-robust inference on the **8 blocks** (7 df)"
- `S0A_ADDENDUM_PREFLIGHT_REPORT.md:606` — "there are only 8 blocks | CONFIRMED,
  `seed.nunique() == 400`"

*Immutable design freeze — corrected BY REFERENCE from 01B, not edited:*
- `01A_ADDENDUM_PROTOCOL_FREEZE.yaml:362-366` and `:411-417`

*A0.1 products that were correctable and were still WRONG — **both CORRECTED
2026-08-25**, leaving no editable site that asserts the refuted premise:*
- `S0B_ADVISOR_RULING_IMPLEMENTATION_REPORT.md` §1 — the heading "D13 —
  block-clustered inference on 8 blocks, 7 df" now reads "…as ruled (8 blocks,
  7 df) — **PREMISE SINCE REFUTED**" and carries a status correction naming
  01B Q6 and `S0B_D13_PREMISE_INVESTIGATION.md`.
- `scripts/run_sim1b_dense_addendum.py` — the `addendum_block` docstring, the
  **origin** of the false premise in the A0 chain, now states the block
  structure factually (8 fixed design blocks; 400 draws; cluster =
  `(block, replicate)`, size 6), records what the exclusions actually buy
  (`max|da| = max|db| = 0.0` across `delta_eta` and `n_train`), and defers the
  unit to 01B Q6. `addendum_blocks()` got the same treatment. The dry-run banner
  no longer prints `parameter-draw blocks (D13) 8 (7 df)`; it prints
  `design blocks … 8`, `parameter draws per arm … 400`, and
  `inferential unit … OPEN -- 01B Q6`.

  *Every remaining site carrying the premise is in an immutable file* (`S0A_*`,
  `01A`) and is corrected by reference, as listed above.

**Why the S0A files were not edited.** Prohibition PR3 and the advisor's own
instruction — "Do not overwrite or erase the A0 freeze or council record" — are
absolute. The A0 record is the evidence of *what he was told when he ruled*.
Editing it would destroy the only trace of why D13 says what it says and would
make the correction unauditable. It is corrected by reference, in the same way
01A is.

**Verified this session: no S0A file was edited.** Every S0A artefact hashes and
dates as follows, all mtimes predating the start of A0.1:

```
00fbe65472347bdd837e62e08eed8f45fb37c2499835af399e921d1174848f56  2026-08-19 14:37  scripts/s0a_addendum_microbenchmark.py
980517723403350c38d8cbb1278cd48e3209e041ab8afeda02055ab2a0c9d373  2026-08-19 15:25  S0A_ADDENDUM_COUNCIL_REVIEW.md
b4d8bcbbd099d20a0a7a0be74eb9c38ed0da74b08912fecc8584eb9d617aaae3  2026-08-19 14:39  S0A_ADDENDUM_MICROBENCHMARK_ROWS.csv
4cdc5e684f488acaf70d0e94b266cd89c53728abdbd30c730252c06646653f6c  2026-08-19 15:24  S0A_ADDENDUM_PREFLIGHT_REPORT.md
dca73d0505df8f5babe087da67a962c3dc6d61e89a0a6fb3d3b051abc4df4f73  2026-08-19 15:23  S0A_ADDENDUM_RESOURCE_ESTIMATE.csv
6f293d33c686349d4a044e4cce902702d19a747c5cb044017b18193122945336  2026-08-19 15:23  S0A_ADDENDUM_TEST_REPORT.md
157eb0114ce28711feffab87db73a2ad65ca1a5e5f601b9735d2ac7ee1673028  2026-08-19 15:23  01A_ADDENDUM_PROTOCOL_FREEZE.yaml
f6d64fc0335d7cd31a881930294a856a81186bcd306868daf44952ca7d8e9d23  2026-08-11 18:36  01_PROTOCOL_FREEZE.yaml
```

**No raw output is affected and no cell needs re-running.** This is an
inference-scheme defect only. Verified: `RAW FREEZE MANIFEST ADDENDUM: 10/10
MATCH`, superset check 5/5, exit 0; nothing under `raw/` has an mtime later than
2026-08-12 19:55; zero addendum cells have ever been executed. None of A1–A15 or
AD1–AD15 changes. The completed arm's 13/13 statement is untouched.

Two defects were also found in the **immutable 01A** and are reported, not fixed:
`AD8` says "about 9 of 2,400 cells" for a 3×3×13 spot check, which is 117 cells
(9 counts only (scenario, replicate) pairs); and
`design.row_count.independently_confirmed` cites the frozen d=3 twin as
*confirmation* of the addendum's row count when it is a **projection**. Does the
advisor want an erratum entry, or is this record sufficient?

---

## 8. RESOURCE POSITION

Source: `S0B_RESOURCE_CONFIRMATION.csv`, which SUPERSEDES
`S0A_ADDENDUM_RESOURCE_ESTIMATE.csv` (left byte-identical).

| quantity | value | share of ceiling |
|---|---|---|
| Projected A1 CPU | **8.573 core-hours** (CI [8.473, 8.667]) | **42.87%** of the 20 core-hour ceiling; headroom 11.427 |
| Projected A1 disk | **0.2026 GB** | 1.01% of the 20 GB ceiling |
| Wall time at 8 workers | 1.072 h | — |
| A0.1's own probe spend (charged to A0.1, not to A1) | 0.3641 core-hours | — |

Composition: C1 base cells 8.570064 (anchor 5.930868 measured on the frozen d=3
twin × measured d-ratio 1.025065 × runner overhead 1.0069 × the 1.4 calibration
carried forward from A0) + C2 D17 reference 0.003187 + C4 block bootstrap
0.000066.

**Corrections to A0's figures.** Four, all confined to the A0.1 file; both A0 CSVs
were opened read-only and are byte-identical.

1. **Disk, material.** A0 priced 294.7 B/row on the 1B *probe* schema. The A1
   runner writes **78 fields**, measured at **870.9 B/row** — 2.96× larger. Disk
   goes 0.084 GB → 0.2026 GB, a 2.4× increase driven almost entirely by the row
   schema. Still 1.01% of the ceiling.
2. **The d-ratio's evidence base.** A0 had 3 matched pairs, one of which carried
   43% of the weight at n=500. A0.1 bought 32 pair measurements over all 8 blocks;
   the largest single-measurement weight falls to 2.7%. A0's point estimate
   1.030345 lies **inside** the new CI [1.013130, 1.036365] and is CONFIRMED —
   but A0's published band [1.0169, 1.0500] was the min/max of 3 pairs and
   **understated** the per-pair spread, which is really [0.934, 1.100].
3. **A0's own probe spend.** Published 0.1085 core-hours; recomputed from the A0
   CSV, 0.108498 (the six e2e values sum to 387.316 s, not 387.4, and the unit
   layer to 3.2765 s, not ~5). Never part of the A1 budget.
4. **Two chained-rounding discrepancies** in A0's published band low (8.443 vs
   8.4435) and weighted ratio (1.0303 vs 1.0304 from its own rounded inputs).
   Full-precision values are correct; the published components carry too few
   digits to reproduce them.

Combined effect on the A0 headline: none. The ceiling verdict is unchanged
(A0 said 42.8%, the re-projection says 42.9%). Peak RSS 241.5 MB/worker,
1.887 GiB across 8 workers on a 16 GB host.

One multiplier could not be measured and was assumed: the number of separately
bootstrapped reported quantities (2,000). It is immaterial — even 100,000 would
cost 0.0033 core-hours, 0.017% of the ceiling.

The stale D17-CSV size in that file (§6.5) moves disk by +0.00005 GB and changes
nothing at the stated precision.

---

## 9. STATUS BLOCK

### 9.0 TERMINAL STATUS (2026-08-25) — THIS IS THE OPERATIVE BLOCK

```
CT2I ADDENDUM STATUS: TERMINATED_BEFORE_EXECUTION
FULL ADDENDUM CELLS RUN: 0
ADDENDUM_RUN: false
REAL-DATA MODELS RUN: 0
GPU HOURS USED: 0
MANUSCRIPTS MODIFIED: 0
COMPLETED RAW RESULT FILES CHANGED: 0
PHASE A1: WILL NEVER RUN
OPEN ADVISOR QUESTIONS (01B Q1-Q8): CLOSED BY TERMINATION, NOT BY ANSWER
DECISION RECORD: simulation-results-ct2i/DENSE_ADDENDUM_DECISION.md
NEXT ACTION: NONE — THE ADDENDUM IS DISCONTINUED; NO APPROVAL IS BEING AWAITED
```

### 9.1 SUPERSEDED — the block as reported at the close of A0.1, 2026-08-25

**The block below is preserved verbatim as the record of what was reported at the time. It is
SUPERSEDED. Its `NEXT ACTION: WAIT FOR ADVISOR APPROVAL BEFORE FULL A1 EXECUTION` line is no
longer true: the advisor ruled the same day, and the ruling was to terminate rather than to
approve. Read every FAIL, OPEN and gate verdict in it as closed by termination — none of them
will ever be re-evaluated, because the arm they gate will never be run.**

```
CT2I ADDENDUM A0.1 STATUS: BLOCKED  [SUPERSEDED — see 9.0: TERMINATED_BEFORE_EXECUTION]
FULL ADDENDUM CELLS RUN: 0
REAL-DATA MODELS RUN: 0
GPU HOURS USED: 0
D13 BLOCK-CLUSTERED INFERENCE: FAIL
D14 DENSE-SIGNAL INTERPRETATION FROZEN: PASS
RAW AND SIGNAL-NORMALIZED ESTIMANDS FROZEN: PASS (formulas); AGGREGATION OPEN (01B Q8)
D15 RAW MANIFEST COVERAGE: PASS
D16 E1 CLAUSES AND DECISION RULES: FAIL
D17 INDEPENDENT REFERENCE CHECK: 624/624 on the d3_frozen SENSITIVITY arm (G4 NOT_EVALUATED); 0/624 on the addendum GATE arm
D18 REAL A1 RUNNER GATE: FAIL
TYPED FAILURE TESTS: 48/48
N500 AND N5000 RUNNER TESTS: PASS
EXACT_OR_MC LABEL TEST: PASS
FULL TEST SUITE: 1086/1086
PROJECTED A1 CPU CORE-HOURS: 8.573
CRITICAL VETO COUNT: 16
NEXT ACTION: WAIT FOR ADVISOR APPROVAL BEFORE FULL A1 EXECUTION
  [SUPERSEDED 2026-08-25 — no approval is being awaited; the addendum was
   TERMINATED BEFORE EXECUTION. Operative next action: see 9.0.]
```

**Why each non-PASS field reads as it does.** A ruling whose premise is refuted
is not a PASS.

- **D13 — FAIL.** Its factual premise is false (§2a), `01B rulings.D13.status` is
  `PREMISE_REFUTED_ADVISOR_RULING_REQUIRED`, neither scheme is operative, and no
  block-clustered estimator, interval or bootstrap exists in code. A0.1 delivered
  only the data structure (a `block_key` on every emitted row, invariant to the
  contrasted factors) that makes either scheme computable.
- **D16 — FAIL.** The clauses are frozen in writing, which is what A0.1 could
  deliver, but as decision rules they do not currently function: E1c's primary
  restriction is vacuous on the d=3 side (§2c); the primary statistic already
  determines `NOT_SUPPORTED` before any cell runs while the raw contrast is
  positive at t = +4.64 (§2b); `D16.common_statistic.inference` inherits D13; **the aggregation of
  the normalized contrast is not determined, and its two candidate readings have
  opposite signs (01B Q8, added 2026-08-25)**; the BH family size is
  data-dependent (G-S5); and no E1a/E1b/E1c analysis code, BH adjustment or
  outcome classification exists.
- **D17 — reported as two numbers, not one.** The harness PASSES 624/624 on the
  frozen d=3 arm, which is a **sensitivity** run: the summary line itself reads
  `gate=SENSITIVITY_ONLY reportable_for_AD1_AD2=N/A_NOT_THE_GATE_ARM`, and G4 is
  `NOT_EVALUATED` because 05b predates the column. The addendum **gate** arm
  requires production rows on disk and cannot run at A0.1: 0 of the 624 required
  gate cells have been evaluated. AD1/AD2 are not passed.
- **D18 — FAIL.** AD15 is conjunctive over its items and is an A1 gate
  (`01B AD15.a0_1_status`). Item 11 is NOT IMPLEMENTED; item 3 is closed by
  detection rather than removal; item 1's "produces every addendum row" clause is
  a provenance claim about output that does not exist. What A0.1 delivers is that
  every item has a test that fires if the runner regresses, exercised on
  non-frozen probes. That is not a passed AD15.
- **D14 / estimands / D15 — PASS, with one qualification.** D14 is accepted and
  closed; the framing token and forbidden labels are frozen; both normalized
  estimands, their exact denominators and the `1.0e-6` `NOT_IDENTIFIED`
  tolerance are frozen and read from the parent freeze at run time. *The
  qualification:* D14 defines the two ratios **per arm** and neither D14 nor D16
  says how the d=5 minus d=3 **contrast of a ratio** is formed. That is `01B Q8`
  and it is scored against D16, not against D14 — the formulas themselves are
  frozen and unambiguous. Measured at A0.1: no cell is `NOT_IDENTIFIED` (minimum
  denominator 2.713e-03 log, 1.354e-03 Brier, against the 1e-06 tolerance), so
  that rule's handling is not in play. the manifest verifier returns `10/10 MATCH`,
  superset 5/5, exit 0. The disclosed exclusions (AD15 item 11's missing lint,
  `raw/sim1b_replicates_parts/`) are recorded in §5 and §6.5 rather than being
  hidden behind these PASSes.

---

## 10. VERIFICATION LOG — every command run for this report

Read-only unless stated. No file was modified, no git write was issued, no
addendum cell was run. Working directory `/Users/Eric/Desktop/114/ct2i-benchmark`.

| # | command | observed |
|---|---|---|
| 1 | `PYTHONPATH=src python3 -m pytest -q` | `1086 passed, 13 warnings in 21.77s`, exit 0 |
| 2 | `… --collect-only` | `1086 tests collected` |
| 3 | per-module collect | `test_a0_dense_addendum_properties.py` 281 · `test_a1_runner_smoke.py` 91 · `test_a0_1_reconciliation.py` 24 · `test_a0_2_defect_closure.py` 58 |
| 4 | `python3 scripts/run_sim1b_dense_addendum.py --dry-run` | 48 scenarios, 13 configs, 50 reps, 76 rows/rep, `PROJECTED CELL COUNT: 182,400 … -> MATCH`, `D17 reference cells (48 x 13 x 1) 624 (01B minimum 624)`, `No cell executed.`, exit 0. **Re-run 2026-08-25 after the banner correction: identical, and it now prints `design blocks … 8`, `parameter draws per arm … 400`, `inferential unit … OPEN -- 01B Q6` instead of the refuted `parameter-draw blocks (D13) 8 (7 df)`** |
| 5 | `python3 scripts/s0b_reference_gap_check.py --arm d3_frozen --stored --out <scratch>` | `cells=624 … cells_over_tolerance=0 fiber_count_mismatches=0 stored_mc_gate_checked=624 stored_mc_gate_violations=0 fingerprint_checked=0 gates=G1:PASS,G2:PASS,G3:PASS,G4:NOT_EVALUATED gate=SENSITIVITY_ONLY reportable_for_AD1_AD2=N/A_NOT_THE_GATE_ARM RESULT=PASS`; 625 lines. Written to the scratchpad; the package CSV's sha256 `23d5ed55…0e2ef1` is identical before and after |
| 6 | same, `--inject-defect fiber_permute / fiber_swap / fiber_merge` | G3 fires 166 / 6 / 610 of 624; G2 fires only on `fiber_merge` (624 mismatches); G1 never fires (5.44e-15 / 5.55e-15 / 6.22e-15); G4 `NOT_EVALUATED` in all three |
| 7 | `python3 scripts/s0b_g4_fingerprint_bite.py --out-dir <scratchpad>` (synthetic stored fingerprints; **published 2026-08-25**, previously a scratchpad-only driver) | `fingerprint_checked=624` in all three runs: clean **0/624** (G4 PASS) · `fiber_permute` **297/624** · `fiber_swap` **295/624** (G4 FAIL); G3 fires 0 / 166 / 6. Cited by `01B V12.command_to_reproduce_G4` |
| 20 | `python3 scripts/s0b_d13_premise_probe.py --section variance --reps 50` | method A collapse-first fixed-factor share **55.1%** (SD of 8 block means 0.028494, mean within-block draw SE 0.019098, implied fixed-factor SD 0.021147); method A delta-independent **81.7%** — the earlier figure, reproduced exactly; method B range **14.9%–56.8%** over 8 encoder/learner/quantity combinations, reproduced exactly (§6.3) |
| 21 | `python3 scripts/s0b_normalized_contrast_sensitivity.py --reps 50` | E1a per-arm A1 **−0.01815** (SE 0.01007, t = −1.80, 1/8); A2 −0.01964; A3 −0.01790; A6 −0.01822; common-denominator **A4 +0.34759** (t = +5.57, 8/8) and **A5 +0.19357** (t = +6.01, 8/8); raw contrast +0.00919 (t = +4.64, 8/8). E1b A1 −0.05182 (t = −2.64, 2/8); **E1b raw only +0.00129 (t = +0.62)**; A4 +0.11646, A5 +0.04619. No cell NOT_IDENTIFIED (min denominator 2.713e-03 log / 1.354e-03 Brier vs tolerance 1e-06). Basis of `01B Q8` |
| 22 | `csv` resum of `S0B_RESOURCE_CONFIRMATION.csv` C5_DISK rows after the `d17_reference_csv` correction | **0.202622 GB**; headline 0.2026 GB and 1.01% ceiling fraction unchanged |
| 23 | `PYTHONPATH=src python3 -m pytest -q` (after all 2026-08-25 edits) | `1086 passed`, exit 0 — unchanged from row 1 |
| 8 | `python3 scripts/verify_raw_freeze_manifest_addendum.py` | `RAW FREEZE MANIFEST ADDENDUM: 10/10 MATCH`, `superset check: 5/5 … -> PASS`, 0 mismatched / missing / unlisted, exit **0** |
| 9 | `shasum -a 256` over every `S0A_*` / `s0a_*` file and `01A`, `01_PROTOCOL_FREEZE` | all as listed in §7; all mtimes 2026-08-11/19, before A0.1 began |
| 10 | `git status --porcelain` | 25 entries (10 modified, 15 untracked); **byte-identical at the start and at the end of this session**; `HEAD = 02855025…` |
| 11 | `find raw -type f -mtime -7 \| wc -l` | **0**. Newest file under `raw/` is 2026-08-12 19:55. `find simulation-results-ct2i -iname '*dense_addendum*'` → nothing |
| 12 | parameter-draw regeneration (no cell, no data read) | 8 blocks · 400 seeds · **400 distinct (a,b) signatures** · `max abs(a(r1)−a(r2)) = 2.2952915731512284` · `max abs(da)` across `delta_eta` = **0.0** |
| 13 | `pytest -k "replicate_still_varies_the_draw or parameter_draw_identical_across_delta_eta"` | 5 passed, 276 deselected |
| 14 | pandas over `05b_SIM1B_REPLICATE_RESULTS.parquet` (M=5,K=4) | 182,400 rows · `seed.nunique()` **400** · 48 scenarios · replicates 1..50; `count` fiber_count `{24,32,36,48,64}`, max 64, `frac<1024 = 1.0000`; every encoder `frac<1024 = 1.0000`, arm max 768 |
| 15 | `python3 <scratchpad>/council_sci/p3_predict_E1.py` | the E1a/E1b block in §2(b), reproduced digit for digit; width-identity check `max abs(rel_log(B0)−rel_log(B1/B2))` for `hash_shared` = 2.209e-14 (E1a's collapse premise holds); for `hash_column` = 2.521e-01 (correctly does not collapse) |
| 16 | in-memory reverts (pytest plugins in the scratchpad; nothing on disk touched) | C2 → 3 failed / 3 passed · A-C4 → 4 failed / 7 passed · A-C3 → 5 failed / 1 passed · C1 → 2 failed / 2 passed · A-C5 → 0 failed / 3 passed (see §4 caveat) |
| 17 | harness under a derived reference implementation | `!! REFERENCE_NOT_INDEPENDENT … EXACTLY 0.0 in every one of the 78 cells for BOTH metrics`, `RESULT=FAIL`, exit 1 |
| 18 | console-block test selections | typed-failure 48/48 · n500/n5000 13/13 · exact_or_mc 3/3 |
| 19 | `git diff --stat src/…/sim1_core.py` and the diff | 39 insertions, 0 deletions; adds only `partition_fingerprint` |

**Contradictions between an observed value and an earlier claim, printed rather
than reconciled:**

**All six were resolved on 2026-08-25.** Each row now says what it was and how
it was closed; nothing below is left for the reader to reconcile.

1. **01B `a0_1_verification.V12`** recorded G4 firing on 297/624 and 295/624
   under three named commands that print `fingerprint_checked=0`,
   `G4_partition_fingerprint:NOT_EVALUATED`. → **RESOLVED.** The driver is
   published as `scripts/s0b_g4_fingerprint_bite.py`; V12 now carries two
   labelled command blocks, the exact conditions, and a `provenance_correction`.
   297, 295, 166 and 6 all re-reproduced this session (§6.2).
2. **`S0B_ADVISOR_RULING_IMPLEMENTATION_REPORT.md`**: `1,027 passed / 1,027
   collected` vs observed 1,086/1,086, and a Q1–Q8 list colliding with 01B's
   Q1–Q7 on the label "Q6". → **RESOLVED.** Headline refreshed to 1,086/1,086
   with the +59 accounted for; its items renumbered **IR-1 … IR-8** with a
   mapping column; 01B declared the single authority for question numbering; its
   D13 heading given a status correction (§6.5).
3. **`S0B_REFERENCE_IMPLEMENTATION_TEST_REPORT.md`**: `211,395 B` vs observed
   **260,631 B**; the `REFERENCE_REPLICATES = (1,)` drift described as
   unresolved; a two-gate D17 that is now four. → **RESOLVED.** Sizes corrected,
   §8 marked RESOLVED (R1) with the original discrepancy retained, and a
   four-gate currency notice added (§6.5).
4. **`S0B_RESOURCE_CONFIRMATION.csv`** row `d17_reference_csv` priced 338.8 B/row
   from the stale 211,395 B. → **RESOLVED.** 417.7 B/row = 0.000261 GB;
   `TOTAL_DISK` resummed 0.202572 → 0.202622; headline 0.2026 GB and 1.01%
   unchanged (§6.5).
5. **`S0B_COUNCIL_REVIEW.md`** contains no mention of `partition_fingerprint`,
   `gate 4` or `NOT_EVALUATED`, and marks C4 / A-C1 "CLOSURE IN PROGRESS".
   → **RESOLVED WITHOUT EDITING IT.** The file is a frozen verbatim record. Its
   two open findings now have an explicit final status in §3 (DISPOSITION
   UPDATE), and its 82% verdict is corrected by ERRATUM E-1 in §6.3. **No line
   of that file was changed.**
6. **The "82%" clustered-variance figure** (council seat 3, MAJOR-1) — **not a
   contradiction after all.** It reproduces exactly (81.7%); the corrected
   shared-draw figure is **55.1%**; the 14.9%–56.8% range is a different
   estimand that also reproduces exactly. All three are correct computations of
   three different quantities (§6.3, ERRATUM E-1). The A0 record's "2.4×
   understatement" against the measured 1.00–1.95 **does** remain a live
   contradiction.

---

## 11. PROHIBITIONS HONOURED

Zero addendum cells. Zero real-data models. Zero GPU hours. No file under
`/Users/Eric/Desktop/114/碩論/` was read or written. No real dataset, image,
prediction or manuscript was touched. `01_PROTOCOL_FREEZE.yaml`,
`01A_ADDENDUM_PROTOCOL_FREEZE.yaml`, every `S0A_*` record,
**`S0B_COUNCIL_REVIEW.md`**, both raw-freeze manifests and every frozen raw
output are unmodified and hash as recorded. No git write command of any kind was
issued. Every probe artefact was written to the scratchpad, outside the
repository.

**What the 2026-08-25 consistency pass modified**, stated because the earlier
wording ("this report is the only file created; no existing file was modified")
no longer holds: this report; `01B_ADDENDUM_ADVISOR_RULINGS.yaml` (v4 → v5,
AMENDMENT-5); `S0B_ADVISOR_RULING_IMPLEMENTATION_REPORT.md`;
`S0B_REFERENCE_IMPLEMENTATION_TEST_REPORT.md`; `S0B_RESOURCE_CONFIRMATION.csv`;
`scripts/run_sim1b_dense_addendum.py` (docstrings and the dry-run banner only —
no behaviour, no seed rule, no row count); and one file created,
`scripts/s0b_g4_fingerprint_bite.py`. The full suite is **1,086 passed / 1,086
collected** before and after, and the `--dry-run` still projects 182,400
EXECUTED rows and executes nothing.

~~**Stop. Phase A1 is not authorised. Answer Q6 first, then Q8.**~~

**SUPERSEDED 2026-08-25. Phase A1 is not merely unauthorised — it is discontinued. Q6 and
Q8 will not be answered; they are CLOSED BY TERMINATION. Nothing further is required of the
advisor on the addendum. See `DENSE_ADDENDUM_DECISION.md`.**
