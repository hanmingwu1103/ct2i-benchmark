"""Stamp the authoritative commit SHA into the package metadata (Phase R, D1).

A file that lives inside commit C cannot contain C's own SHA at write time --
that is precisely how 00_README.md, 02_ENVIRONMENT_AND_COMMIT.json and
PACKAGE_SHA256.json ended up naming three different commits. So the report
generators write the placeholder token PENDING_STAMP_SEE_PACKAGE_PROVENANCE,
and this script writes the real SHA into the four metadata files IN THE WORKING
TREE once the commit exists. The ZIP is then built from the stamped tree, so the
delivered package names exactly one commit everywhere.

The repository-root REPAIR_REPORT.md is stamped by the same mechanism, for the
same reason: the copy committed into the repository carries the tokens, and the
copy shipped in the return package carries the concrete values. Two of the
report's values -- the delivered archive's SHA-256 and its byte size -- cannot
be derived from the commit SHA, because they only exist once the archive has
been built, so they have tokens of their own and are supplied as OPTIONAL
arguments. An optional argument that is not supplied leaves its token in place;
it is never replaced with an empty string.

The operation is deterministic and idempotent: it is pure textual substitution
with no timestamps, no randomness, no subprocess and no network. Running it
again with the same arguments is a no-op (the tokens are already gone), and
running it again with a different SHA re-stamps the four metadata files cleanly,
so the stamped tree can be reproduced byte-for-byte from the tagged commit.
REPAIR_REPORT.md is the one file whose substitution is one-way, because its
tokens appear in free prose rather than in one anchored line: to re-stamp it
with a different SHA, restore the committed copy first
(`git checkout -- REPAIR_REPORT.md`) and run this script again. The script
detects that situation and reports it rather than silently doing nothing.

This script does NOT commit, tag or push anything.

Usage: stamp_provenance.py <full-40-char-sha> [<zip-sha256>] [<zip-bytes>]
       stamp_provenance.py --check
       --check reports what is currently stamped and exits without writing.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTD = REPO / "simulation-results-ct2i"

# The commit quality gate in 19_VALIDATION_REPORT.md is generated unchecked with
# an Option A explanation, because the in-repo copy genuinely does not carry the
# SHA. Stamping satisfies it, so the same one line is rewritten here. The gate
# text is imported, never duplicated: two copies of a literal are exactly how
# the metadata drifted in the first place.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_s1_reports import COMMIT_GATE, commit_gate_line   # noqa: E402

PLACEHOLDER = "PENDING_STAMP_SEE_PACKAGE_PROVENANCE"
# In markdown the SHA always appears exactly once per file, in this literal
# form, so the substitution target is unambiguous.
MD_PATTERN = re.compile(
    r"(AUTHORITATIVE COMMIT: `)(" + PLACEHOLDER + r"|[0-9a-f]{40})(`)")

GATE_PATTERN = re.compile(
    r"^- \[[ x]\] " + re.escape(COMMIT_GATE) + r".*$", re.M)

MD_FILES = ["00_README.md", "19_VALIDATION_REPORT.md", "20_RESULT_HANDOFF_MEMO.md"]
JSON_FILE = "02_ENVIRONMENT_AND_COMMIT.json"

# ---------------------------------------------------------------- report ----
# REPAIR_REPORT.md lives one level above the package directory, at the repo
# root, and is committed WITH its tokens in place -- that is the whole point:
# the committed copy states every status fact truthfully (COMPLETE / YES) and
# only the self-referential identifiers are deferred to this stamp.
REPORT_FILE = "REPAIR_REPORT.md"
ZIP_SHA_PLACEHOLDER = "PENDING_ZIP_SHA256_SEE_SHA256SUMS"
ZIP_BYTES_PLACEHOLDER = "PENDING_ZIP_BYTES_SEE_SHA256SUMS"
# The console block of section 15 is the anchor used to detect an already
# stamped report, so a re-stamp with a different SHA can be reported instead of
# silently skipped.
REPORT_ANCHOR = re.compile(
    r"^AUTHORITATIVE COMMIT: (" + PLACEHOLDER + r"|[0-9a-f]{40})$", re.M)


def normalise_zip_bytes(raw: str) -> str:
    """'55384105' or '55,384,105' -> '55,384,105'. Deterministic, no I/O."""
    digits = raw.replace(",", "").strip()
    if not re.fullmatch(r"[0-9]+", digits):
        raise ValueError(f"not a byte count: {raw!r}")
    return f"{int(digits):,}"


def report_state() -> dict:
    """What REPAIR_REPORT.md currently carries. Read-only."""
    p = REPO / REPORT_FILE
    if not p.exists():
        return {"present": False}
    txt = p.read_text(encoding="utf-8")
    m = REPORT_ANCHOR.search(txt)
    return {
        "present": True,
        "text": txt,
        "commit": m.group(1) if m else "(no console AUTHORITATIVE COMMIT line)",
        "sha_tokens": txt.count(PLACEHOLDER),
        "zip_sha_tokens": txt.count(ZIP_SHA_PLACEHOLDER),
        "zip_bytes_tokens": txt.count(ZIP_BYTES_PLACEHOLDER),
    }


def current() -> dict:
    out = {}
    jp = OUTD / JSON_FILE
    if jp.exists():
        out[JSON_FILE] = json.loads(jp.read_text(encoding="utf-8")).get(
            "full_commit_sha", "(absent)")
    for name in MD_FILES:
        p = OUTD / name
        if not p.exists():
            out[name] = "(file absent)"
            continue
        txt = p.read_text(encoding="utf-8")
        m = MD_PATTERN.search(txt)
        out[name] = m.group(2) if m else "(no AUTHORITATIVE COMMIT line)"
        gm = GATE_PATTERN.search(txt)
        if gm:
            out[f"  {name} :: commit quality gate"] = (
                "[x] satisfied" if gm.group(0).startswith("- [x]")
                else "[ ] pending stamp")
    st = report_state()
    if not st["present"]:
        out[REPORT_FILE] = "(file absent)"
    else:
        out[REPORT_FILE] = st["commit"]
        out[f"  {REPORT_FILE} :: tokens left"] = (
            f"commit {st['sha_tokens']}, zip-sha256 {st['zip_sha_tokens']}, "
            f"zip-bytes {st['zip_bytes_tokens']}")
    return out


def stamp_report(sha: str, zip_sha: str | None, zip_bytes: str | None,
                 changed: list, problems: list) -> None:
    """Pure substitution of the three stamp tokens in REPAIR_REPORT.md."""
    st = report_state()
    if not st["present"]:
        # Not a failure: the package stamp is independent of the report.
        print(f"NOTE: {REPORT_FILE} not found at {REPO}; nothing to stamp there.")
        return
    txt = st["text"]
    if st["sha_tokens"] == 0 and re.fullmatch(r"[0-9a-f]{40}", st["commit"]) \
            and st["commit"] != sha:
        problems.append(
            f"{REPORT_FILE}: already stamped with {st['commit']}, which is not "
            f"{sha}. Restore the committed copy "
            f"(git checkout -- {REPORT_FILE}) and re-run.")
        return
    subs = [(PLACEHOLDER, sha)]
    if zip_sha is not None:
        subs.append((ZIP_SHA_PLACEHOLDER, zip_sha))
    if zip_bytes is not None:
        subs.append((ZIP_BYTES_PLACEHOLDER, zip_bytes))
    new = txt
    counts = []
    for token, value in subs:
        n = new.count(token)
        counts.append(f"{token} x{n}")
        new = new.replace(token, value)
    if new != txt:
        (REPO / REPORT_FILE).write_text(new, encoding="utf-8")
        changed.append(REPORT_FILE)
    print(f"{REPORT_FILE}: substituted " + ", ".join(counts))
    left = []
    if zip_sha is None and new.count(ZIP_SHA_PLACEHOLDER):
        left.append(f"{ZIP_SHA_PLACEHOLDER} x{new.count(ZIP_SHA_PLACEHOLDER)}")
    if zip_bytes is None and new.count(ZIP_BYTES_PLACEHOLDER):
        left.append(
            f"{ZIP_BYTES_PLACEHOLDER} x{new.count(ZIP_BYTES_PLACEHOLDER)}")
    if left:
        print(f"{REPORT_FILE}: left in place (no value supplied): "
              + ", ".join(left))


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--check" in sys.argv:
        for k, v in current().items():
            print(f"{k:38s} {v}")
        return 0
    if not 1 <= len(args) <= 3:
        print(__doc__)
        return 2
    sha = args[0].strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        print(f"not a full 40-character commit SHA: {args[0]!r}")
        return 2

    zip_sha = None
    if len(args) >= 2:
        zip_sha = args[1].strip().lower()
        if not re.fullmatch(r"[0-9a-f]{64}", zip_sha):
            print(f"not a SHA-256 hex digest: {args[1]!r}")
            return 2
    zip_bytes = None
    if len(args) >= 3:
        try:
            zip_bytes = normalise_zip_bytes(args[2])
        except ValueError as exc:
            print(str(exc))
            return 2

    changed = []
    jp = OUTD / JSON_FILE
    if not jp.exists():
        print(f"FAIL: {JSON_FILE} missing")
        return 1
    env = json.loads(jp.read_text(encoding="utf-8"))
    if env.get("full_commit_sha") != sha:
        env["full_commit_sha"] = sha
        jp.write_text(json.dumps(env, indent=2), encoding="utf-8")
        changed.append(JSON_FILE)

    problems = []
    for name in MD_FILES:
        p = OUTD / name
        if not p.exists():
            problems.append(f"{name}: file missing")
            continue
        t = p.read_text(encoding="utf-8")
        n = len(MD_PATTERN.findall(t))
        if n != 1:
            problems.append(f"{name}: expected exactly one AUTHORITATIVE COMMIT "
                            f"line, found {n}")
            continue
        new = MD_PATTERN.sub(lambda m: m.group(1) + sha + m.group(3), t)
        new = GATE_PATTERN.sub(lambda _m: commit_gate_line(sha), new)
        if new != t:
            p.write_text(new, encoding="utf-8")
            changed.append(name)

    stamp_report(sha, zip_sha, zip_bytes, changed, problems)

    for k, v in current().items():
        print(f"{k:38s} {v}")
    if problems:
        print("\nFAIL:")
        for pr in problems:
            print(f"  {pr}")
        return 1
    print(f"\nstamped {sha}; files rewritten: {changed or '(already stamped)'}")
    print("NOTE: PACKAGE_SHA256.json is regenerated by build_return_package.py "
          "AFTER this stamp, so it carries the same SHA.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
