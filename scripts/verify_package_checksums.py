"""Independent checksum verifier for the return package (Phase R, R15).

Deliberately shares NO code with scripts/build_return_package.py: it walks the
package itself, re-hashes every file, and compares against PACKAGE_SHA256.json
and PACKAGE_SHA256SUMS.txt. A verifier that imported the builder's helpers
would only prove the builder is self-consistent.

Checks, for the package manifest PACKAGE_SHA256.json
  1. every manifest entry matches the file on disk
  2. no package file is missing from the manifest
  3. ZERO self-entries: neither manifest hashes itself or the other manifest
  4. the manifest declares its exclusions ("manifest_excludes")
  5. the detached PACKAGE_SHA256SUMS.txt agrees with the JSON manifest exactly

and, for the Phase A0.1 manifest A0_1_DELIVERABLES_SHA256.json (Phase A0.1)
  6. every A0.1 entry matches the file on disk
  7. ZERO self-entries: it hashes neither itself nor either package manifest
  8. it declares its exclusions ("manifest_excludes")
  9. no in-package A0.1 deliverable (01B_*, S0B_*, RAW_FREEZE_MANIFEST_ADDENDUM)
     is missing from it
 10. ruling D15's ordering: PACKAGE_SHA256.json was generated AFTER the A0.1
     manifest it hashes, so its entry for that manifest is satisfiable

Why a SECOND manifest rather than more entries in PACKAGE_SHA256.json: nine of
the twenty A0.1 files are scripts and test modules that live OUTSIDE
simulation-results-ct2i/, and every key in PACKAGE_SHA256.json is resolved by
in_package() relative to the package directory. A "scripts/..." key there would
resolve to a path inside the package and report MISSING ON DISK forever. The
A0.1 manifest therefore resolves its keys against the REPOSITORY ROOT, and this
verifier covers both.

This verifier is deliberately absent from both manifests. An instrument that
hashed itself in the manifest it checks would add no independent assurance.

Usage: verify_package_checksums.py [package_dir]
       (default: <repo>/simulation-results-ct2i; also works on an unzipped copy,
       where the A0.1 out-of-package deliverables are reported as SKIPPED
       because scripts/ and tests/ are not part of the shipped package)
Exit code 0 only if every check that could run passes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

MANIFEST_JSON = "PACKAGE_SHA256.json"
MANIFEST_SUMS = "PACKAGE_SHA256SUMS.txt"
MANIFEST_A0_1 = "A0_1_DELIVERABLES_SHA256.json"
# Any file whose name is one of these may never appear as an entry in any of
# them. Three separate releases of this package shipped a self-hashing file.
ALL_MANIFESTS = (MANIFEST_JSON, MANIFEST_SUMS, MANIFEST_A0_1)
# In-package A0.1 deliverables are recognised by name, so a future S0B_*
# report that is added but never hashed is reported instead of ignored.
A0_1_INPACKAGE_PREFIXES = ("01B_", "S0B_", "RAW_FREEZE_MANIFEST_ADDENDUM")


def in_package(rel: str) -> Path:
    """Manifest keys are relative to the package's PARENT; strip that prefix.

    Comparing package-RELATIVE paths (not basenames) means two same-named files
    in different subdirectories can never mask one another (post-review 5b).
    """
    parts = Path(rel).parts
    return Path(*parts[1:]) if len(parts) > 1 else Path(rel)


def sha(p: Path) -> str:
    h = hashlib.sha256()
    if p.is_dir():
        for f in sorted(p.rglob("*")):
            if f.is_file():
                h.update(f.name.encode())
                h.update(f.read_bytes())
    else:
        h.update(p.read_bytes())
    return h.hexdigest()


def verify_a0_1(outd: Path) -> tuple[bool, str]:
    """Checks 6-9 for A0_1_DELIVERABLES_SHA256.json. Returns (ok, summary).

    Keys are REPOSITORY-ROOT relative, because nine of the twenty A0.1 files
    are scripts and tests outside the package. They are resolved against the
    package's parent, which is the repository root in a checkout. In an unzipped
    copy that parent holds no scripts/ or tests/, so those entries are reported
    as SKIPPED rather than failing a package that was never meant to carry them.
    """
    mp = outd / MANIFEST_A0_1
    if not mp.exists():
        return False, f"A0.1 CHECKSUMS: FAIL ({MANIFEST_A0_1} not found)"
    man = json.loads(mp.read_text(encoding="utf-8"))
    files = man.get("files", {})
    root = outd.parent
    print(f"\nA0.1 manifest: {mp.name}")
    print(f"A0.1 entries: {len(files)}")

    # 7. self-entries -- an entry for any manifest can never be satisfiable
    selfs = [k for k in files if Path(k).name in ALL_MANIFESTS]
    print(f"A0.1 self-entries: {len(selfs)}" + (f"  -> {selfs}" if selfs else ""))

    # 8. declared exclusions
    excl = man.get("manifest_excludes")
    ok_excl = isinstance(excl, list) and MANIFEST_A0_1 in excl
    print(f"A0.1 manifest_excludes declared: {'yes' if ok_excl else 'NO'} ({excl!r})")

    # 6. entries vs disk
    in_repo = (root / "scripts").is_dir() and (root / "tests").is_dir()
    match = mismatch = absent = skipped = 0
    for rel, want in sorted(files.items()):
        f = root / rel
        if not f.exists():
            if not in_repo and not rel.startswith("simulation-results-ct2i/"):
                skipped += 1
                continue
            print(f"  MISSING ON DISK: {rel}")
            absent += 1
            continue
        got = sha(f)
        if got == want:
            match += 1
        else:
            mismatch += 1
            print(f"  MISMATCH: {rel}\n    manifest {want}\n    on disk  {got}")
    if skipped:
        print(f"  SKIPPED (out-of-package, not present in an unzipped copy): {skipped}")

    # 9. in-package A0.1 deliverables that the manifest forgot
    listed = set(files)
    unlisted = sorted(
        f"simulation-results-ct2i/{q.name}" for q in outd.iterdir()
        if q.is_file() and q.name.startswith(A0_1_INPACKAGE_PREFIXES)
        and f"simulation-results-ct2i/{q.name}" not in listed)
    for u in unlisted:
        print(f"  NOT IN A0.1 MANIFEST: {u}")

    # 10. D15 ordering. PACKAGE_SHA256.json hashes this manifest, so it must
    # have been written afterwards; otherwise its entry is already stale.
    ordered = True
    pkg = outd / MANIFEST_JSON
    if pkg.exists():
        pman = json.loads(pkg.read_text(encoding="utf-8"))
        if f"{outd.name}/{MANIFEST_A0_1}" in pman.get("files", {}):
            ordered = pman.get("generated_utc", "") >= man.get("generated_utc", "")
            print(f"D15 ordering (package manifest generated last): "
                  f"{'yes' if ordered else 'NO -- package manifest is older'}")

    total = len(files) - skipped
    ok = (mismatch == 0 and absent == 0 and not unlisted and not selfs
          and ok_excl and ordered and total > 0)
    line = ("A0.1 CHECKSUMS: "
            + (f"{match}/{total} MATCH" + (f" ({skipped} skipped)" if skipped else "")
               if ok else "FAIL"))
    return ok, line


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    outd = Path(args[0]).resolve() if args else \
        Path(__file__).resolve().parents[1] / "simulation-results-ct2i"
    mj = outd / MANIFEST_JSON
    if not mj.exists():
        print(f"FAIL: {MANIFEST_JSON} not found in {outd}")
        return 1
    man = json.loads(mj.read_text(encoding="utf-8"))
    files = man.get("files", {})
    print(f"package: {outd}")
    print(f"manifest entries: {len(files)}")

    # 3. self-entries
    # A manifest may never hash ITSELF or its own detached twin. It MAY hash
    # A0_1_DELIVERABLES_SHA256.json, which is written BEFORE it (ruling D15:
    # the package manifest is generated last), so that hash is satisfiable and
    # tampering with the A0.1 manifest is detected. Check 10 enforces the order.
    self_entries = [k for k in files
                    if Path(k).name in (MANIFEST_JSON, MANIFEST_SUMS)]
    print(f"self-entries: {len(self_entries)}"
          + (f"  -> {self_entries}" if self_entries else ""))

    # 4. declared exclusions
    excl = man.get("manifest_excludes")
    ok_excl = isinstance(excl, list) and MANIFEST_JSON in excl
    print(f"manifest_excludes declared: {'yes' if ok_excl else 'NO'} ({excl!r})")

    # 1. entries vs disk
    match = mismatch = absent = 0
    for rel, want in sorted(files.items()):
        # resolved by package-relative path, so an unzipped copy under a
        # different parent directory verifies identically
        p = outd / in_package(rel)
        if not p.exists():
            print(f"  MISSING ON DISK: {rel}")
            absent += 1
            continue
        got = sha(p)
        if got == want:
            match += 1
        else:
            mismatch += 1
            print(f"  MISMATCH: {rel}\n    manifest {want}\n    on disk  {got}")

    # 2. package files absent from the manifest
    listed = {in_package(r) for r in files}
    unlisted = []
    for p in sorted(outd.rglob("*")):
        if not p.is_file():
            continue
        if "/raw/" in str(p) or p.name.endswith(".log"):
            continue
        if p.name in (MANIFEST_JSON, MANIFEST_SUMS) and p.parent == outd:
            continue
        if p.relative_to(outd) not in listed:
            unlisted.append(str(p.relative_to(outd)))
    for u in unlisted:
        print(f"  NOT IN MANIFEST: {u}")

    # 5. detached sums file
    ms = outd / MANIFEST_SUMS
    sums_ok = ms.exists()
    if sums_ok:
        parsed = {}
        for line in ms.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            h, _, rel = line.partition("  ")
            parsed[rel] = h
        sums_ok = parsed == files
        print(f"detached {MANIFEST_SUMS}: "
              f"{'agrees with the JSON manifest' if sums_ok else 'DISAGREES'} "
              f"({len(parsed)} lines)")
    else:
        print(f"detached {MANIFEST_SUMS}: MISSING")

    total = len(files)
    print(f"\n{match}/{total} MATCH, {mismatch} mismatch, {absent} missing, "
          f"{len(unlisted)} unlisted, self-entries: {len(self_entries)}")
    ok = (mismatch == 0 and absent == 0 and not unlisted
          and not self_entries and ok_excl and sums_ok and total > 0)
    pkg_line = "PACKAGE CHECKSUMS: " + (f"{match}/{total} MATCH" if ok else "FAIL")
    print(pkg_line)

    ok_a0, a0_line = verify_a0_1(outd)
    print("\n" + pkg_line)
    print(a0_line)
    print("ALL CHECKSUMS: " + ("PASS" if (ok and ok_a0) else "FAIL"))
    return 0 if (ok and ok_a0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
