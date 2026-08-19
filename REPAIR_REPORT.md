# REPAIR_REPORT.md — cT2I simulation package, Phase R

**STATUS: DRAFT.** Steps 0–8 of the Phase R work order are executed and verified.
Two independent post-Step-8 reviews (fresh-context verifier + adversarial
council-seat-2 refutation) then found three real and three cosmetic
disclosure/metadata defects, all fixed and regenerated — see §13. Steps 9–11
(commit, tag, push, stamp, ZIP build, formal council) are **not** done, by
instruction. Every field naming the Phase R commit SHA or the ZIP SHA-256 is a
placeholder and is marked as such.

**Nothing in this repair is committed.** All changes sit uncommitted in the
working tree at parent commit `82ca32868f42cb95d2add6527b0ee57649bf7ebd`.

| headline | value |
|---|---|
| REAL-DATA MODELS RUN | 0 |
| REAL-DATA FILES MODIFIED | 0 |
| MANUSCRIPTS MODIFIED | 0 |
| COMPLETED RAW RESULT FILES CHANGED | **0** (5/5 verified byte-identical, §3) |
| SIM1 ACCEPTANCE TABLE | 13/13 MATCH |
| FIGS3 RERENDER | PASS |
| SIM2 FIGURE RERENDER | PASS |
| PACKAGE CHECKSUMS | 49/49 MATCH, self-entries 0 |
| CPU OVERRUN DISCLOSED | YES — RETROSPECTIVELY RATIFIED PROCESS DEVIATION |
| SIMULATION CELLS EXECUTED IN PHASE R | 0 |

Environment for every step: `/Users/Eric/.pyenv/versions/3.11.9/bin/python3`
(Python 3.11.9, numpy 2.4.1, pandas 2.3.3, scikit-learn 1.8.0, scipy 1.17.0,
lightgbm 4.7.0, matplotlib 3.10.8, macOS-arm64) — the exact interpreter recorded
in `02_ENVIRONMENT_AND_COMMIT.json`. The conda env `t2i` (Python 3.10.19) was
deliberately **not** used: different numpy/sklearn/matplotlib would change figure
rendering.

---

## 1. The authoritative commit

### 1.1 Decision

The pre-repair package named **three different commits in three metadata files**.
All three are stale build stamps on one linear branch:

```
4dce8fb -> 701bd89 -> e638d1f -> 3a37dd3 -> 82ca328 (pre-repair HEAD, tag sim-only-s1-complete)
```

| SHA | where it appeared | why it is REJECTED |
|---|---|---|
| `4dce8fbb…` | `PACKAGE_SHA256.json` inside `simulation-results-ct2i_3a37dd30.zip` | It is where the corrected Simulation 1C decomposition and criteria A14b/A14c enter, but three later commits carry packaging, `.gitignore` and README/manifest work that the delivered package depends on. It is a strict subset of the branch tip. |
| `e638d1fb…` | `02_ENVIRONMENT_AND_COMMIT.json`, `19_VALIDATION_REPORT.md`, `20_RESULT_HANDOFF_MEMO.md` | Adds only `.gitignore` rules and untracks three ZIP blobs — no scientific content, and two later commits follow it. It was stamped only because `run_s1_reports.py` recorded `git rev-parse HEAD` at report-generation time, i.e. the *previous* commit. |
| `3a37dd30…` | `00_README.md`, working-tree `PACKAGE_SHA256.json` | Touches only `build_return_package.py`, `run_s1_reports.py` and the metadata wording. Superseded one commit later. Chosen for the ZIP filename purely because the build script truncated `git rev-parse HEAD` to eight characters. |

**Authoritative pre-repair parent: `82ca32868f42cb95d2add6527b0ee57649bf7ebd`.**
Because the branch is linear, it is a strict superset of all three: it carries
every frozen simulation script, the corrected 1C decomposition, A14b/A14c, the
final summary/figure/table generators and the final README, and it is the target
of the existing annotated tag `sim-only-s1-complete`. Its working tree was clean
and its `PACKAGE_SHA256.json` verified 48/49 (the single failure being the
manifest hashing itself).

**The authoritative identifier reported to the advisor is the NEW Phase R
commit** created on top of `82ca328`, together with the annotated tag
`sim-only-s1-complete-v2`. That commit does not yet exist; see §1.2.

No identifier here was chosen because it appeared in a report.

