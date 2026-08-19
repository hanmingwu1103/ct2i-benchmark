# S0A Preflight Report — Dense-Signal Simulation 1B Addendum (Phase A0)

**Phase:** A0 (preflight) **only**. **Addendum cells run: 0. Real-data models run: 0.
GPU hours: 0.**
**Design frozen:** `simulation-results-ct2i/01A_ADDENDUM_PROTOCOL_FREEZE.yaml`
(M = 5, K = 4, d = M = 5; 48 scenarios; 13 encoder configurations; 50 replicates;
182,400 rows).
**Parent protocol:** `01_PROTOCOL_FREEZE.yaml` — **not edited, not extended, not
renumbered.** Acceptance criteria A1–A15 are untouched and the completed arm's 13/13
statement stands unchanged; it is never restated as "13/13 + n".
**Repository state:** branch `simulation-only/manuscript-revision`, HEAD
`931ee5644acbdc4d6d7ae2f5bf2c9b035819c40c`. **A0 performed no git write of any kind** —
no commit, tag, push, add, checkout, reset or config. Every new file is left in the
working tree.

---

## 1. Executive summary

**A0 PREFLIGHT IS COMPLETE. THE DESIGN IS NOT APPROVED FOR A1 AS DRAFTED.**

The mechanical side is sound: 264 new property tests pass, the 632 pre-existing tests are
still green, the five frozen raw outputs re-hash 5/5, seed disjointness is proved, and the
measured projection is **8.55 CPU core-hours against a 20 core-hour ceiling**.

The scientific side did not survive review. A four-seat council — **Codex and Gemini in
the two mandated seats, both filled for real, plus two supplementary fresh-context Claude
reviewers** — returned **four distinct CRITICAL findings** and every seat independently
concluded "do not execute as written". The three most important:

1. **§4a — an UNDISCLOSED confound, larger than the disclosed one, raised independently
   by three of four seats and confirmed by the host.** The frozen linear predictor sums
   one main effect per active coordinate with no normalisation by d, so raising d from 3
   to 5 at fixed `tau` **increases total signal strength**. Measured: `sd(eta)` is larger
   at d = 5 in **all 24** factor combinations (24/24, ratio range 1.038–1.437 on independent
   recomputation) and the Bayes risk falls
   correspondingly. Because the hash fiber partition is bit-for-bit identical at both d,
   the entire d = 5 − d = 3 hash difference could be "the same partition destroys more of
   a larger-variance eta" — which is *not* E1's mechanism, and points the same way as
   E1's prediction. The freeze's "exactly one factor" and `nothing_else_differs: true`
   were **false and are withdrawn**. → decision **D14**, advisor ruling required.
2. **§5 — the pre-registered uncertainty scheme was anti-conservative.** The 48 scenario
   pairs are not 48 independent units: the block key excludes `delta_eta` and `n_train`,
   so they cluster into **8** parameter-draw blocks. Confirmed:
   `df[(df.M==5)&(df.K==4)].seed.nunique() == 400 == 8 × 50`. One seat measured a 2.4×
   understatement of the standard error and a conclusion that flips significance.
   → **D13**, corrected to block-clustered inference on 8 blocks (7 df); open to override.
3. **§4 — the interaction-saturation confound (D1)** stands as originally disclosed, and
   is now known to be a change in interaction **placement** as well as density: at d = 3
   the pairs are {(0,1),(0,2),(1,2)}, at d = 5 they are {(0,1),(0,2),(0,3)} — all on the
   one coordinate the designed-merge map collapses, leaving coordinate 4 purely additive.

Every factually false statement the council identified has been **corrected in the freeze,
with each correction marked in place** so the record shows what was claimed and why it
changed. Nothing was changed to make a veto disappear. **Five decisions (D14–D18) remain
unresolved and require an advisor ruling before A1 may begin.**

---

## 2. What was frozen

`01A_ADDENDUM_PROTOCOL_FREEZE.yaml` is a sibling of the parent freeze and is
self-contained enough that A1 can be executed from it without re-deciding anything. It
fixes:

| item | value | matched to the d = 3 twin? |
|---|---|---|
| M, K | 5, 4 | yes — the only (M, K) where `K**M = 1024 <= ENUM_CAP` |
| `d_active` | **5 (= M)** | **no — the single intentional difference** |
| marginal | uniform, zipf | yes |
| tau | 0.5, 1.5 | yes |
| `interaction_pairs` | 0, 3 | count matched, **saturation not** — see §4 |
| `delta_eta` | 0.0, 0.1, 0.3 | yes |
| `n_train` | 500, 5000 (nested) | yes |
| `n_eval` | 50,000 | yes |
| replicates | 50 | yes |
| scenarios | **48** | one-to-one with the 48 existing (M=5, K=4) 1B scenarios |
| encoder configurations | **13** (7 non-hash + 2 hash x 3 widths) | yes |
| bucket widths | B0 = 10, B1 = 20, B2 = 40 | yes — widths depend on (M, K) only, never on d |
| learners | oracle + logistic everywhere; LightGBM + MLP on the 6-config heavy subset at width "" / B1 | yes |
| rows | **182,400** = 76 x 50 x 48 | exactly the d = 3 twin's row count |

Everything else — natural-log and one-coordinate-Brier conventions, the Rao-Blackwellised
risk estimator, the `delta_eta` construction, all encoder constants (hash seed 20260810,
length-prefixed column-aware token, unsigned counting, `target_alpha` 20.0,
`woe_pseudocount` 0.5, `woe_clip` 5.0, 4 ordered-CatBoost permutations, HOMALS rank 2,
`KFold(5, shuffle=True, stratified=False)`), every learner hyperparameter, all
tolerances, and the typed-failure vocabulary — is inherited **verbatim by explicit
reference** rather than copied, with exactly two intentional differences recorded:
`d_active`, and a disjoint seed / scenario-id namespace.

