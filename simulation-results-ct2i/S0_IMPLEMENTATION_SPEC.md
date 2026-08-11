# S0 Implementation Specification — cT2I Simulation 1

**Phase:** S0 (preflight). **Scope:** simulation only.
**Authoritative specification:** `CT2I_STUDENT_SIMULATION_ONLY_EXPERIMENT_PLAN.md`
**Machine-readable freeze:** `simulation-results-ct2i/01_PROTOCOL_FREEZE.yaml`
**Baseline commit:** `7f6b62035951df7d032d0a3eab04cb3c9b0328b4`
**Branch:** `simulation-only/manuscript-revision`

This document resolves every implementation ambiguity listed in step 6 of the
execution prompt. It is the prose companion to the machine-readable freeze; where
the two could be read differently, the YAML governs.

No real dataset, real-data model, image, prediction, or target is read, trained,
regenerated, or modified anywhere in what follows.

---

## 1. Notation and conventions

Binary outcome $Y \in \{0,1\}$, categorical predictor vector
$X = (X_1,\dots,X_M)$, deterministic or sample-fitted encoding $Z = \varphi(X)$,
posterior $\eta(x) = P(Y = 1 \mid X = x)$.

| Convention | Frozen value |
|---|---|
| Logarithm | natural (nats) throughout, matching Stage 2 |
| Brier loss | one-coordinate, $(y - p)^2$ |
| Probability clip | $\varepsilon = 10^{-12}$ |
| Bayes log risk | $R_{\log}(X) = \mathbb{E}[H(\eta(X))]$, $H(q) = -q\ln q - (1-q)\ln(1-q)$ |
| Bayes Brier risk | $R_{\mathrm{bri}}(X) = \mathbb{E}[\eta(X)(1-\eta(X))]$ |
| Encoded risks | same functionals applied to $\bar\eta(z) = \mathbb{E}[\eta(X) \mid Z = z]$ |

The two identities under test:

$$R_{\log}(Z) - R_{\log}(X) = I(Y; X \mid Z), \qquad
  R_{\mathrm{bri}}(Z) - R_{\mathrm{bri}}(X) = \mathbb{E}\big[\operatorname{Var}\{\eta(X) \mid Z\}\big].$$

The second holds because
$\sum_f P(f)\bar\eta(f) = \mathbb{E}[\eta]$, so the Brier difference telescopes to
$\mathbb{E}[\eta^2] - \sum_f P(f)\bar\eta(f)^2$, which is exactly the expected
conditional variance.

**Independent verification paths.** Each right-hand side is computed by code that
does *not* reuse the left-hand side: $I(Y;X\mid Z)$ as a per-cell
Kullback–Leibler sum $\sum_x p(x)\,\mathrm{KL}(\mathrm{Bern}(\eta(x)) \,\|\,
\mathrm{Bern}(\bar\eta(z(x))))$, and $\mathbb{E}[\operatorname{Var}(\eta\mid Z)]$
as a per-fiber weighted variance. A dedicated property test
(`test_identity_paths_are_independent`) permutes the fiber assignment and confirms
the identity still holds while the *value* changes, which rules out the identity
being true by construction.

That alone is not sufficient, as the Codex S0 review correctly pointed out: the
two formulas are structurally separate but both consume the same
`fiber_posteriors` aggregation, so a defect in fiber grouping, masses, or
conditional means could make both sides agree *incorrectly*, and permuting the
partition would not expose it. `reference_gap_report` therefore provides a
second, dependency-free implementation — pure-Python dict grouping and `math`,
no numpy reductions, no `bincount`, no shared helper — and
`test_fast_path_matches_dependency_free_reference` asserts agreement across the
grid. A shared aggregation bug would have to be reproduced independently in both
implementations to survive.

---

## 2. Probability distributions and parameter generation

**Coordinates are independent**, $X_j \sim p_{\mathrm{marg}}$ on $\{0,\dots,K-1\}$:

- `uniform`: $p(k) = 1/K$
- `zipf`: $p(k) \propto (k+1)^{-1.2}$, normalised

Independence is what makes the exact fiber algebra tractable and is stated as an
assumption, not an approximation.