### 1.2 Why the commit SHA is a placeholder (decision D1, Option A)

"Record the same full commit SHA in every package metadata file" cannot be
satisfied by a file that lives *inside* that commit: a commit's SHA is not
knowable before the commit exists. Stamping `git rev-parse HEAD` at write time —
what the old code did — always records the *previous* commit, and is exactly how
the three-way conflict arose.

Option A was adopted:

1. All repairs go into one commit `C_final` on
   `simulation-only/manuscript-revision`.
2. Metadata inside `C_final` names the **repository, branch and annotated tag**
   as authoritative and carries the literal token
   `PENDING_STAMP_SEE_PACKAGE_PROVENANCE` in the commit-SHA field.
3. After `C_final` exists and is tagged, the new deterministic
   `scripts/stamp_provenance.py <full-sha>` writes the real SHA into the four
   metadata files **in the working tree only**.
4. `scripts/build_return_package.py` then reads the stamped SHA, regenerates
   `00_README.md` and both checksum manifests from it, and names the archive
   `simulation-results-ct2i-repaired_<full 40-char sha>.zip`.

The delivered ZIP therefore names exactly one commit everywhere. The tree is left
dirty by design after stamping, and the stamped tree is reproducible
byte-for-byte from the tagged commit by re-running `stamp_provenance.py` with the
same SHA — verified idempotent and reversible in a sandbox (§9, Step 8).

**Placeholders to be filled after Step 9:**

| field | value |
|---|---|
| AUTHORITATIVE REPOSITORY | `https://github.com/hanmingwu1103/ct2i-benchmark.git` |
| AUTHORITATIVE BRANCH | `simulation-only/manuscript-revision` |
| AUTHORITATIVE COMMIT | `<C_final — PENDING>` |
| ANNOTATED TAG | `sim-only-s1-complete-v2` (**not yet created**) |
| TAG REMOTELY VERIFIED | `<PENDING — see the credential blocker, §8>` |
| REPAIRED ZIP | `simulation-results-ct2i-repaired_<C_final>.zip` (**not yet built**) |
| REPAIRED ZIP SHA256 | `<PENDING>` |

---

## 2. What was repaired

| # | defect | fix | file(s) |
|---|---|---|---|
| R8 | `TabS2` showed 15 lexicographically sorted rows, four of them `NOT EVALUATED`, and omitted A14b/A14c | table is now driven by `07_SIM1_ACCEPTANCE_REPORT.json` in one mandated order and raises on any id mismatch | `scripts/run_sim1_tables.py` |
| R9 | `FigS3` Hamming-weight panels drew ±1.11e-16 floating-point residuals as a signal curve on a 1e-16 axis; the legend sat inside a data panel | panels inside the frozen `zero_gap_abs = 1e-12` tolerance are drawn as exact zero with the residual stated in words; both rows of a column share one y-scale; one figure-level legend below the axes | `scripts/run_sim1_figures.py` |
| R10 | Sim 2 panel B put two series of different magnitude on one unlabelled axis; panel C's log axis produced malformed σ minor-tick labels | panel B gets a `twinx()` right axis, both axes labelled and colour-keyed, one legend outside the axes; panel C pins the ticks `0.005 0.010 0.030` with `FormatStrFormatter("%.3f")` and suppressed minor labels | `scripts/run_sim2_figures.py` |
| R11 | the three mandated caption clarifications were partly missing, and no durable caption artefact existed | footnotes sharpened on FigS2/FigS4; new `10_SIM1_FIGURES/FIGURE_CAPTIONS.md` holds the final caption text for all six figures and is registered in the package manifest | `scripts/run_sim1_figures.py`, new caption file, `scripts/build_return_package.py` |
| R12 | four metadata files named three different commits | one `provenance()` helper feeds every metadata file; SHA placeholder + `stamp_provenance.py` | `scripts/run_s1_reports.py`, new `scripts/stamp_provenance.py` |
| R13 | the 88.11-vs-80 core-hour overrun was disclosed as an open question | deviation D11 and a new validation-report section §4a now carry the exact status `RETROSPECTIVELY RATIFIED PROCESS DEVIATION` | `scripts/run_s1_reports.py` |
| R15 | `PACKAGE_SHA256.json` hashed itself, had no `manifest_excludes`, was written *after* the ZIP (so the shipped copy was always one build stale), and no detached sums file existed | manifests are written **before** the archive, exclude themselves and each other, declare `manifest_excludes`, and are joined by a detached `PACKAGE_SHA256SUMS.txt`; a new independent verifier re-checks all of it | `scripts/build_return_package.py`, new `scripts/verify_package_checksums.py` |
| R16 | ZIP filename used `commit[:8]` | filename now carries the full 40-character SHA and the `-repaired_` prefix; the build refuses to run unstamped unless `--allow-unstamped` is passed | `scripts/build_return_package.py` |