The frozen contrast **AC-D** is `value(d=5) − value(d=3)` at the full matching key,
aggregated over 48 matched scenario pairs, with `representation_loss`,
`learner_shortfall`, `total_excess_risk`, log loss, Brier, ROC-AUC and PR-AUC reported
**separately and never summed**. Pre-registered expectations **E1–E4** are written down
as predictions, deliberately **not** as gates, following the precedent of retired
criterion A11. E4 states in the freeze that a null or reversed result is a publishable
finding and must be reported as such.

Twelve addendum acceptance criteria **AD1–AD12** live in their own namespace and will be
evaluated into a separate `07A_..._ACCEPTANCE_REPORT.json`.

All thirteen decisions D0–D12 are recorded in the freeze with a one-line rationale each,
so any of them can be overridden at this gate. Adopted: D0 keep the Phase R stamp files
as they are; **D1 match the interaction count and disclose the saturation confound**;
**D2 disjoint seeds with a matched block key**; D3 new runner file, leave
`run_sim1b_finite.py` and `sim1_core.py` byte-identical; D4 AC-D forms its own BH family;
D5 sizing memo and stop if the projection approaches 20 (not triggered); D6 wrap the
FigS4 footnote and pin the width, keeping the text on the figure; D7 the existing
token-in-tree / value-in-shipped-copy pattern for the ZIP SHA-256; **D8 yes, a 1-of-48
end-to-end probe is the required basis for extrapolation**; D9 the figure-data blob lives
in the ZIP only and is gitignored; D10 A0 commits nothing; **D11 Claude reviewers in the
Codex/Gemini seats, disclosed**; D12 `rows` means EXECUTED with a separate `rows_success`.

---

## 3. Unit and property tests — AT1–AT16

Full detail in `S0A_ADDENDUM_TEST_REPORT.md`. Commands and exit codes:

```
$ cd /Users/Eric/Desktop/114/ct2i-benchmark
$ PYTHONPATH=src python3 -m pytest tests/test_a0_dense_addendum_properties.py -q
264 passed in 10.59s                        exit code 0

$ PYTHONPATH=src python3 -m pytest tests/ -q
896 passed, 13 warnings in 15.23s           exit code 0
```

896 = 632 pre-existing (unchanged, still green) + 264 new. **AT1–AT16 all PASS.**
Fourteen of the sixteen criteria are exact assertions rather than tolerance checks and
eight are exhaustive over the full 1024-state space.

The headline verification number: across a 24-draw structurally complete grid, over all
1024 states, for **all 13 configurations including both hash encoders at all three
widths**,

```
max |R_log(Z) − R_log(X) − I(Y;X|Z)| = 2.325e-16      tolerance 1e-10
max |R_bri(Z) − R_bri(X) − E[Var(eta|Z)]| = 8.327e-17  tolerance 1e-10
```

This is the addendum's main methodological asset and should be stated as such: because
`4**5 = 1024 <= ENUM_CAP = 1e6`, the dense-signal arm is the **only** 1B configuration in
which every reported quantity, for every encoder including both hashes, is an exact
population quantity rather than a Monte Carlo estimate.

### Three findings the tests surfaced

**F1 — the nested `n_train` rule is load-bearing for the LABELS, not the covariates.**
A test drafted as a sanity guard failed, and the failure was correct. Under PCG64 the
covariate block of an independent n = 500 draw *is* bitwise the prefix of the n = 5000
draw, because `sample_records` draws all covariates in one row-major
`rng.choice(K, (n, M), p)` call. The labels are not: 213 of 500 differ. So the frozen
nesting rule must be implemented by explicit slicing, exactly as `run_sim1b_finite.py`
does; re-drawing at n = 500 would silently unpair the two training-size arms **on the
labels while leaving X identical**, which no covariate-level check would catch. The test
now asserts the true behaviour on X, eta and y.

**F2 — `collision_count` and `occupied_buckets` are declared but never written.** Both
are NULL for all 1,094,400 rows of the frozen 1B output. An addendum criterion gating on
them would be unfalsifiable, so AD11 carries an explicit `must_not_depend_on` clause and
AT11 asserts the invariant on the hash layer itself instead (exactly and exhaustively:
20 tokens, 1024 states, both token schemes, B ∈ {10, 20, 40}).

**F3 — the fitted `count` encoder is injective at d = 5 under Zipf (1024 fibers) and
merging under uniform (768 fibers)**, because it maps a level to its *sample* count.
Expectation E1 names `count` among the merging encoders; it is only testable on `count`
within the uniform stratum, and E1 must be reported per marginal rather than pooled.

---

## 4. THE DISCLOSED CONFOUND (decision D1) — read before any d = 5 minus d = 3 number

**One sentence for the advisor:** because `interaction_pairs` is held at 3, which is 100%
of the C(3,2) = 3 pairs available at d = 3 but only 30% of the C(5,2) = 10 available at
d = 5, the d = 5 versus d = 3 contrast varies signal dimension **and** interaction density
jointly — the *number* of interaction terms is held fixed, the *saturation* is not — and
no choice of `interaction_pairs` can hold both constant.

- **Held fixed:** the number of interaction terms in the linear predictor (3), which is
  what the risk depends on.
- **Not held fixed:** interaction saturation, 100% → 30%. At d = 3 the target is *fully*
  interactive over the active block; at d = 5 it is only *partially* interactive.
- **Why irreducible:** matching the count and matching the saturation are both
  defensible, and they are incompatible. There is no neutral option.
- **The alternative, available to the advisor at this gate:** set
  `interaction_pairs = [0, 10]` at d = 5 to match saturation instead of count; or run
  both, which doubles the arm to 72 scenarios / 273,600 rows at roughly 1.5x the
  projected core-hours — still inside the 20 core-hour cap.