**Active block.** Only the first $d$ coordinates carry signal:

| Component | $d$ | State space enumerated |
|---|---|---|
| 1A | $d = M$ (every coordinate active) | $K^M \le 4^5 = 1024$ |
| 1B | $d = \min(M, 3)$ | $K^d \le 50^3 = 125{,}000$ |
| 1C | $d = 5$ named coordinates | $2^5 = 32$ patterns |

Simulation 1A is the exact-theory arm and uses the **full** state space with no
sparsity assumption. Simulation 1B deliberately studies the wide, sparse-signal
regime — many categorical variables of which few matter — which is both the
realistic setting for the manuscript's data and the condition under which the
active block stays exactly enumerable. This is a design decision, recorded here
and in the freeze, not an artefact.

**Parameter draws**, all from `numpy.random.default_rng(seed)` (PCG64):

- main effects $a_j(k) \sim \mathcal{N}(0,1)$, then $p$-centred so
  $\sum_k p(k)a_j(k) = 0$;
- interaction arrays $b_{jl}(k,k') \sim \mathcal{N}(0,1)$, then $p$-double-centred
  via $b \leftarrow b - \mathbf{1}(p^\top b) - (bp)\mathbf{1}^\top + p^\top b p$,
  so both $p$-weighted marginals vanish;
- interaction pairs $P$ = the first `n_int` pairs of the lexicographic enumeration
  of $\{(j,l): j<l,\ j,l \in A\}$ — deterministic given $d$, never randomly chosen;
- linear predictor $g(x) = \tau\big(\sum_{j\in A} a_j(x_j) + \sum_{(j,l)\in P} b_{jl}(x_j,x_l)\big)$,
  $\beta_0 = 0$;
- $\eta_{\mathrm{raw}}(x) = \mathrm{logistic}(g(x))$.

Centring means $\tau$ is a genuine signal-scale knob rather than a confounded
prevalence shift, and $\beta_0 = 0$ keeps marginal prevalence near $0.5$, so
degenerate single-class draws do not arise.

---

## 3. Exact meaning and construction of `Delta_eta`

This was the single largest ambiguity in the plan, which asks for
"within-fiber spread `Delta_eta` in {0, 0.1, 0.3}" and for fibers deliberately
constructed with constant or varying posteriors. Two readings are possible:
`Delta_eta` as a *descriptive statistic* of whatever the logistic model happens to
produce, or as a *controlled construction parameter*. **The frozen reading is the
second**, because only that makes "lossless versus lossy merge" a designed
contrast rather than an observed one.

**Definition.** $\Delta_\eta$ is the maximum within-fiber posterior range of the
designed merge encoder $\varphi_D$ over fibers of positive probability:

$$\Delta_\eta := \max_{f:\ P(f)>0}\ \Big(\max_{x \in f} \eta(x) - \min_{x \in f} \eta(x)\Big).$$

**Designed merge map.** $\varphi_D$ merges coordinate 0 pairwise,
$k \mapsto \lfloor k/2 \rfloor$, leaving all other coordinates intact. With $K=4$
every fiber holds exactly two cells; with $K=3$ the fibers are $\{0,1\}$ and
$\{2\}$. Fibers of size $\ge 2$ with positive mass therefore always exist, and the
implementation asserts this.

**Construction.** For each fiber $f$ let $m(f)$ be the $p$-weighted mean of
$\eta_{\mathrm{raw}}$ over $f$, and let $s(x) \in [-1,1]$ be the *rank shape*:
cells of $f$ ordered by $(\eta_{\mathrm{raw}}, \text{cell})$ ascending receive
$s = -1 + 2i/(r-1)$ for $i = 0,\dots,r-1$; singleton fibers receive $s = 0$. Then

$$\boxed{\ \eta(x) = 0.20 + 0.60\, m(f(x)) + \tfrac{\Delta_\eta}{2}\, s(x)\ }$$

**Properties, all exact and asserted in code or tests:**

1. $\eta \in [0.05, 0.95]$ always, since $m \in [0,1]$ and $|\Delta_\eta/2| \le 0.15$.
   Clipping therefore *never* occurs; `impose_delta_eta` raises rather than
   silently clipping if this is ever violated.
2. Every fiber with $r \ge 2$ has range exactly $\frac{\Delta_\eta}{2}(1 - (-1)) = \Delta_\eta$.
   Verified by `test_delta_eta_is_exactly_the_within_fiber_range` to $10^{-12}$.
3. $\Delta_\eta = 0 \Rightarrow \eta$ constant on every $\varphi_D$ fiber, so
   $\varphi_D$ is a **lossless non-injective** encoder — zero gap.
4. $\Delta_\eta > 0 \Rightarrow$ strictly positive gap.
5. Injective encoders have zero gap at every $\Delta_\eta$.

**What the construction is, and what it is not.** The affine squash
$m \mapsto 0.20 + 0.60m$ is order-preserving, so the *ordering* of fiber means
from the logistic model is retained exactly; it exists only to guarantee
property 1. But the construction must not be described as a faithful
logistic-main-effects-and-interactions DGP at the cell level, and the following
two points are stated explicitly because an earlier draft overstated them:

- $\eta$ is **not** the logistic model evaluated cell by cell. Cell-level
  posterior magnitudes are replaced by *fiber mean plus rank score*; the
  logistic model survives as the driver of the between-fiber structure, not the
  within-fiber structure.
- The rank shape is symmetric about zero in the *unweighted* sense, so under a
  Zipf marginal it is **not** probability-centred, and the post-squash fiber mean
  is generally **not** exactly $0.20 + 0.60\,m(f)$. Preservation of the fiber
  mean is not claimed and is not needed; what is claimed, and what is asserted
  to $10^{-12}$ by test, is that the within-fiber *range* equals $\Delta_\eta$
  exactly — because that range **is** the definition of $\Delta_\eta$.

This is therefore a deliberately synthetic, controlled-loss DGP, which is what
the theorem check requires. Manuscript wording must say so rather than describing
it as a generic logistic DGP.
*(Both points raised by the Codex S0 review, MAJOR.)*

**Closed-form corroboration.** With $K$ even and a uniform marginal, every fiber
holds two equiprobable cells, so
$\mathbb{E}[\operatorname{Var}(\eta \mid Z)] = (\Delta_\eta/2)^2$ exactly. The
measured Brier gap at $\Delta_\eta = 0.3$ is $0.0225 = (0.15)^2$, matching to
$10^{-12}$ (`test_brier_gap_matches_closed_form_for_paired_fibers`). This is an
independent check on the whole construction.

---

## 4. Exact Bayes-risk calculations

For a deterministic encoder, fibers are obtained by grouping enumerated cells on
their integer code; float-valued codes (the count encoder) are quantised to
exact integers at $10^{12}$ before grouping, so fiber identity is never decided by
floating-point equality.

Per fiber: $P(f) = \sum_{x \in f} p(x)$ and
$\bar\eta(f) = \sum_{x\in f} p(x)\eta(x) / P(f)$. Then

$$R_{\log}(Z) = \sum_f P(f) H(\bar\eta(f)), \qquad
  R_{\mathrm{bri}}(Z) = \sum_f P(f)\bar\eta(f)(1-\bar\eta(f)).$$

All sums use `np.bincount` with explicit `minlength`, so empty fibers cannot
silently shift indices.

**Measured accuracy at S0.** Across the full property-test grid the largest
absolute identity error was $2.2\times10^{-15}$ — roughly five orders of
magnitude inside the frozen $10^{-10}$ tolerance.

---

## 5. Monte Carlo integration accuracy

The design deliberately minimises reliance on Monte Carlo integration.

| Arm | Population quantity | Method |
|---|---|---|
| 1A, all encoders | exact | full enumeration of $K^M \le 1024$ cells |
| 1C, shared-value hash | exact | closed form (§6) |
| 1B, coordinate-wise encoders | exact | enumeration of the active block, $K^d \le 125{,}000$ |
| 1B, hash encoders | **not identified** | reported as `NOT_IDENTIFIED`, gap column NULL |

**Why the hash encoders are not identified in 1B.** A hashed record's
bucket-count vector sums contributions from all $M$ coordinates, including the
inactive ones, so its fibers do not factorise over the active block and the
population gap is not computable at this state-space size. Rather than substitute
a noisy plug-in estimate and present it as a theoretical value, the theoretical
gap is recorded as NULL with `theoretical_gap_status = NOT_IDENTIFIED`; empirical
risks, AUCs, collision counts and occupied-bucket counts are still reported. **No
scientific claim depends on this**, because the exact hashing result is supplied by
Simulation 1C, where it is available in closed form.

**Finite-sample risk estimation is Rao-Blackwellised.** Because $\eta(x_i)$ is
known exactly for every evaluation record, the conditional expected loss replaces
the realised loss:

$$\mathbb{E}[\text{log loss} \mid x] = -\eta\ln\hat p - (1-\eta)\ln(1-\hat p),
\qquad
\mathbb{E}[\text{Brier} \mid x] = \eta(1-\eta) + (\eta - \hat p)^2.$$

Substituting $\hat p = \eta$, $\hat p = \bar\eta(z)$, and $\hat p = $ the fitted
learner's prediction makes

$$\text{total excess risk} = \text{representation loss} + \text{learner shortfall}$$

hold **exactly** on the evaluation sample; `decompose()` asserts the residual is
below $10^{-9}$ and raises otherwise. Realised labels are still drawn and are used
for ROC-AUC and PR-AUC, which require actual outcomes. Evaluation sample size is
$n_{\text{eval}} = 50{,}000$; the within-replicate integration MCSE is reported
per cell alongside the across-replicate MCSE.

---

## 6. Simulation 1C: exact treatment of the shared-value hash

For binary records the shared-value hash sees only the bare tokens `"0"` and
`"1"`. A record with Hamming weight $w$ contributes $w$ to bucket $b_1$ and
$M-w$ to bucket $b_0$. Therefore

- $b_0 \ne b_1$: $Z$ is a **bijection of $w$**, giving exactly $M+1$ reachable
  encodings — the Stage 1 proposition;
- $b_0 = b_1$: $Z[b_0] = M$ for every record, giving exactly $1$.

Both are verified against brute-force enumeration of all $2^M$ records for
$M \le 14$, and collapsing widths are located by scan rather than assumed absent.

Because the encoder's fibers are indexed by $w$, every population quantity reduces
to a sum over $w = 0,\dots,M$. The conditional law of the 5 signal coordinates
given $w$ is hypergeometric — the number active among the first 5 satisfies
$a \mid w \sim \mathrm{Hypergeom}(M, w, 5)$, and given $a$ the active subset is
uniform over the $\binom{5}{a}$ patterns — so $\bar\eta(w)$, $\operatorname{Var}(\eta\mid w)$,
both Bayes risks, $I(Y;X\mid Z)$ and $\mathbb{E}[\operatorname{Var}(\eta\mid Z)]$
are all closed-form. The whole headline hashing result is therefore **exact, not
Monte Carlo**.

**Overgeneralisation guard.** Under the Hamming-weight target $\eta$ is itself a
function of $w$, so the gap is **exactly zero**: shared-value hashing is adequate
there. This is measured, not asserted, at every $M \in \{10,50,200,1000\}$, and it
is what prevents the manuscript from overgeneralising the historical failure into
a claim about feature hashing in general.

**Column-aware hashing** admits no such reduction, so its population gap is
`NOT_IDENTIFIED`. What *is* established exactly for it is the absence of the
deterministic Hamming-weight collapse: its reachable-encoding count, its
injectivity on the active block, its occupied buckets and its collision count.

---

## 7. Hash functions, signed/unsigned convention, bucket widths

| Item | Frozen value |
|---|---|
| Hash | `blake2b`, keyed with an 8-byte little-endian seed, 8-byte digest, little-endian int, `mod B` |
| Seed | `20260810` (retained verbatim from the baseline) |
| Sign convention | **unsigned counting**, both encoders |
| Column-aware token | `f"{len(col)}:{col}={val}"` |
| Shared-value token | the bare `val` |
| Bucket widths | $B = \max(2, \mathrm{round}(c \cdot K_{\mathrm{tot}}))$, $c \in \{0.5, 1, 2\}$, $K_{\mathrm{tot}} = M \cdot K$ |

Python's built-in `hash()` is salted per process and is never used.

**Why unsigned.** Signs are deliberately disabled so the *only* difference between
column-aware and shared-value hashing is the presence of column identity in the
token. This isolates the mechanism the manuscript attributes the collapse to; a
signed variant would confound sign cancellation with column identity.

**Why the token is length-prefixed.** Without the prefix, a column named `a` with
value `b=c` and a column named `a=b` with value `c` produce the same token. The
prefix makes the encoding unambiguous.

**Recorded deviation.** The baseline repository fixes $B$ by a cardinality
staircase (16/32/64/`min(M,1024)`) because the real-data benchmark needs one
value. The simulation must *sweep* $B$, so the staircase is overridden by the
factor rule above. The hash function, seed, token construction and unsigned
counting are unchanged, and a property test asserts the simulation encoder is
**byte-identical** to the baseline at matched $B$.

**Collisions are measured, never assumed absent.** $B \ge$ the number of tokens
does not imply zero collisions: at $M=50$, $B=100$ there are 100 tokens but only
63 occupied buckets and 37 collisions. `collision_count`, `occupied_buckets` and
`reachable_encodings` are recorded for every hash cell.

---

## 8. Smoothing constants and unseen-level handling

All retained verbatim from the baseline commit.

| Encoder | Smoothing | Unseen level at transform |
|---|---|---|
| Target | $\alpha = 20.0$; prior = mean of **fitted** labels only | prior |
| WoE | pseudocount $0.5$ per class, class totals augmented by $0.5 K_c$ so the class-conditional probabilities stay normalised; clip $\pm 5.0$ | $0.0$ (neutral evidence, not the prior) |
| Ordered CatBoost | 4 permutations, $\alpha = 1.0$ | prior |
| Count | — | $0.0$; denominator = number of fitted rows |
| Label | — | reserved index $0$ |
| One-hot | — | dedicated `UNSEEN` column per variable |
| HOMALS | rank $r = 2$ | — |

---

## 9. Out-of-fold supervised encoder construction

- Supervised encoders are fitted **only** on the simulation training sample.
- Training rows receive **out-of-fold** codes; test rows are transformed with the
  mapping fitted on the **full** training sample.
- Folds: `KFold(n_splits=5, shuffle=True, random_state=seed_oof)`.

**Why `KFold` and not `StratifiedKFold`.** Stratified fold assignment depends on
$y$. That would make the no-training-row-self-influence invariant untestable:
flipping a single label would move fold boundaries and legitimately change other
rows' codes, so the test could not distinguish leakage from re-partitioning. With
label-independent folds the invariant is exact and is asserted bitwise. With
$n_{\text{train}} \ge 500$ and $\eta \in [0.05, 0.95]$, single-class folds are
practically impossible; if one ever occurs it is a typed failure, not a silent
degradation.

**Theoretical conditioning.** Target, WoE and ordered CatBoost are sample-fitted,
so their population Bayes-on-$Z$ risk is defined **conditional on the fitted
mapping** $\varphi_S$: representation loss is
$R_{\text{Bayes}}(\varphi_S(X)) - R_{\text{Bayes}}(X)$, evaluated by applying the
fixed fitted mapping to the population. This matches the Stage 2 S1C7 convention.

### 9.1 Finding: own-label leakage through the ordered-CatBoost prior

The baseline `OrderedCatBoostEncoder` keeps a row's own label out of the numerator
sum, but takes `prior` to be the mean of $y$ over **all** fitted rows, the row
included. The row's own label therefore re-enters its own code through the prior,
with magnitude about $\alpha/(n(\text{count}+\alpha))$ — measured at
$\sim 7\times10^{-5}$ for $n = 400$. It is small but systematic, and it violates
the invariant Phase S0 is required to test. The baseline repository's own PC2 test
exercises **only the target encoder**, so this channel was never asserted there.

**Resolution.** The baseline encoder is **not modified** — it produced the frozen
real-data results and this is a simulation-only assignment. Simulation 1B instead
uses `OrderedCatBoostRunningPrior` (`ordered_catboost_sim`), which replaces the
fixed prior with a *running* prior: the mean of $y$ over strictly preceding rows
in the same permutation, falling back to a data-independent constant $0.5$ for the
first row. Self-influence is then exactly zero, which is also what ordered target
statistics prescribe. Two tests pin this: one asserts the baseline channel exists
and is bounded by $1/n$, the other asserts the simulation variant's is exactly
zero. **This is a deviation and is reported to the advisor.**

---

## 10. Fixed learner settings

Frozen, modest, prespecified. Nothing is searched or adapted per scenario.

| Learner | Settings |
|---|---|
| `bayes_z_oracle` | predicts $\bar\eta(z)$; no fitting |
| `logistic` | `StandardScaler` → `LogisticRegression(C=1.0, solver='lbfgs', max_iter=2000)`; L2 by default (the `penalty` argument is deprecated in scikit-learn 1.8 and removed in 1.10, so it is not passed) |
| `lightgbm` | `n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=20, reg_lambda=1.0, n_jobs=1, deterministic=True, force_row_wise=True` |
| `mlp` | `StandardScaler` → `MLPClassifier(hidden_layer_sizes=(64,32), relu, alpha=1e-4, lr_init=1e-3, max_iter=300, early_stopping=True, n_iter_no_change=15, validation_fraction=0.15)` |

### 10.1 Streaming evaluation

The encoded evaluation matrix reaches $50{,}000 \times 2{,}000$ float64 = 763 MB
at the widest cell. Materialising it was both the memory ceiling and the dominant
runtime cost. Phase S1 therefore **streams**: encode a chunk of `EVAL_CHUNK =
10,000` rows, predict, accumulate, discard. Measured peak RSS is 806 MB per
worker, so 8 workers fit comfortably in the 16 GB host. The hash transform is
additionally vectorised (chunked `bincount` rather than a Python row × column
loop), giving a 3× speed-up with byte-identical output, asserted by test.

---

## 11. Uncertainty calculations

| Quantity | Method |
|---|---|
| Across-replicate MCSE | $\mathrm{sd}/\sqrt{R}$, $R = 50$ (1B, 1C) or $100$ (1A) |
| Within-replicate integration MCSE | sd of pointwise contributions $/\sqrt{n_{\text{eval}}}$ |
| Confidence intervals | normal 95%, mean $\pm 1.96\,\mathrm{MCSE}$ |
| Medians | nonparametric percentile bootstrap, $B = 2000$, seed `90210` |

Both MCSE components are reported; they are never combined into a single opaque
error bar. Exact-enumeration cells carry `mcse = 0.0` and `exact_or_mc = "exact"`,
so exact and estimated quantities are never averaged together as if comparable.

---

## 12. Multiplicity and summary rules

- **Family:** the six prespecified hypotheses H1–H6.
- **H1, H2** are tolerance checks against an exactly known theoretical value, not
  significance tests. They are adjudicated by the maximum absolute identity error
  against the frozen $10^{-10}$ tolerance and receive **no** multiplicity
  adjustment. They are settled exactly in 1A and 1C and corroborated in the 1B
  cells where the theoretical gap is identified.
- **H3–H6** use prespecified contrasts with Benjamini–Hochberg FDR control at
  0.05 within the family. Raw and adjusted p-values are both reported.
- The ten principal contrasts (C1–C10) are enumerated in the freeze. **No contrast
  is added after seeing results.**
- H6 (rare-category instability) is measured as the across-replicate standard
  deviation of representation loss for target, WoE and ordered CatBoost,
  contrasted between uniform and Zipf marginals at matched $K$.
- Raw replicate-level outputs are frozen **before** any summary is inspected.
- Failed cells carry a typed status and NULL metrics; no failure is ever stored as
  a valid zero or a chance-level AUC. `theoretical_gap_status` is a *separate*
  column from the run `status`, because a cell may succeed while its population
  gap is unidentified.

---

## 13. Plotting and table plan

Frozen before the run; panels are not chosen for favourability. Full column and
panel lists are in `01_PROTOCOL_FREEZE.yaml` under `figures:` and `tables:`.

**Figures** — vector PDF + editable SVG, matplotlib, 8 pt, colourblind-safe
palette, single column 3.5 in / double 7.2 in:

| Figure | Content | Placeholders |
|---|---|---|
| S1 | estimated vs theoretical log-loss and Brier gaps; residual panel | `SIM1-FIG-01`, `SIM-FIG-01` |
| S2 | representation loss vs within-fiber spread, faceted by marginal | `SIM1-FIG-02` |
| S3 | shared-value vs column-aware hash as $M$ grows; **both** targets, 2 × 3 | `SIM1-FIG-03` |
| S4 | representation loss and learner shortfall by $n_{\text{train}}$ and learner | `SIM1-FIG-04` |
| Sim 2 | three panels: optimism vs $K$ with bound; regret/instability; $K$=72 vs 8 | `SIM2-FIG-01`, `SIM-FIG-02` |

Representation loss and learner shortfall are **never** merged into a single bar.

**Tables** — CSV + LaTeX booktabs: S1 design and factor levels (reflecting the
design actually executed); S2 acceptance summary, one row per criterion A1–A15;
S3 principal contrasts with uncertainty, restricted to C1–C10; Sim 2 criterion /
maximum observed / bound / pass.

---

## 14. Simulation 2

Scientific design **frozen by Stage 2 and not changed**. The task is reproduction
or regeneration only. Validation targets: max absolute honest independent-test
reporting bias $\approx 6.5\times10^{-4}$; max observed/theoretical oracle-bound
ratio $\approx 0.847$; $K{=}72$ minus $K{=}8$ oracle advantage $\approx 0.0049$,
$0.0097$, $0.0292$ at $\sigma = 0.005, 0.01, 0.03$.

If a reproduction differs beyond Monte Carlo tolerance, the simulation is **not**
tuned to match; seeds, conventions, code versions and formula definitions are
investigated and the finding reported as-is.

The authoritative output was produced under numpy 2.4.6; the S0 environment has
numpy 2.4.1. PCG64 streams are stable across these versions, so a bitwise match is
expected — confirming it is a Phase S1 verification step, not an assumption.

---

## 14a. Stated limitations

These bound what the simulations can support. They are recorded here so the
advisor's prose does not overreach, and so a hostile reviewer finds them already
disclosed rather than discovered.

1. **In Simulation 1B, $M$ is a noise-dimension factor, not a width factor.**
   With $d = \min(M,3)$ the active block is *identical* at $M = 5$ and $M = 20$ —
   same three coordinates, same $K$, same interactions. The only difference is 2
   versus 17 pure-noise columns. Every "effect of $M$" reported from 1B is
   therefore an effect of the noise-to-signal *feature ratio*, mediated through
   the learner, and none of it is an effect of encoding width on representation.
   In particular one-hot's dimension penalty grows with $M$ while achievable
   signal stays constant, and hash encoders are diluted in proportion to $M$.
   **No 1B scenario has many informative high-cardinality columns**, which is the
   regime the manuscript's data occupies. This must be stated in the TabS1
   caption and the FigS4 caption. Simulation 1A retains $d = M$, so the exact
   theorem check is unaffected. *(Raised by the S0 design review, MAJOR M7.)*
2. **Column-aware hashing has no identified population gap** in 1C, and only in
   the enumerable cells of 1B ($M = 5$, $K \in \{4,12\}$). Outside those,
   contrasts C1 and C2 are empirical finite-sample comparisons only, and *both*
   `representation_loss` and `learner_shortfall` are NULL because both require
   $R_{\text{Bayes}}(Z)$.
2a. **Label and one-hot are not injective on the 1B population.** Both carry an
   UNSEEN bucket fitted from the training sample, so unseen levels collapse:
   measured representation loss $0.0031$ at $K = 50$, Zipf, $n_{\text{train}} =
   500$. They are exact injective controls in **1A only**; in 1B they are the
   *reference* arm of C1/C4, not a zero-gap control, and H3 is confirmed in 1A
   alone. *(Raised by the S0 design review, MINOR m7.)*
3. **The 1C width trend is an ensemble statement.** The position-specific target
   is re-randomised per seed and centred with an unweighted pattern mean, so
   "loss grows with $M$" is a property of the specified DGP ensemble, not a
   universal monotonic law. It is reported with replicate-level uncertainty.
4. **Marginal prevalence is only approximately $0.5$.** Centring and $\beta_0 = 0$
   set the prevalence of $\eta_{\mathrm{raw}}$, but the rank construction and
   affine squash shift it slightly. This is a description, not a degeneracy: the
   frozen band $[0.05, 0.95]$ keeps every cell well away from the boundary.
5. **$\Delta_\eta$ is engineered on designed-merge fibers**, which exist in 1A but
   not in the 1B encoder list. Monotonicity in $\Delta_\eta$ is a gated criterion
   (A6) only in 1A, and only for the designed merge encoder: measured over the
   1A grid with matched seeds, monotonicity fails for **9.4%** of $\Delta$-triples
   under column-aware hashing and **16.2%** under shared-value hashing. That is
   real mathematics — for encoders other than $\varphi_D$ the conditional
   variance picks up a cross term linear in $\Delta$ that can be negative — not a
   bug. *(Raised by the S0 design review, MAJOR M2.)*
6. **The designed-merge result is a construction identity.** The Brier gap is an
   exact function of $(K, \text{marginal}, \Delta_\eta)$ alone; $M$, $\tau$, the
   interaction count and the seed are analytically inert. H4/A5/C5 on that
   encoder verify the construction, and cannot distinguish "the theorem holds"
   from "we imposed the answer". A companion analysis regresses the exact gap on
   *observed* spread using the 1A hash and count cells, which is the version of
   H4 that can fail. *(MAJOR M1.)*
7. **The count encoder's population behaviour is a knife-edge tie phenomenon.**
   Under a uniform marginal all $K$ levels have exactly equal probability, so the
   population count map collapses the whole space to one fiber; under Zipf it is
   perfectly injective. There is no intermediate regime, and no real marginal is
   exactly uniform. Its finite-sample analogue is an integer-tie mixture with an
   atom at zero (measured mean $0.0056$, SD $0.0110$ at $K=4$, uniform,
   $n = 500$), so bootstrap rather than normal intervals are primary for any
   count-encoder contrast. *(MAJOR M4.)*
8. **Marginal prevalence is near $0.5$ in every cell**, since $\beta_0 = 0$ and
   the affine squash pin it there. There is no class-imbalance factor anywhere,
   so PR-AUC carries little independent information and the "rare category" story
   never interacts with a rare outcome. *(MINOR m8.)*
9. **A7 is brute-force verified only for $M \le 14$.** At the production widths
   $M \in \{50, 200, 1000\}$ the criterion evaluates the same closed form it is
   checking, backed by the Stage 1 proposition. TabS2 must say so. *(MINOR m2.)*

## 15. Deviations from the plan, recorded

1. **Ordered CatBoost variant** (§9.1) — a running-prior variant is used in the
   simulation because the baseline leaks a row's own label through the prior. The
   baseline encoder is left untouched.
2. **Bucket-width rule** (§7) — the baseline cardinality staircase is overridden by
   the swept factor rule, as the plan requires $B$ to be a factor. Output is
   byte-identical at matched $B$.
3. **1B theoretical gap for hash encoders** (§5) — reported as `NOT_IDENTIFIED`
   rather than estimated, with the exact result supplied by 1C instead.
4. **1B active block** (§2) — $d = \min(M,3)$, the wide sparse-signal regime.
   Simulation 1A remains fully general with $d = M$.
5. **`penalty` argument** (§10) — not passed to `LogisticRegression`, as it is
   deprecated in scikit-learn 1.8; L2 is the default and $C$ pins the
   regularisation.
6. **LightGBM installed** — absent from the S0 environment, installed at the
   version pinned in `requirements.lock.txt` (`lightgbm==4.7.0`).

All six are listed again in `S0_PREFLIGHT_REPORT.md` and will be carried into
`19_VALIDATION_REPORT.md`.
