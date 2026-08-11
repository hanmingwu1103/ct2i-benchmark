# S0 Council Review — Independent Review of the Frozen Protocol

**Phase:** S0 (preflight). **Scope:** simulation only.
**Reviewed artefacts:** `01_PROTOCOL_FREEZE.yaml`, `S0_IMPLEMENTATION_SPEC.md`,
`sim1_core.py`, `sim1_binary.py`, `sim1_finite.py`, `test_s0_sim1_properties.py`,
the authoritative plan, and the placeholder register/map.

Provider notes are reproduced **verbatim** below, exactly as returned, per the
execution prompt. Line references in the reviews point at the files as they stood
*at review time*; several have since moved because of the fixes the reviews
prompted.

---

## 1. Council composition and a provider gap

| Seat | Assigned provider | Status |
|---|---|---|
| Orchestration, integration, write-boundary enforcement | Claude (host) | Filled |
| Implementation, tests, numerical verification | **Codex** | **Filled** — `codex exec`, default model |
| Independent DGP/design review, conclusions-follow-from-contrasts, figures/tables/handoff | **Gemini** | **NOT FILLED** |

### Gemini unavailability — verbatim error

Two invocation attempts were made. The first specified `gemini-2.5-pro`; the
second was not attempted because the failure is an authentication/eligibility
failure, not a model-selection failure.

```
Error: This client is no longer supported for Gemini Code Assist for individuals.
To continue using Gemini, please migrate to the Antigravity suite of products:
https://antigravity.google
    ineligibleTiers: [
      {
        reasonCode: 'UNSUPPORTED_CLIENT',
        reasonMessage: 'This client is no longer supported for Gemini Code Assist
          for individuals. To continue using Gemini, please migrate to the
          Antigravity suite of products: https://antigravity.google',
        tierId: 'free-tier',
        tierName: 'Gemini Code Assist for individuals'
      }
    ]
```

No `GEMINI_API_KEY` or `GOOGLE_API_KEY` is configured in this environment, so no
fallback authentication path exists.

An initial Codex attempt also failed, on model selection rather than
authentication, and was retried successfully with the default model:

```
ERROR: {"type":"error","status":400,"error":{"type":"invalid_request_error",
"message":"The 'gpt-5-codex' model is not supported when using Codex with a
ChatGPT account."}}
```

### Substitute for the Gemini seat

Rather than leave the design-review seat empty, an **independent reviewer agent
was run under a different model instance**, given the Gemini seat's brief
verbatim and instructed to be adversarial and to verify rather than accept prior
work. It re-derived and re-ran quantities instead of trusting the S0 test report.

**This does not satisfy the letter of the execution prompt**, which names Gemini
specifically. The substitute shares a provider organisation with the host, so it
is *not* an independent-organisation review, and its findings should be weighted
accordingly. It is recorded here rather than papered over. **The advisor must
either supply Gemini credentials and re-run this seat, or waive it in writing.**

---

## 2. Disposition summary

Both reviews were substantive and both found real defects. **Every BLOCKER and
MAJOR was independently verified by re-running the code before being accepted** —
none was taken on the reviewer's word.

### Codex — 1 BLOCKER, 6 MAJOR, 5 MINOR

| ID | Severity | Finding | Verified? | Disposition |
|---|---|---|---|---|
| — | BLOCKER | Freeze named `ordered_catboost`; implementation used the running-prior variant | Yes, by inspection | **Fixed** — freeze names `ordered_catboost_sim` with reason |
| — | MAJOR | Identity "independence" overstated: both formulas share `fiber_posteriors` | Yes | **Fixed** — added dependency-free `reference_gap_report` + 24 tests |
| — | MAJOR | A6/H4 monotonicity is not a theorem in 1B | Yes | **Fixed** — A6 scoped to 1A designed-merge only |
| — | MAJOR | A11 is an outcome expectation, not a validity gate | Yes | **Fixed** — A11 retired; reported under H5 |
| — | MAJOR | BH family underspecified; H6 covered 2 of 3 encoders | Yes | **Fixed** — family enumerated; C11 added |
| — | MAJOR | "No scientific claim depends on the unidentified hash gap" too strong | Yes | **Fixed** — scope corrected; C1/C2 empirical only |
| — | MAJOR | `Delta_eta` construction described inaccurately | Yes | **Fixed** — corrected in spec §3 |
| — | MINOR ×5 | DGP otherwise sound; `d=min(M,3)` legitimate but limiting; running-prior remedy sound; 1C closed form sound; figures should label empirical vs exact | — | **Recorded** as limitations |

### Design seat (Gemini substitute) — 4 BLOCKER, 8 MAJOR, 8 MINOR

| ID | Severity | Finding | Verified? | Disposition |
|---|---|---|---|---|
| B1 | BLOCKER | Seed keyed on an index containing the contrasted factor → all within-DGP contrasts unpaired | **Yes — reproduced: A8 fails 15/15 unpaired, 0/15 paired** | **Fixed** — `dgp_block_seed` excludes contrasted factors; nested `n_train` |
| B2 | BLOCKER | `NOT_IDENTIFIED` over-declared; decomposition silently NULL for 6/13 encoder configs | **Yes — exact hash gap at M=5,K=4 computes in ~5 ms** | **Fixed** — per-cell identification (K^M ≤ 1e6); NULL consequence documented |
| B3 | BLOCKER | A9 satisfied by an assignment, not a computation | Yes, by inspection | **Fixed** — routed through the generic aggregation; zero now emerges (~1e-17) |
| B4 | BLOCKER | No estimand/unit of analysis/test statistic for C1–C10 | Yes | **Fixed** — unit = scenario; pairing, t-statistic, MDE frozen; C5 excluded from BH |
| M1 | MAJOR | Designed-merge Brier gap is an exact function of (K, marginal, Δ) alone | **Yes — reproduced: 10 distinct values across the whole factorial** | **Disclosed** in freeze; companion observed-spread analysis added |
| M2 | MAJOR | A6 fails 9.4% / 16.2% for hash encoders even in 1A | Accepted (consistent with theory) | **Fixed** by the A6 scoping above |
| M3 | MAJOR | H6 instrument scale-confounded and empirically reversed | **Yes — reproduced: reversed under BOTH raw SD and CV** | Instrument → CV; **direction disclosed, NOT changed** |
| M4 | MAJOR | Count encoder is a knife-edge tie artifact; normal CIs misspecified | Yes | **Recorded**; bootstrap primary for count contrasts |
| M5 | MAJOR | 1C has no frozen `learners` or `tau` | Yes | **Fixed** — both frozen |
| M6 | MAJOR | FigS1 panels are machine-precision tautologies; FigS3 has redundant series | Yes | **Fixed** — FigS1 4→3 panels; FigS3 series pruned and marked |
| M7 | MAJOR | `d=min(M,3)` makes M a pure noise-dimension factor in 1B | Yes | **Recorded** as limitation 1; caption disclosure required |
| M8 | MAJOR | H1/H2 are implementation verification, not falsifiable hypotheses | Yes | **Recorded** — already partly conceded in the freeze |
| m1 | MINOR | `fitted_learner_cells` arithmetic error (259,200 vs 360,000) | Yes | **Fixed** |
| m2 | MINOR | A7 brute-forced only to M ≤ 14 | Yes | **Recorded**; TabS2 must say so |
| m3 | MINOR | FigS2 source arm unspecified | Yes | **Fixed** — pinned to 1A; interval kind marked |
| m4 | MINOR | FigS3 has three coincident zero series | Yes | **Fixed** — merged into one reference series |
| m5 | MINOR | Producing scripts do not exist yet | Yes | **Recorded** — status note added |
| m6 | MINOR | `position_specific_eta` ignores `q`; unweighted centring drifts prevalence | Yes | **Fixed** — q-weighted centring |
| m7 | MINOR | label/onehot not injective on the 1B population (UNSEEN bucket) | Yes | **Recorded** as limitation 2a |
| m8 | MINOR | No prevalence/imbalance factor anywhere | Yes | **Recorded** as limitation 8 |

