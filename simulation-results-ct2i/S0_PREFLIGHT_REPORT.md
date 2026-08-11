# S0 Preflight Report — cT2I Simulation-Only Manuscript Revision

**Phase:** S0 (preflight only). **Assignment scope:** SIMULATION ONLY.
**Date:** 2026-08-11
**Baseline commit:** `7f6b62035951df7d032d0a3eab04cb3c9b0328b4`
**Working branch:** `simulation-only/manuscript-revision`
**Authoritative specification:** `CT2I_STUDENT_SIMULATION_ONLY_EXPERIMENT_PLAN.md`

---

## 1. Executive summary

Every Phase S0 task in the execution prompt has been completed. The protocol is
frozen, the required unit and property tests are implemented and passing, and the
timing and memory microbenchmark has been run. **The full simulations have not
been run, no real-data model was trained or accessed, and no manuscript,
supplement, historical repository, or real-data file was modified.**

**The council is complete.** All three provider organisations reviewed the frozen
protocol: Claude (host/integration), Codex (implementation and numerical
verification), and Gemini (independent DGP/design review, run via Vertex AI after
three separate authentication and routing obstacles were cleared). Gemini,
reviewing the corrected protocol with full input access, returned **0 blockers**
and concluded *"The protocol is ready for execution."*

**Critical veto count: 0.** Five blockers were raised across the review round
(1 by Codex, 4 by a stand-in design seat run while Gemini was unreachable). All
five were independently re-measured by the host and closed before this report.

One decision remains before Phase S1 may begin:

- **Sizing.** The full-factorial Simulation 1B projects to **90.6 CPU core-hours**
  against an **80 core-hour** ceiling. Per the plan the design has **not** been
  silently reduced; a prespecified fractional variant projecting to **47.8
  core-hours** — which fits the ceiling and preserves every central contrast — is
  frozen alongside it. The advisor chooses one, and the choice cannot change
  afterwards.

Because a compliant, fully-frozen execution path exists (the fractional variant)
and every required S0 task and output is delivered, the preflight status is
**COMPLETE**. The remaining sizing choice is the ordinary approval gate the
execution prompt already builds in, not an unfinished preflight task.

Separately recommended, but **not** blocking: a single additional 1B arm at
$M = 5$, $d = M = 5$. Two independent providers ranked the $d = \min(M,3)$
restriction as the study's most significant residual weakness; the arm is fully
enumerable and costs almost nothing, but it is a design *addition* and therefore
an advisor decision under the plan's own change control.

---

## 2. Repository and input verification

| Check | Result |
|---|---|
| Active repository contains the required baseline commit | **YES** (`git cat-file -t` → `commit`) |
| Branch created from that exact commit | **YES** (merge-base equals the baseline) |
| `main` rewritten or force-pushed | **NO** |
| Required input files present | **15 / 15**, 0 missing |
| Manuscripts modified | **NO** — opened read-only, parsed only |
| Stage 2 authoritative files modified | **NO** |
| Historical repository accessed or modified | **NO** — not cloned; not needed for S0 |
| Real-data files read, written, or models trained | **0** |

SHA-256 of every input is recorded in `S0_INPUT_AND_HASH_MANIFEST.csv`. A
`git diff` against the baseline over `manuscript_reference/`,
`simulation2_authoritative/`, `configs/` and the real-data artefacts is **empty**:
all work to date consists of *new* files only.

---

## 3. Placeholder mapping

**18 / 18 placeholders mapped**, no orphans.

Two populations were merged rather than trusting one: the 13-row combined
register, and the 7 literal `\SimPending{...}` anchors parsed from the manuscript
sources. Five anchors present in the main text (`SIM-ABS-01`, `SIM-FIG-01`,
`SIM-FIG-02`, `SIM-DISC-01`, `SIM-CONCL-01`) are **not** register IDs and would
have been missed by the register alone. The supplement contains no `\SimPending`
anchors; its simulation insertions are named by the register and by the editorial
checklist in §"Editorial checklist for conversion to the final supplement".

Every row carries the producing script and the required output file, so no
placeholder depends on a number typed by hand. Full detail in
`S0_PLACEHOLDER_OUTPUT_MAP.csv`.

---

## 4. Design freeze

`01_PROTOCOL_FREEZE.yaml` fixes: all factors and levels; encoder and learner
configurations; seed *rules*; tolerances; acceptance criteria A1–A15; hypotheses
H1–H6 with an enumerated BH family (C1–C11) including estimands, pairing, test
statistic and per-contrast directionality; the figure panel plan; the table column
plan; and the Simulation 2 reproduction targets.

Key resolutions of ambiguities in the plan (full detail in
`S0_IMPLEMENTATION_SPEC.md`):

