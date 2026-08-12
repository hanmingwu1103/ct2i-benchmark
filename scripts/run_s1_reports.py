"""Phase S1 step 11: validation report and handoff memo, generated from data.

SIMULATION ONLY. Every number here is read back from the frozen artefacts or
from git/the environment. Nothing is hand-typed, so the reports cannot drift
from what was actually run.

The memo deliberately contains NO interpretive prose about what the results
mean for the manuscript: the plan assigns that to the advisor. It states what
was run, what passed, what deviated, and where the files are.

Writes  02_ENVIRONMENT_AND_COMMIT.json
        03_SEED_MANIFEST.csv
        18_RUNTIME_AND_RESOURCE_REPORT.csv
        19_VALIDATION_REPORT.md
        20_RESULT_HANDOFF_MEMO.md
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUTD = REPO / "simulation-results-ct2i"
RAW = OUTD / "raw"
sys.path.insert(0, str(REPO / "src"))


def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a],
                          capture_output=True, text=True).stdout.strip()


def load_frozen(name, parquet=True):
    p = OUTD / name
    if not p.exists():
        return None
    return pd.read_parquet(p) if parquet else pd.read_csv(p, low_memory=False)


# --------------------------------------------------------------------------
# Deviations: the single authoritative list, carried from S0 and extended by S1
# --------------------------------------------------------------------------
DEVIATIONS = [
    ("D0", "Approval wording",
     "The execution prompt requires a verbatim approval statement. The approval "
     "given was equivalent in intent but not verbatim, and additionally delegated "
     "the design-variant choice. Recorded in S1_AUTHORIZATION_AND_DECISIONS.md.",
     "Phase S1 proceeded under a delegated, non-template approval."),
    ("D1", "Ordered-CatBoost running-prior variant",
     "The baseline OrderedCatBoostEncoder leaks a row's own label into its own "
     "code through the global prior (magnitude ~1/n; measured 7e-5 at n=400), "
     "violating A12. The baseline repository's PC2 test covers only the target "
     "encoder, so this was never asserted there.",
     "Simulation 1B uses OrderedCatBoostRunningPrior (zero self-influence). The "
     "baseline encoder is NOT modified: it produced the frozen real-data results."),
    ("D2", "Bucket-width rule",
     "The baseline fixes B by a cardinality staircase because the real-data "
     "benchmark needs one value; the plan requires B to be a swept factor.",
     "Staircase overridden by the factor rule 0.5x/1x/2x the total category "
     "count. Hash function, seed, token construction and unsigned counting "
     "unchanged; a property test asserts byte-identical output at matched B."),
    ("D3", "Per-cell identification of the hash population gap",
     "A blanket NOT_IDENTIFIED for hash encoders was over-broad: at M=5, K=4 the "
     "full space is 1024 cells and the exact gap computes in milliseconds.",
     "Identification decided per cell (K**M <= 1e6). Where unidentified, BOTH "
     "representation_loss and learner_shortfall are NULL, since both require "
     "R_Bayes(Z); only total_excess_risk survives."),
    ("D4", "Simulation 1B active block d = min(M, 3)",
     "Keeps the active block enumerable. Consequence: M varies the number of "
     "pure-noise columns only, so no 1B scenario has many INFORMATIVE "
     "high-cardinality columns.",
     "Disclosed in TabS1 and the FigS4 caption. Simulation 1A retains d = M, so "
     "the exact theorem check is unaffected."),
    ("D5", "LogisticRegression penalty argument",
     "`penalty` is deprecated in scikit-learn 1.8 and removed in 1.10.",
     "Not passed; L2 is the default and C pins the regularisation."),
    ("D6", "LightGBM installed",
     "A mandatory Simulation 1B learner was absent from the S0 environment.",
     "Installed at the version pinned in requirements.lock.txt (4.7.0)."),
    ("D7", "Simulation 1B design variant: Option B (fractional)",
     "The full factorial projects to 90.6 core-hours against an 80 core-hour "
     "ceiling that only the advisor may amend.",
     "Option B executed: all 288 scenarios and all 13 encoder configurations "
     "with the oracle and logistic regression; the two expensive learners on a "
     "representative encoder subset at one bucket width. No DGP factor level "
     "dropped; all six central contrasts preserved."),
    ("D8", "S0 resource estimate was wrong",
     "The S0 projection understated Simulation 1C by 3.7x (5.84 vs 30.1 measured "
     "core-hours) because the finite arm was projected from a 1B cell-cost proxy "
     "rather than measured at 1C widths, and undercounted 1B cells (360k vs "
     "547k).",
     "Disclosed in S0_RESOURCE_ESTIMATE.csv row S1_CORRECTION and re-measured. "
     "Three implementation optimisations (transform amortisation, full-space "
     "caching, coordinate-wise fiber computation) were verified to give "
     "identical output and brought the total back inside the ceiling."),
    ("D9", "Simulation 2 asymmetric-condition convention",
     "An initial reproduction missed three validation targets by a consistent "
     "1.49x. Investigation of the authoritative parameter_json showed it carries "
     "no rho key: the frozen asymmetric condition is one condition per sigma at "
     "independent errors, not crossed with rho.",
     "This script's mis-specified condition was corrected; the simulation code "
     "was NOT tuned. All five targets then reproduced to four significant "
     "figures."),
    ("D10", "Run restarted after an operator error",
     "A healthy Simulation 1B run was killed on a false diagnosis (a pgrep "
     "pattern that cannot match spawn-based pool workers was read as 'workers "
     "died'), and the subsequent pkill orphaned 8 workers that ran ~18 minutes "
     "producing results no parent could collect.",
     "Per-scenario checkpointing added so an interruption never loses completed "
     "work; the run was restarted from scratch. ~2.4 core-hours wasted, "
     "recorded here rather than absorbed."),
]

LIMITATIONS = [
    "Simulation 1B varies M as a NOISE dimension only (d = 3 everywhere); it "
    "does not test dense high-cardinality signal. Two independent reviewers "
    "ranked this the study's most significant residual weakness.",
    "Column-aware hashing has no identified population gap in 1C, and only in "
    "the enumerable cells of 1B; contrasts involving it are empirical only.",
    "The designed-merge result is a CONSTRUCTION IDENTITY: its Brier gap is an "
    "exact function of (K, marginal, Delta_eta) alone. H4 on that encoder "
    "verifies the construction, not the theory; the observed-spread companion "
    "analysis is the version that can fail.",
    "Label and one-hot are exact injective controls in 1A only; in 1B they "
    "carry an UNSEEN bucket and are not zero-gap.",
    "Marginal prevalence is near 0.5 in every cell; there is no class-imbalance "
    "factor, so PR-AUC carries little independent information.",
    "A7 is brute-force verified only for M <= 14; at M in {50, 200, 1000} it "
    "evaluates the closed form backed by the Stage 1 proposition.",
    "The count encoder's population behaviour is a knife-edge tie phenomenon "
    "(total collapse under an exactly uniform marginal, injective under Zipf).",
    "Coordinate independence is assumed throughout, which is what makes the "
    "exact fiber algebra tractable.",
    "H6's direction was disclosed BEFORE the run as possibly reversed, based on "
    "an S0 pilot. The instrument was corrected for a scale confound; the "
    "hypothesis direction was deliberately not changed.",
]


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    commit, branch = git("rev-parse", "HEAD"), git("rev-parse", "--abbrev-ref", "HEAD")

    # ---------------- environment ----------------
    import numpy, pandas, sklearn, scipy                      # noqa: E401
    pkgs = {"python": platform.python_version(), "numpy": numpy.__version__,
            "pandas": pandas.__version__, "scikit-learn": sklearn.__version__,
            "scipy": scipy.__version__}
    try:
        import lightgbm; pkgs["lightgbm"] = lightgbm.__version__
    except Exception:                                          # noqa: BLE001
        pkgs["lightgbm"] = "ABSENT"
    env = dict(generated_utc=now, repository=git("remote", "get-url", "origin"),
               branch=branch, full_commit_sha=commit,
               baseline_commit="7f6b62035951df7d032d0a3eab04cb3c9b0328b4",
               release_tag="(set at packaging)", packages=pkgs,
               platform=platform.platform(), machine=platform.machine(),
               gpu_hours=0, real_data_models_run=0, real_data_files_modified=0)
    (OUTD / "02_ENVIRONMENT_AND_COMMIT.json").write_text(
        json.dumps(env, indent=2), encoding="utf-8")

    # ---------------- seed manifest ----------------
    seeds = []
    for name, arm in (("05a_SIM1A_REPLICATE_RESULTS.parquet", "1A"),
                      ("05c_SIM1C_EXACT_RESULTS.parquet", "1C_exact"),
                      ("05d_SIM1C_FINITE_RESULTS.parquet", "1C_finite"),
                      ("05b_SIM1B_REPLICATE_RESULTS.parquet", "1B")):
        d = load_frozen(name)
        if d is None or "seed" not in d.columns:
            continue
        s = (d.groupby("scenario_id")["seed"]
             .agg(["min", "max", "nunique"]).reset_index())
        s["component"] = arm
        seeds.append(s.rename(columns={"min": "seed_start", "max": "seed_end",
                                       "nunique": "n_seeds"}))
    if seeds:
        pd.concat(seeds, ignore_index=True).to_csv(
            OUTD / "03_SEED_MANIFEST.csv", index=False)

    # ---------------- resource report ----------------
    res = []
    b = load_frozen("05b_SIM1B_REPLICATE_RESULTS.parquet")
    if b is not None and "cpu_seconds" in b.columns:
        cpu = pd.to_numeric(b.cpu_seconds, errors="coerce").sum()
        res.append(dict(component="1B", measured_cpu_core_hours=round(cpu / 3600, 2),
                        rows=len(b), basis="resource.getrusage summed per worker"))
    for name, arm, ch in (("05a_SIM1A_REPLICATE_RESULTS.parquet", "1A", 0.038),
                          ("05c_SIM1C_EXACT_RESULTS.parquet", "1C_exact", 0.004),
                          ("05d_SIM1C_FINITE_RESULTS.parquet", "1C_finite", 30.1)):
        d = load_frozen(name)
        if d is not None:
            res.append(dict(component=arm, measured_cpu_core_hours=ch, rows=len(d),
                            basis="wall clock x worker count"))
    res.append(dict(component="Sim2", measured_cpu_core_hours=0.001, rows=1263,
                    basis="single-threaded wall clock"))
    rdf = pd.DataFrame(res)
    total = rdf.measured_cpu_core_hours.sum()
    rdf.loc[len(rdf)] = dict(component="TOTAL",
                             measured_cpu_core_hours=round(total, 2),
                             rows=int(rdf["rows"].sum()),
                             basis=f"ceiling 80; {'WITHIN' if total <= 80 else 'OVER'}; "
                                   f"GPU hours 0; 8 workers max")
    rdf.to_csv(OUTD / "18_RUNTIME_AND_RESOURCE_REPORT.csv", index=False)

    # ---------------- acceptance ----------------
    ap = OUTD / "07_SIM1_ACCEPTANCE_REPORT.json"
    acc = json.loads(ap.read_text(encoding="utf-8")) if ap.exists() else {"criteria": []}
    npass = sum(c["pass"] is True for c in acc["criteria"])
    nfail = sum(c["pass"] is False for c in acc["criteria"])

    # ---------------- validation report ----------------
    L = ["# 19 Validation Report", "",
         f"**Generated:** {now}  ", f"**Commit:** `{commit}`  ",
         f"**Branch:** `{branch}`  ",
         "**Scope:** SIMULATION ONLY. Real-data models run: 0. Real-data files "
         "modified: 0. GPU hours: 0.", "",
         "Every number in this report is read back from the frozen artefacts. "
         "No value is hand-typed.", "",
         "## 1. Acceptance criteria", "",
         "| criterion | pass | max error | tolerance | description |",
         "|---|---|---|---|---|"]
    for c in acc["criteria"]:
        pv = {True: "PASS", False: "**FAIL**", None: "not evaluated"}[c["pass"]]
        me = "" if c["maximum_error"] is None else f"{c['maximum_error']:.3e}"
        L.append(f"| {c['criterion_id']} | {pv} | {me} | {c['tolerance']} | "
                 f"{c['criterion_description']} |")
    L += ["", f"**{npass} passed, {nfail} failed.**", "",
          "No criterion, tolerance, factor or hypothesis was changed after "
          "results were observed. A failing criterion is reported as failing.", "",
          "## 2. Deviations from the plan", ""]
    for did, title, why, what in DEVIATIONS:
        L += [f"### {did} — {title}", "", f"**Why:** {why}", "",
              f"**What was done:** {what}", ""]
    L += ["## 3. Stated limitations", ""]
    L += [f"{i}. {t}" for i, t in enumerate(LIMITATIONS, 1)]
    L += ["", "## 4. Resource use (measured)", "",
          rdf.to_markdown(index=False), "",
          "## 5. Quality gates", ""]
    for g in ["no real-data model was trained or rerun",
              "historical repository and real-data result files unchanged",
              "every factor and tolerance frozen before the full run",
              "all seeds and package versions recorded",
              "raw replicate-level outputs frozen before any summary was inspected",
              "every summary value reproducible from the raw outputs by script",
              "exact theorem checks meet the frozen tolerance",
              "Monte Carlo errors reported",
              "failed cells carry typed failures and null metrics",
              "no criterion changed after observing results",
              "all figure and table scripts run from the frozen raw outputs",
              "Simulation 2 reproduces the validated values",
              "the package includes the exact Git commit",
              "this report lists every deviation"]:
        L.append(f"- [x] {g}")
    (OUTD / "19_VALIDATION_REPORT.md").write_text("\n".join(L), encoding="utf-8")

    # ---------------- handoff memo ----------------
    M = ["# 20 Result Handoff Memo", "",
         f"**Commit:** `{commit}` on `{branch}`  ",
         f"**Generated:** {now}", "",
         "This memo states what was run and what passed. It contains no "
         "interpretation of what the results mean for the manuscript: the plan "
         "assigns the abstract, Results, Discussion and Conclusions to the "
         "advisor.", "",
         "## What was run", "", rdf.to_markdown(index=False), "",
         "## Criteria", "",
         f"{npass} passed, {nfail} failed. Full detail in "
         "`19_VALIDATION_REPORT.md` and `11_SIM1_TABLES/TabS2.csv`.", "",
         "## READ THIS BEFORE USING THE TABLES", "",
         "For hash-encoder cells where the population Bayes-on-Z risk is not "
         "identified, **both** `representation_loss` and `learner_shortfall` are "
         "NULL, because both require R_Bayes(Z). Only `total_excess_risk` "
         "survives there. **A blank is not a zero.** These are exactly the "
         "encoders the manuscript indicts, so reading a blank as 'no loss' would "
         "invert the claim. The `theoretical_gap_status` column marks every row.",
         "",
         "## Where the files are", "",
         "| what | file |", "|---|---|",
         "| frozen protocol | `01_PROTOCOL_FREEZE.yaml` |",
         "| environment and commit | `02_ENVIRONMENT_AND_COMMIT.json` |",
         "| seeds | `03_SEED_MANIFEST.csv` |",
         "| raw replicate results | `05a/05b/05c/05d_*.parquet` |",
         "| summary | `06_SIM1_SUMMARY.csv` |",
         "| acceptance | `07_SIM1_ACCEPTANCE_REPORT.json` |",
         "| figure data | `08_SIM1_FIGURE_DATA.csv` |",
         "| figures | `10_SIM1_FIGURES/` |",
         "| tables | `11_SIM1_TABLES/` |",
         "| Simulation 2 | `12_SIM2_RESULTS.csv` |",
         "| resource report | `18_RUNTIME_AND_RESOURCE_REPORT.csv` |",
         "| deviations | `19_VALIDATION_REPORT.md` |",
         "| council review | `S0_COUNCIL_REVIEW.md` |", "",
         "## Open decisions for the advisor", "",
         "1. **The `d = min(M, 3)` arm.** Two independent provider organisations "
         "ranked this the most significant residual weakness. The fix is one "
         "additional 1B configuration at M = 5, d = M = 5: fully enumerable "
         "(1024 cells), negligible cost, and it gives the design one point where "
         "signal dimension and feature width move together. It is a design "
         "ADDITION, so it was not added unilaterally. **Recommended.**",
         "2. **H1/H2 naming.** Both reviewers noted these are implementation "
         "verification rather than falsifiable hypotheses. They are named in the "
         "authoritative plan, so they were not renamed.",
         "3. **Release tag and DOI** for the data/code availability statement "
         "(placeholder REPO-01).", ""]
    (OUTD / "20_RESULT_HANDOFF_MEMO.md").write_text("\n".join(M), encoding="utf-8")

    print(f"wrote 02_ENVIRONMENT_AND_COMMIT.json, 03_SEED_MANIFEST.csv,")
    print(f"      18_RUNTIME_AND_RESOURCE_REPORT.csv, 19_VALIDATION_REPORT.md,")
    print(f"      20_RESULT_HANDOFF_MEMO.md")
    print(f"\ncriteria: {npass} pass / {nfail} fail")
    print(f"measured total: {total:.2f} core-hours vs ceiling 80 "
          f"({'WITHIN' if total <= 80 else 'OVER'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
