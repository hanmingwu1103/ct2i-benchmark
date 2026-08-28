"""Phase S1 step 12: assemble the return package.

SIMULATION ONLY. Builds 00_README.md from the frozen artefacts, verifies that
every file the plan's Part III requires is present (or explains its absence),
records a sha256 for each, and writes the ZIP.

Refuses to build a package that is missing a required file, so an incomplete
return cannot be handed over by accident.

00_README.md is NOT regenerated wholesale. Later phases add sections to it
(the Phase A0.1 deliverables index, for one) that this template knows nothing
about, and a template-driven rewrite deleted them silently. build_readme()
therefore regenerates ONLY the '## ' sections it authors, carries every other
section over verbatim, and raises ReadmeMergeError -- writing nothing -- if the
result would drop a single heading or downgrade the provenance stamp.

Phase R changes:
  * the checksum manifests are written BEFORE the archive is created, so the
    shipped manifest is never one build stale (that is why the manifest inside
    simulation-results-ct2i_3a37dd30.zip disagreed with its own payload);
  * PACKAGE_SHA256.json excludes itself and PACKAGE_SHA256SUMS.txt and records
    that exclusion explicitly, so no entry hashes the manifest that contains it;
  * a detached PACKAGE_SHA256SUMS.txt is emitted alongside it;
  * the ZIP carries the FULL 40-character commit SHA, read from the stamped
    02_ENVIRONMENT_AND_COMMIT.json rather than truncated from git HEAD.

Final release changes:
  * --final names the archive simulation-results-ct2i-final_<short-sha>.zip,
    the advisor's release naming. The Phase R name stays the default so the
    archives already in the repository root remain addressable by the rule that
    produced them, and so the rename is an explicit, recorded choice;
  * --skip-readme regenerates the manifests WITHOUT rewriting 00_README.md.
    It exists for the second manifest pass of the release: after the archive is
    built, the delivered FINAL_SIMULATION_HANDOFF.md is stamped with the
    archive's SHA-256, which makes the on-disk manifests stale and they must be
    rewritten. Re-rendering the README there would change nothing but its
    "Built:" timestamp, gratuitously diverging the delivered tree from the
    shipped archive, so that pass skips it.

Usage: build_return_package.py [--allow-partial] [--allow-unstamped]
                              [--manifest-only] [--overwrite-archive]
                              [--final] [--skip-readme]
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTD = REPO / "simulation-results-ct2i"

README_NAME = "00_README.md"
MANIFEST_JSON = "PACKAGE_SHA256.json"
MANIFEST_SUMS = "PACKAGE_SHA256SUMS.txt"
# Written by Phase A0.1, not by this script. It is hashed BY PACKAGE_SHA256.json
# (ruling D15: the package manifest is generated last), never the other way.
MANIFEST_A0_1 = "A0_1_DELIVERABLES_SHA256.json"
# Neither manifest may appear inside either manifest: a hash of the file that
# carries it can never be satisfied.
MANIFEST_EXCLUDES = [MANIFEST_JSON, MANIFEST_SUMS]
SHA_PLACEHOLDER = "PENDING_STAMP_SEE_PACKAGE_PROVENANCE"
# The one line scripts/stamp_provenance.py rewrites in 00_README.md.
STAMP_LINE = re.compile(r"^AUTHORITATIVE COMMIT: `([^`]*)`", re.M)
# Must match scripts/run_s1_reports.py AUTHORITATIVE_TAG: every metadata file
# has to name ONE authoritative tag (requirement R12). The Phase R tag is named
# beside it with its role stated, so the two can never be confused.
AUTHORITATIVE_TAG = "ct2i-simulations-v1.0"
SUPERSEDED_PHASE_R_TAG = "sim-only-s1-complete-v2"


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


class ReadmeMergeError(RuntimeError):
    """The README cannot be regenerated without losing content."""


def split_sections(text):
    """(preamble_lines, [(heading, section_lines), ...]), split on '## '.

    A section runs from one top-level '## ' heading to the next, so every '### '
    subheading, table and paragraph travels with the section that owns it.
    """
    lines = text.split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith("## ")]
    if not idx:
        return lines, []
    secs = []
    for j, i in enumerate(idx):
        end = idx[j + 1] if j + 1 < len(idx) else len(lines)
        secs.append((lines[i], lines[i:end]))
    return lines[:idx[0]], secs


def headings(text):
    return [l for l in text.split("\n") if l.startswith("#")]


def merge_readme(existing: str, rendered: str):
    """Regenerate only the sections this builder authors; keep the rest verbatim.

    Returns (merged_text, regenerated_headings, preserved_headings). Raises
    ReadmeMergeError -- and the caller writes nothing -- rather than emit a
    README that has lost content a later phase put there.
    """
    epre, esecs = split_sections(existing)
    rpre, rsecs = split_sections(rendered)
    for label, secs in (("on disk", esecs), ("from the template", rsecs)):
        heads = [h for h, _ in secs]
        dup = sorted({h for h in heads if heads.count(h) > 1})
        if dup:
            raise ReadmeMergeError(
                f"{README_NAME} {label} has duplicate section heading(s) "
                f"{dup}; the merge cannot tell which copy the builder owns.")
    rmap = dict(rsecs)
    out, regen, kept = list(rpre), [], []
    for h, body in esecs:            # existing order wins, so preserved
        if h in rmap:                # sections stay where their author put them
            out += rmap[h]
            regen.append(h)
        else:
            out += body
            kept.append(h)
    for h, body in rsecs:            # builder sections the file does not have yet
        if h not in regen:
            out += body
            regen.append(h)
    merged = "\n".join(out)

    lost = [h for h in headings(existing) if h not in headings(merged)]
    if lost:
        raise ReadmeMergeError(
            f"regenerating {README_NAME} would DROP {len(lost)} heading(s) the "
            f"builder did not author:\n    " + "\n    ".join(lost)
            + f"\n  The file on disk is {len(existing)} bytes; the merge would "
            f"leave {len(merged)}. Nothing was written.")
    for h, body in esecs:
        if h not in rmap and "\n".join(body) not in merged:
            raise ReadmeMergeError(
                f"section {h!r} was not carried over verbatim; refusing to "
                f"write a {README_NAME} whose preserved content was altered.")
    was, now = STAMP_LINE.search(existing), STAMP_LINE.search(merged)
    if was and re.fullmatch(r"[0-9a-f]{40}", was.group(1)) and not (
            now and re.fullmatch(r"[0-9a-f]{40}", now.group(1))):
        raise ReadmeMergeError(
            f"{README_NAME} carries the stamped commit {was.group(1)}, and the "
            f"regenerated header would replace it with "
            f"{now.group(1) if now else '(no AUTHORITATIVE COMMIT line)'}. Run "
            f"scripts/stamp_provenance.py <full-sha> first. Nothing was "
            f"written.")
    return merged, regen, kept


def render_readme(commit, branch) -> str:
    """The builder-authored sections only. Pure: returns text, writes nothing."""
    acc = json.loads((OUTD / "07_SIM1_ACCEPTANCE_REPORT.json").read_text()) \
        if (OUTD / "07_SIM1_ACCEPTANCE_REPORT.json").exists() else {"criteria": []}
    npass = sum(c["pass"] is True for c in acc["criteria"])
    nfail = sum(c["pass"] is False for c in acc["criteria"])
    L = [
        "# cT2I Simulation-Only Result Package", "",
        f"**Release tag:** `{AUTHORITATIVE_TAG}` — the final simulation release "
        "tag; quote this when citing the package, it is the stable identifier. "
        f"Superseded Phase R tag: `{SUPERSEDED_PHASE_R_TAG}` (the Phase R "
        "release, retained as history, not the current release).  ",
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
        "1. `FINAL_SIMULATION_HANDOFF.md` — the release report: identifiers, "
        "row counts, acceptance, resource use, limitations, and the exact files "
        "intended for manuscript insertion.",
        "2. `20_RESULT_HANDOFF_MEMO.md` — what was run, what passed, where "
        "everything is, and the open decisions.",
        "3. `19_VALIDATION_REPORT.md` — every deviation from the plan and every "
        "stated limitation.",
        "4. `11_SIM1_TABLES/TabS2.csv` — acceptance criteria, one row each.", "",
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
    return "\n".join(L)


def build_readme(present, commit, branch) -> None:
    """Write 00_README.md, preserving every section this builder did not write."""
    rendered = render_readme(commit, branch)
    p = OUTD / README_NAME
    if not p.exists():
        p.write_text(rendered, encoding="utf-8")
        print(f"{README_NAME}: created from the template "
              f"({len(rendered)} bytes)")
        return
    existing = p.read_text(encoding="utf-8")
    merged, regen, kept = merge_readme(existing, rendered)
    p.write_text(merged, encoding="utf-8")
    print(f"{README_NAME}: {len(regen)} builder section(s) regenerated, "
          f"{len(kept)} preserved verbatim"
          + (" (" + ", ".join(k.lstrip("# ") for k in kept) + ")" if kept else "")
          + f"; {len(existing)} -> {len(merged)} bytes")


def main() -> int:
    allow_partial = "--allow-partial" in sys.argv
    allow_unstamped = "--allow-unstamped" in sys.argv
    manifest_only = "--manifest-only" in sys.argv
    final = "--final" in sys.argv
    skip_readme = "--skip-readme" in sys.argv
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
    if skip_readme:
        print(f"--skip-readme: {README_NAME} left exactly as it is on disk")
    else:
        try:
            build_readme(present, commit, branch)
        except ReadmeMergeError as exc:
            print(f"REFUSING to rewrite {README_NAME}: {exc}\n"
                  f"  {README_NAME} is UNCHANGED and no package was built. Fix "
                  f"the cause above -- teach render_readme() the missing "
                  f"section, rename a duplicated heading, or stamp the commit "
                  f"-- and re-run.")
            return 1
    present[README_NAME] = True

    missing = [n for n, req, _ in REQUIRED if req and not (OUTD / n).exists()]
    print(f"required files present: {sum(1 for n,r,_ in REQUIRED if r and (OUTD/n).exists())}"
          f"/{sum(1 for _,r,_ in REQUIRED if r)}")
    for m in missing:
        print(f"  MISSING: {m}")
    if missing and not allow_partial:
        print("\nREFUSING to build an incomplete package. "
              "Re-run after the missing steps, or pass --allow-partial.")
        return 1

    zname = (f"simulation-results-ct2i-final_{commit[:8]}.zip" if final
             else f"simulation-results-ct2i-repaired_{commit}.zip")
    zpath = REPO / zname
    if zpath.exists() and not manifest_only \
            and "--overwrite-archive" not in sys.argv:
        print(f"REFUSING to overwrite the existing archive {zpath.name} "
              f"({zpath.stat().st_size/2**20:.1f} MB). An archive is named by "
              "its commit, and REPAIR_REPORT.md is stamped with that archive's "
              "sha256 and byte size, so replacing it in place silently "
              "invalidates the stamp. Move it aside, or pass "
              "--overwrite-archive if you really mean to replace it.")
        return 1

    # ---- manifests FIRST, so the archive ships the manifest of its own payload
    files = package_files()
    manifest = {str(p.relative_to(OUTD.parent)): sha(p) for p in files}
    (OUTD / MANIFEST_SUMS).write_text(
        "".join(f"{h}  {rel}\n" for rel, h in manifest.items()), encoding="utf-8")
    generated = datetime.now(timezone.utc).isoformat()
    (OUTD / MANIFEST_JSON).write_text(
        json.dumps(dict(commit=commit, branch=branch,
                        generated_utc=generated,
                        manifest_excludes=[MANIFEST_JSON],
                        also_excluded=[MANIFEST_SUMS],
                        excluded_note="raw/ inputs and *.log working files are "
                                      "not part of the package; neither "
                                      "manifest hashes itself or the other "
                                      "manifest",
                        n_files=len(manifest), files=manifest), indent=2),
        encoding="utf-8")
    print(f"wrote {MANIFEST_JSON} and {MANIFEST_SUMS} ({len(manifest)} hashed files)")

    # ---- ruling D15: the package manifest is generated LAST, so its entry for
    # the Phase A0.1 manifest is satisfiable. Checked, not assumed.
    a0 = OUTD / MANIFEST_A0_1
    if a0.exists():
        key = f"{OUTD.name}/{MANIFEST_A0_1}"
        a0_gen = json.loads(a0.read_text(encoding="utf-8")).get(
            "generated_utc", "")
        if key not in manifest:
            print(f"FAIL: {MANIFEST_A0_1} is not hashed by {MANIFEST_JSON}; the "
                  "A0.1 deliverables would ship unprotected.")
            return 1
        if a0_gen > generated:
            print(f"FAIL (D15): {MANIFEST_A0_1} ({a0_gen}) is NEWER than "
                  f"{MANIFEST_JSON} ({generated}); the package manifest must be "
                  "generated last, or its entry for the A0.1 manifest is "
                  "already stale. Regenerate the A0.1 manifest, then re-run.")
            return 1
        print(f"D15 ordering: {MANIFEST_JSON} generated last ({generated}) and "
              f"hashes {MANIFEST_A0_1} ({a0_gen})")
    else:
        print(f"NOTE: {MANIFEST_A0_1} absent; A0.1 deliverables not covered.")

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
