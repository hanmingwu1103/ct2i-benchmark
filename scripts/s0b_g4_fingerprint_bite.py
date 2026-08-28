#!/usr/bin/env python3
"""Gate-4 (canonical partition fingerprint) bite proof on the frozen d=3 arm.

TERMINAL STATUS (2026-08-25)
----------------------------
The dense-signal M = 5, K = 4, d = 5 addendum was PERMANENTLY DISCONTINUED
BEFORE EXECUTION by the advisor.  addendum_run = false;
addendum_status = TERMINATED_BEFORE_EXECUTION; full addendum cells run: 0;
Phase A1 will never run.  Nothing here is pending, planned or awaiting
approval.  This script is retained ONLY as design-audit provenance; nothing it
measures is a study result.  Decision record:
simulation-results-ct2i/DENSE_ADDENDUM_DECISION.md

WHY THIS SCRIPT EXISTS
----------------------
`05b_SIM1B_REPLICATE_RESULTS.parquet` predates the `fiber_fingerprint` column
that gate G4 compares against, so on the only arm that exists G4 reads
`fingerprint_checked=0` and `G4_partition_fingerprint:NOT_EVALUATED`. The plain
`s0b_reference_gap_check.py --arm d3_frozen --stored [--inject-defect ...]`
commands therefore CANNOT produce a G4 count, and any record that quotes a G4
mismatch count beside those commands is quoting a number those commands do not
print.

This driver supplies the missing precondition explicitly and reproducibly: it
builds the stored fingerprint map from the CLEAN recomputed digests already
persisted in `S0B_REFERENCE_GAP_CHECK_d3_frozen.csv` — exactly what a conforming
A1 runner would have written, had A1 ever run — and injects it into `load_stored` in-process.
Everything else is the production checker, unmodified.

WHAT THIS IS NOT
----------------
This is NOT end-to-end evidence on real production output. G4's first real
evaluation is on Phase A1's own rows. Read its result as: correct, measured, and
obtained through a synthetic stand-in for a column no existing arm carries.

USAGE (an out-of-package --out-dir is MANDATORY)
-----------------------------------------------
    cd /Users/Eric/Desktop/114/ct2i-benchmark
    PYTHONPATH=src /Users/Eric/.pyenv/versions/3.11.9/bin/python3 \
      scripts/s0b_g4_fingerprint_bite.py --out-dir /tmp/g4_bite

Runtime about 30 s. Executes ZERO addendum cells, fits no learner, mutates no
source file, and refuses to write anywhere inside `simulation-results-ct2i/`.
Cited by `01B a0_1_verification.V12`.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PKG = REPO / "simulation-results-ct2i"
CLEAN_CSV = PKG / "S0B_REFERENCE_GAP_CHECK_d3_frozen.csv"
DEFECTS = ("none", "fiber_permute", "fiber_swap")
EXPECTED_CELLS = 624

sys.path[:0] = [str(REPO / "src"), str(REPO / "scripts")]
import s0b_reference_gap_check as S0B  # noqa: E402


def load_clean_fingerprints() -> dict:
    """The recomputed digests of the clean run: the conforming-runner stand-in."""
    clean = {}
    with open(CLEAN_CSV, newline="") as fh:
        for row in csv.DictReader(fh):
            key = (row["scenario_id"], int(row["replicate"]),
                   row["encoder"], row["width_label"] or "")
            clean[key] = row["recomputed_fiber_fingerprint"]
    if len(clean) != EXPECTED_CELLS or not all(clean.values()):
        raise SystemExit(
            f"expected {EXPECTED_CELLS} non-empty recomputed fingerprints in "
            f"{CLEAN_CSV.name}, found {len(clean)}")
    return clean


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--out-dir", type=Path, required=True,
                    help="directory for the per-defect CSVs; MUST be outside "
                         "simulation-results-ct2i/")
    ap.add_argument("--defect", choices=DEFECTS, action="append", default=None,
                    help="repeatable; default: all three")
    args = ap.parse_args(argv)

    out_dir = args.out_dir.resolve()
    if PKG == out_dir or PKG in out_dir.parents:
        ap.error("refusing to write a synthetic-fingerprint artefact into the "
                 "package directory; these CSVs are never frozen")
    out_dir.mkdir(parents=True, exist_ok=True)
    defects = tuple(args.defect) if args.defect else DEFECTS

    clean = load_clean_fingerprints()
    original_load_stored = S0B.load_stored

    def load_stored_with_fingerprints(arm):
        stored = original_load_stored(arm)
        injected = 0
        for key, value in stored.items():
            if key in clean:
                value["fiber_fingerprint"] = clean[key]
                injected += 1
        print(f"[driver] injected {injected} synthetic stored fingerprints "
              f"(source: {CLEAN_CSV.name}, column recomputed_fiber_fingerprint)")
        return stored

    S0B.load_stored = load_stored_with_fingerprints
    try:
        rc = 0
        for defect in defects:
            print("#" * 24, f"defect={defect}")
            rc |= S0B.run("d3_frozen", out_dir / f"g4_{defect}.csv",
                          defect, True, None)
    finally:
        S0B.load_stored = original_load_stored
    print("\n[driver] G4 is EVALUATED here only because the stored fingerprints "
          "are synthetic. A non-zero exit under an injected defect is the "
          "INTENDED outcome (the gate bit).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