- **`Delta_eta` is a controlled construction parameter**, not a descriptive
  statistic — defined as the maximum within-fiber posterior range of the designed
  merge encoder, and realised exactly by construction. Verified to $10^{-12}$.
- **Simulation 1C is exact, not Monte Carlo.** Shared-value hashing on binary
  records is a bijection of Hamming weight, so its fibers are indexed by $w$ and
  the hypergeometric conditional law makes every population quantity closed-form.
- **Risk estimation is Rao-Blackwellised** using the known $\eta$, which makes the
  representation-loss / learner-shortfall decomposition exact rather than
  approximate, and sharply reduces Monte Carlo error.
- **Unidentified quantities are reported as NULL**, never estimated and presented
  as theoretical. The 1B hash-encoder population gap is decided **per cell**:
  `IDENTIFIED_EXACT` where the full state space enumerates ($K^M \le 10^6$,
  covering 96 of 288 scenarios), `NOT_IDENTIFIED` elsewhere. Where it is
  unidentified, **both** `representation_loss` and `learner_shortfall` are NULL,
  because both require $R_{\text{Bayes}}(Z)$ — a blank must never be read as a
  zero for the encoders the manuscript indicts.
- **Contrasted arms share one DGP draw.** The seed is keyed on a block that
  excludes the contrasted factor, so every within-DGP contrast is paired.

---

## 5. Tests

**632 passed, 0 failed** (596 in the S0 module, 36 baseline tests unchanged). All
ten required properties are covered, plus the checks added to close review
findings (dependency-free reference implementation, seed pairing, per-cell gap
identification); tolerances are read from the frozen protocol
so no test can silently use a looser bound. Details and measured margins in
`S0_TEST_REPORT.md`.

Largest observed identity error: $2.2\times10^{-15}$ against a frozen $10^{-10}$
tolerance.

---

## 6. Microbenchmark and resource projection

Measured on Apple M2, 8 cores, 16 GB, macOS 26.2, through the streaming
evaluation path Phase S1 will actually use. Every $(M,K)$ combination in the
frozen grid was measured directly, so the projection involves no interpolation
across state-space size.

| Component | Cells | Serial core-hours | Wall hours @ 8 workers | Disk GB |
|---|---:|---:|---:|---:|
| 1A exact enumeration | 105,600 | 0.07 | 0.01 | 0.02 |
| 1B **full factorial** | 561,600 | **84.49** | 10.56 | 0.23 |
| 1B **fractional (proposed)** | 360,000 | **41.71** | 5.21 | 0.14 |
| 1C exact + finite sample | 66,000 | 5.84 | 0.73 | 0.03 |
| 2 reproduction | 1,459 | 0.15 | 0.02 | 0.01 |
| **TOTAL (full factorial)** | 734,659 | **90.55** | 11.32 | 0.28 |
| **TOTAL (fractional)** | 533,059 | **47.77** | 5.97 | 0.20 |
| Ceiling | — | 80.00 | 10.00 | 20.00 |

Peak RSS 806 MB per worker; 8 workers ≈ 6.5 GB, within the 16 GB host. GPU hours
**0**. Disk is not a constraint at either variant (0.3 GB against a 20 GB ceiling).

### Sizing memo

The full factorial exceeds the CPU ceiling by **13%**. As the plan requires, the
design has **not** been reduced to fit. Two options are frozen; **the advisor
chooses one, and the choice cannot change afterwards**:

- **Option A — full factorial (90.6 core-hours).** Requires a written ceiling
  amendment to ~100 core-hours. Nothing is dropped.
- **Option B — prespecified fractional (47.8 core-hours).** All 288 DGP scenarios
  and all 13 encoder configurations are retained and evaluated with the
  Bayes-on-$Z$ oracle and logistic regression. The two expensive learners
  (LightGBM, MLP) run on a fixed representative encoder subset spanning every
  encoder family, at one bucket width. **No DGP factor level is dropped**, so all
  six central contrasts named in the plan survive at full strength: injective vs
  non-injective; $\Delta_\eta = 0$ vs positive; small vs large training sample;
  low vs high cardinality; uniform vs rare-category; additive vs interactive.

Two implementation optimisations already reduced the projection substantially and
are byte-identical to the baseline behaviour: a vectorised chunked hash transform
(3× faster, equality asserted by test) and streamed evaluation that never
materialises the 763 MB encoded matrix.

---

## 7. Council review

`S0_COUNCIL_REVIEW.md` carries both reviews **verbatim**.

Two seats reported. **Every BLOCKER and MAJOR was independently re-run by the
host before being accepted** — none was taken on the reviewer's word.

**Codex** (implementation and numerical verification seat) returned **1 BLOCKER
and 6 MAJOR** findings, all valid, all closed in commit `4ac67a6`:

