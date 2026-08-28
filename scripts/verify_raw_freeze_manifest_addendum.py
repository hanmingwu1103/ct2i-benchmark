"""Independent verifier for RAW_FREEZE_MANIFEST_ADDENDUM.json (D15).

Deliberately shares NO code with the ad hoc generator that produced the
addendum manifest: it walks the files on disk, re-hashes them itself, and
compares against the manifest and against the original RAW_FREEZE_MANIFEST.json.
A verifier that imported the generator's helpers would only prove the
generator is self-consistent (same failure mode scripts/verify_package_checksums.py
was written to avoid for the return package).

Checks
  1. every hashed entry (raw_csv_top_level + frozen_result_outputs_carried_forward)
     matches the file on disk (SHA-256, byte size)
  2. every entry carried forward from RAW_FREEZE_MANIFEST.json still matches
     RAW_FREEZE_MANIFEST.json's own hash -- i.e. the addendum manifest really is
     a strict superset, not a re-statement with drifted values
  3. every top-level raw/*.csv file on disk is listed (nothing unlisted, nothing
     missing) -- glob is re-derived from disk, never copied from the manifest
  4. pending_a1_addendum_outputs entries carry the terminal status
     TERMINATED_BEFORE_EXECUTION_NEVER_PRODUCED and NO sha256 key (a real hash
     there would mean someone invented a placeholder hash, which is explicitly
     prohibited). NOTE: the addendum was PERMANENTLY DISCONTINUED BEFORE
     EXECUTION on 2026-08-25 -- full addendum cells run: 0 -- so those three
     declared outputs will never exist and no hash will ever be filled in for
     them. The category key keeps its historical name; its contents are
     design-audit provenance, not pending work. See
     simulation-results-ct2i/DENSE_ADDENDUM_DECISION.md.
  5. ZERO self-entries: the manifest must not contain any entry whose relative
     path or expected_relative_path resolves to the manifest's own filename

Usage: verify_raw_freeze_manifest_addendum.py [simulation-results-ct2i dir]
       (default: <repo>/simulation-results-ct2i)
Exit code 0 only if every check passes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ADDENDUM_MANIFEST = "RAW_FREEZE_MANIFEST_ADDENDUM.json"
OLD_MANIFEST = "RAW_FREEZE_MANIFEST.json"


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    resd = Path(args[0]).resolve() if args else \
        Path(__file__).resolve().parents[1] / "simulation-results-ct2i"

    am_path = resd / ADDENDUM_MANIFEST
    om_path = resd / OLD_MANIFEST
    if not am_path.exists():
        print(f"FAIL: {ADDENDUM_MANIFEST} not found in {resd}")
        return 1
    if not om_path.exists():
        print(f"FAIL: {OLD_MANIFEST} not found in {resd}")
        return 1

    addendum = json.loads(am_path.read_text(encoding="utf-8"))
    old = json.loads(om_path.read_text(encoding="utf-8"))
    cats = addendum.get("categories", {})
    raw_csv = cats.get("raw_csv_top_level", {})
    carried = cats.get("frozen_result_outputs_carried_forward", {})
    pending = cats.get("pending_a1_addendum_outputs", {})

    print(f"package: {resd}")
    print(f"addendum manifest entries: raw_csv_top_level={len(raw_csv)}, "
          f"frozen_result_outputs_carried_forward={len(carried)}, "
          f"pending_a1_addendum_outputs={len(pending)}")
    print(f"addendum status: {addendum.get('addendum_status', 'UNDECLARED')} "
          f"(addendum_run={addendum.get('addendum_run')}) -- the "
          f"{len(pending)} declared A1 outputs will never exist")

    matched = mismatched = missing = 0
    self_entries = []

    def own_name_hit(rel: str) -> bool:
        return Path(rel).name == ADDENDUM_MANIFEST

    # --- 1 & 5: raw_csv_top_level ---
    for name, meta in sorted(raw_csv.items()):
        rel = meta["relative_path"]
        if own_name_hit(rel):
            self_entries.append(rel)
            continue
        p = resd / rel
        if not p.exists():
            print(f"  MISSING ON DISK: {rel}")
            missing += 1
            continue
        got = sha256_of(p)
        got_size = p.stat().st_size
        if got == meta["sha256"] and got_size == meta["size_bytes"]:
            matched += 1
        else:
            mismatched += 1
            print(f"  MISMATCH: {rel}\n    manifest sha256={meta['sha256']} size={meta['size_bytes']}\n"
                  f"    on disk  sha256={got} size={got_size}")

    # --- 1, 2 & 5: frozen_result_outputs_carried_forward, cross-checked vs OLD manifest ---
    superset_ok = True
    for name, meta in sorted(carried.items()):
        rel = meta["relative_path"]
        if own_name_hit(rel):
            self_entries.append(rel)
            continue
        p = resd / rel
        if not p.exists():
            print(f"  MISSING ON DISK: {rel}")
            missing += 1
            superset_ok = False
            continue
        got = sha256_of(p)
        if got != meta["sha256"]:
            mismatched += 1
            superset_ok = False
            print(f"  MISMATCH (addendum manifest): {rel}")
        else:
            matched += 1
        if name not in old:
            print(f"  NOT A SUPERSET: {name} carried forward but absent from {OLD_MANIFEST}")
            superset_ok = False
            continue
        if old[name]["sha256"] != got:
            print(f"  SUPERSET DRIFT: {name} does not match {OLD_MANIFEST}'s own hash")
            superset_ok = False

    old_covered = sum(1 for name in old if name in carried)
    superset_ok = superset_ok and (old_covered == len(old))
    print(f"superset check: {old_covered}/{len(old)} old-manifest entries carried forward "
          f"with matching hash -> {'PASS' if superset_ok else 'FAIL'}")

    # --- 3: every top-level raw/*.csv on disk is listed ---
    raw_dir = resd / "raw"
    on_disk = {p.name for p in raw_dir.glob("*.csv")} if raw_dir.is_dir() else set()
    listed = {meta["relative_path"].split("/")[-1] for meta in raw_csv.values()}
    unlisted = sorted(on_disk - listed)
    phantom = sorted(listed - on_disk)
    for u in unlisted:
        print(f"  ON DISK BUT NOT IN MANIFEST: raw/{u}")
    for u in phantom:
        print(f"  IN MANIFEST BUT NOT ON DISK: raw/{u}")

    # --- 4: terminated addendum entries must be spec-only, never hashed ---
    # The addendum was TERMINATED BEFORE EXECUTION (2026-08-25): these three
    # declared outputs will never be produced, so a hash on any of them would be
    # fabricated. The historical "PENDING_A1" token is still accepted so that an
    # older copy of the manifest verifies, but the terminal token is the one the
    # shipped manifest carries.
    TERMINAL_STATUS = "TERMINATED_BEFORE_EXECUTION_NEVER_PRODUCED"
    bad_pending = []
    for name, meta in sorted(pending.items()):
        rel = meta.get("expected_relative_path", name)
        if own_name_hit(rel):
            self_entries.append(rel)
        if meta.get("status") not in (TERMINAL_STATUS, "PENDING_A1"):
            bad_pending.append((name, "missing/incorrect status"))
        if "sha256" in meta:
            bad_pending.append((name, "carries a sha256 -- fabricated hash for a nonexistent file"))
    for name, why in bad_pending:
        print(f"  BAD PENDING ENTRY: {name} ({why})")

    # --- 5: self-reference guard, final tally ---
    print(f"self-entries: {len(self_entries)}" + (f"  -> {self_entries}" if self_entries else ""))
    assert not self_entries, "self-reference guard violated: manifest references its own filename"

    total = len(raw_csv) + len(carried)
    ok = (mismatched == 0 and missing == 0 and not unlisted and not phantom
          and not self_entries and not bad_pending and superset_ok and total > 0)

    print(f"\n{matched}/{total} MATCH, {mismatched} mismatched, {missing} missing, "
          f"{len(unlisted) + len(phantom)} unlisted, self-entries: {len(self_entries)}")
    print("RAW FREEZE MANIFEST ADDENDUM: " + (f"{matched}/{total} MATCH" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