`00_README.md` additionally named the OLD tag `sim-only-s1-complete` (it read
`git tag --points-at HEAD`), which would have left the four metadata files
disagreeing about the tag as well as the commit. The README now takes the tag
from a constant matching `run_s1_reports.py`, so all four files name
`sim-only-s1-complete-v2`, the same branch, the same repository and the same SHA
placeholder — verified by grep across the four files.

Two incidental, rendering-only fixes are recorded for completeness: the Sim 2
panel-A note was moved so it no longer sits under the legend, and the FigS4
"rows omitted" annotation was moved so it no longer sits on a data point.
Neither changes a number.

### 2.1 Retired acceptance criteria (decision D5)

Trimming `TabS2` to the 13 evaluated criteria removed the only visible record of
A11, A12, A13 and A15. A new section **§1a of `19_VALIDATION_REPORT.md`** records
each id and where it is still verified: A11 retired pre-run as a restatement of a
reported result; A12 verified via deviation D1 (baseline self-influence 7e-5 at
n = 400, hence `OrderedCatBoostRunningPrior`); A13 verified as the S0 preflight
bitwise-replay gate plus `03_SEED_MANIFEST.csv`; A15 verified in
`14_SIM2_ACCEPTANCE_REPORT.json` (5/5). None was dropped to make the table pass.

---

## 3. Raw-output freeze — proof of no change

`shasum -a 256`, recorded before any edit (Step 0) and again after Step 8:

| file | SHA-256 | before | after |
|---|---|---|---|
| `05a_SIM1A_REPLICATE_RESULTS.parquet` | `648b9a5ddb70bfc2a7130fbaa2160f2789f63f446d1670928c8f392f7362fe09` | ✔ | ✔ identical |
| `05b_SIM1B_REPLICATE_RESULTS.parquet` | `5b5a191031be52d0e53c11fcd3655a5d92e53187b9c625d10693c72c6a3ba5cc` | ✔ | ✔ identical |
| `05c_SIM1C_EXACT_RESULTS.parquet` | `1ebb5f533b0602de6e609ecafb7f1b1fa1f5a99a8f5727ceca96c9bc195541e8` | ✔ | ✔ identical |
| `05d_SIM1C_FINITE_RESULTS.parquet` | `a4b69963f07ff7bdc6b7440e1a714477a9ef3e0ade1a7ad8046a6b2bdea6285c` | ✔ | ✔ identical |
| `12_SIM2_RESULTS.csv` | `cf3ecf180ee28f9ee0c2ce71a20aeb2ad2ad66a66d17133e50c39c07b12d92e7` | ✔ | ✔ identical |

All five also match `RAW_FREEZE_MANIFEST.json` (which itself was not modified).
`simulation-results-ct2i/raw/**`, `01_PROTOCOL_FREEZE.yaml` and
`manuscript_reference/**` were read only, never written. **COMPLETED RAW RESULT
FILES CHANGED: 0.**

No simulation cell was executed. `run_sim1a_exact.py`, `run_sim1b_finite.py`,
`run_sim1c_hash.py`, `run_sim2_reproduce.py`, `run_simulations.py`,
`run_pilot.py` and `run_smoke.py` were never invoked.

---

## 4. Raw-to-summary reproduction

`run_sim1_summarize.py` was re-run from the frozen raw CSVs (it writes only
`06_SIM1_SUMMARY.csv` and `07_SIM1_ACCEPTANCE_REPORT.json`; it contains no
`to_parquet` call).

* `06_SIM1_SUMMARY.csv` — regenerated output **byte-identical** to the saved copy
  (434 rows).
* `07_SIM1_ACCEPTANCE_REPORT.json` — **byte-identical**, 13 passed / 0 failed.
* raw parquet + CSV hashes unchanged afterwards.