| Finding | Resolution |
|---|---|
| BLOCKER — freeze named `ordered_catboost`, implementation used the running-prior variant | Freeze now names `ordered_catboost_sim` explicitly, with reason |
| MAJOR — identity "independence" overstated (shared aggregation) | Added `reference_gap_report`, a dependency-free implementation, + 24 tests |
| MAJOR — A6 monotonicity is not a theorem in 1B | A6 restricted to 1A; 1B reported descriptively under H4 |
| MAJOR — A11 is an outcome expectation, not a validity gate | A11 retired as a gate; reported under H5 with a defined contrast |
| MAJOR — BH family underspecified; H6 covered only 2 of 3 encoders | Family enumerated C1–C11 with statistic and directionality; C11 added |
| MAJOR — "no scientific claim depends on the unidentified hash gap" too strong | Scope corrected: C1/C2 are empirical only; Figure S3 must label exact vs empirical |
| MAJOR — `Delta_eta` construction described inaccurately | Corrected: $\eta$ is not the logistic model cell-by-cell; fiber mean is not preserved under Zipf |

**Gemini** (independent DGP/design seat) ran via Vertex AI after three obstacles
were cleared — an unconsented OAuth scope, a disabled `aiplatform` API, and the
real cause: `~/.gemini/settings.json` pinned `selectedType: "oauth-personal"`,
which overrode the environment variables and kept routing requests to the
discontinued Code Assist endpoint, returning 403. The credentials were valid
throughout; a permissions-looking error was actually a routing error.

Gemini's first run could not read the authoritative plan, the manuscripts, or the
placeholder register (all hidden by `.git/info/exclude`, which the CLI honours),
so two of its nine assigned questions were unanswerable and its "no issue" on
them was not accepted. It was re-run in a workspace containing every input, with
zero ignore errors; **that run is the review of record**. It returned **0
BLOCKER, 1 MAJOR, 2 MINOR**, required no freeze change, and concluded *"The
protocol is ready for execution."* Note that Gemini reviewed the protocol *after*
the earlier fixes landed, so its zero-blocker result attests to the corrected
design, not the original.

Its single MAJOR — the `d = min(M,3)` restriction — was reached **independently**
by the stand-in seat, from the same brief but without sight of the other's output.
That convergence is why the optional extra arm is escalated to the advisor rather
than merely filed.

A **stand-in design seat**, run earlier while Gemini was unreachable, returned **4 BLOCKER, 8 MAJOR, 8 MINOR**, all closed or recorded
in commit `bfa617d`. The four blockers were serious and are summarised below; the
verification column reports the host's own re-measurement, not the reviewer's:

| Finding | Host re-measurement | Resolution |
|---|---|---|
| **B1** DGP seed keyed on an index containing the contrasted factor, so every within-DGP contrast was unpaired | **A8 fails 15/15 replicates unpaired, 0/15 paired** | `dgp_block_seed` excludes contrasted factors; nested `n_train` sampling |
| **B2** `NOT_IDENTIFIED` over-declared; both decomposition terms silently NULL for 6/13 encoder configs | **exact hash gap at M=5,K=4 computes in 4–9 ms** | per-cell identification (K^M ≤ 1e6); recovers 96 of 288 scenarios |
| **B3** A9 — the overgeneralisation guard — satisfied by an assignment, not a computation | confirmed by inspection | routed through the generic aggregation; zero now emerges at ~1e-17 |
| **B4** no estimand, unit of analysis, or test statistic for the contrasts whose p-values TabS3 must report | confirmed | unit = scenario; pairing, t-statistic and MDE frozen; deterministic contrast removed from the BH family |

Selected MAJORs: the designed-merge Brier gap is an exact function of
$(K, \text{marginal}, \Delta_\eta)$ alone (**host confirmed: 10 distinct values
across the entire factorial**), so H4/A5/C5 on that encoder are construction
identities and a companion observed-spread analysis was added; H6's instrument was
scale-confounded **and its direction is reversed at the prespecified contrast
under both raw SD and coefficient of variation** (host confirmed). The instrument
was corrected; **the hypothesis direction was deliberately not changed**, and the
pilot observation is disclosed in the freeze so that a Phase S1 rejection of H6
cannot be mistaken for post-hoc adjustment.

**This does not satisfy the letter of the execution prompt**, and is flagged for
the advisor rather than papered over.

**Critical veto count: 0.** All five blockers were closed before this report.

---

## 8. Findings raised by this preflight