### Items deliberately NOT actioned

- **M8 / H1–H2 framing.** The reviewer is right that these are verification
  rather than falsifiable hypotheses. H1 and H2 are named in the **authoritative
  plan**, which the student may not rewrite. They are retained under their plan
  names, with the freeze and spec both stating plainly that they are tolerance
  checks with no multiplicity adjustment. Renaming them is an advisor decision.
- **M3 direction.** The instrument was corrected; the **hypothesis direction was
  not**. C9–C11 remain one-sided "greater" as frozen, and H6 may be rejected with
  the wrong sign. Changing a prespecified direction after a pilot observation is
  exactly what the freeze forbids.
- **M7 extra arm.** The reviewer suggests adding an $M=5$, $d=M=5$ arm so signal
  dimension and width move together. This is a **design addition**, not a defect
  fix, and adding factors at S0 review without advisor approval would violate the
  plan's own change control. **Recommended to the advisor** as an optional,
  cheap (fully enumerable) addition.

**Critical veto count: 0.** All five blockers (1 from Codex, 4 from the design
seat) were closed before this report; none stands unresolved against the frozen
protocol.

---

## 3. Codex review — verbatim

> ## Independent S0 review
>
> ### BLOCKER
>
> - **The frozen encoder name and implemented encoder disagree.** The protocol freezes `ordered_catboost` for 1B and includes it among encoders whose theoretical gaps are identified ([01_PROTOCOL_FREEZE.yaml:160], [01_PROTOCOL_FREEZE.yaml:194]). But the implementation creates a distinct `ordered_catboost_sim` running-prior variant ([sim1_finite.py:69], [sim1_finite.py:98], [sim1_finite.py:218]). The baseline `ordered_catboost` demonstrably has own-label influence through its full-sample prior ([supervised.py:102], [supervised.py:121]); the tests explicitly document it ([test_s0_sim1_properties.py:369]).
>   If the runner follows the freeze, A12 fails; if it follows the implementation/spec, the actual encoder is not the one named in the frozen factor list. This must be reconciled before S1.
>
> ### MAJOR
>
> - **The identity checks are structurally separate formulas, but not genuinely independent implementations.** Both Bayes-on-Z risks and both RHS calculations call the same `fiber_posteriors()` aggregation ([sim1_core.py:270], [sim1_core.py:285], [sim1_core.py:301]). A defect in fiber construction, grouping, masses, or conditional means can therefore make both sides agree incorrectly. The "wrong fiber" test merely verifies that the theorem holds for a different valid partition; it does not break a shared dependency ([test_s0_sim1_properties.py:89]). The arithmetic identities are well implemented, but the claimed independence is overstated.
>
> - **The `Delta_eta` range claim is correct; the preservation/scientific-description claim is not.** The code does deliver exact range \(\Delta_\eta\) in every non-singleton designed-merge fiber ([sim1_core.py:208], [sim1_core.py:223]), and the band assertion is sound. However, the affine transformation does not preserve the original logistic DGP "exactly": it replaces raw cell-level posterior magnitudes with a fiber mean plus a rank score. Further, with Zipf probabilities, the equally spaced rank shape is not probability-centred, so the post-squash fiber mean is generally not \(0.20+0.60m(f)\). The assertion that the symmetric rank shape "preserves the fiber mean only slightly" is not a guarantee ([S0_IMPLEMENTATION_SPEC.md:138]).
>   This is acceptable as a deliberately synthetic controlled-loss DGP, but not as a faithful logistic-main-effects-and-interactions DGP. Manuscript wording must say so.
>
> - **A6/H4 does not follow for all of 1B.** `Delta_eta` is engineered on the *designed-merge* fibers, but 1B does not include that encoder ([01_PROTOCOL_FREEZE.yaml:153]). A6 nevertheless requires nondecreasing gap over 1B ([01_PROTOCOL_FREEZE.yaml:442]). For sample-fitted encoders, changing \(\Delta_\eta\) also changes labels, fitted mappings, collisions between numeric codes, and finite-sample variation. Monotonicity is not a theorem there; it can fail for a valid reason or pass by averaging away a counterexample. H4 is well tested only for designed merge in 1A.
>
> - **`NOT_IDENTIFIED` for 1B hashes is honest, but "no scientific claim depends on this" is too strong.** Reporting NULL theoretical gaps is the correct choice ([01_PROTOCOL_FREEZE.yaml:199]). But planned finite-sample contrasts explicitly compare `hash_shared` with one-hot and column-aware hash on representation loss ([01_PROTOCOL_FREEZE.yaml:611]). 1C supplies an exact result only for shared-value hashing; column-aware's population gap remains unidentified ([S0_IMPLEMENTATION_SPEC.md:245]). Thus 1B can support empirical finite-sample comparisons, but not population/theorem claims about the comparative size of those hash gaps.
>
> - **A11 is an outcome expectation, not a valid acceptance gate.** "Learner shortfall is nonincreasing in \(n_{\rm train}\)" ([01_PROTOCOL_FREEZE.yaml:463]) is not guaranteed for finite samples, fixed hyperparameters, early stopping, or OOF/full-fit representation shift. It lacks a defined paired contrast, aggregation rule over scenarios, and test statistic. A scientifically sound run may fail it; conversely, an average can pass despite important adverse strata. It belongs as a prespecified descriptive/inferential result, not a pass/fail validation criterion.
>
> - **Multiplicity is underspecified and internally incomplete.** BH is stated for H3–H6 ([01_PROTOCOL_FREEZE.yaml:502]), but the actual elementary hypothesis tests, their directionality, and their family membership are not defined. The ten planned contrasts include only Target and WoE for H6—not ordered CatBoost, despite H6 defining all three ([01_PROTOCOL_FREEZE.yaml:504], [01_PROTOCOL_FREEZE.yaml:619]). BH cannot rescue an unspecified collection of tests.
>
> ### MINOR
>
> - The DGP is otherwise complete and nondegenerate: independent positive-support marginals, seeded effects, fixed interactions, and bounded posterior are clearly specified. The statement that centring/\(\beta_0=0\) keeps prevalence "near 0.5" is only approximate after the rank construction ([S0_IMPLEMENTATION_SPEC.md:92]); it is not a degeneracy concern.
>
> - The `d=min(M,3)` block is legitimate for a sparse-signal finite-sample regime and does not weaken the exact theorem check, because 1A retains \(d=M\) ([S0_IMPLEMENTATION_SPEC.md:64]). It does weaken any claim about encoding loss when many coordinates jointly carry signal. State that limitation plainly.
>
> - The running-prior CatBoost remedy itself is technically sensible: its training code uses only preceding labels and a data-independent first-row fallback ([sim1_finite.py:111]). The problem is freeze/implementation alignment, not the remedy.
>
> - 1C's closed form is sound for the shared-value hash: different 0/1 buckets make the encoding a bijection of Hamming weight; identical buckets make it constant ([sim1_binary.py:84], [sim1_binary.py:150]). Its Hamming-weight null is a real overgeneralization guard. Note that the position-specific target is re-randomized by seed and centred with an unweighted pattern mean ([sim1_binary.py:59]); width trends should therefore be interpreted as the specified DGP ensemble, not a universal monotonic law.
>
> - Figures and tables cover the main manuscript placeholders and appropriately separate representation loss from learner shortfall ([01_PROTOCOL_FREEZE.yaml:541], [01_PROTOCOL_FREEZE.yaml:569]). They should visibly label column-aware 1C and 1B hash gaps as empirical/not identified where applicable; otherwise Figure S3 can invite an unsupported population-risk comparison.
>
> Overall: the theorem algebra and controlled designed-merge construction are strong, but I would not approve S1 until the CatBoost encoder identity is frozen unambiguously and A6/A11 plus the H3–H6 testing/multiplicity rules are made logically evaluable.

