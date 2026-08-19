# S0A Test Report — Dense-Signal Addendum Unit and Property Tests (Phase A0)

**Phase:** A0 (preflight). **Scope:** simulation only. **Addendum cells run: 0.**
**Test module:** `tests/test_a0_dense_addendum_properties.py`
**Design under test:** `simulation-results-ct2i/01A_ADDENDUM_PROTOCOL_FREEZE.yaml`
(M = 5, K = 4, d = M = 5)
**Tolerance source:** `simulation-results-ct2i/01_PROTOCOL_FREEZE.yaml` (`tolerances:`),
read at run time, so no test can silently use a looser bound than the committed one.
**Environment:** Python 3.11.9 (`/Users/Eric/.pyenv/versions/3.11.9/bin/python3`),
numpy 2.4.1, pandas 2.3.3, scikit-learn 1.8.0, scipy 1.17.0, lightgbm 4.7.0,
pyarrow 24.0.0, pytest 9.0.3, macOS arm64, 8 cores, 16 GB.

---

## Result

```
$ cd /Users/Eric/Desktop/114/ct2i-benchmark
$ PYTHONPATH=src python3 -m pytest tests/test_a0_dense_addendum_properties.py -q
264 passed in 10.59s                                    exit code 0

$ PYTHONPATH=src python3 -m pytest tests/ -q
896 passed, 13 warnings in 15.23s                       exit code 0
```