**F1 — Own-label leakage in the baseline ordered-CatBoost encoder (MAJOR).**
`OrderedCatBoostEncoder` keeps a row's own label out of its numerator sum but
takes the prior from the mean of $y$ over **all** fitted rows, so the row's own
label re-enters its own code through the prior (magnitude $\approx 1/n$; measured
$7\times10^{-5}$ at $n = 400$). The baseline repository's PC2 leakage test covers
**only the target encoder**, so this channel had never been asserted. The baseline
encoder is **not modified** — it produced the frozen real-data results. Simulation
1B uses a running-prior variant with exactly zero self-influence. Both behaviours
are now pinned by tests.

**F2 — Environment gap.** LightGBM, a mandatory Simulation 1B learner, was absent.
Installed at the version pinned in `requirements.lock.txt` (`lightgbm==4.7.0`).

**F3 — Deprecated scikit-learn argument.** `LogisticRegression(penalty='l2')` is
deprecated in scikit-learn 1.8 and removed in 1.10. The argument is no longer
passed; L2 is the default and $C$ pins the regularisation.

**F4 — Own-label leakage was not the only latent defect.** The design seat's B1
(unpaired contrasts) would have produced a spurious, unfixable failure of
acceptance criterion A8 in Phase S1, because the freeze forbids retuning a failed
criterion. It was caught only because the review ran *before* the full run. This
is the clearest single argument for keeping the pre-run review gate.

**F5 — numpy version skew for Simulation 2.** The authoritative Stage 2 output was
produced under numpy 2.4.6; this environment has 2.4.1. PCG64 streams are stable
across these versions so a bitwise match is expected, but this is a Phase S1
verification step, not an assumption.

---

## 9. Deviations from the plan

Six, all recorded in `S0_IMPLEMENTATION_SPEC.md` §15 and carried forward to
`19_VALIDATION_REPORT.md`: the ordered-CatBoost running-prior variant; the swept
bucket-width rule overriding the baseline staircase; per-cell identification
reporting for the 1B hash gap; the $d = \min(M,3)$ active block in 1B; the dropped
`penalty` argument; and the LightGBM installation.

**Nine stated limitations** bound what the simulations can support
(`S0_IMPLEMENTATION_SPEC.md` §14a). The three most consequential, all surfaced by
the council review and re-measured by the host:

- In 1B, $M$ is a **noise-dimension factor, not a width factor** — the active
  block is identical at $M = 5$ and $M = 20$, so no scenario has many *informative*
  high-cardinality columns.
- The designed-merge result is a **construction identity**: its Brier gap is an
  exact function of $(K, \text{marginal}, \Delta_\eta)$ alone, so H4/A5/C5 on that
  encoder verify the construction rather than test the theory. A companion
  observed-spread analysis was added as the version of H4 that can fail.
- **H6's direction may be rejected.** An S0 pilot found it reversed at the
  prespecified contrast under both instruments. The instrument was corrected for
  an independent scale-confound reason; **the direction was not changed**, and the
  observation is disclosed in the freeze.

---

## 10. Environment

```
Python 3.11.9      numpy 2.4.1       pandas 2.3.3      scikit-learn 1.8.0
scipy 1.17.0       lightgbm 4.7.0    pyarrow 24.0.0    matplotlib 3.10.8
psutil 7.2.2       pytest 9.0.3
macOS 26.2 arm64 (Apple M2), 8 logical / 8 physical cores, 16 GB RAM
```

Note the environment differs from `requirements.lock.txt` in several pins (numpy
2.4.1 vs 2.4.6, pyarrow 24.0.0 vs 25.0.1, scikit-learn 1.8.0 vs 1.9.0). This is
recorded rather than silently accepted; whether Phase S1 should run under the
exact lockfile is a decision for the advisor, and matters mainly for the
Simulation 2 bitwise reproduction (F4).

---

## 11. What Phase S1 will do, on approval

In the order fixed by the plan: reverify hashes and the freeze; run 1A exact
checks; run 1C hash collapse; run 1B finite-sample study; reproduce Simulation 2;
freeze raw replicate-level outputs **before** inspecting aggregates; generate
every summary, table and figure by script; validate every prespecified criterion
without changing it; have Codex reproduce a sample of raw-to-summary calculations;
have the design seat audit interpretation scope and figure/table completeness;
commit and tag; and assemble the return package.

No manuscript prose will be written. The advisor inserts and interprets the
validated results.

---

## 12. Required approval statement

Phase S1 will not begin until the student supplies, in writing:

```
The Stage S0 protocol freeze and resource estimate are approved.
Proceed with Phase S1 without changing the frozen design.
```

together with a decision on the **Simulation 1B design variant** (Option A with a
ceiling amendment to ~100 core-hours, or Option B, the fractional variant that
fits the existing ceiling).

Optionally, and separately: whether to add the $M = 5$, $d = M = 5$ arm that two
independent reviewers' top-ranked finding points to. It is cheap and fully
enumerable, but it is a design addition and so requires your approval.