- **Mandatory reporting if D1 stands:** the confound must appear in the A1 validation
  report, in the `FigS4_updated` caption, and wherever a d = 5 minus d = 3 difference is
  quoted. The manuscript must not read such a difference as a pure dimensionality effect.

This is the single most important scientific caveat of the addendum and it is not buried:
it has its own top-level block in the freeze
(`disclosed_confound_interaction_saturation`) and its own numeric assertion in the test
suite (AT7).

---

## 4a. THE UNDISCLOSED CONFOUND found at council review (decision D14)

**One sentence:** the frozen linear predictor
`g(x) = tau * (sum_{j in A} a_j(x_j) + sum_{(j,l) in P} b_jl(x_j,x_l))` draws one
p-centred standard-normal main effect **per active coordinate with no normalisation by
d**, so raising d from 3 to 5 at fixed `tau` adds two main effects and makes the d = 5 arm
carry strictly more signal than the d = 3 arm.

**Measured at A0**, 10 addendum-seeded draws in each of the **24** (marginal × tau × n_int ×
Δη) combinations at M = 5, K = 4. The grid is 2 × 2 × 2 × 3 = **24**; an earlier draft of
this report and of the freeze said 16, which is arithmetically wrong and contradicted the
test module's own `IDENTITY_GRID` comment and `S0A_ADDENDUM_TEST_REPORT.md`, both of which
already said 24 draws.

| | sd(eta) d=3 | sd(eta) d=5 | ratio | R_log(X) d=3 | R_log(X) d=5 |
|---|---|---|---|---|---|
| uniform, τ 0.5, n_int 0, Δη 0.0 | 0.0820 | 0.1060 | **1.293** | 0.6790 | 0.6698 |
| zipf, τ 0.5, n_int 0, Δη 0.0 | 0.0741 | 0.1059 | **1.429** | 0.6817 | 0.6696 |
| uniform, τ 1.5, n_int 3, Δη 0.3 | 0.2408 | 0.2485 | 1.032 | 0.5625 | 0.5531 |

The ratio exceeds 1 in **every one of the 24 combinations**, range **1.038–1.437** —
**confirmed by independent recomputation**: a fresh-context verifier re-ran the whole grid
from scratch and obtained 24/24 with that range.

**The three rows above are ILLUSTRATIVE, not the evidence.** They were printed from a
console session that was not shipped with a script, so a reader could not reproduce them
value-for-value; the numbers are left exactly as measured and are **not** adjusted to
match any later recomputation. The reproducible statement is the full-grid computation
below, which is the one the claim rests on. Run from the repository root:

```bash
PYTHONPATH=src:tests python3 - <<'PY'
import itertools, numpy as np
import test_a0_dense_addendum_properties as T

def sd_eta(marg, tau, n_int, delta, d, rep):
    blk = T.addendum_block(marg, tau, n_int)
    prm = T.CORE.draw_params(T.M_ADD, T.K_ADD, marg, tau, n_int, delta,
                             T.addendum_seed(blk, rep), d_active=d)
    tab = T.FIN.build_eta_table(prm)
    m = float((tab.p_cell * tab.eta).sum())
    return float(np.sqrt((tab.p_cell * (tab.eta - m) ** 2).sum()))

for lo in (1, 0):                      # replicate window 1-10 (host) and 0-9 (verifier)
    ratios = []
    for g in itertools.product(T.MARGINALS, T.TAUS, T.N_INTS, T.DELTAS):
        a = np.mean([sd_eta(*g, 3, r) for r in range(lo, lo + 10)])
        b = np.mean([sd_eta(*g, 5, r) for r in range(lo, lo + 10)])
        ratios.append(b / a)
    print("reps %d-%d: n=%d  ratio>1 in %d  range %.3f-%.3f"
          % (lo, lo + 9, len(ratios), sum(r > 1 for r in ratios),
             min(ratios), max(ratios)))
PY
```

Output (≈ 3 s, no cell executed, nothing written):

```
reps 1-10: n=24  ratio>1 in 24  range 1.032-1.429
reps 0-9:  n=24  ratio>1 in 24  range 1.038-1.437
```

The only difference between the two lines is which ten replicate indices are averaged.
Both give **24/24**, so the confound's existence and direction do not depend on that
choice; the headline range quoted above is the verifier's window.

**Why it bites.** Representation loss scales with the within-fiber variance of eta. For
the hash encoders the fiber partition is built on the full `K**M = 1024` space and depends
on M and K but **never on d**, so it is bit-for-bit identical in both arms. The entire
d = 5 − d = 3 hash difference is therefore "the same fixed partition destroys more of a
larger-variance eta" — which is **not** the mechanism E1 attributes it to ("a non-injective
encoder can no longer merge only pure-noise columns"). Confound and prediction point the
same way, so a confirmation of E1 is not by itself evidence for E1's *mechanism*.

**Why it is irreducible as frozen.** `dgp.linear_predictor` is inherited verbatim from the
immutable parent freeze.

**Advisor options at this gate (D14).** (1) Proceed and disclose, reporting both raw and
signal-normalised AC-D — recommended, and free, because `risk_x` is recorded on every row
so normalised gaps are computable post hoc. (2) Normalise `tau` by `sqrt(d)`, recorded as
a third intentional departure from the inherited DGP. (3) Add a signal-matched third arm,
isolating dimensionality from signal strength.

**Mandatory reporting if D14 option 1 stands:** any claim that the d difference is a
*dimensionality* effect must carry the signal-normalised version alongside it.

---

## 5. Seeds and the pairing consequence (decision D2)

Two mandates pull in opposite directions. Execution-prompt step 3 requires seeds
**disjoint** from the original run, so the addendum is not a partial re-run of the same
draws. Pairing power would be maximised by **sharing** the d = 3 seed so the two arms
differ only in d. These are incompatible.