The same determinism holds downstream: `03_SEED_MANIFEST.csv`,
`18_RUNTIME_AND_RESOURCE_REPORT.csv`, `TabS1`, `TabS3`, `08_SIM1_FIGURE_DATA.csv`
(1,122,000 rows), `14_SIM2_ACCEPTANCE_REPORT.json`, `15_SIM2_FIGURE_DATA.csv` and
`17_SIM2_SUMMARY_TABLE.csv` were all rewritten by the repaired scripts and came
back byte-identical — they do not appear in `git status`.

---

## 5. TabS2 — 13/13

Before: 15 rows, sorted `A1, A10, A11, A12, A13, A14, A15, A2 … A9`; A11/A12/
A13/A15 shown as `NOT EVALUATED`; **A14b and A14c absent**.

Root cause: `tab_s2()` iterated `sorted(01_PROTOCOL_FREEZE.yaml
["acceptance_criteria"])`. That freeze mapping is immutable and predates the
Codex audit fix, so it structurally *dropped* A14b/A14c and structurally *added*
the retired ids. The acceptance JSON — not the freeze YAML — is the record of
what was evaluated.

After: **13 data rows, all `PASS`**, in exactly the mandated order

```
A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A14, A14b, A14c
```

Verified: symmetric-difference of the table's id set against
`07_SIM1_ACCEPTANCE_REPORT.json`'s `criteria[].criterion_id` is **empty**; no
`NOT EVALUATED` row; no retired id present; `TabS2.tex` carries the same 13 ids
in the same order. The generator now raises `SystemExit` if the JSON and the
mandated order disagree in either direction, rather than silently dropping rows.

The A7 verification-scope note required by S0 review m2 is retained.

---

## 6. Figures

Regenerated once from the frozen inputs; every figure file was rewritten without
error: `FigS1`, `FigS2`, `FigS3`, `FigS3_auc`, `FigS4` (PDF + SVG) and
`16_SIM2_FIGURE` (PDF + SVG).

**FigS3 — before/after.** Before, each Hamming-weight panel autoscaled to its own
±1.11e-16 residual, so a reader saw a 1e-16 axis and a curve that looked like
structure; the legend sat inside panel (row 0, col 0) over the data. After, the
measured extremes are checked against the frozen tolerance
(`max |gap| = 1.1e-16 < zero_gap_abs = 1e-12`), those panels are drawn as exact
zero with the residual stated on the panel as "floating-point residual, not
signal", the two rows of each column share one y-scale, and a single figure-level
legend sits below the axes. The 2×3 position-specific vs Hamming-weight structure
is preserved, and the column-aware hash remains omitted from the loss axis with
the NOT-IDENTIFIED note intact. Confirmed by opening the rendered PDF: no axis
carries a 1e-16 offset and no legend overlaps a data axis.

**Sim 2 figure — before/after.** Panel B now shows validation regret on a
labelled left axis and winner instability on a labelled `twinx()` right axis,
colour-keyed, with one legend below the panel; panel spacing was widened so the
right-hand label does not collide with panel C. Panel C's x-axis shows exactly
`0.005 0.010 0.030`. Confirmed by opening the rendered PDF.

**Numerical invariance.** `14_SIM2_ACCEPTANCE_REPORT.json` (5/5),
`15_SIM2_FIGURE_DATA.csv` and `17_SIM2_SUMMARY_TABLE.csv` are byte-identical to
their pre-repair copies, proving no number moved. `08_SIM1_FIGURE_DATA.csv` is
also byte-identical, at **1,122,000 rows before and after** (decision D7: the row
count was recorded precisely because this file is regenerated and hashed; nothing
was dropped).

**Captions (R11).** The three mandated clarifications now appear both on the
rendered figures and in the new `10_SIM1_FIGURES/FIGURE_CAPTIONS.md`:
FigS2's shaded band is the *minimum-to-maximum range across DGP conditions*, not
a confidence interval; the completed 1B arm uses *d = 3 in every existing cell*;
and `NOT_IDENTIFIED` population-gap cells are *omitted, not assigned zero*.
No manuscript file was touched.

---

## 7. CPU overrun

`18_RUNTIME_AND_RESOURCE_REPORT.csv` TOTAL row is unchanged: **88.11 core-hours,
ceiling 80, OVER**. The figure was not concealed, not re-estimated downward and
not absorbed into another line.

`19_VALIDATION_REPORT.md` now carries the mandated status verbatim in three
places (deviation D11, new §4a, and the summary), and
`20_RESULT_HANDOFF_MEMO.md` carries it once:

> **RETROSPECTIVELY RATIFIED PROCESS DEVIATION**

quoting the completion plan §7 — the advisor's acceptance of the completion plan
constitutes retrospective ratification of the reported overrun. The three numbers
88.11 / 80 / 8.11 (10.1 %) are all present. GPU hours: 0.

Both reports also now state **ADDENDUM RUN: NO** — the targeted addendum (the
M = 5, d = M = 5 Simulation 1B configuration) was not executed and remains an
open advisor decision.

---

## 8. Checksums and packaging

Independent verifier `scripts/verify_package_checksums.py` (shares no code with
the builder — it walks the package itself):

```
manifest entries: 49
self-entries: 0
manifest_excludes declared: yes (['PACKAGE_SHA256.json'])
detached PACKAGE_SHA256SUMS.txt: agrees with the JSON manifest (49 lines)
49/49 MATCH, 0 mismatch, 0 missing, 0 unlisted, self-entries: 0
PACKAGE CHECKSUMS: 49/49 MATCH
```

Ordering is now: build README → hash the package → write
`PACKAGE_SHA256SUMS.txt` → write `PACKAGE_SHA256.json` → create the archive
(which contains both manifests). The previous code wrote the manifest *after*
`zipfile` closed, which is why the manifest shipped inside
`simulation-results-ct2i_3a37dd30.zip` disagreed with its own payload.

`raw/` inputs and `*.log` working files remain excluded from the package, which
is why the manifest has 49 entries rather than 49 + 289.

The archive is **not built** in this phase. Its name will be
`simulation-results-ct2i-repaired_<full 40-char sha>.zip`; the dry run confirms
the full-SHA form and the builder now refuses to run against unstamped metadata
unless `--allow-unstamped` is given. `.gitignore` was extended with
`simulation-results-ct2i-repaired_*.zip` — the existing pattern used an
underscore and would not have matched the new hyphenated name, so `git add -A`
in Step 9 would otherwise have committed a ~55 MB binary.

**Superseded artefact (decision D3).** `simulation-results-ct2i_3a37dd30.zip`
(55,364,846 B, SHA-256
`0ac070a2940331ce829e1ae0f7b3146a889cb9ed22df8f246824116381f73715`) is left in
place at the repo root, git-ignored and untouched. It is the **superseded**
return package: its internal `PACKAGE_SHA256.json` names `4dce8fbb…`, its
`02_ENVIRONMENT_AND_COMMIT.json` names `e638d1fb…` and its `00_README.md` names
`3a37dd30…` — the three-way conflict this repair removes. Both ZIPs can be
returned; the advisor should cite only the repaired one.

**Remote push blocker (unresolved, decision D2).** `git ls-remote origin` fails
with "Repository not found" — the osxkeychain credential in use has no access —
while the active `gh` account has `push: true` on the private repo. Neither the
branch nor any tag exists on GitHub today. Gate 2 and `TAG REMOTELY VERIFIED`
cannot be satisfied without changing git's credential setup, which is a
permission-sensitive action and was **not** performed here.

---

## 9. Evidence log (steps 0–8)

| step | what | result |
|---|---|---|
| 0 | raw-freeze baseline; branch safety | HEAD `82ca328…`, tree clean, 5/5 raw hashes match `RAW_FREEZE_MANIFEST.json` |
| 1 | raw → summary reproduction | `06` and `07` regenerate **byte-identical**; 13 pass / 0 fail; raw hashes unchanged |
| 2 | TabS2 generation fix | 13 rows, mandated order, all PASS, id set == JSON id set, retired ids absent, A14b/A14c present; TabS1/TabS3 byte-identical |
| 3 | FigS3 rerender | no 1e-16 axis, legend outside the data region, 2×3 structure preserved, PDF + SVG rewritten, figure-data row count unchanged |
| 4 | Sim 2 figure rerender | panel B twin labelled axes + external legend; panel C ticks `0.005 0.010 0.030`; `14`/`15`/`17` byte-identical |
| 5 | captions | three mandated sentences present in the rendered figures and in the new `FIGURE_CAPTIONS.md`; file registered in `REQUIRED` |
| 6 | regenerate all figures once | 10 figure files + Sim 2 figure rewritten without error; raw hashes re-verified unchanged |
| 7 | overrun ratification + metadata | mandated string present ×3 in `19`, ×1 in `20`; 88.11/80/8.11 intact; `ADDENDUM RUN: NO`; one `provenance()` source for all metadata |
| 8 | packaging + checksums | verifier `49/49 MATCH`, `self-entries: 0`, `manifest_excludes` present, detached sums file present, full-SHA ZIP naming confirmed by dry run; `stamp_provenance.py` proved deterministic, idempotent and reversible in a sandbox (the real tree was left unstamped) |

