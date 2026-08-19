"""Independent checksum verifier for the return package (Phase R, R15).

Deliberately shares NO code with scripts/build_return_package.py: it walks the
package itself, re-hashes every file, and compares against PACKAGE_SHA256.json
and PACKAGE_SHA256SUMS.txt. A verifier that imported the builder's helpers
would only prove the builder is self-consistent.

Checks
  1. every manifest entry matches the file on disk
  2. no package file is missing from the manifest
  3. ZERO self-entries: neither manifest hashes itself or the other manifest
  4. the manifest declares its exclusions ("manifest_excludes")
  5. the detached PACKAGE_SHA256SUMS.txt agrees with the JSON manifest exactly

Usage: verify_package_checksums.py [package_dir]
       (default: <repo>/simulation-results-ct2i; also works on an unzipped copy)
Exit code 0 only if every check passes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

MANIFEST_JSON = "PACKAGE_SHA256.json"
MANIFEST_SUMS = "PACKAGE_SHA256SUMS.txt"


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
    print("PACKAGE CHECKSUMS: " + (f"{match}/{total} MATCH" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