**Adopted: disjoint seeds with a matched block key.** The addendum uses
`seed = 2_000_000_000 + 1000 * (blake2b(repr(block)) % 1e6) + replicate` with the same
block shape `(M, K, marginal, tau, interaction_pairs)` and the same exclusions
(`delta_eta`, `n_train`), so within-DGP contrasts stay paired exactly as in the parent
freeze — the invariant whose absence made criterion A8 fail 15/15 replicates.

**The statistical consequence, corrected at council review.** The two arms share the
block *structure* but not the parameter *draws*, so AC-D is paired at the **condition**
level, not the replicate level, and between-draw variance is not differenced out.

An earlier draft of this report and of the freeze then said "the effective sample size is
n = 48" and instructed A1 to compute uncertainty on that basis. **That was wrong and is
WITHDRAWN BY DECISION D13** — recorded here, and in the freeze under
`seeds.pairing_consequence.uncertainty_instruction_superseded`, rather than deleted. No
operative sentence in either document now tells A1 to use a per-scenario denominator.

The 48 scenarios are generated from only
**8 distinct parameter draws**: the block key `(M, K, marginal, tau, interaction_pairs)`
excludes `delta_eta` and `n_train`, so 2 marginals × 2 tau × 2 interaction levels = 8
blocks of 6 scenarios each. Verified on the frozen twin:
`df[(df.M==5)&(df.K==4)].seed.nunique() == 400 == 8 blocks × 50 replicates`. Between-draw
variance — precisely the component condition-level pairing fails to remove — is exactly
the clustered component, so `sd/sqrt(48)` understates the standard error. One seat
measured a **2.4× understatement** on an exact population probe, with a hash contrast
reading t = +3.3 (significant) naively and t = +1.31 (null) clustered.

Two further reductions in effective n, both measured on the frozen twin:

- Representation loss is **exactly** invariant to `n_train` for `label`, `onehot`,
  `hash_shared` and `homals` (`max|Δ| = 0.0`), so 24 of the 48 pairs are literal
  duplicates for that quantity.
- `hash_shared` representation loss is **identical across B0/B1/B2** (`max|Δ| = 0.0`),
  because the shared-value token space holds only K = 4 tokens; its three bucket-width
  contrasts are one piece of evidence, not three, and must be collapsed before entering
  the BH family.

**Adopted correction (D13):** cluster-robust inference on the **8 blocks** (7 df), with a
block-resampling bootstrap and the effective n stated per quantity. Freezing a procedure
three seats called anti-conservative would be a worse error than correcting it before
approval, and the correction only widens intervals. Open to advisor override.

**Rejected alternative and why:** sharing the d = 3 seeds would give replicate-level
pairing and much better power, but it would violate step 3 and would make the addendum's
Monte Carlo error dishonest, because the arm would not be a new sample.

**Disjointness is proved, not asserted.** The largest seed realised anywhere in the
completed run is 995,419,050 and the largest derived seed 995,619,050; every addendum
seed is at least 2,000,000,001, a margin of over 1e9. AT6 additionally enumerates all
2,400 addendum seeds plus their derived train/eval seeds and asserts an empty
intersection with all 5,900 realised seeds from `03_SEED_MANIFEST.csv`, and checks that
the OOF namespace (`91211 + 17*replicate`) is disjoint from the original
(`4211 + 17*replicate`). **PASS.**

---

## 6. Timing microbenchmark and the resource projection

**Method, and why it is this method.** The package discloses four consecutive
underestimates: `S0_RESOURCE_ESTIMATE.csv` projected the 1B fractional arm at **41.71**
core-hours against **57.97** measured (1.39x), and its `S1_CORRECTION` row records that
1C was understated by **3.7x** because it was projected from a 1B cell-cost proxy instead
of measured at 1C widths; `run_s1_reports.py` deviation D11 calls the 1B miss "the fourth
consecutive underestimate". Every one of those errors came from composing a proxy instead
of measuring. So A0 measured at the addendum's own configuration (decision D8) and
reports both a raw and a calibrated projection.

**The anchor is measured, not projected.** From the frozen 05b parquet, read-only:
`df[(df.M==5)&(df.K==4)].cpu_seconds.sum()/3600` = **5.931 core-hours** for an arm with
the identical M, K, encoders, learners, bucket widths, replicate count and row count —
differing from the addendum in `d_active` alone. The microbenchmark's only job is
therefore the **d = 5 / d = 3 cost ratio**.

**What was measured.** `scripts/s0a_addendum_microbenchmark.py` in two layers, output in
`S0A_ADDENDUM_MICROBENCHMARK_ROWS.csv`:

- *Unit layer (M1–M8)*, both d in one process. The d-sensitive operations are small in
  absolute terms — the eta table grows 64 → 1024 cells (ratio 10.6x on an operation
  costing 2.5 ms) and the `ebar_coordinatewise` probe grows 12 → 20 rows (ratio 1.75x on
  15 ms) — while every dominant operation is d-invariant as predicted: sampling 0.99x,
  hash full-space fibers 0.97x (they depend on M and K, not d), learner fit 1.02x,
  chunked evaluation prediction 1.00x.
- *End-to-end layer (D8)*: **three matched pairs** of whole-scenario probes at d = 3 and
  d = 5, 10 replicates x 13 configurations each, through a probe copy of the 1B scenario
  loop that takes `d_active` as a **parameter**, so both arms are timed on byte-identical
  code. `run_sim1b_finite.py` was **not executed**; it was imported only for
  `ebar_coordinatewise`.

| probe pair | d = 3 CPU | d = 5 CPU | ratio |
|---|---|---|---|
| zipf, tau 1.5, n_int 3, Δη 0.3, n_train 500 | 52.156 s | 53.520 s | 1.0262 |
| zipf, tau 1.5, n_int 3, Δη 0.3, n_train 5000 | 73.255 s | 74.493 s | 1.0169 |
| uniform, tau 0.5, n_int 0, Δη 0.0, n_train 5000 | 65.313 s | 68.579 s | 1.0500 |