Full command-by-command log:
`scratchpad/phaseR_impl_log.md` (session scratchpad).

---

## 10. Files changed (all uncommitted)

Modified — scripts:
`scripts/build_return_package.py`, `scripts/run_s1_reports.py`,
`scripts/run_sim1_figures.py`, `scripts/run_sim1_tables.py`,
`scripts/run_sim2_figures.py`, `.gitignore`

Modified — generated package files:
`00_README.md`, `02_ENVIRONMENT_AND_COMMIT.json`,
`10_SIM1_FIGURES/FigS1.{pdf,svg}`, `FigS2.{pdf,svg}`, `FigS3.{pdf,svg}`,
`FigS3_auc.{pdf,svg}`, `FigS4.{pdf,svg}`, `11_SIM1_TABLES/TabS2.{csv,tex}`,
`16_SIM2_FIGURE.{pdf,svg}`, `19_VALIDATION_REPORT.md`,
`20_RESULT_HANDOFF_MEMO.md`, `PACKAGE_SHA256.json`

New:
`scripts/stamp_provenance.py`, `scripts/verify_package_checksums.py`,
`simulation-results-ct2i/10_SIM1_FIGURES/FIGURE_CAPTIONS.md`,
`simulation-results-ct2i/PACKAGE_SHA256SUMS.txt`, `REPAIR_REPORT.md`

Not touched: the five frozen raw outputs, `RAW_FREEZE_MANIFEST.json`, `raw/**`,
`01_PROTOCOL_FREEZE.yaml`, `manuscript_reference/**`, `simulation2_authoritative/`,
`configs/`, `src/`, `tests/`, and everything under the thesis workspace.

---

## 11. Recorded discrepancies and open questions for the advisor

1. **Audit vs code, Sim 2 panel B (decision D6).** The 2026-08-16 audit describes
   "panel B's right axis and legend" as crowded. The pre-repair code had **no**
   right axis at all: both series shared one unlabelled axis, which is why the
   panel was unreadable. The fix satisfies the audit's intent by *creating* the
   labelled right axis the audit assumed existed. The discrepancy is recorded
   rather than quietly reconciled.

2. **Figure scripts read `raw/*.csv`, not `08_SIM1_FIGURE_DATA.csv` (D8).** The
   completion plan says figures are rerendered "from frozen figure-data files";
   in fact `run_sim1_figures.py` reads the frozen raw CSVs directly and *emits*
   `08_SIM1_FIGURE_DATA.csv`. Reading raw is read-only and reproduces the same
   numbers (the emitted file came back byte-identical), so the pipeline was left
   as it is rather than rewritten during a repair phase.

3. **`requirements.lock.txt` disagrees with the environment that produced the
   package (D9).** The lock pins matplotlib 3.11.1 / numpy 2.4.6 / sklearn 1.9.0;
   the package was produced with 3.10.8 / 2.4.1 / 1.8.0, which is what
   `02_ENVIRONMENT_AND_COMMIT.json` records. The lock file was **left untouched**:
   upgrading to it would change figure rendering. Open question — should the lock
   be re-pinned to the environment that actually ran, or is the divergence
   accepted as-is?

4. **Council seats (D4).** The execution prompt mandates a Claude/Codex/Gemini
   council with provider notes preserved verbatim. Codex and Gemini seats are not
   wired up in this environment. The seats will be filled by **independent
   fresh-context Claude agents**, disclosed as such; `CRITICAL VETO COUNT` will be
   sourced from those reviews. No veto count is fabricated, and no provider note
   is invented.

5. **Remote push authorisation (D2).** See §8. Pushing this branch to the
   advisor's private repository under the currently active `gh` account needs
   explicit confirmation before Step 9.

---

## 12. What is NOT done

Steps 9–11 of the work order are outstanding, by instruction:

* no `git commit`, no `git tag`, no `git push`, no change to git config or
  credentials — every change above is uncommitted;