896 = 632 pre-existing tests (unchanged and still green — A0 is not allowed to break
the original arm's verification) + 264 new addendum tests.

**Measured identity errors across the whole A0 grid** (24 DGP draws x 13 encoder
configurations, exhaustive over all 1024 states):

```
max |R_log(Z) - R_log(X) - I(Y;X|Z)|  = 2.325e-16     tolerance 1e-10
max |R_bri(Z) - R_bri(X) - E[Var|Z]|  = 8.327e-17     tolerance 1e-10
```

Six orders of magnitude inside the frozen tolerance, on both hash encoders as well
as the coordinate-wise ones — which is only possible because 4**5 = 1024 enumerates.

**Provenance — regenerate both figures in one command.** The two maxima above are
asserted test-by-test (AT2, `test_logloss_identity_holds_for_every_configuration` and
`test_brier_identity_holds_for_every_configuration`) against
`tolerances.exact_identity_abs = 1e-10`, read from `01_PROTOCOL_FREEZE.yaml`, but pytest
prints only pass/fail. Run this from the repository root to print the maxima themselves
(≈ 9 s; imports the test module, runs no addendum cell, writes nothing):

```bash
PYTHONPATH=src:tests python3 -c "import test_a0_dense_addendum_properties as T; R=[r for g in T.IDENTITY_GRID for r in T._reports_for_draw(*g).values()]; print(len(R),'reports from',len(T.IDENTITY_GRID),'draws'); print('logloss %.4e' % max(r['identity_error_logloss'] for r in R)); print('brier   %.4e' % max(r['identity_error_brier'] for r in R))"
```

Output:

```
312 reports from 24 draws
logloss 2.3245e-16
brier   8.3267e-17
```

Both are compared against the frozen tolerance **1e-10** (`exact_identity_abs`), so the
margin is ~6 orders of magnitude. **Confirmed by independent recomputation:** a
fresh-context verifier obtained the same 2.3245e-16 / 8.3267e-17.

---

## AT1-AT16 outcomes

| id | test class | asserts | kind | tests | result |
|---|---|---|---|---|---|
| AT1 | `TestFullSpaceEnumeratesExactly` | 1024x5 cell grid, all states distinct, `sum(p_cell) = 1` under both marginals, eta finite at all 1024 states, d = M | exact, exhaustive | 10 | PASS |
| AT2 | `TestEbarCoordinatewiseMatchesDirectAtD5` | the `d*K = 20`-row probe route equals direct 1024-cell enumeration **bitwise**, partition and ebar, for all 7 non-hash encoders x 2 marginals x 2 n_train | exact | 29 | PASS |
| AT3 | `TestExactIdentitiesAllThirteenConfigsAtD5` | log-loss identity `<= 1e-10` on **all 13 configurations including both hashes at B0/B1/B2**, over the full 1024-state enumeration, on a 24-draw grid | exact, exhaustive | (shared) | PASS |
| AT4 | same class | Brier identity, same coverage | exact, exhaustive | 51 total | PASS |
| AT5 | `TestInjectiveZeroGapAtD5` | `label` and `onehot` yield exactly 1024 distinct fibers and gap `<= 1e-12` at every Delta_eta; a merging encoder is checked to have a positive gap so the zero is not vacuous | exact, exhaustive | 50 | PASS |
| AT6 | `TestAddendumSeedsDisjointFromOriginal` | addendum seed set, its derived train/eval seeds and its OOF namespace are all disjoint from the 5,900 realised seeds in `03_SEED_MANIFEST.csv`; disjointness is also structural (min addendum seed exceeds max original + offsets); scenario-id namespaces disjoint; grid arithmetic 76 x 50 x 48 = 182,400 | exact | 6 | PASS |
| AT7 | `TestAddendumBlockPairingPreserved` | drawn `(a, b)` bitwise identical across all three Delta_eta levels and both n_train levels within a block (the invariant whose absence made A8 fail 15/15); different blocks differ; replicate still varies the draw; **and the D1 confound is asserted numerically** (3 of 3 pairs at d=3 versus 3 of 10 at d=5) | exact | 8 | PASS |
| AT8 | `TestNestedNTrainDraw` | n=500 is bitwise the prefix of the n=5000 draw at d=5, and eta lookup agrees between table and sample | exact | 3 | PASS |
| AT9 | `TestDeltaEtaConstructionExactAtD5` | all 512 designed-merge fibers have size exactly 2 and realise `max(eta)-min(eta) = Delta_eta` to `<= 1e-15` (worst observed 8.3e-17); eta inside [0.05, 0.95] at all 1024 states, so clipping never occurs; lossless at Delta=0 and strictly lossy above | exhaustive | 49 | PASS |
| AT10 | `TestHashGapIdentifiedAtM5K4` | `4**5 = 1024 <= ENUM_CAP`, `hash_gap_identified(5,4) is True`, and the function's signature takes no `d` — so identification cannot depend on d; exact full-space gap available for both hashes at all three widths | exact | 8 | PASS |
| AT11 | `TestCollisionsAndBucketsExact` | the bucket table equals an independent token-by-token recomputation; collision and occupied-bucket counts are exactly predictable at B in {10,20,40} for both token schemes; full-space fiber counts are exact (240/363/768 column-aware, 56/56/56 shared-value); column-aware never loses more than shared-value | exact, exhaustive | 19 | PASS |
| AT12 | `TestNoSelfInfluenceAtD5` | flipping a training row's own label leaves its own `target` / `woe` / `ordered_catboost_sim` code bitwise unchanged at d=5 (criterion A12 re-established in the dense regime), with a sanity check that OTHER rows do move it | exact | 5 | PASS |
| AT13 | `TestSeedReplayBitwiseAtD5` | one scenario replays bitwise across all 13 configurations, every field of every gap report; a different replicate gives a different draw; the eta table replays bitwise | exact | 3 | PASS |
| AT14 | `TestTypedFailureNulls` | every typed failure carries NULL in all 11 metric fields and is never 0.0 or 0.5; metrics cannot be smuggled into a failure; SUCCESS requires metrics; an out-of-band Delta_eta raises rather than clipping silently | exact | 8 | PASS |
| AT15 | `TestDecompositionIdentityAtD5` | `total_excess_risk = representation_loss + learner_shortfall` within 1e-9 on fitted cells, 6 encoder configurations x 2 metrics, with a real fitted logistic learner and the population ebar | tolerance 1e-9 | 12 | PASS |
| AT16 | `TestOriginalRawUnchanged` | SHA-256 of all five frozen raw outputs match `RAW_FREEZE_MANIFEST.json`; `raw/sim1b_replicates.csv` still has 1,094,401 lines; `01_PROTOCOL_FREEZE.yaml` still carries exactly A1-A15 and contains no addendum content | exact | 3 | PASS |

**Total: 264 tests, 264 passed, 0 failed.** Fourteen of the sixteen criteria are exact
assertions rather than tolerance checks; eight are exhaustive over the full 1024-state
space. That is what `4**5 = 1024` buys, and it is why this particular addendum is
unusually cheap to verify.

---

## Findings surfaced BY the tests (not defects in the design, but facts A1 must respect)

**F1 — the nested `n_train` rule is load-bearing for the LABELS, not the covariates.**
A test drafted as a sanity guard ("an independent n=500 draw is not the prefix of the
n=5000 draw") FAILED, and the failure was correct: under PCG64 the covariate block of
an independent n=500 draw *is* bitwise the prefix, because `sample_records` draws all
covariates with one `rng.choice(K, (n, M), p)` call consumed row-major. The labels are
NOT: `rng.random(n)` is reached after 25,000 covariate variates at n=5000 against 2,500
at n=500, so 213 of 500 labels differ. Consequence: the frozen nesting rule
(`seeds.n_train_pairing`) must be implemented by explicit slicing, exactly as
`run_sim1b_finite.py` does. Re-drawing at n=500 would silently unpair the two
training-size arms on the labels while leaving X identical — a failure that would be
invisible in any covariate-level check. The test now asserts the true behaviour on all
three of X, eta and y.

**F2 — `collision_count` and `occupied_buckets` are never written.** Both columns are
declared in `run_sim1b_finite.FIELDS` but no code path assigns them; they are NULL for
all 1,094,400 rows of the frozen 1B output (verified:
`df[['collision_count','occupied_buckets']].notna().sum()` is 0 and 0). Any addendum
criterion gating on them would be unfalsifiable. AT11 therefore asserts the invariant on
the hash layer itself, exactly and exhaustively, and `AD11` carries an explicit
`must_not_depend_on` clause. Recorded as known gap G1 in the freeze.

**F3 — the fitted `count` encoder is injective at d = 5 under Zipf and merging under
uniform.** Measured: 1024 fibers under `zipf`, 768 under `uniform`, because the encoder
maps a level to its *sample* count and Zipf makes the four level-counts distinct almost
surely. Expectation E1 names `count` among the merging encoders; it is only testable on
`count` within the uniform stratum. E1 must be reported per marginal, not pooled. This
is written into the freeze under `expectations.E1.measured_caveat_recorded_at_A0`.

---

## What these tests do NOT establish

- They do not run an addendum cell, and no result row exists. AT1-AT16 verify that the
  frozen design is implementable, exactly verifiable and seed-disjoint; they say nothing
  about the scientific outcome.
- AT15 is a tolerance check (1e-9), not an exact one, and it is evaluated on a sampled
  set of fitted cells rather than exhaustively. AD5 must re-evaluate it on every executed
  cell in A1.
- AT8's coverage of the nesting rule is a property of `sample_records`; the A1 runner must
  still be checked to *use* the slice rather than redraw. That check belongs to A1.
- AT13 spot-checks bitwise replay on one scenario. AD8 widens it to >= 3 scenarios x 3
  replicates in A1.
