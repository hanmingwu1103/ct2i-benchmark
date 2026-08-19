"""Phase S1 step 12: assemble the return package.

SIMULATION ONLY. Builds 00_README.md from the frozen artefacts, verifies that
every file the plan's Part III requires is present (or explains its absence),
records a sha256 for each, and writes the ZIP.

Refuses to build a package that is missing a required file, so an incomplete
return cannot be handed over by accident.

Phase R changes:
  * the checksum manifests are written BEFORE the archive is created, so the
    shipped manifest is never one build stale (that is why the manifest inside
    simulation-results-ct2i_3a37dd30.zip disagreed with its own payload);
  * PACKAGE_SHA256.json excludes itself and PACKAGE_SHA256SUMS.txt and records
    that exclusion explicitly, so no entry hashes the manifest that contains it;
  * a detached PACKAGE_SHA256SUMS.txt is emitted alongside it;
  * the ZIP carries the FULL 40-character commit SHA, read from the stamped
    02_ENVIRONMENT_AND_COMMIT.json rather than truncated from git HEAD.

Usage: build_return_package.py [--allow-partial] [--allow-unstamped]
                              [--manifest-only]
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTD = REPO / "simulation-results-ct2i"

MANIFEST_JSON = "PACKAGE_SHA256.json"
MANIFEST_SUMS = "PACKAGE_SHA256SUMS.txt"
# Neither manifest may appear inside either manifest: a hash of the file that
# carries it can never be satisfied.
MANIFEST_EXCLUDES = [MANIFEST_JSON, MANIFEST_SUMS]
SHA_PLACEHOLDER = "PENDING_STAMP_SEE_PACKAGE_PROVENANCE"
# Must match scripts/run_s1_reports.py AUTHORITATIVE_TAG: every metadata file
# has to name ONE tag (requirement R12).
AUTHORITATIVE_TAG = "sim-only-s1-complete-v2"


def package_files():
    """Every file that belongs in the package, in a stable order.

    raw/ and *.log are working inputs, not deliverables, and both manifests are
    excluded from the hashed set.
    """
    out = []
    for p in sorted(OUTD.rglob("*")):
        if not p.is_file():
            continue
        if "/raw/" in str(p) or p.name.endswith(".log"):
            continue
        if p.name in MANIFEST_EXCLUDES and p.parent == OUTD:
            continue
        out.append(p)
    return out


def stamped_commit():
    """The authoritative full SHA, as stamped by scripts/stamp_provenance.py."""
    p = OUTD / "02_ENVIRONMENT_AND_COMMIT.json"
    if not p.exists():
        return SHA_PLACEHOLDER
    return json.loads(p.read_text(encoding="utf-8")).get(
        "full_commit_sha", SHA_PLACEHOLDER)

# (filename, required, note when absent/substituted)
REQUIRED = [
    ("00_README.md", True, ""),
    ("01_PROTOCOL_FREEZE.yaml", True, ""),
    ("02_ENVIRONMENT_AND_COMMIT.json", True, ""),
    ("03_SEED_MANIFEST.csv", True, ""),
    ("04_SIM1_SCENARIO_MANIFEST.csv", False,
     "superseded by 11_SIM1_TABLES/TabS1.csv, which reports the design as "
     "EXECUTED rather than as planned"),
    ("05a_SIM1A_REPLICATE_RESULTS.parquet", True,
     "the plan's single 05_SIM1_REPLICATE_RESULTS.parquet is split by arm "
     "(05a/05b/05c/05d) because the arms have different schemas"),
    ("05b_SIM1B_REPLICATE_RESULTS.parquet", True, ""),
    ("05c_SIM1C_EXACT_RESULTS.parquet", True, ""),
    ("05d_SIM1C_FINITE_RESULTS.parquet", True, ""),
    ("06_SIM1_SUMMARY.csv", True, ""),
    ("07_SIM1_ACCEPTANCE_REPORT.json", True, ""),
    ("08_SIM1_FIGURE_DATA.csv", True, ""),
    ("09_SIM1_TABLE_DATA.csv", False, "table data is emitted per table in 11_SIM1_TABLES/"),
    ("10_SIM1_FIGURES", True, ""),
    ("10_SIM1_FIGURES/FIGURE_CAPTIONS.md", True,
     "final caption text for every publication figure, added in Phase R"),
    ("11_SIM1_TABLES", True, ""),
    ("12_SIM2_RESULTS.csv", True, ""),
    ("13_SIM2_SUMMARY.csv", False, "Simulation 2 summary is carried in 17_SIM2_SUMMARY_TABLE.csv"),
    ("14_SIM2_ACCEPTANCE_REPORT.json", True, ""),
    ("15_SIM2_FIGURE_DATA.csv", True, ""),
    ("16_SIM2_FIGURE.pdf", True, ""),
    ("17_SIM2_SUMMARY_TABLE.csv", True, ""),
    ("18_RUNTIME_AND_RESOURCE_REPORT.csv", True, ""),
    ("19_VALIDATION_REPORT.md", True, ""),
    ("20_RESULT_HANDOFF_MEMO.md", True, ""),
    # S0 provenance, carried so the reviewer can see the pre-run gate
    ("S0_PROTOCOL_FREEZE_PROVENANCE", False, ""),
    ("S0_IMPLEMENTATION_SPEC.md", True, ""),
    ("S0_COUNCIL_REVIEW.md", True, ""),
    ("S0_PREFLIGHT_REPORT.md", True, ""),
    ("S0_TEST_REPORT.md", True, ""),
    ("S0_RESOURCE_ESTIMATE.csv", True, ""),
    ("S0_INPUT_AND_HASH_MANIFEST.csv", True, ""),
    ("S0_PLACEHOLDER_OUTPUT_MAP.csv", True, ""),
    ("S1_AUTHORIZATION_AND_DECISIONS.md", True, ""),
    ("RAW_FREEZE_MANIFEST.json", True, ""),
]


def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a],
                          capture_output=True, text=True).stdout.strip()


def sha(p: Path) -> str:
    h = hashlib.sha256()
    if p.is_dir():
        for f in sorted(p.rglob("*")):
            if f.is_file():
                h.update(f.name.encode()); h.update(f.read_bytes())
    else:
        h.update(p.read_bytes())
    return h.hexdigest()


def build_readme(present, commit, branch):
    acc = json.loads((OUTD / "07_SIM1_ACCEPTANCE_REPORT.json").read_text()) \
        if (OUTD / "07_SIM1_ACCEPTANCE_REPORT.json").exists() else {"criteria": []}
    npass = sum(c["pass"] is True for c in acc["criteria"])
    nfail = sum(c["pass"] is False for c in acc["criteria"])
    L = [
        "# cT2I Simulation-Only Result Package", "",
        f"**Release tag:** `{AUTHORITATIVE_TAG}` — quote this when citing the "
        "package; it is the stable identifier.  ",
        f"**Repository:** {git('remote', 'get-url', 'origin')}  ",
        f"AUTHORITATIVE COMMIT: `{commit}`  ",
        f"**Branch:** `{branch}`  ",
        "The repository, branch and annotated tag above are the authoritative "
        "identifiers. The commit SHA is stamped by `scripts/stamp_provenance.py` "
        "after the commit exists, because a file inside a commit cannot carry "
        "that commit's own SHA at write time.  ",
        f"**Built:** {datetime.now(timezone.utc).isoformat()}  ",
        "**Scope:** SIMULATION ONLY — real-data models run: 0, real-data files "
        "modified: 0, GPU hours: 0.", "",
        "## Start here", "",
        "1. `20_RESULT_HANDOFF_MEMO.md` — what was run, what passed, where "
        "everything is, and the open decisions.",
        "2. `19_VALIDATION_REPORT.md` — every deviation from the plan and every "
        "stated limitation.",
        "3. `11_SIM1_TABLES/TabS2.csv` — acceptance criteria, one row each.", "",
        f"**Acceptance: {npass} passed, {nfail} failed.**", "",
        "## One thing that will mislead you if you skip it", "",
        "Where the population Bayes-on-Z risk is not identified (hash encoders "
        "outside the enumerable cells), **both** `representation_loss` and "
        "`learner_shortfall` are NULL, because both require R_Bayes(Z). Only "
        "`total_excess_risk` survives there. **A blank is not a zero.** Those are "
        "the encoders the manuscript indicts, so reading a blank as \"no loss\" "
        "would invert the claim. Every row carries `theoretical_gap_status`.", "",
        "## What is NOT in here", "",
        "No manuscript prose. The plan assigns the abstract, Results, Discussion "
        "and Conclusions to the advisor; this package supplies validated numbers, "
        "figures and tables only.", "",
        "## Contents", "", "| file | present | sha256 (first 16) | note |",
        "|---|---|---|---|",
    ]
    for name, req, note in REQUIRED:
        p = OUTD / name
        ok = p.exists()
        if name == "00_README.md":
            # Self-reference: this table is built BEFORE the README it lives in
            # is written, so any hash printed here is the hash of the PREVIOUS
            # build and can never be right. Same bug class as R15 in
            # PACKAGE_SHA256.json (post-review finding 2). The authoritative
            # hash of this file is in PACKAGE_SHA256SUMS.txt, written after it.
            L.append(f"| `{name}` | yes | (self \u2014 see "
                     f"PACKAGE_SHA256SUMS.txt) | {note} |")
            continue
        L.append(f"| `{name}` | {'yes' if ok else ('MISSING' if req else 'n/a')} | "
                 f"{sha(p)[:16] if ok else ''} | {note} |")
    L += ["", "## Reproducing every number", "",
          "```bash",
          "python3 scripts/run_sim1a_exact.py        # Simulation 1A, exact",
          "python3 scripts/run_sim1c_hash.py both    # Simulation 1C, exact + finite",
          "python3 scripts/run_sim1b_finite.py       # Simulation 1B (Option B)",
          "python3 scripts/run_sim2_reproduce.py     # Simulation 2 reproduction",
          "python3 scripts/run_sim1_summarize.py     # summary + acceptance",
          "python3 scripts/run_sim1_figures.py       # figures",
          "python3 scripts/run_sim1_tables.py        # tables",
          "python3 scripts/run_s1_reports.py         # validation report + memo",
          "```", "",
          "Seeds are a deterministic function of (component, block, replicate); "
          "the block excludes the contrasted factor so both arms of every "
          "within-DGP contrast share one parameter draw.", ""]
    (OUTD / "00_README.md").write_text("\n".join(L), encoding="utf-8")


def main() -> int:
    allow_partial = "--allow-partial" in sys.argv
    allow_unstamped = "--allow-unstamped" in sys.argv
    manifest_only = "--manifest-only" in sys.argv
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    commit = stamped_commit()
    if len(commit) != 40 or not all(c in "0123456789abcdef" for c in commit):
        if not allow_unstamped:
            print(f"provenance not stamped (full_commit_sha = {commit!r}).\n"
                  "Run scripts/stamp_provenance.py <full-sha> first, or pass "
                  "--allow-unstamped for a dry run.")
            return 1
        print(f"WARNING: building UNSTAMPED (full_commit_sha = {commit!r})")

    present = {n: (OUTD / n).exists() for n, _, _ in REQUIRED}
    build_readme(present, commit, branch)
    present["00_README.md"] = True

    missing = [n for n, req, _ in REQUIRED if req and not (OUTD / n).exists()]
    print(f"required files present: {sum(1 for n,r,_ in REQUIRED if r and (OUTD/n).exists())}"
          f"/{sum(1 for _,r,_ in REQUIRED if r)}")
    for m in missing:
        print(f"  MISSING: {m}")
    if missing and not allow_partial:
        print("\nREFUSING to build an incomplete package. "
              "Re-run after the missing steps, or pass --allow-partial.")
        return 1

    # ---- manifests FIRST, so the archive ships the manifest of its own payload
    files = package_files()
    manifest = {str(p.relative_to(OUTD.parent)): sha(p) for p in files}
    (OUTD / MANIFEST_SUMS).write_text(
        "".join(f"{h}  {rel}\n" for rel, h in manifest.items()), encoding="utf-8")
    (OUTD / MANIFEST_JSON).write_text(
        json.dumps(dict(commit=commit, branch=branch,
                        generated_utc=datetime.now(timezone.utc).isoformat(),
                        manifest_excludes=[MANIFEST_JSON],
                        also_excluded=[MANIFEST_SUMS],
                        excluded_note="raw/ inputs and *.log working files are "
                                      "not part of the package; neither "
                                      "manifest hashes itself or the other "
                                      "manifest",
                        n_files=len(manifest), files=manifest), indent=2),
        encoding="utf-8")
    print(f"wrote {MANIFEST_JSON} and {MANIFEST_SUMS} ({len(manifest)} hashed files)")

    zpath = REPO / f"simulation-results-ct2i-repaired_{commit}.zip"
    if manifest_only:
        print(f"--manifest-only: archive NOT built. It would be written to "
              f"{zpath.name}")
        print("verify with: python3 scripts/verify_package_checksums.py")
        return 0

    # ---- then the archive, which carries both manifests
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in files + [OUTD / MANIFEST_SUMS, OUTD / MANIFEST_JSON]:
            z.write(p, p.relative_to(OUTD.parent))
    print(f"\nwrote {zpath.name}  ({zpath.stat().st_size/2**20:.1f} MB, "
          f"{len(files) + 2} files: {len(files)} hashed + 2 manifests)")
    print("verify with: python3 scripts/verify_package_checksums.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