*(Ratios recomputed to full precision from the microbenchmark rows after two council seats
found three of them rounded from console output. Net effect on the projection: +0.004
core-hours. The earlier figures were 1.0249 / 1.0164 / 1.0505.)*

**The arithmetic.**

```
r(n=500)  = 53.520 / 52.156                              = 1.026152
r(n=5000) = mean(74.493/73.255, 68.579/65.313)           = 1.033453
r         = (2.524478*1.026152 + 3.406390*1.033453) / 5.930868
                                                         = 1.030345
            (weights are the anchor's own n_train CPU split, 2.524 h / 3.406 h)
observed ratio spread over the 3 pairs                    = [1.016900, 1.050005]

raw_proj   = 5.930868 * 1.030345                         = 6.111 core-hours
             band from the ratio spread                    [6.031, 6.227]
calib_proj = 6.111 * 1.4                                 = 8.555 core-hours
             band                                          [8.444, 8.718]
wall_hours = 6.111 / 8 workers  = 0.76 h raw, 1.07 h calibrated
headroom   = 20 - 8.555                                  = 11.445 core-hours
```

**Probe-fidelity check.** At d = 3 the single-process probe costs 260.8 s per 50-replicate
scenario at n = 500 and 366.3 s at n = 5000, against 378.7 s and 511.0 s in the frozen
run — the real run costs ~1.4x the probe because it ran 8 workers on 8 cores. That factor
is already inside the anchor and cancels out of the ratio, which is exactly why the ratio
rather than the absolute probe cost is the extrapolated quantity.

**Verdict against the cap: PASS with wide margin.** The **calibrated 8.555 core-hours** is
**42.8% of the 20 core-hour ceiling**; even the top of the band (8.718) is 43.6%. The
value that goes on the console block is the calibrated one, not the raw one. Decision D5
(sizing memo and stop) is therefore not triggered.

**Memory.** Peak RSS 242–253 MB per probe worker, indistinguishable between d = 3 and
d = 5. x 8 workers ≈ 2.0 GB, against a 16 GB host and the 806 MB/worker envelope already
recorded for the far heavier M = 20, K = 50 cells.

**Disk**, from bytes/row measured on the d = 5 probe output (294.7 B/row CSV,
54.8 B/row parquet):

```
raw addendum CSV      182,400 * 294.7  = 53.8 MB
05e parquet           182,400 *  54.8  = 10.0 MB
summary / figure data / tables / checkpoints (<= 2x parquet, generous) = 20.0 MB
total                                  ~ 0.084 GB   against a 20 GB ceiling (0.42%)
```

**A0's own cost:** 387.4 s of end-to-end probe plus ~5 s of unit probes = **0.109
core-hours**, charged to A0.

**The probe output is a TIMING PROBE, not an addendum result.** Its 4,560 rows carry
`status = "TIMING_PROBE_NOT_A_RESULT"`, were written to a scratch directory **outside**
`simulation-results-ct2i/`, and are not summarised, plotted, or reported anywhere as a
dense-signal finding. No addendum result file exists.

---

## 7. The four mandatory A1 corrections — verified, specified, NOT implemented

**All four are A1 scope. None was implemented in A0.** Each is specified below precisely
enough to execute.

### Correction 1 — TabS1: WoE missing and 979,200 vs 1,094,400. CONFIRMED, both counts.

*Evidence.* `11_SIM1_TABLES/TabS1.csv` row `1B` lists 8 encoders
(`count, hash_column, hash_shared, homals, label, onehot, ordered_catboost_sim, target`)
with `woe` absent, and `rows = 979200`. The frozen parquet says otherwise:
`len(df)` = **1,094,400**; `df.status.value_counts()` = `{SUCCESS: 979200,
SKIPPED_INELIGIBLE: 115200}`; `sorted(df.encoder.unique())` returns **9** encoders with
`woe` present and `((df.encoder=='woe') & (df.status=='SUCCESS')).sum()` = 57,600, i.e.
100% success. Corroborated by `wc -l raw/sim1b_replicates.csv` = 1,094,401.
1,094,400 is the executed count; the 115,200 difference is the typed absence recorded as
deviation D12 (192 unidentified scenarios x 2 hash encoders x 3 widths x 50 replicates
x 2 metrics = 115,200, exact). The package currently contradicts itself:
`20_RESULT_HANDOFF_MEMO.md` line 20 already states `1B ... 1094400`.

*Root cause, one function, two bugs.* `scripts/run_sim1_tables.py`, `tab_s1`:
`g = d[d.status == "SUCCESS"]` (bug 1, drives `rows=len(g)`) and
`", ".join(str(x) for x in sorted(g[c].dropna().unique())[:8])` inside `lv()` (bug 2).

*The additional finding the reconnaissance surfaced, and which A0 has now widened.* The
`[:8]` truncation is **not** WoE-specific and **not** 1B-specific. Measured against all
four frozen component parquets:

| TabS1 row | column | true distinct | printed | silently dropped |
|---|---|---|---|---|
| 1A | `bucket_width` | 12 | 8 | 20, 24, 30, 40 |
| 1C exact | `bucket_width` | 11 | 8 | 1000, 2000, 4000 |
| 1C finite | `bucket_width` | 11 | 8 | 1000, 2000, 4000 |
| 1B | `encoder` | 9 | 8 | **woe** |
| 1B | `bucket_width` | **15** | 8 | 160, 240, 250, 480, 500, 1000, 2000 |

So **every one of the four component rows is wrong**, and fixing only WoE would leave
TabS1 wrong in five places. The largest bucket widths — precisely the ones the manuscript's
hash argument depends on — are the ones dropped.