* `scripts/stamp_provenance.py` has **not** been run against the real tree (it
  was exercised only in a sandbox copy);
* the repaired ZIP has **not** been built, so there is no ZIP SHA-256 yet;
* the council review has not been run, so `CRITICAL VETO COUNT` is not yet
  determined;
* the mandatory final console block is therefore not printed here — it can only
  be completed once the commit, tag, push, stamp, ZIP and council are done.

---

## 13. Post-review fixes (takeover)

Steps 0–8 above (§9's evidence log) were audited by two independent
fresh-context reviews substituting for the mandated Codex/Gemini council
seats (decision D4): a fresh-context **verifier** agent and an adversarial
**council-seat-2 refutation** agent (`scratchpad/phaseR_council_seat2.md`).
Both reviews found **no scientific drift, no acceptance-criteria tuning, no
frozen-protocol or raw-data violation, and no figure dishonesty** — every
change in §9 remained formatting, ordering, rendering, packaging, prose or
provenance. They did find three real disclosure/metadata-hygiene defects and
three cosmetic ones, all fixed below. No number in `07_SIM1_ACCEPTANCE_REPORT.
json`, `06_SIM1_SUMMARY.csv`, `14_SIM2_ACCEPTANCE_REPORT.json`, or any frozen
raw output changed while fixing any of these.

| # | finding | resolution | where |
|---|---|---|---|
| 1 (REAL) | `19_VALIDATION_REPORT.md` asserted `- [x] the package includes the exact Git commit` unconditionally, three lines below a table naming the commit `PENDING_STAMP_SEE_PACKAGE_PROVENANCE` — the gate was true by hard-coded text, not by fact. | `scripts/run_s1_reports.py` now derives the checkbox from the SHA actually present via `commit_gate_line()`: unchecked with an Option A explanation while unstamped, `[x]` with the stamped SHA once `scripts/stamp_provenance.py` has run. Both scripts import the same function so the two states can never disagree. Regenerated: `19_VALIDATION_REPORT.md` line 203 now reads `- [ ] ... NOT YET SATISFIED IN THIS COPY. Option A ...`. | `scripts/run_s1_reports.py` (`COMMIT_GATE`, `commit_gate_line`), `scripts/stamp_provenance.py` |
| 2 (REAL) | `00_README.md`'s own row in its file table printed a stale intermediate hash (`7d7b635d...`), never the file's real hash — `build_readme()` runs before the README is written, so the self-row can never be correct (same bug class as R15/`PACKAGE_SHA256.json`, left open at that time). | `build_return_package.py::build_readme()` now special-cases its own filename and prints `(self — see PACKAGE_SHA256SUMS.txt)` instead of a hash; the true hash is only ever recorded in the detached sums file, written after the README is finalized. Verified: `shasum -a 256 00_README.md` == the `PACKAGE_SHA256SUMS.txt` entry for it, byte for byte. | `scripts/build_return_package.py::build_readme()` |
| 3 (REAL) | `matplotlib` (which renders every figure) was absent from `02_ENVIRONMENT_AND_COMMIT.json` and the §0 Environment table in `19_VALIDATION_REPORT.md`, while the "all seeds and package versions recorded" gate was checked and §11.3 (old) argued from a matplotlib version the package never recorded. | `scripts/run_s1_reports.py` now imports `lightgbm`, `matplotlib` and `pyarrow` alongside the core packages and writes them into the `pkgs` dict that feeds both the JSON and the report table. Regenerated: `02_ENVIRONMENT_AND_COMMIT.json` records `"matplotlib": "3.10.8"`; `19_VALIDATION_REPORT.md` §0 lists `matplotlib | 3.10.8`. `00_README.md` carries no package-version list (only a file/hash table), so nothing there needed a change. | `scripts/run_s1_reports.py` |
| 4 | `FigS4`'s caption said "Error bars are standard errors across cells", but the rendered PDF shows no visible bars in either panel. Recomputed from `05b_SIM1B_REPLICATE_RESULTS.parquet`: the largest cell-wise SEM is ≈2.3e-4 on a panel-(a) axis spanning ≈0.16, and ≈1.1e-3 on a panel-(b) axis spanning ≈2.6 — genuinely smaller than the plotting marker, not a plotting bug. Inflating the bars to be visible would misstate their true magnitude (new statistical content), so the caption was corrected instead, per instruction to prefer that over changing what is plotted. | `10_SIM1_FIGURES/FIGURE_CAPTIONS.md`'s FigS4 entry now reads "...in every cell the standard error is smaller than the plotting marker, so no bar is separable from its marker in the rendered figure." The in-figure footnote in `scripts/run_sim1_figures.py::fig_s4()` was extended to match ("error bars are standard errors, smaller than the marker in every cell here so no bar is visually separable from its marker"). `FigS4.pdf`/`.svg` rerendered and visually confirmed (rendered to PNG and read back): still no separable bars, footnote text now present and accurate. No error-bar values or statistics were changed. | `scripts/run_sim1_figures.py::fig_s4()`, `simulation-results-ct2i/10_SIM1_FIGURES/FIGURE_CAPTIONS.md` |
| 5a (COSMETIC) | `19_VALIDATION_REPORT.md` deviation D11 gave two different numbers in one block: "Why:" said "Measured total 88.1 core-hours" while "What was done:" said 88.11. | Both lines are generated from the same `88.11` literal in `scripts/run_s1_reports.py`'s D11 `why` text; regenerated `19_VALIDATION_REPORT.md` now reads 88.11 in both the "Why:" and "What was done:" lines (lines 141/143). 88.11 / 80 / 8.11 (10.1%) unchanged and not re-estimated. | `scripts/run_s1_reports.py` (`DEVIATIONS`, D11) |
| 5b (COSMETIC) | `scripts/verify_package_checksums.py`'s "file present but unlisted" check compared **basenames** (`p.name not in named`), so two same-named files in different subdirectories could mask one another (no such collision existed today, but the check did not guard against it). | Rewritten to compare package-relative paths: `in_package()` strips the package's parent prefix from each manifest key, and the unlisted check tests `p.relative_to(outd) not in listed` instead of a basename set. Re-run after the fix: `49/49 MATCH, 0 mismatch, 0 missing, 0 unlisted, self-entries: 0`. | `scripts/verify_package_checksums.py` (`in_package()`) |
| 5c (COSMETIC) | `19_VALIDATION_REPORT.md` §1's acceptance-criteria table and `11_SIM1_TABLES/TabS2.csv` list the same 13 criteria in two different orders: §1 follows `07_SIM1_ACCEPTANCE_REPORT.json`'s natural order (A1–A6, A10, A7, A8, A9, A14b, A14c, A14), TabS2 follows the mandated order (A1–A10, A14, A14b, A14c) required by decision R8. | This is intentional, not a defect: TabS2 is the deliverable the plan constrains to one exact order; §1 exists as a human-readable cross-check and is explicitly scoped to that role by the sentence immediately below it ("`TabS2.csv` carries exactly these criteria, in the order A1-A10, A14, A14b, A14c, and nothing else."). Both tables list the identical 13-id set with identical pass/value fields — verified by symmetric difference — so the order difference cannot hide or duplicate a criterion. No generator change was made for this item. | `scripts/run_s1_reports.py` §1 table vs `scripts/run_sim1_tables.py::tab_s2()` |

**Regeneration after the fixes above:** `scripts/run_sim1_figures.py` (all
`10_SIM1_FIGURES/*` + `08_SIM1_FIGURE_DATA.csv`, 1,122,000 rows, unchanged
row count), `scripts/run_sim1_tables.py` (`11_SIM1_TABLES/*`, TabS2 still
13/13 mandated order), `scripts/run_sim2_figures.py` (`16_SIM2_FIGURE.*`,
`14`/`15`/`17` byte-identical), `scripts/run_s1_reports.py` (`02`, `03`, `18`,
`19`, `20`), then `scripts/build_return_package.py --allow-unstamped
--manifest-only` (`00_README.md`, `PACKAGE_SHA256.json`,
`PACKAGE_SHA256SUMS.txt`). The five frozen raw outputs were re-hashed after
every regeneration and remain 5/5 identical to `RAW_FREEZE_MANIFEST.json`
(§3). `scripts/verify_package_checksums.py` re-run at the end: **49/49
MATCH, 0 mismatch, 0 missing, 0 unlisted, self-entries: 0**.

Still not done, unchanged from §12: commit / tag / push / stamp / ZIP build /
formal council run with `CRITICAL VETO COUNT`. This session's two reviews
stand in for that council per decision D4 but are not themselves the
mandated final council pass.
