# S1 Authorization and Design Decisions

**Phase:** S1 (full execution). **Scope:** SIMULATION ONLY.
**Frozen protocol:** `01_PROTOCOL_FREEZE.yaml` (unchanged since S0 sign-off).
**Preflight:** `S0_PREFLIGHT_REPORT.md` — status COMPLETE, critical veto count 0.

---

## 1. Authorization

The student authorized Phase S1 and delegated the open decisions to the executing
agent, in their own words:

> 你自己審查後決定，ok就跑
> *("You review it yourself and decide; if it's OK, run it.")*

### Recorded deviation D0 — approval wording

The execution prompt requires this exact statement before S1 may begin:

```
The Stage S0 protocol freeze and resource estimate are approved.
Proceed with Phase S1 without changing the frozen design.
```

The approval actually given was equivalent in intent but **not verbatim**, and it
additionally delegated the design-variant choice rather than simply approving a
pre-selected one. The intent was unambiguous, so execution proceeded. This is
recorded here and carried into `19_VALIDATION_REPORT.md` so the advisor can see
exactly what authority the run was carried out under, rather than discovering it
implicitly.

---

## 2. Decision 1 — Simulation 1B design variant: **Option B (fractional)**

**Chosen:** the prespecified fractional variant, 360,000 fitted-learner cells,
projected **47.77 CPU core-hours** total.

**Rejected:** the full factorial, projected **90.55 core-hours**.

### Why this is not a preference but an authority question

The execution prompt states the resource limits as:

> Unless the advisor provides a written amendment:
> `CPU core-hours: 80 maximum`

The ceiling belongs to the **advisor**. Option A at 90.55 core-hours exceeds it
and would require a written advisor amendment. No such amendment exists, and
neither the student nor the executing agent can grant one. Option B fits inside
the existing ceiling.

So under the authority actually in force, Option B is not merely the cautious
choice — it is the only lawful one. Choosing Option A would have meant a run
carried out in breach of a stated resource limit on the strength of a delegation
that could not confer that power.

### What Option B does and does not give up

Retained at full strength:

- all **288 DGP scenarios** — no factor level dropped anywhere;
- all **13 encoder configurations**, each evaluated with the Bayes-on-$Z$ oracle
  and logistic regression;
- all **six central contrasts** named in the plan: injective vs non-injective;
  $\Delta_\eta = 0$ vs positive; small vs large training sample; low vs high
  cardinality; uniform vs rare-category marginal; additive vs interactive target.

Reduced: the two expensive learners (LightGBM, small MLP) run on a fixed
representative encoder subset spanning every encoder family, at one bucket width,
rather than on all 13 configurations at all three widths.

This reduction was **prespecified at S0, before any result was seen**, exactly as
the plan permits ("A fractional factorial design may be proposed only before the
full run and must preserve all central contrasts").

---

## 3. Decision 2 — the additional $M=5$, $d=M=5$ arm: **not added**

Two independent provider organisations (Gemini, and the stand-in design seat)
each ranked the $d = \min(M,3)$ restriction as the study's most significant
residual weakness, and the executing agent had itself recommended adding an
$M = 5$, $d = M = 5$ arm so that signal dimension and feature width move together.

**It is nevertheless not added.** Three reasons, in order of weight:

1. **The approval's own terms.** The authorization template reads "Proceed with
   Phase S1 *without changing the frozen design*." Adding a factor level is a
   design change. Interpreting a delegated decision as licence to expand the
   design would read the delegation more broadly than it was written.
2. **Nothing reviewed would be what ran.** All three council seats signed off on
   the design as frozen. Adding an arm afterwards means executing a configuration
   no reviewer assessed in its final form — which defeats the purpose of having
   held the review before the run.
3. **Nothing is lost by waiting.** The arm is independent of everything else and
   fully enumerable (1024 cells, negligible cost). It can be added later as a
   supplementary arm on the advisor's instruction, with no rerun of anything else
   required.

The recommendation is therefore carried forward to `20_RESULT_HANDOFF_MEMO.md`
for the advisor, not silently actioned.

---

## 4. Standing constraints for this run

Unchanged from S0 and re-asserted here:

- no real dataset, real-data model, image, prediction, or target is read,
  trained, regenerated, or modified;
- the manuscripts, the supplement, the historical repository, and the Stage 2
  authoritative files are read-only;
- GPU hours: **0**;
- no criterion, tolerance, factor, or hypothesis is changed after results are
  observed;
- raw replicate-level outputs are frozen **before** any aggregate is inspected;
- every reported number and figure is generated by script;
- failed cells carry a typed status and NULL metrics.

---

## 5. Execution order

Per the plan's recommended order, with one engineering addition: the cheap exact
arms run **first** and their pipeline is validated end to end before the
~42 core-hour finite-sample arm is committed.

1. Reverify input hashes and the frozen protocol.
2. Build the runner scripts.
3. Simulation 1A — exact theorem checks (~0.07 core-hours).
4. Simulation 1C — hash collapse (~5.8 core-hours).
5. Simulation 1B — finite-sample study, Option B (~41.7 core-hours).
6. Simulation 2 — reproduction under the frozen Stage 2 protocol.
7. Freeze raw outputs.
8. Generate summaries, tables, figures by script.
9. Validate every prespecified criterion without changing it.
10. Codex reproduces a sample of raw-to-summary calculations.
11. Gemini audits interpretation scope and figure/table completeness.
12. Commit, tag, and assemble the return package.

No manuscript prose is written at any stage.