*Fix for A1.* (a) Remove the `[:8]` cap in `lv()` for every column, or raise it above the
largest true level count; (b) compute `rows` from the unfiltered frame and add a separate
`rows_success` column (decision D12), keeping `status = "EXECUTED"` truthful; (c)
re-verify **all four** component rows against the parquets, not just 1B; (d) add the
addendum row (M = 5, K = 4, d = 5, 48 scenarios, 182,400 rows); (e) regenerate both
`TabS1.csv` and `TabS1.tex`.

### Correction 2 — FigS4 canvas width and SVG. CONFIRMED wide; SVG already satisfied.

*Evidence.* PDF MediaBox widths, read from the rendered files:
FigS1 450.49 pt (6.26 in), FigS2 556.13 pt (7.72 in), FigS3 599.51 pt (8.33 in),
**FigS4 1458.93 pt = 20.26 in — 2.8x the frozen `figures.style.double_column_in = 7.2`**.
`FigS4.svg` agrees at `width="1459.249687pt"`.

*Mechanism, both ingredients present in the source.* `scripts/run_sim1_figures.py` line 41
sets `savefig.bbox: "tight"`; line 240 creates the figure at `figsize=(DOUBLE, 2.6)`; lines
276–283 add a single unwrapped ~470-character `fig.text(.5, -.16, ...)` footnote. The tight
bbox expands the saved canvas to enclose the text, so the drawn area stays 7.2 in and
centred while the canvas grows to 20.26 in — roughly 6.5 in of empty canvas each side.
FigS2 and FigS3 use the same idiom with shorter strings, which is why they are mildly over
7.2 in; **they must be normalised in the same pass** or the package ships three page widths.

*SVG.* Already emitted — `save()` at lines 57–61 writes both `pdf` and `svg`, and
`FigS4.svg` (106,726 B) already exists. `figures.style.format: [pdf, svg]` mandates both.
No new plumbing; re-running the fixed `save()` path satisfies "corrected PDF and SVG".

*Fix for A1 (decision D6).* Wrap the footnote with `textwrap.fill()` to the figure width
and pin the saved width (explicit `bbox_inches` or `constrained_layout`) so the canvas is
7.2 in. **Keep the text on the figure** — `FIGURE_CAPTIONS.md` states the on-figure
statement exists precisely so a caption edit cannot lose the `d = 3` and
`NOT_IDENTIFIED` qualifications. Reword the `FigS4_updated` caption to *"the original 1B
arm uses d = 3 in every cell; the dense-signal addendum cells use d = M = 5"* without
weakening the `NOT_IDENTIFIED` qualification, since "d = 3 in every existing cell" becomes
false for the combined figure. Normalise FigS2 and FigS3 in the same pass.

### Correction 3 — repository README. CONFIRMED: all five items missing.

*Evidence.* `README.md` is 1,131 bytes and predates the entire simulation arm. It
documents only the real-data project, a `## Layout` list of `src/ tests/ configs/
scripts/ docs/`, and a licence section. Missing: the branch
`simulation-only/manuscript-revision`; the commit `931ee56…` (no 40-hex string anywhere);
the tag `sim-only-s1-complete-v2`; any reproduction command (none of `run_sim1a_exact.py`,
`run_sim1b_finite.py`, `run_sim1c_hash.py`, `run_sim2_reproduce.py`,
`run_sim1_summarize.py`, `run_sim1_figures.py`, `run_sim1_tables.py`, `run_s1_reports.py`,
`build_return_package.py`, `verify_package_checksums.py` is named); and package contents —
`simulation-results-ct2i/` and `simulation2_authoritative/` are absent from the Layout list.

*Additional defect not named by the advisor.* The `Status:` line is stale and misleading:
it describes the repo as Stage-2 pilot infrastructure with no mention that the branch
carries a completed, tagged, 1.41M-row simulation package. A reader arriving from a
data-availability statement would conclude no simulation exists. The same edit must
refresh it.

*Fix for A1.* Add a simulation section naming branch, final commit, final tag, the
reproduction commands, and the package contents; refresh the Status line. Documentation
only — no code, no results.

### Correction 4 — ZIP SHA-256 in the result handoff memo. CONFIRMED absent; stampable.

*Evidence.* `20_RESULT_HANDOFF_MEMO.md` carries repository, branch, annotated tag,
`AUTHORITATIVE COMMIT: 931ee56…`, pre-repair parent, row counts, CPU accounting,
acceptance, file map and open decisions — and **no 64-hex string anywhere** (`grep -cE
'[0-9a-f]{64}'` returns 0), despite the completion plan §9 and §14 both requiring it.

*Can the existing mechanism do it?* Yes, with a mechanical extension.
`scripts/stamp_provenance.py` already takes `[<zip-sha256>] [<zip-bytes>]`, already
validates with `re.fullmatch(r"[0-9a-f]{64}", zip_sha)` (line 79 region) and already
normalises byte counts — **but** substitutes the ZIP tokens only in
`REPORT_FILE = "REPAIR_REPORT.md"` (line 72), while the package files in
`MD_FILES = ["00_README.md", "19_VALIDATION_REPORT.md", "20_RESULT_HANDOFF_MEMO.md"]`
(line 64) receive only the *commit* token via `MD_PATTERN`.

*Fix for A1, three steps.* (1) In `scripts/run_s1_reports.py`, have the memo generator
emit `**Return package SHA-256:** PENDING_ZIP_SHA256_SEE_SHA256SUMS` (and optionally the
byte-count token). (2) In `scripts/stamp_provenance.py`, extend the ZIP substitution to
run over `MD_FILES` as well as `REPORT_FILE`, reusing the same two placeholders and the
same hex validation, and preserving the existing rule that an unsupplied optional argument
leaves its token in place and is never replaced with an empty string. (3) Keep the
ordering: stamp → `build_return_package.py` regenerates checksums → ZIP.

