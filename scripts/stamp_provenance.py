"""Stamp the authoritative commit SHA into the package metadata (Phase R, D1).

A file that lives inside commit C cannot contain C's own SHA at write time --
that is precisely how 00_README.md, 02_ENVIRONMENT_AND_COMMIT.json and
PACKAGE_SHA256.json ended up naming three different commits. So the report
generators write the placeholder token PENDING_STAMP_SEE_PACKAGE_PROVENANCE,
and this script writes the real SHA into the package metadata files and the
repository-root README.md IN THE WORKING TREE once the commit exists. The ZIP is then built from the stamped tree, so the
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
                           [--only=NAME,...] [--exclude=NAME,...]
       stamp_provenance.py --check
       --check reports what is currently stamped and exits without writing.

--only / --exclude restrict a run to a subset of the target files, named by
basename; --check always reports every target. They exist because one release
can legitimately need two different SHAs. REPAIR_REPORT.md is a Phase R
historical document: its prose describes the Phase R push readbacks, the
section 14.6 generation map and the tag sim-only-s1-complete-v2, so stamping it
with a later release SHA would turn true statements false. It is therefore
stamped with the Phase R identifiers and every other file with the current
release's, in two invocations over disjoint file sets. Both are pure textual
substitution, both are reproducible from the command line, and no stamp value
is ever hand-edited into a file.
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
# The repository-root README.md carries the same `AUTHORITATIVE COMMIT:` line
# and says of itself that this script writes the SHA into it. It lives outside
# the package directory, so it needs its own entry: without it the released
# README would keep the token for ever while every other metadata file named a
# commit -- the exact metadata disagreement Option A exists to prevent.
ROOT_MD_FILES = ["README.md"]
JSON_FILE = "02_ENVIRONMENT_AND_COMMIT.json"


def md_targets() -> list:
    """(path, display name) for every markdown file carrying the stamp line."""
    return ([(OUTD / n, n) for n in MD_FILES]
            + [(REPO / n, n) for n in ROOT_MD_FILES])

# ---------------------------------------------------------------- report ----
# REPAIR_REPORT.md lives one level above the package directory, at the repo
# root, and is committed WITH its tokens in place -- that is the whole point:
# the committed copy states every status fact truthfully (COMPLETE / YES) and
# only the self-referential identifiers are deferred to this stamp.
REPORT_FILE = "REPAIR_REPORT.md"
# simulation-results-ct2i/FINAL_SIMULATION_HANDOFF.md carries the same three
# tokens for the same reason, one level deeper: it reports the SHA-256 and byte
# size of the archive it is itself shipped inside, and no file can carry the
# hash of a container that does not exist until after the file is written. The
# copy inside the ZIP keeps the tokens and points at the detached sums file;
# the delivered on-disk copy is stamped once the archive exists, after which
# the on-disk manifests are regenerated so the delivered tree still verifies.
HANDOFF_FILE = "FINAL_SIMULATION_HANDOFF.md"
REPORT_FILES = [(REPORT_FILE, REPO / REPORT_FILE),
                (HANDOFF_FILE, OUTD / HANDOFF_FILE)]
ZIP_SHA_PLACEHOLDER = "PENDING_ZIP_SHA256_SEE_SHA256SUMS"
ZIP_BYTES_PLACEHOLDER = "PENDING_ZIP_BYTES_SEE_SHA256SUMS"
# The final archive is named by the SHORT sha, so a report that names the
# archive needs the abbreviation as a token of its own; deriving it from the
# full SHA at stamp time is the whole point -- an identifier typed by hand is
# an identifier that can disagree with the commit.
SHORT_PLACEHOLDER = "PENDING_SHORT_SHA_SEE_PACKAGE_PROVENANCE"
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


def report_state(p: Path) -> dict:
    """What one token-carrying report currently holds. Read-only."""
    if not p.exists():
        return {"present": False}
    txt = p.read_text(encoding="utf-8")
    m = REPORT_ANCHOR.search(txt)
    return {
        "present": True,
        "text": txt,
        "commit": m.group(1) if m else "(no console AUTHORITATIVE COMMIT line)",
        "sha_tokens": txt.count(PLACEHOLDER),
        "short_tokens": txt.count(SHORT_PLACEHOLDER),
        "zip_sha_tokens": txt.count(ZIP_SHA_PLACEHOLDER),
        "zip_bytes_tokens": txt.count(ZIP_BYTES_PLACEHOLDER),
    }


def current() -> dict:
    out = {}
    jp = OUTD / JSON_FILE
    if jp.exists():
        out[JSON_FILE] = json.loads(jp.read_text(encoding="utf-8")).get(
            "full_commit_sha", "(absent)")
    for p, name in md_targets():
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
    for name, path in REPORT_FILES:
        st = report_state(path)
        if not st["present"]:
            out[name] = "(file absent)"
            continue
        out[name] = st["commit"]
        out[f"  {name} :: tokens left"] = (
            f"commit {st['sha_tokens']}, short-sha {st['short_tokens']}, "
            f"zip-sha256 {st['zip_sha_tokens']}, "
            f"zip-bytes {st['zip_bytes_tokens']}")
    return out


# The full set of stampable targets, named by basename. --only / --exclude are
# validated against it, so a typo is refused rather than silently stamping
# nothing.
ALL_TARGETS = ([JSON_FILE] + MD_FILES + ROOT_MD_FILES
               + [n for n, _ in REPORT_FILES])


def selection(argv) -> set:
    """Target basenames this invocation may write. Pure; raises on a typo."""
    only, excl = None, set()
    for a in argv:
        if a.startswith("--only="):
            only = (only or set()) | {s.strip() for s in
                                      a[len("--only="):].split(",") if s.strip()}
        elif a.startswith("--exclude="):
            excl |= {s.strip() for s in
                     a[len("--exclude="):].split(",") if s.strip()}
    unknown = sorted(((only or set()) | excl) - set(ALL_TARGETS))
    if unknown:
        raise ValueError(f"unknown stamp target(s) {unknown}; known targets are "
                         f"{ALL_TARGETS}")
    return (set(ALL_TARGETS) if only is None else set(only)) - excl


def stamp_report(name: str, path: Path, sha: str, zip_sha: str | None,
                 zip_bytes: str | None, changed: list, problems: list) -> None:
    """Pure substitution of the three stamp tokens in one report file."""
    st = report_state(path)
    if not st["present"]:
        # Not a failure: the package stamp is independent of the report.
        print(f"NOTE: {name} not found at {path.parent}; nothing to stamp there.")
        return
    txt = st["text"]
    if st["sha_tokens"] == 0 and re.fullmatch(r"[0-9a-f]{40}", st["commit"]) \
            and st["commit"] != sha:
        problems.append(
            f"{name}: already stamped with {st['commit']}, which is not "
            f"{sha}. Restore the committed copy "
            f"(git checkout -- {name}) and re-run.")
        return
    subs = [(PLACEHOLDER, sha), (SHORT_PLACEHOLDER, sha[:8])]
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
        path.write_text(new, encoding="utf-8")
        changed.append(name)
    print(f"{name}: substituted " + ", ".join(counts))
    left = []
    if zip_sha is None and new.count(ZIP_SHA_PLACEHOLDER):
        left.append(f"{ZIP_SHA_PLACEHOLDER} x{new.count(ZIP_SHA_PLACEHOLDER)}")
    if zip_bytes is None and new.count(ZIP_BYTES_PLACEHOLDER):
        left.append(
            f"{ZIP_BYTES_PLACEHOLDER} x{new.count(ZIP_BYTES_PLACEHOLDER)}")
    if left:
        print(f"{name}: left in place (no value supplied): "
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

    try:
        sel = selection(sys.argv[1:])
    except ValueError as exc:
        print(str(exc))
        return 2
    skipped = sorted(set(ALL_TARGETS) - sel)
    print(f"targets: {sorted(sel)}")
    if skipped:
        print(f"NOT stamped by this invocation: {skipped}")

    changed = []
    jp = OUTD / JSON_FILE
    if JSON_FILE in sel:
        if not jp.exists():
            print(f"FAIL: {JSON_FILE} missing")
            return 1
        env = json.loads(jp.read_text(encoding="utf-8"))
        if env.get("full_commit_sha") != sha:
            env["full_commit_sha"] = sha
            jp.write_text(json.dumps(env, indent=2), encoding="utf-8")
            changed.append(JSON_FILE)

    problems = []
    for p, name in md_targets():
        if name not in sel:
            continue
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

    for name, path in REPORT_FILES:
        if name in sel:
            stamp_report(name, path, sha, zip_sha, zip_bytes, changed, problems)

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