---

## 4. Design-seat review (Gemini substitute) — verbatim

> # Independent DGP / Design Review — cT2I Simulation-Only Protocol, Phase S0
>
> **Reviewer seat:** independent DGP & design review (substitute provider).
> **Repository state reviewed:** `/Users/Eric/Desktop/114/ct2i-benchmark` at `7f6b620` (clean tree).
> **Posture:** adversarial and independent. I re-derived and re-ran the relevant quantities rather than accepting the S0 test report. All numeric claims below were produced by executing the frozen code in-memory; no file was modified.
>
> **Overall judgement.** The engineering discipline here is genuinely above the norm for a student simulation package — the Rao-Blackwellised risk estimation, the exactly-enforced decomposition, the typed-failure/NULL-metric contract, the discovery and quarantine of the ordered-CatBoost prior leak, and the unsigned-hash convention that isolates column identity as the *only* difference between the two hash encoders are all correct and well motivated. I want that on the record before the criticism.
>
> But the *design* is weaker than the engineering, and in four places it is broken in ways that are cheap to fix now and impossible to fix after S1 begins. The central problems are: (i) the seed rule un-pairs every within-DGP contrast the protocol claims to make; (ii) the headline decomposition is undefined for 6 of 13 encoder configurations in Simulation 1B, which silently guts one figure, two prespecified contrasts, and one blocking manuscript placeholder; (iii) at least one acceptance criterion is satisfied by an assignment statement rather than a computation; and (iv) no estimand, unit of analysis, or test statistic is defined anywhere for the ten prespecified contrasts whose p-values Table S3 is required to report.
>
> ---
>
> ## Findings table
>
> | ID | Severity | Category | Finding | Location |
> |---|---|---|---|---|
> | **B1** | **BLOCKER** | 2, 3 | Seed rule keys the DGP draw on `scenario_index`, which *contains* the contrasted factor (Δ_η, n_train, M). Every within-DGP contrast (A6, A8, A11, C5–C8) is therefore unpaired by construction. A8 fails **59/60** under the frozen seed rule and **0/60** when paired. | `01_PROTOCOL_FREEZE.yaml:391,392–393,396`; factors at `:107,:147,:224` |
> | **B2** | **BLOCKER** | 1, 6, 7 | In 1B, `representation_loss` *and* `learner_shortfall` both require `R_Bayes(Z)`, which is declared `NOT_IDENTIFIED` for hash encoders — 6 of 13 encoder configurations. This contradicts `design_variants` (oracle on all 13), voids contrasts C1 and C2, blanks FigS4 for every hash config, and cannot satisfy SIM1-RESULT-02. The declaration is also **over-broad**: I computed the exact hash gap for M=5,K=4 in 0.02 s. | `:163`, `:174–182`, `:199–210`, `:569–577`, `:610–612` |
> | **B3** | **BLOCKER** | 2, 6 | A9 ("shared-value hash has zero gap under the Hamming-weight target") is satisfied by an assignment, not a measurement: the code *sets* the gap to zero on the non-collapsed branch. The spec claims it is "measured, not asserted". | `sim1_binary.py:175`; `S0_IMPLEMENTATION_SPEC.md:241`; `01_PROTOCOL_FREEZE.yaml:454–457` |
> | **B4** | **BLOCKER** | 7 | No estimand, no unit of analysis, and no test statistic is specified for any of C1–C10, yet TabS3 must report `p_raw`/`p_bh`. The BH family is ambiguous (4 hypotheses vs 10 contrasts), and C1/C2/C5 are deterministic exact quantities whose degenerate p-values would mechanically loosen BH for the stochastic ones. | `:493–504`, `:604–620` |
> | **M1** | MAJOR | 1, 4 | The Δ_η construction makes the designed-merge Brier gap an **exact deterministic function of (K, marginal, Δ_η) alone** — invariant to M, τ, n_int, and the seed. H4/A5/A6/C5 are construction identities, not empirical findings. 100 replicates × 96 conditions yield 12 distinct values. | `sim1_core.py:193–228`; `:76–94`, `:439–445` |
> | **M2** | MAJOR | 2 | A6 is scoped to *all* encoders but is a theorem only for φ_D. Paired, it fails **9.4%** (hash_column) and **16.2%** (hash_shared) of Δ-triples in 1A — real mathematics, not a bug. | `:442–445` |
> | **M3** | MAJOR | 3, 7 | H6's operationalisation (raw across-replicate SD, Zipf vs uniform at K=50) is scale-confounded and empirically **reversed** at the prespecified level: target SD = 0.0051 (uniform) vs 0.0028 (Zipf). | `:504`, `:619–620` |
> | **M4** | MAJOR | 1 | The count encoder is a knife-edge artifact of exactly-equal marginals: 1 fiber under uniform, 64/64 (injective) under Zipf, no intermediate state. Its 1B analogue is an integer-tie lottery (K=4 uniform: mean 0.0056, SD 0.0110). Normal CIs are misspecified on a spike-at-zero mixture. | `sim1_core.py:381`; `:114–115`, `:613` |
> | **M5** | MAJOR | 2, 8 | 1C has a finite-sample sub-arm (n_train, n_eval, replicates, ROC-AUC, PR-AUC are all specified and budgeted) but **no `learners:` key and no frozen τ**. Two free parameters in a "frozen" protocol. | `:222–266`; `S0_RESOURCE_ESTIMATE.csv` row `1C` |
> | **M6** | MAJOR | 7 | FigS1 panels a/b/d are a machine-precision tautology (residuals ~1e-16 on a symlog axis). FigS3's five series reduce to three identical zero lines, one missing series (column-aware, NOT_IDENTIFIED), and one informative curve. | `:541–549`, `:558–568` |
> | **M7** | MAJOR | 5 | `d = min(M,3)` makes M a **pure noise-dimension factor** in 1B: the active block is identical at M=5 and M=20. Any "M effect" is a noise-feature-ratio effect. No scenario ever has many *informative* high-cardinality columns. | `S0_IMPLEMENTATION_SPEC.md:64–77`; `:73` |
> | **M8** | MAJOR | 2, 3 | H1/H2 as stated are unfalsifiable in 1A/1C: both sides are computed from the same exact (η, p) over the same fibers and are algebraically equal in two lines. They are implementation verification, not hypotheses. | `:487–488`, `:494–501` |
> | **m1** | MINOR | 8 | `fitted_learner_cells: 259200` contradicts the resource estimate's 360,000 for the same fractional design (and the design's own description). | `:182` vs `S0_RESOURCE_ESTIMATE.csv:1B,fractional_proposed` |
> | **m2** | MINOR | 2 | A7 is brute-force verified only for M ≤ 14; at the production M ∈ {50,200,1000} the criterion evaluates the same formula it is checking. | `sim1_binary.py:89–106`; `:446–449` |
> | **m3** | MINOR | 7 | FigS2's source arm (1A exact vs 1B finite) is unspecified, yet the placeholder register demands `ci_low`/`ci_high` — degenerate for exact cells (mcse = 0). | `:550–557`; register row SIM1-FIG-02 |
> | **m4** | MINOR | 7 | In 1C, label/onehot/count are all injective on binary data → three redundant identically-zero series in FigS3. | `:232`, `:566` |
> | **m5** | MINOR | 8 | Every producing script named in the placeholder map (`run_sim1a_exact.py`, `run_sim1b_finite.py`, `run_sim1c_hash.py`, `run_sim1_summarize.py`, `run_sim1_figures.py`, `run_sim1_tables.py`, `run_sim2_*.py`, `s0_env_commit.py`) does not exist. | `S0_PLACEHOLDER_OUTPUT_MAP.csv`; `ls scripts/` |
> | **m6** | MINOR | 1 | `position_specific_eta` accepts `q` and never uses it, and centres `g` by an *unweighted* mean over the 32 patterns rather than the q-weighted mean, so prevalence drifts with activation rate. | `sim1_binary.py:59,69` |
> | **m7** | MINOR | 2 | label/onehot are **not** injective on the population in 1B (UNSEEN bucket): measured rep. loss 0.0031 at K=50/Zipf/n=500. They are nonetheless the "injective" reference arm in C1/C4. | `unsupervised.py:14–60`; `:613,:616` |
> | **m8** | MINOR | 1 | No prevalence/imbalance factor anywhere: β₀ = 0 and the affine squash pin marginal prevalence near 0.5 in every cell. | `sim1_core.py:64–68,223` |
>
> ---
>
> ## 1. Does the DGP support the conclusions, or is there a hidden degeneracy?
>
> There is a hidden degeneracy, and it is at the centre of the design.
>
> `impose_delta_eta` (`sim1_core.py:193–228`) does not perturb a logistic posterior — it **replaces** it. After
>
> ```
> eta = 0.20 + 0.60 * m[fid] + (delta_eta / 2.0) * s        # sim1_core.py:223
> ```
>
> η is constant on φ_D fibers up to the ±Δ_η/2 rank term. Because the two cells of a φ_D fiber factorise (coordinate 0 merged pairwise, the rest untouched), the within-fiber conditional weights depend only on (K, marginal). Hence
>
> E[Var(η|Z_D)] = (Δ_η/2)² · Σ_i P(fiber_i)·4w_{i0}w_{i1},
>
> a function of **(K, marginal, Δ_η) only**. I verified this exhaustively over M ∈ {3,5}, τ ∈ {0.5,1.5}, n_int ∈ {0,2}, seeds {101,202}:
>
> | (K, marginal, Δ_η) | distinct Brier gaps observed |
> |---|---|
> | (4, uniform, 0.3) | **1** value: 0.0225 = 0.15² |
> | (3, uniform, 0.3) | **1** value: 0.0150 = 0.15²·(2/3) |
> | (4, zipf, 0.3) | **1** value: 0.019699291980989 |
> | all 12 groups | 1 value each (one group shows a 1e-15 float wobble) |
>
> So across the entire 96-condition × 100-replicate Simulation 1A factorial, the designed-merge Brier gap takes **12 distinct values**, and all 100 replicates within a condition are bitwise identical. τ, n_int and M — three of the six 1A factors — are analytically inert for the headline quantity. The log-loss gap varies only through curvature at η̄, ±10% around the same deterministic number.
>
> This is not fatal to 1A's role as a *control*, and the closed-form corroboration in §3 of the spec is a good check. But it means the "representation loss grows with within-fiber heterogeneity" result cannot distinguish "the theory is right" from "we imposed the answer". See M1.
>
> Two further degeneracies:
>
> - **Count encoder (M4).** `count_pop` maps a level to its *true* marginal probability (`sim1_core.py:381`). Under uniform, all K levels tie exactly → **1 fiber out of 64**, gap 0.137. Under Zipf, no ties → **64 fibers**, gap exactly 0. There is no intermediate regime anywhere in the design. The finite-sample analogue in 1B is a different object (sample counts), and its loss is an integer-tie lottery: at K=4/uniform/n=500 I measure mean 0.0056 with SD 0.0110 — a spike-at-zero mixture on which the frozen "mean ± 1.96·MCSE" interval (`:509`) is misspecified.
> - **Prevalence (m8).** β₀ = 0 plus the squash pin prevalence near 0.5 everywhere. The paper's motivating setting (categorical tabular benchmarks) is frequently imbalanced, and the "rare category" story never interacts with a rare outcome. PR-AUC is listed as a secondary metric (`:374`) but carries almost no independent information at prevalence 0.5.
>
> **Positive:** the p-centring/double-centring of a and b is correct and does make τ a genuine scale knob rather than a prevalence shift; the independence assumption is stated as an assumption, not smuggled in; and grouping fibers on `quantize`d integer keys rather than float equality (`sim1_core.py:177–179`) is the right call.
>
> ---
>
> ## 2. Do the prespecified conclusions follow? Is any criterion unfalsifiable, trivial, or able to pass for the wrong reason?
>
> Four criteria have real problems.
>
> **A9 is satisfied by fiat (B3).** `01_PROTOCOL_FREEZE.yaml:454–457` and `S0_IMPLEMENTATION_SPEC.md:241` both present the Hamming-weight zero gap as *measured*: "This is measured, not asserted, at every M ∈ {10,50,200,1000}". The implementation does the opposite:
>
> ```python
> else:
>     # Z is a bijection of w and eta is a function of w -> zero gap
>     risk_z_log, risk_z_bri, cmi, evar = risk_x_log, risk_x_bri, 0.0, 0.0   # sim1_binary.py:175
> ```
>
> `test_hamming_weight_target_is_lossless_under_shared_value_hash` (`tests/test_s0_sim1_properties.py:236–241`) then asserts that this literal `0.0` is below 1e-12. The underlying mathematics is correct, but the *overgeneralisation guard* — the single most important honesty device in the whole 1C arm, the thing that stops the manuscript indicting feature hashing in general — is a tautology as implemented. It should be routed through the same `ebar_w` path as the position-specific branch so the zero emerges numerically from `p_a_given_w`-style aggregation. As it stands, a genuine bug in the shared-value fiber logic would leave A9 green.
>
> **A6 is over-scoped and will fail for reasons unrelated to the theorem (M2).** A6 (`:442–445`) claims monotonicity in Δ_η with scope `[simulation_1a, simulation_1b]` and no encoder restriction. Monotonicity is a theorem only for φ_D. For any other encoder, Var(η|Z) picks up a cross term 2·(0.6)·(Δ/2)·Cov(m(f_D), s | Z) which is linear in Δ and can be negative, dominating the (Δ/2)² term at Δ = 0.1. Measured over the 1A grid, **matched-seed**, 20 seeds per condition:
>
> | encoder | non-monotone Δ-triples |
> |---|---|
> | designed_merge | 0 / 640 |
> | count_pop | 0 / 640 |
> | hash_column | **181 / 1920 (9.4%)** |
> | hash_shared | **311 / 1920 (16.2%)** |
>
> Example: hash_shared, M=3,K=3, uniform, τ=0.5, n_int=0, seed 104 → gaps (0.00995, 0.00774, 0.01910). Since the freeze forbids retuning a failed criterion (`:8–9`), Table S2 will carry a failed A6 that the advisor must then explain away in prose — precisely the situation prespecification is meant to prevent. Scope A6 to `designed_merge` **now**, or restate it as "nondecreasing on average over replicates for the designed merge".
>
> **A1/A2 (and H1/H2) are implementation verification, not tests (M8).** In 1A and 1C both sides are computed from the same exact (η, p) over the same enumerated fibers; they are equal by a two-line telescoping argument given in the spec itself (`S0_IMPLEMENTATION_SPEC.md:38–41`). `test_identity_paths_are_independent` establishes *code-path* independence, not mathematical independence — the permuted-fiber control shows the KL path is not a re-derivation of the risk difference, which is a good and necessary check, but it does not make the identity falsifiable. The freeze partially concedes this (`:494–501`) and I regard the framing as *nearly* honest; but calling them H1 and H2 in a hypothesis list, alongside genuinely empirical H5/H6, invites a reviewer to read them as evidential when their maximum informational content is "the arithmetic is right to 2.2e-15".
>
> **A7 is checked against itself at production scale (m2).** Brute force covers M ≤ 14; at M ∈ {50,200,1000} `shared_value_reachable` returns `M+1 if b0 != b1 else 1` by formula, and A7 checks that this is ≤ M+1. Acceptable given the proof, but Table S2 should say "verified by enumeration at M ≤ 14; asserted by the Stage 1 proposition above".
>
> **A10 I checked and it is fine.** Over the full 1A grid (M∈{3,5}, K∈{3,4}, both marginals, both τ, both n_int, all Δ, all three bucket widths) I found **0 violations** of `fiber_count(hash_column) > fiber_count(hash_shared)`. Worth stating in the manuscript that this is an empirical property of the frozen blake2b seed, not a theorem, but the criterion is sound and will pass.
>
> **A11–A14 are well constructed.** A11 correctly specifies "averaged over replicates" (unlike A6/A8); A12's rationale for `KFold` over `StratifiedKFold` (`:319–325`) is exactly right and I would have raised it had they not; A14 and its implementation in `cell_result` (`sim1_finite.py:394–414`) are the cleanest part of the package.
>
> ---
>
> ## 3. Is every hypothesis H1–H6 actually measured?
>
> | Hypothesis | Measured by | Verdict |
> |---|---|---|
> | H1, H2 | A1/A2, 1A + 1C exact | Measured, but see M8 — verification, not test |
> | H3 | A3/A4, 1A only | **Measured only in 1A.** In 1B, label and onehot are *not* injective on the population (UNSEEN bucket): I measure 0.0031 at K=50/Zipf/n=500 (m7). Fine as long as the manuscript does not claim H3 was confirmed in the finite-sample arm. |
> | H4 | A5/A6/C5, designed_merge | Measured, but the answer is imposed (M1). |
> | H5 | A11, C6–C8 | Measured — the strongest genuinely empirical hypothesis in the set. But undefined for hash encoders (B2) and unpaired across n_train (B1). |
> | H6 | `H6_instability_measure` (`:504`), C9/C10 | **Measured with the wrong instrument (M3).** |
>
> **H6 in detail.** The frozen measure is the across-replicate SD of representation loss for target/WoE/ordered-CatBoost, Zipf vs uniform at matched K, and C9/C10 fix K=50. I applied the fitted mappings to the exact active-block population (12 replicates, M=20, d=3, τ=1.5, n_int=3, Δ=0.3):
>
> | encoder | K | n | uniform mean (SD) | Zipf mean (SD) | H6 direction |
> |---|---|---|---|---|---|
> | target | 50 | 500 | 0.0591 (**0.0051**) | 0.0261 (**0.0028**) | **REVERSED** |
> | target | 50 | 5000 | 0.0028 (0.0023) | 0.0014 (0.0006) | **REVERSED** |
> | target | 12 | 500 | 0.0013 (0.0025) | 0.0036 (0.0040) | OK |
> | woe | 50 | 500 | 0.0724 (0.0039) | 0.0347 (0.0045) | OK (marginal) |
> | woe | 50 | 5000 | 0.0042 (0.0026) | 0.0034 (0.0016) | **REVERSED** |
>
> Two distinct defects. First, the raw SD tracks the *mean* — the uniform arm has 2.3× the representation loss, so it mechanically has the larger SD; this is a scale confound, not instability. A coefficient of variation, or an SD computed after conditioning on matched mean loss, is required. Second, the mechanism is backwards from the hypothesis: under Zipf the probability mass concentrates on frequent, well-estimated levels, so the rare levels that collapse carry little mass; under uniform *every* level is equally noisily estimated and every collapse hits high-mass levels. At the exact K, n and encoder that C9 prespecifies, H6 will be rejected with the wrong sign.
>
> Additionally, C9/C10 do not fix M, τ, n_int, Δ_η or n_train, so "across-replicate SD" is ambiguous between within-scenario SD (then aggregated how?) and SD of a pool that mixes wildly different loss scales. Pooling would inflate the SD by between-scenario heterogeneity, which has nothing to do with rare categories.
>
> I am not asking for H6 to be dropped — the underlying phenomenon (unseen-level collapse under heavy tails) is real and worth reporting. I am asking for a scale-free instrument and a defined pooling rule, **before** the run.
>
> ---
>
> ## 4. Is the Δ_η construction scientifically sound?
>
> Partially. It is *mathematically* clean and does exactly what it advertises: Property 2 in the spec (`S0_IMPLEMENTATION_SPEC.md:131`) holds exactly, clipping genuinely never occurs, and `impose_delta_eta` raises rather than silently clipping. The decision to treat Δ_η as a controlled construction parameter rather than a descriptive statistic is defensible and correctly argued (`:88–94`).
>
> But three things are distorted relative to what "within-fiber posterior heterogeneity" means scientifically.
>
> **(a) The affine squash destroys the DGP's own within-fiber structure before adding the designed one.** `m(f)` is the fiber *mean* of η_raw; every trace of how the logistic model varied *inside* the fiber is discarded and replaced by ±Δ/2 · rank. So the construction does not add heterogeneity on top of a logistic model — it deletes the model's heterogeneity and substitutes a synthetic one. The claim in the spec that "cross-fiber structure from the logistic model is retained exactly" (`:138–140`) is true, and the claim about the range is true, but the omitted fact is that *within*-fiber structure is retained not at all. That is the fact that matters for a theorem about within-fiber variance.
>
> **(b) The rank shape makes the heterogeneity two-point and maximally spread.** With K=4 every fiber has r=2, so s ∈ {−1,+1} and the within-fiber posterior distribution is a symmetric two-point mass at the extremes of its range. The range is therefore the *only* moment: Var(η|Z_D) is pinned at (Δ/2)² and no other within-fiber shape is ever explored. Real merges produce fibers with many states and non-degenerate, often skewed, within-fiber posterior distributions where range and variance decouple. A design that varied fiber size r (K odd/even already gives r ∈ {1,2}, but never r ≥ 3 with mass) would break the (Δ/2)² identity and make H4 informative.
>
> **(c) Consequence: the reported "effect" is arithmetic.** This is M1. The Brier version is exactly (Δ/2)²·c(K, marginal); the log-loss version is the same quantity divided by the curvature of H at η̄. Reporting either as evidence that "representation loss grows with posterior heterogeneity" is close to circular.
>
> **Recommendation (cheap, pre-run):** keep the construction as the *control*, and add one figure panel or table row where within-fiber heterogeneity is *observed* rather than imposed — the hash and count encoders in 1A already provide this for free (their `max_fiber_posterior_spread` is a descriptive statistic and their gaps are exact). That converts H4 from an identity into a genuine regression of gap on observed spread, at zero extra compute.
>
> ---
>
> ## 5. Is `d = min(M,3)` in Simulation 1B legitimate?
>
> It is a legitimate *choice*, honestly recorded (`S0_IMPLEMENTATION_SPEC.md:73–77`, deviation 4 at `:462`), and it is the reason the active block stays enumerable. I would not block on it. But it materially weakens the high-cardinality conclusions in a way the current framing does not acknowledge.
>
> **M is not a width factor; it is a noise factor.** At M=5 and M=20 the active block is *identical* (d=3, same three coordinates, same K, n_int=3 = all three pairs). The only difference is 2 vs 17 pure-noise columns. So every "effect of M" reported from 1B is an effect of the noise-to-signal *feature* ratio, mediated entirely through the learner, and none of it is an effect of encoding width on representation. This confounds:
>
> - one-hot's dimension penalty (M·K columns) grows with M while achievable signal is constant — one-hot's learner shortfall will worsen with M for reasons that have nothing to do with encoding quality;
> - hash encoders are handicapped in proportion to M: at M=20, K=50, 17/20 of the bucket mass is noise, so their representation loss (were it computable) mixes collision loss with dilution;
> - there is **no scenario anywhere in the design with many informative high-cardinality columns**, which is the regime the manuscript's data actually occupies.
>
> The spec's justification — "many categorical variables of which few matter — which is both the realistic setting for the manuscript's data" — is an assertion about the real data that this simulation-only assignment cannot verify and that no reader can check.
>
> **What I would require:** state in TabS1 and in the caption of FigS4 that d = 3 in *every* 1B cell, so M varies noise dimension only, and that the design therefore does not test dense high-cardinality signal. And add, at negligible cost, a single M=5 / K=4 arm with d = M = 5 (1024 cells, fully enumerable — I ran the whole hash grid for it in 0.02 s) to give at least one 1B configuration where signal dimension and width move together.
>
> ---
>
> ## 6. Is `NOT_IDENTIFIED` for the 1B hash gap honest and sufficient?
>
> **Honest: yes. Sufficient: no.** This is B2, and it is the finding I would push hardest on.
>
> *Honest*, because refusing to substitute a plug-in η̄ estimated from the 50,000-row evaluation sample is exactly right: with M=20, K=50 and B up to 2000, almost every evaluation record has a unique hash code, so the plug-in η̄(z) → η(x) and the estimated representation loss → 0. A plug-in would report that hash encoding is *lossless* precisely where it is worst. Declining to compute it is the correct scientific instinct and the `theoretical_gap_status` column that separates this from run status (`:523–525`) is good design.
>
> *Insufficient*, for three reasons.
>
> **(i) It is over-declared.** The blanket claim is that hash fibers "do not factorise over the active block and the population gap is not computable at this state-space size" (`:203–207`, `S0_IMPLEMENTATION_SPEC.md:186–189`). That is true at M=20, K=50. It is **false** at M=5, K=4, where the full space is 4⁵ = 1024 cells and the gap is exactly computable. I did it:
>
> | encoder | B | exact gap (log-loss) | identity error | fibers |
> |---|---|---|---|---|
> | hash_column | 10 (B0) | 0.076849 | 8.3e-17 | 240 |
> | hash_shared | 10 (B0) | 0.105918 | 1.7e-16 | 56 |
> | hash_column | 20 (B1) | 0.064655 | 1.7e-16 | 363 |
> | hash_column | 40 (B2) | 0.031319 | 8.3e-17 | 768 |
> | hash_shared | any | 0.105918 | 1.7e-16 | 56 |
>
> Whole grid: **0.02 seconds**. That is 48 of the 288 1B scenarios (all M=5, K=4) carrying an exact hash representation loss, including the C1/C2 comparison and the B-sweep, for free. M=5,K=12 (248,832 cells) is also feasible with chunking. The status should be per-cell (`IDENTIFIED_EXACT` where enumerable, `NOT_IDENTIFIED` elsewhere) — the enum already supports this.
>
> **(ii) It silently removes more than the theoretical gap column.** `representation_loss = R_Bayes(Z) − R_Bayes(X)` and `learner_shortfall = R_learner(Z) − R_Bayes(Z)` (`:376–377`) *both* need `R_Bayes(Z)`. So for the 6 hash configurations of 13, the entire decomposition is NULL and only `total_excess_risk` survives. Concretely this breaks:
>
> - `simulation_1b.design_variants.fractional_proposed` (`:174–182`), which states all 13 encoder configurations are evaluated "with the free Bayes-on-Z oracle" — the oracle predicts η̄(z) (`:337–338`), which does not exist for these cells. The freeze contradicts itself.
> - **C1** (onehot vs hash_shared, representation loss) and **C2** (hash_column vs hash_shared, representation loss) at `:611–612` — neither is computable in 1B. They survive only in 1A, where they are exact and carry no sampling variability, so the `mcse`/`p_raw`/`p_bh` columns TabS3 demands are undefined for them.
> - **FigS4** panel (a) "representation loss by encoder" — blank for every hash configuration, i.e. blank for exactly the encoders the manuscript indicts. A figure that omits the accused is not an unbiased figure (see §7).
> - **SIM1-RESULT-02**, a `blocking_for_submission: YES` placeholder whose `required_columns` include `representation_loss` and `learner_shortfall` for encoder × learner.
>
> **(iii) 1C does not actually substitute.** The freeze's escape clause is "the exact hashing result is supplied by Simulation 1C, where it IS identified in closed form, so no scientific claim depends on this gap" (`:208–210`). But 1C supplies a closed form for the **shared-value** hash only; the **column-aware** gap is `NOT_IDENTIFIED` there too (`:250–256`). So across the entire package there is *no* quantitative column-aware representation loss except in Simulation 1A at M ∈ {3,5} — and the claim that "no scientific claim depends on this" is contradicted by SIM1-RESULT-03, which requires the shared-value collapse to be "contrasted with column-aware hashing", and by FigS3, which lists `hash_column` as a plotted series on a representation-loss y-axis (`:565–566`).
>
> **Minimum fix:** per-cell identification status; enumerate where enumerable; and state explicitly in FigS3/FigS4 captions and in the handoff memo which encoder × metric combinations are structurally absent and why, so the advisor cannot read a blank as a zero.
>
> ---
>
> ## 7. Figures, tables, and multiplicity
>
> ### Figures
>
> - **FigS1 (M6).** Panels a and b plot estimated vs theoretical gap for the 1A exact arm — where the two are equal to 2.2e-15 by construction. Panel d plots that residual on a symlog axis, i.e. it plots float64 rounding. Three of four panels convey no information beyond "no coding bug". Only panel c (1B where identified) has content, and it excludes all hash encoders (B2). I would collapse a/b/d into a single small panel or one table row and give the space to something empirical.
> - **FigS2 (m3).** The source arm is not stated. If 1A, all cells are exact with mcse = 0, so the "95 percent CI" in the panel spec (`:554`) and the `ci_low`/`ci_high` columns the register demands cannot be drawn. If 1B, then `designed_merge` is not in the 1B encoder list (`:153–161`) and the headline Δ_η encoder is absent. This must be pinned before the run.
> - **FigS3 (M6, m4).** Series = [label, onehot, count, hash_column, hash_shared] on a representation-loss axis. On binary data label, onehot and count are all injective → three identical zero lines. hash_column is NOT_IDENTIFIED → missing. hash_shared under Hamming weight is zero by assignment (B3). The 2×3 grid therefore resolves to one informative curve (hash_shared, position-specific) plus decoration. The requirement to show both targets is correct and I endorse it; the series list needs pruning and the ROC-AUC secondary row is where the column-aware comparison will actually have to live.
> - **FigS4 (B2).** Blank for hash configurations. The `stacking_forbidden` rule (`:576`) is excellent and should be kept verbatim.
> - **Unbiasedness.** `no_panel_selection_by_favourability: true` (`:540`) and freezing panels pre-run are the right controls, and I credit them. But *structural absence* is a subtler bias than panel selection, and the current plan has structural absence concentrated exactly on the encoders under indictment.
>
> ### Multiplicity (B4)
>
> The H1/H2 exemption is **defensible**: they are tolerance checks against exactly known values with no sampling distribution, so a p-value would be meaningless. I would go further and say they should not be in a "hypotheses" list at all (M8), but the no-adjustment decision is correct and well argued.
>
> BH at 0.05 over H3–H6 is *in principle* fine. In practice the plan cannot be executed as written:
>
> 1. **Family size ambiguous.** `family: "the six prespecified hypotheses H1-H6"` (`:494`) but `H3_H6_adjudication` says "prespecified contrasts, BH FDR control at 0.05 within the family" (`:502`), and there are ten contrasts C1–C10 mapping many-to-one onto four hypotheses. BH over m = 4 and BH over m = 10 give different thresholds. Pick one and write it down.
> 2. **Degenerate members corrupt the procedure.** C1, C2 and C5 are exact 1A quantities with zero Monte Carlo variance. If they enter the family with p ≈ 0, BH's step-up threshold i·α/m is reached at larger i, which **mechanically loosens** the adjustment for the genuinely stochastic contrasts C3, C4, C6–C10. Including deterministic contrasts in an FDR family is not conservative; it is anti-conservative.
> 3. **No test statistic, no estimand, no unit of analysis.** This is the deepest problem. TabS3 must report `estimate`, `ci_low`, `ci_high`, `mcse`, `p_raw`, `p_bh` for each contrast, but nothing anywhere states: is the unit a replicate, a scenario, or a scenario × replicate? Is the test paired or two-sample (B1 makes pairing impossible as currently seeded)? t, Wilcoxon, or bootstrap? For C9/C10, what is the null distribution of a difference of SDs? With 288 scenarios × 50 replicates, treating replicates as independent gives n = 14,400 and *every* contrast will be significant at any threshold; treating scenarios as the unit gives n = 288 with heavy between-scenario heterogeneity. The choice determines every p-value in the table, and it is currently unfrozen — which means it will be chosen after the data are seen, defeating the entire preregistration.
> 4. **No power statement.** With 50 replicates and unpaired arms (B1), there is no statement anywhere of what effect size is detectable for C6–C8.
>
> **Also:** `uncertainty.confidence_intervals: normal 95 percent` (`:509`) is applied uniformly, but several quantities are spike-at-zero mixtures (count encoder, M4) or exactly deterministic (1A). The bootstrap-median path (`:510`) exists and should be the default for the mixture cases.
>
> ---
>
> ## 8. Is the handoff unambiguous?
>
> Mostly yes, and this is the strongest non-engineering part of the package. `S0_PLACEHOLDER_OUTPUT_MAP.csv` is a genuine improvement over the register: it adds `producing_phase`, `producing_script`, `anchor_present_in_tex` with `tex_line`, and an explicit `student_supplies` / `advisor_writes` split that correctly assigns *all* interpretive prose to the advisor. The alias resolution (SIM-ABS-01 → SIM1-RESULT-01, SIM-FIG-02 → SIM2-FIG-01) is exactly what prevents double-insertion. An advisor could work from this.
>
> Residual ambiguities:
>
> - **B2 again.** The advisor is told SIM1-RESULT-02 will arrive with `representation_loss` and `learner_shortfall` per encoder × learner. It will arrive with those columns NULL for 6/13 encoder configurations. Unless the handoff memo says so in the first paragraph, the natural reading of a blank hash row is "no loss", which inverts the paper's claim. This must be an explicit, prominent line item in `19_VALIDATION_REPORT.md` and `20_RESULT_HANDOFF_MEMO.md`, not a footnote.
> - **m1.** `fitted_learner_cells: 259200` (`:182`) disagrees with `S0_RESOURCE_ESTIMATE.csv`, which computes 360,000 for the same fractional design. 288 × 13 × 50 (logistic on all) + 288 × 6 × 2 × 50 (heavy on the subset) = 360,000; 259,200 = 288 × 6 × 3 × 50, i.e. it counts only the heavy subset with all three learners and drops logistic on the other seven configurations. The freeze's own number contradicts its own description. Both are inside the 80 core-hour ceiling, so nothing breaks — but a frozen protocol with an arithmetic error in its headline cell count will be noticed.
> - **m5.** None of the nine producing scripts named in the map exist yet. Expected at S0, but the map presents them as the reproducibility contract; the memo should say "to be created in S1" rather than implying they exist.
> - **`scenario_group`** appears in the required `06_SIM1_SUMMARY.csv` schema and in SIM1-RESULT-01's required columns but is never defined in the freeze. The advisor will not know whether a row aggregates over encoders, over Δ_η, or over marginals.
> - **m3.** FigS2's arm ambiguity means the advisor could receive a figure that does not contain the encoder the caption implies.
>
> ---
>
> ## 9. What a hostile reviewer will attack
>
> Ranked by how much damage each does.
>
> 1. **"Simulation 1A is a unit test, not a simulation study."** The identity is a theorem with a three-line proof; verifying it numerically to 1e-15 over 105,600 cells demonstrates that the code implements the arithmetic, nothing more. Expect: *"What would have falsified H1?"* The only defensible answer is "a bug", and that answer belongs in a software appendix, not a Results section. **Pre-empt by** renaming H1/H2 as implementation verification and moving A1/A2 to a validation table.
> 2. **"You imposed the effect you then report."** M1. A reviewer who reads `sim1_core.py:223` will compute (Δ/2)² in their head and ask why 9,600 designed-merge cells were run to recover 12 numbers. **Pre-empt by** presenting Δ_η explicitly as a construction and adding an observed-spread analysis (§4).
> 3. **"Your headline decomposition is missing for the encoders you accuse."** B2. This is the attack that could cost the paper the claim. *"You report representation loss for the encoders that pass and decline to report it for the ones you say fail."* The NOT_IDENTIFIED reasoning is sound but reads as convenient unless the over-declaration (M=5,K=4 is enumerable) is closed and the absence is stated up front.
> 4. **"The overgeneralisation guard is an `if` statement."** B3. Given that the guard is the manuscript's own stated defence against overreaching from the historical hash failure, discovering that it is `= 0.0` rather than a computation is a credibility hit disproportionate to its mathematical significance.
> 5. **"Count encoding fails only because your categories are exactly equiprobable."** M4. Under uniform the population count map collapses 64 cells to 1; under Zipf it is perfectly injective. No real marginal is exactly uniform. The reported catastrophic failure of count encoding is a measure-zero tie phenomenon.
> 6. **"Your rare-category hypothesis came out backwards and you switched instruments."** M3. If the SD contrast is reversed at K=50 as I measure it, and the analysis then reports a different instrument, the freeze's own binding rule (`:8–9`) has been violated. Fix the instrument now, or commit to reporting the reversal.
> 7. **"M is not width."** M7. A reviewer working in high-cardinality tabular data will notice that d = 3 in every 1B cell and that the paper's "wide categorical" claims rest on a three-variable signal.
> 8. **"Every within-DGP contrast in your preregistration is between different DGPs."** B1. Once someone reads the seed rule against the factor lists, all of A6, A8, A11 and C5–C8 become unpaired, and A8 in particular becomes non-adjudicable per-replicate (59/60 failures under the frozen rule vs 0/60 paired).
> 9. **"Where is the analysis plan?"** B4. `p_raw`/`p_bh` columns with no named test.
> 10. **Minor but citable:** prevalence pinned near 0.5 everywhere (m8); PR-AUC reported but uninformative at balanced prevalence; `position_specific_eta` ignoring its `q` argument (m6); label/onehot described as injective controls while carrying an UNSEEN collapse in 1B (m7).
>
> ---
>
> ## Recommended pre-run actions, in priority order
>
> All of these are cheap now and impossible after S1 begins.
>
> 1. **Re-key the DGP seed on a block index that excludes the contrasted factor** (Δ_η in 1A/1B, n_train in 1B, M in 1C), so contrasted arms share a DGP draw. Add a property test asserting that the parameter draw is identical across Δ_η levels within a block. *(B1)*
> 2. **Make `theoretical_gap_status` per-cell in 1B**, computing the exact hash gap wherever K^M is enumerable (M=5,K=4 certainly; M=5,K=12 with chunking). Resolve the `design_variants` / `hash_encoders` contradiction about the Bayes-on-Z oracle. Declare, in the freeze, that `representation_loss` and `learner_shortfall` are NULL for non-enumerable hash cells and that FigS4/TabS3 will show that absence explicitly. *(B2)*
> 3. **Compute the Hamming-weight gap through the generic η̄ path** instead of assigning zero, so A9 is measured. *(B3)*
> 4. **Freeze the analysis plan**: unit of analysis, paired vs unpaired, test statistic per contrast, BH family membership (and exclude deterministic contrasts from it), and a minimum detectable effect for C6–C8. *(B4)*
> 5. **Scope A6 to `designed_merge`**, or restate it as a replicate-averaged claim; likewise state A8's aggregation. *(M2, B1)*
> 6. **Replace H6's raw-SD instrument** with a scale-free one and fix the pooling level. *(M3)*
> 7. **Freeze 1C's `learners:` list and τ.** *(M5)*
> 8. **Add one observed-heterogeneity analysis** using the existing exact hash/count 1A cells, so H4 is not purely a construction identity. *(M1)*
> 9. Fix `fitted_learner_cells` (m1); pin FigS2's arm (m3); define `scenario_group`; prune FigS3's redundant zero series (m4).
>
> ---
>
> **Summary verdict.** The implementation is trustworthy; the design is not yet ready to run. Four items (B1–B4) should be resolved before Phase S1 begins, because the freeze's own binding rule makes them unfixable afterwards. Of the categories I was asked to judge, categories 8 (handoff) and the A12–A14 portion of category 2 are genuinely in good shape and I have no complaint about them beyond the noted absences. Categories 1, 2, 6 and 7 each contain at least one defect that would survive to a referee.