*The ordering hazard, and decision D7.* The ZIP's SHA-256 is computed over the ZIP, which
contains the memo; writing the hash into the memo changes the memo, changes the ZIP, and
changes the hash. This is not solvable by iteration. **Adopted: the existing
`REPAIR_REPORT.md` pattern** — the tracked in-repo copy keeps the token, the ZIP is built
from the stamped tree, and the hash is reported *outside* the archive (console block,
`PACKAGE_SHA256SUMS.txt`, advisor memo). This must be disclosed to the advisor so the
token in the repository copy is not read as an omission.

---

## 8. Council review — BOTH MANDATED SEATS FILLED FOR REAL

The execution prompt (A0 step 9) and the completion plan (§12 task 7) both require
**independent Codex and Gemini design reviews**, with provider notes preserved verbatim.

**The A0 work order asserted that neither provider was available in this environment and
planned a disclosed Claude substitution (decision D11). That premise was tested rather
than accepted, and it was false.** Both CLIs are installed and authenticated — `codex`
(`gpt-5.6-terra`) and `gemini` (`gemini-2.5-pro` via Vertex AI, project
`wq-alphas-prod-2607`) — matching the S0 precedent recorded in `S0_COUNCIL_REVIEW.md`.
The mandated seats were therefore **filled with the real providers**: Codex on
implementation/verification, Gemini on design/scope. The two fresh-context Claude
reviewers already launched are retained as **supplementary**, exactly as the S0 round
retained its Claude stand-in once Gemini became reachable. **No substitution was needed
and no output anywhere is attributed to a provider that did not produce it.**

| Seat | Provider | CRITICAL VETO |
|---|---|---|
| Implementation / verification | **Codex** (`gpt-5.6-terra`) | **2** |
| Design / scientific scope | **Gemini** (`gemini-2.5-pro`, Vertex AI) | **1** |
| Supplementary design | Claude, fresh context | **2** |
| Supplementary implementation | Claude, fresh context | **1** |
| **Distinct after de-duplication** | | **4** |

**All four seats independently reached "do not execute as written."** The four distinct
CRITICAL findings, each verified by the host before being accepted:

| # | finding | raised by | host check |
|---|---|---|---|
| C1 | total signal strength is not held constant when d goes 3 → 5 (§4a) | Gemini + both Claude seats | CONFIRMED, 24/24 combinations |
| C2 | the uncertainty scheme treats 48 clustered pairs as independent; there are only 8 blocks (§5) | Claude-design CRITICAL, Gemini MAJOR | CONFIRMED, `seed.nunique() == 400` |
| C3 | the A1 runner does not exist, so no preflight test exercises it; the seed rule is reimplemented three times | Codex | CONFIRMED — inherent to A0, converted to gate AD13 / decision D18 |
| C4 | AD10's `raw/*.csv` clause is unsatisfiable — the manifest has no `raw/` entry, and AT16 checks only a line count | Codex | CONFIRMED — decision D15 |

Convergent MAJOR findings the host also verified: Simulation 1A at M = 5, K = 4 is
**already** d = M = 5 and exact (52,800 rows, `n_cells = 1024`, 100 replicates), so the
freeze's uniqueness claim overstated and the population half of E1 is already answerable
from frozen data at zero cost; the hash seed, ordered-CatBoost permutation seeds (977–980)
and bootstrap seed (90210) are intentionally **shared** constants, making "every derived
seed is disjoint" overbroad; AD1/AD2 are self-checks as specified because
`exact_gap_report` derives both sides of the identity from one aggregation (the repo ships
`reference_gap_report` for exactly this and the preflight did not use it); `IDENTITY_GRID`
runs at `n_train = 5000`, replicate 1 only; `run_sim1b_finite.py:151-152` silently
`continue`s on a setup exception, writing no typed row; and `exact_or_mc == "mc"` on all
182,400 `IDENTIFIED_EXACT` rows.

All four seats independently confirmed the **resource arithmetic** and that **A0 left the
frozen artefacts untouched**. Two seats flagged that three of five ratios in
`S0A_ADDENDUM_RESOURCE_ESTIMATE.csv` do not reproduce to the fourth decimal from the rows
they cite (n = 500: 1.0262 measured against 1.0249 stated) — a ≈ 0.1% effect that does not
move the 8.55-versus-20 verdict.

**Response.** Every factually false statement was corrected in the freeze with the
correction marked in place. The uncertainty scheme was changed to block-clustered
inference (D13). **Nothing was changed to make a veto disappear:** C1 is now a fully
disclosed second confound awaiting an advisor ruling (D14), C2 is an adopted correction
open to override (D13), C3 and C4 became gates AD13/AD14 and decisions D15/D18.

**Four decisions remain UNRESOLVED and require an advisor ruling before A1: D14
(signal-strength confound), D15 (AD10 raw coverage), D16 (E1 decision rule), D17 (AD1/AD2
independence).** D18 (runner-first) is deliberately **not** in that set: its status is
`INHERENT_TO_A0_BECOMES_AN_A1_GATE`, so it is a mandatory A1 gate (criterion AD13), not an
open question awaiting a ruling.

Verbatim reviews from all four seats: `S0A_ADDENDUM_COUNCIL_REVIEW.md`.

---

## 9. NOT RUN IN A0 — explicit list

- **No addendum cell was executed.** `FULL ADDENDUM CELLS RUN: 0`. No
  `05e_..._RESULTS.parquet`, no `06A_` summary, no `07A_` acceptance report, no
  `08A_` figure data, no `03A_` seed manifest — none of these files exists.
- **`run_sim1a_exact.py`, `run_sim1b_finite.py`, `run_sim1c_hash.py`,
  `run_sim2_reproduce.py`, `run_simulations.py`, `run_pilot.py`, `run_smoke.py` were
  never invoked.** `run_sim1b_finite` was *imported* as a module, for
  `ebar_coordinatewise` only.
