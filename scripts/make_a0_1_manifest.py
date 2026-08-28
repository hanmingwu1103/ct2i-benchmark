"""Regenerate simulation-results-ct2i/A0_1_DELIVERABLES_SHA256.json.

The Phase A0.1 manifest was produced ad hoc, in a scratchpad, and was never
committed as a script. Its own prose says so, and says that its hashes were
taken BEFORE the termination pass rewrote several of the documents it covers --
so it shipped knowingly stale, on the promise that ruling D15's final
regeneration would supersede it. This script is that regeneration, and it is
committed so the values are re-derivable rather than re-typed.

Two invariants it enforces, both by assertion rather than by convention:

  1. SELF-REFERENCE. No entry may name any of the three manifests. A manifest
     entry for the file that carries it can never be satisfied -- this package
     has shipped a self-hashing file three times. The file list is enumerated
     LITERALLY below; no glob can sweep a manifest in. assert_no_self_entries()
     re-checks the literal list before anything is hashed and raises
     SelfEntryError if it ever regresses. Prove it fires with
     `make_a0_1_manifest.py --prove-self-entry-guard`, which feeds the guard a
     poisoned list and reports whether it refused.

  2. STAMP INVARIANCE. No listed file may contain a stamp placeholder token,
     so scripts/stamp_provenance.py cannot change any hash here and this
     manifest is valid both before and after stamping. That is why
     00_README.md is excluded: it carries the AUTHORITATIVE COMMIT token and
     is covered by PACKAGE_SHA256.json instead, which ruling D15 regenerates
     last. scripts/verify_package_checksums.py is excluded because hashing the
     instrument inside the thing it checks adds no independent assurance.

Ordering: this manifest must be written BEFORE PACKAGE_SHA256.json, which
hashes it. build_return_package.py and verify_package_checksums.py both check
that ordering against generated_utc and fail if it is violated.

Usage: make_a0_1_manifest.py <full-40-char-sha>
       make_a0_1_manifest.py --prove-self-entry-guard
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTD = REPO / "simulation-results-ct2i"
MANIFEST = OUTD / "A0_1_DELIVERABLES_SHA256.json"

MANIFEST_NAMES = ("A0_1_DELIVERABLES_SHA256.json", "PACKAGE_SHA256.json",
                  "PACKAGE_SHA256SUMS.txt")
STAMP_TOKENS = ("PENDING_STAMP_SEE_PACKAGE_PROVENANCE",
                "PENDING_ZIP_SHA256_SEE_SHA256SUMS",
                "PENDING_ZIP_BYTES_SEE_SHA256SUMS")

# Enumerated literally, repository-root relative. Eleven in-package A0.1
# deliverables and nine scripts/tests that live outside the package -- which is
# why this is a second manifest at all: every key in PACKAGE_SHA256.json is
# resolved relative to the package directory.
FILES = [
    "simulation-results-ct2i/01B_ADDENDUM_ADVISOR_RULINGS.yaml",
    "simulation-results-ct2i/RAW_FREEZE_MANIFEST_ADDENDUM.json",
    "simulation-results-ct2i/S0B_ADVISOR_RULING_IMPLEMENTATION_REPORT.md",
    "simulation-results-ct2i/S0B_COUNCIL_REVIEW.md",
    "simulation-results-ct2i/S0B_D13_PREMISE_INVESTIGATION.md",
    "simulation-results-ct2i/S0B_FINAL_GATE_REPORT.md",
    "simulation-results-ct2i/S0B_NORMALIZED_CONTRAST_SENSITIVITY.md",
    "simulation-results-ct2i/S0B_REFERENCE_GAP_CHECK_d3_frozen.csv",
    "simulation-results-ct2i/S0B_REFERENCE_IMPLEMENTATION_TEST_REPORT.md",
    "simulation-results-ct2i/S0B_RESOURCE_CONFIRMATION.csv",
    "simulation-results-ct2i/S0B_RUNNER_TEST_REPORT.md",
    "scripts/run_sim1b_dense_addendum.py",
    "scripts/s0b_d13_premise_probe.py",
    "scripts/s0b_g4_fingerprint_bite.py",
    "scripts/s0b_normalized_contrast_sensitivity.py",
    "scripts/s0b_reference_gap_check.py",
    "scripts/verify_raw_freeze_manifest_addendum.py",
    "tests/test_a0_1_reconciliation.py",
    "tests/test_a0_2_defect_closure.py",
    "tests/test_a1_runner_smoke.py",
]


class SelfEntryError(RuntimeError):
    """A manifest was about to hash itself or one of its siblings."""


def assert_no_self_entries(paths) -> None:
    """Refuse a file list containing any manifest. Pure; raises or returns."""
    bad = sorted({p for p in paths if Path(p).name in MANIFEST_NAMES})
    if bad:
        raise SelfEntryError(
            f"self-entry refused: {bad} -- a manifest may never hash itself or "
            f"either sibling manifest; the entry could never be satisfied.")


def assert_stamp_invariant(paths) -> None:
    """Refuse a file that carries a stamp token; its hash would not be stable."""
    bad = []
    for rel in paths:
        raw = (REPO / rel).read_bytes()
        if any(tok.encode() in raw for tok in STAMP_TOKENS):
            bad.append(rel)
    if bad:
        raise RuntimeError(
            f"stamp-sensitive file(s) in a stamp-invariant manifest: {bad}")


def sha256(rel: str) -> str:
    return hashlib.sha256((REPO / rel).read_bytes()).hexdigest()


def build(sha: str) -> dict:
    assert_no_self_entries(FILES)
    missing = [f for f in FILES if not (REPO / f).exists()]
    if missing:
        raise FileNotFoundError(f"listed but absent: {missing}")
    assert_stamp_invariant(FILES)
    branch = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    return {
        "manifest_id": "A0_1_DELIVERABLES_SHA256",
        "phase": "A0.1",
        "phase_verdict": "CLOSED — THE ADDENDUM WAS TERMINATED BEFORE EXECUTION",
        "addendum_run": False,
        "addendum_status": "TERMINATED_BEFORE_EXECUTION",
        "addendum_cells_run": 0,
        "terminal_status_note":
            "The dense-signal M = 5, K = 4, d = 5 addendum was PERMANENTLY "
            "DISCONTINUED BEFORE EXECUTION by the advisor on 2026-08-25. Phase "
            "A0.1 is not blocked, not pending and not awaiting approval: it is "
            "closed, and Phase A1 will never run. The files listed below are "
            "retained ONLY as methodological audit records (design-audit "
            "provenance); none of their projected, exploratory or measured "
            "contrasts is a study result. Decision record: "
            "simulation-results-ct2i/DENSE_ADDENDUM_DECISION.md",
        "hashes_are_current":
            "REGENERATED after the termination pass and after the release "
            "stamp, per ruling D15 (checksum manifests last). The superseded "
            "generation of this manifest, dated 2026-08-24T17:26:22Z, carried "
            "the PRE-termination hashes of eleven of these files and said so; "
            "those values are history and every value below supersedes them. A "
            "mismatch against disk now is a real mismatch, not a dating "
            "artefact.",
        "purpose":
            "Integrity coverage for every Phase A0.1 deliverable. Before this "
            "manifest existed, PACKAGE_SHA256.json covered no 01B_* or S0B_* "
            "file and no A0.1 script or test, so nothing produced in this "
            "phase was integrity-protected.",
        "why_a_second_manifest":
            "Nine of the twenty entries are scripts and test modules outside "
            "simulation-results-ct2i/. Every key in PACKAGE_SHA256.json is "
            "resolved relative to the package directory by "
            "verify_package_checksums.in_package(), so a 'scripts/...' key "
            "there would resolve inside the package and report MISSING ON DISK "
            "forever. Keys here are relative to the REPOSITORY ROOT. "
            "scripts/verify_package_checksums.py verifies both manifests and "
            "exits non-zero if either disagrees with disk.",
        "commit": sha,
        "branch": branch,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "path_root": "repository root",
        "generator_script":
            "scripts/make_a0_1_manifest.py (committed; shares no code with "
            "scripts/verify_package_checksums.py, which re-derives every value "
            "independently)",
        "manifest_excludes": list(MANIFEST_NAMES),
        "also_excluded": [
            "simulation-results-ct2i/00_README.md",
            "simulation-results-ct2i/FINAL_SIMULATION_HANDOFF.md",
            "scripts/verify_package_checksums.py",
        ],
        "excluded_note":
            "00_README.md and FINAL_SIMULATION_HANDOFF.md are excluded because "
            "they carry Option A stamp tokens (AUTHORITATIVE COMMIT, and for "
            "the handoff the archive's own SHA-256 and byte size), which "
            "scripts/stamp_provenance.py rewrites after the commit and the "
            "archive exist; their hashes therefore change at stamp time. Both "
            "stay covered by PACKAGE_SHA256.json, which is regenerated after "
            "every stamp. Keeping them out makes this manifest stamp-invariant. "
            "scripts/verify_package_checksums.py is excluded because it is the "
            "instrument that checks this manifest; hashing the checker inside "
            "the thing it checks would add no independent assurance.",
        "self_reference_guard":
            "The file list is enumerated literally in "
            "scripts/make_a0_1_manifest.py; no glob is used, so no pattern can "
            "sweep in the manifest being written. "
            "make_a0_1_manifest.assert_no_self_entries() raises SelfEntryError "
            "on any entry whose basename is one of "
            f"{list(MANIFEST_NAMES)} before anything is hashed (prove it with "
            "`python3 scripts/make_a0_1_manifest.py "
            "--prove-self-entry-guard`), and "
            "scripts/verify_package_checksums.py re-asserts self-entries == 0 "
            "on every run and FAILS if it is not.",
        "stamp_token_policy":
            "VALID PRE- AND POST-STAMP. assert_stamp_invariant() reads every "
            "listed file and refuses to write this manifest if any of them "
            "contains PENDING_STAMP_SEE_PACKAGE_PROVENANCE, "
            "PENDING_ZIP_SHA256_SEE_SHA256SUMS or "
            "PENDING_ZIP_BYTES_SEE_SHA256SUMS, so scripts/stamp_provenance.py "
            "cannot change any hash here. PACKAGE_SHA256.json is the manifest "
            "that IS stamp-sensitive; per ruling D15 it is regenerated last.",
        "n_files": len(FILES),
        "files": {rel: sha256(rel) for rel in FILES},
    }


def prove_guard() -> int:
    """Demonstrate that the self-entry assertion actually fires."""
    for poison in MANIFEST_NAMES:
        probe = FILES[:1] + [f"simulation-results-ct2i/{poison}"]
        try:
            assert_no_self_entries(probe)
        except SelfEntryError as exc:
            print(f"GUARD FIRED for {poison}: {exc}")
        else:
            print(f"GUARD DID NOT FIRE for {poison} -- THIS IS A DEFECT")
            return 1
    assert_no_self_entries(FILES)
    print(f"guard silent on the real {len(FILES)}-entry list, as it must be")
    print("SELF-ENTRY GUARD: PASS")
    return 0


def main() -> int:
    if "--prove-self-entry-guard" in sys.argv:
        return prove_guard()
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if len(args) != 1 or not re.fullmatch(r"[0-9a-f]{40}", args[0].strip().lower()):
        print(__doc__)
        return 2
    man = build(args[0].strip().lower())
    MANIFEST.write_text(json.dumps(man, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"wrote {MANIFEST.relative_to(REPO)}: {man['n_files']} entries, "
          f"commit {man['commit']}, generated {man['generated_utc']}")
    print("self-entries: 0 (asserted before hashing)")
    print("stamp-sensitive entries: 0 (asserted before writing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