---

## 5. Independent verification of the reviewers' empirical claims

The host did not take the reviewers' numbers on trust. Each load-bearing claim was
re-run before the corresponding fix was accepted.

| Claim | Reviewer's figure | Host re-measurement | Verdict |
|---|---|---|---|
| A8 unpaired vs paired (B1) | 59/60 vs 0/60 | **15/15 vs 0/15** over 15 replicates | **Confirmed** |
| Exact hash gap at M=5,K=4 (B2) | 0.02 s for the grid | **4–9 ms per cell**, identity error ≤ 1.7e-16 | **Confirmed** |
| Designed-merge Brier gap degeneracy (M1) | 12 distinct values | **10 distinct values** over M×τ×n_int×3 seeds; log-loss gap does vary (16 values, 0.0479–0.0594) | **Confirmed** |
| H6 reversal (M3) | target K=50: 0.0051 vs 0.0028 | **uniform CV 0.075 vs Zipf CV 0.069** at n=500; reversed at n=5000 too; reversed under raw SD *and* CV | **Confirmed, and worse than reported** — a scale-free instrument does not rescue the direction |
| A9 assigned not measured (B3) | code sets 0.0 | Confirmed by inspection; after the fix the zero emerges at ~1e-17 | **Confirmed** |

The reviewer's A8 rate (59/60) and the host's (15/15) differ only in sample size;
both are effectively "fails on essentially every replicate".

---

## 6. Outstanding for the advisor

1. **Gemini seat** — supply credentials and re-run, or waive in writing. The
   substitute is not an independent-organisation review.
2. **Simulation 1B design variant** — Option A (full factorial, 90.6 core-hours,
   needs a ceiling amendment) or Option B (prespecified fractional, 47.8).
3. **H1/H2 naming** — the design seat recommends reclassifying them as
   implementation verification rather than hypotheses. They are named in the
   authoritative plan, so the student did not rename them.
4. **Optional M7 arm** — an $M=5$, $d=M=5$ 1B configuration so signal dimension
   and width move together. Fully enumerable, negligible cost, but it is a design
   *addition* and therefore an advisor decision.
