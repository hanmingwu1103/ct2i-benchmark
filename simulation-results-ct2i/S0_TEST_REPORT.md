# S0 Test Report — Unit and Property Tests

**Phase:** S0 (preflight). **Scope:** simulation only.
**Test module:** `tests/test_s0_sim1_properties.py`
**Tolerance source:** `simulation-results-ct2i/01_PROTOCOL_FREEZE.yaml` (`tolerances:`)
**Environment:** Python 3.11.9, numpy 2.4.1, pandas 2.3.3, scikit-learn 1.8.0,
scipy 1.17.0, lightgbm 4.7.0, pytest 9.0.3, macOS 26.2 arm64 (Apple M2, 8 cores, 16 GB)

Tests read their tolerances **from the frozen protocol file**, so a test can never
silently use a looser bound than the one committed. Changing a tolerance requires
changing the freeze, which is a tracked, reviewable act.

---

## Result

```
tests/test_s0_sim1_properties.py .......................  577 passed
tests/ (full suite, incl. 36 baseline tests)              613 passed
                                                            0 failed
```

Runtime 2.1 s for the S0 module, 4.6 s for the full suite. Counts include the
24 tests added to close the Codex S0 review finding on identity independence.

---

## Coverage of the ten required properties

| # | Required property (execution prompt step 8) | Test class | Tests | Result |
|---|---|---|---|---|
| 1 | exact log-loss identity | `TestExactIdentities` | 320 (shared with #2) | PASS |
| 2 | exact Brier identity | `TestExactIdentities` | ↑ | PASS |
| 3 | injective zero-gap control | `TestInjectiveControl` | 146 | PASS |
| 4 | lossless non-injective control | `TestMergeControls` | 54 (shared with #5) | PASS |
| 5 | positive-gap lossy merge | `TestMergeControls` | ↑ | PASS |
| 6 | shared-value-hash range at most `M+1` | `TestSharedValueHashRange` | 25 | PASS |
| 7 | column-aware hash distinction | `TestColumnAwareDistinction` | 10 | PASS |
| 8 | no training-row self-influence (supervised) | `TestNoSelfInfluence` | 9 | PASS |
| 9 | deterministic seed replay | `TestSeedReplay` | 5 | PASS |
| 10 | typed-failure / null-metric behaviour | `TestTypedFailures` | 8 | PASS |

All ten are covered. Properties 1–5 are parameterised over a grid spanning both
$(M,K)$ shapes, both marginals, both signal scales, additive and interactive
targets, and all three $\Delta_\eta$ levels — 48 DGP combinations per encoder —
so they are property tests, not single-point smoke checks.

---

## Measured numbers

| Quantity | Frozen tolerance | Observed | Margin |
|---|---|---|---|
| Max abs log-loss identity error | $10^{-10}$ | $2.2\times10^{-15}$ | $\approx 4.7\times10^{4}$ |
| Max abs Brier identity error | $10^{-10}$ | $7.8\times10^{-16}$ | $\approx 1.3\times10^{5}$ |
| Injective encoder gap | $10^{-12}$ | $0.0$ (exact) | exact |
| Lossless merge gap ($\Delta_\eta = 0$) | $10^{-12}$ | $2.8\times10^{-17}$ | $\approx 3.6\times10^{4}$ |
| $\Delta_\eta$ realised vs requested | $10^{-12}$ | exact to $10^{-16}$ | — |
| Brier gap vs closed form $(\Delta_\eta/2)^2$ | $10^{-12}$ | exact to $10^{-16}$ | — |
| Shared-value reachable encodings | exact | $M+1$ at all $M$; $1$ when $b_0=b_1$ | exact |
| Hamming-weight target gap | $10^{-12}$ | $0.0$ (exact) | exact |
| Ordered-CatBoost (sim variant) self-influence | exact $0$ | $0.0$ | exact |

---

## Checks that go beyond the literal requirement

These were added because the literal requirements can be satisfied by code that is
subtly wrong, and a pre-run review is the only place to catch that.

**Identity paths are independent — in two senses**
(`test_identity_paths_are_independent`, `test_fast_path_matches_dependency_free_reference`).
An identity check is worthless if both sides come from the same computation. The
first test permutes the fiber assignment: the identity must still hold (both sides
move together) while the *value* must change, ruling out the identity being true
by construction rather than by theorem.

The Codex S0 review correctly noted that this is not enough on its own, because
both formulas consume the same `fiber_posteriors` aggregation — a defect in fiber
grouping, masses, or conditional means could make both sides agree *incorrectly*,
and permuting the partition would not expose it. The second test therefore
compares the fast path against `reference_gap_report`, a dependency-free
implementation using pure-Python dict grouping and `math` with no numpy
reductions, no `bincount`, and no shared helper. Agreement is asserted to
$10^{-10}$ across the grid, so a shared aggregation bug would have to be
reproduced independently in both implementations to survive.

**Brier gap matches an independent closed form.** With $K$ even and a uniform
marginal every designed-merge fiber holds two equiprobable cells, so
$\mathbb{E}[\operatorname{Var}(\eta\mid Z)] = (\Delta_\eta/2)^2$ exactly. Measured
$0.0225$ at $\Delta_\eta = 0.3$, matching to $10^{-16}$. This is an external check
on the entire $\Delta_\eta$ construction, not a self-consistency check.

**Shared-value range verified by brute force.** The $M+1$ formula is checked
against enumeration of all $2^M$ records for $M \in \{6,10,14\}$ and all tested
bucket widths. Collapsing widths ($b_0 = b_1$, range exactly 1) are located by
scan rather than assumed not to exist.

**Zero-gap controls are not vacuous.** `test_lossless_merge_at_delta_zero` asserts
`merged_fiber_count > 0` and `merged_fiber_mass > 0` before asserting zero gap, so
a bug that made the "merge" injective could not pass as a lossless merge.

**Monotonicity has direction.** `test_gap_increases_with_within_fiber_spread`
asserts strict ordering across $\Delta_\eta \in \{0, 0.1, 0.3\}$, not merely
non-negativity.

**Data-processing sanity.** `test_gaps_are_nonnegative` asserts no encoder ever
*reduces* Bayes risk, across the whole grid.

**Fold assignment is label-independent** (`test_fold_assignment_does_not_depend_on_labels`),
which is what makes property 8 exactly testable rather than approximately testable.

**Self-influence test is not vacuous.** `test_other_rows_do_influence_the_code`
confirms the encoders do use labels at all, so property 8 cannot pass because an
encoder ignores $y$.

**Count-encoder degeneracy is asserted, not discovered later.** Under a uniform
marginal every level shares probability $1/K$, so the population count encoder
collapses the entire state space to a single fiber; under Zipf it is injective.
`test_count_encoder_is_injective_under_zipf_only` pins both behaviours.

**Simulation hash encoder is byte-identical to the baseline.** The vectorised
encoder is an optimisation, not a redefinition; equality is asserted at matched
bucket width, including unseen-level behaviour.

**Failures cannot smuggle metrics.** `cell_result` raises if a non-SUCCESS cell
carries any metric, and if a SUCCESS cell carries none. Tests assert a failed cell
records `None` — explicitly *not* $0.0$ and *not* AUC $=0.5$.

**Silent clipping is impossible.** `impose_delta_eta` raises if $\eta$ would leave
$[0.05, 0.95]$; a test drives it out of band and asserts the raise.

**Decomposition identity is enforced at runtime.** `decompose()` raises if
representation loss + learner shortfall fails to reconstruct total excess risk to
$10^{-9}$, so a broken decomposition cannot reach the output files.

---

## Finding raised by the tests

**Own-label leakage through the ordered-CatBoost prior — MAJOR, resolved for the
simulation, reported to the advisor.**

Property 8 initially failed for `ordered_catboost`. Root cause: the baseline
`OrderedCatBoostEncoder` (`src/ct2i_benchmark/encoders/supervised.py:106`) keeps a
row's own label out of the numerator sum but sets `prior_ = y.mean()` over **all**
fitted rows, so the row's own label re-enters its own code through the prior.
Measured magnitude $\approx 7\times10^{-5}$ at $n = 400$, bounded by $1/n$ — small
but systematic. The baseline repository's own PC2 test
(`tests/test_pc_leakage_invariants.py:52`) exercises **only the target encoder**,
so this channel had never been asserted.

Resolution: the baseline encoder is **not modified**, because it produced the
frozen real-data results and this is a simulation-only assignment. Simulation 1B
uses `OrderedCatBoostRunningPrior`, which takes the prior from strictly preceding
rows in the same permutation (with a data-independent fallback for the first row),
giving exactly zero self-influence. Two tests now pin both behaviours:
`test_baseline_ordered_catboost_leaks_own_label_through_the_prior` asserts the
baseline channel exists and is bounded by $1/n$, and
`test_simulation_variant_removes_the_prior_channel` asserts the variant's is
exactly zero.

This is recorded as deviation 1 in `S0_IMPLEMENTATION_SPEC.md` §15 and will be
carried into `19_VALIDATION_REPORT.md`.

---

## Baseline suite

The 36 tests present at the baseline commit still pass unchanged. No baseline test
was modified, weakened, or skipped.

## Not yet tested (deferred to Phase S1 by design)

- End-to-end reproduction of the Simulation 2 authoritative values — requires the
  full $R = 10{,}000$ run, which is Phase S1 step 5.
- Figure and table generation scripts — these run from frozen raw outputs that do
  not exist until Phase S1.
- Acceptance criteria A6, A8, A15 — these are properties of the *aggregate*
  results and can only be evaluated after the full run. Their tolerances are
  already frozen. (A11 was retired as a gate at S0 review; the underlying
  question is reported under H5 with a defined paired contrast.)