- **No real-data access of any kind.** No dataset, model, image, target or prediction.
  `REAL-DATA MODELS RUN: 0`.
- **No GPU.** `GPU HOURS USED: 0`.
- **No manuscript edit.** Not the main tex, not the supplement, not prose anywhere.
- **`01_PROTOCOL_FREEZE.yaml` unmodified.** No addendum section, no renumbering; it still
  contains exactly A1–A15 and the string "addendum" does not appear in it (asserted by
  AT16).
- **No frozen raw-result file modified.** All five re-hash 5/5 against
  `RAW_FREEZE_MANIFEST.json`, checked at the start and again at the end of A0.
- **No existing acceptance criterion edited or retuned.** The addendum uses the `AD*`
  namespace in its own file.
- **No git write of any kind** — no commit, tag, push, add, checkout, reset or config.
  HEAD is still `931ee56…`. The six Phase R stamped package files and `REPAIR_REPORT.md`
  are left exactly as they were.
- **No ZIP built, no tag created, no `PACKAGE_SHA256*` regenerated** — those belong to A1.
- **None of the four A1 corrections was implemented.** §7 specifies them; it does not
  apply them.

---

## 10. Artefacts produced by A0

| path | what |
|---|---|
| `simulation-results-ct2i/01A_ADDENDUM_PROTOCOL_FREEZE.yaml` | the frozen design, AD1–AD12, contrast AC-D, seed scheme, decisions D0–D12 |
| `simulation-results-ct2i/S0A_ADDENDUM_PREFLIGHT_REPORT.md` | this report |
| `simulation-results-ct2i/S0A_ADDENDUM_TEST_REPORT.md` | AT1–AT16 outcomes in detail |
| `simulation-results-ct2i/S0A_ADDENDUM_MICROBENCHMARK_ROWS.csv` | raw unit-cost, end-to-end and RSS measurements |
| `simulation-results-ct2i/S0A_ADDENDUM_RESOURCE_ESTIMATE.csv` | ratio, projections, band, headroom, disk |
| `simulation-results-ct2i/S0A_ADDENDUM_COUNCIL_REVIEW.md` | both reviews verbatim, with the substitution disclosed on the first line |
| `tests/test_a0_dense_addendum_properties.py` | AT1–AT16, 264 tests |
| `scripts/s0a_addendum_microbenchmark.py` | the timing probe (produces a probe, never a result) |
| scratch, **outside** the package | `TIMING_PROBE_ONLY_*.csv/.parquet` — discarded, not package files |

---

## 10a. Known limitations of the A0 evidence (recorded, A1 scope — not fixed in A0)

These are disclosures, not defects that A0 is authorised to repair. They are recorded so
A1 inherits them explicitly.

1. **The timing extrapolation rests on only three probe pairs, and one of them carries
   43% of the weight.** The d = 5 / d = 3 ratio (§6) is a CPU-weighted average of three
   matched pairs, weighted by the anchor's own `n_train` CPU split. The **single**
   `n_train = 500` pair supplies the whole 2.524 h of that split against a 5.931 h total,
   i.e. **≈ 43% of the weight comes from one measurement**. There is no replication at
   n = 500, so no within-configuration variance is available for that half of the weight,
   and a single anomalous probe would move the projection directly. The projection is
   still measured rather than composed from a proxy, the observed spread across the three
   pairs is narrow (1.0169–1.0500), and the 1.4× calibration plus the 43%-of-cap headroom
   absorb an error many times larger than anything three probes could plausibly hide — so
   this is a **disclosed single-point dependency, not a threat to the cap verdict**. A1
   should either add replicate probes at n = 500 before relying on the ratio for anything
   finer than the cap check, or state the dependency wherever the projection is quoted.

2. **The three illustrative rows in §4a were not shipped with a generating script.** An
   independent verifier could not reproduce them value-for-value (it obtained
   0.0814 → 0.1074, r = 1.319 where the table shows 0.0820 → 0.1060, r = 1.293), because
   the table was printed from a console session. The cause is now identified — the two
   computations average different ten-replicate windows — and the numbers have been left
   exactly as measured rather than adjusted to match. §4a now marks those rows
   **illustrative** and ships the runnable full-grid computation that the claim actually
   rests on; both replicate windows give **24/24** ratios above 1. Any A1 reader who needs
   per-combination values should run that command rather than cite the table.

3. **The exact-identity residuals in `S0A_ADDENDUM_TEST_REPORT.md` are asserted by the
   suite but not printed by it.** The test module checks them against
   `exact_identity_abs = 1e-10` and reports only pass/fail. A one-line regeneration
   command and the tolerance are now stated in that report; A1 should persist the maxima
   as data rather than prose if they are to appear in the manuscript.

---

## 11. Verdict

**A0 preflight work is COMPLETE. The design is NOT APPROVED for A1 as drafted.**

What holds: the design is frozen and self-contained, the verification is exact and
exhaustive where the 1024-state space permits (264 tests, max identity error 2.3e-16), the
seeds are provably disjoint, the frozen artefacts are untouched (5/5), and the resource
projection is measured rather than guessed and sits at 43% of its cap.

What does not: a four-seat council with **both mandated provider seats filled for real**
returned **four distinct CRITICAL findings**, and every seat independently concluded the
design must not execute as written. The freeze's factual errors have been corrected in
place; the design questions they expose have not been decided, and A0 has no authority to
decide them.

**Blocking on an advisor ruling: D14 (signal-strength confound — the most consequential),
D15, D16, D17 — four items. D13 was adopted as a correction and may be overridden. D18 is
not an open question: it is an A1 gate (AD13, runner-first) that A1 must satisfy.**

**Phase A0 stops here and waits for advisor approval before Phase A1.**
