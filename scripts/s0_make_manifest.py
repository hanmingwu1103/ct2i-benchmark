"""Phase S0 step 1: input verification + SHA-256 manifest.

Records every required input file, its resolved local path, size, SHA-256, and
its role. Files named in the execution prompt that live under a different local
path (the prompt names bare filenames; this repository stores them under
manuscript_reference/ and simulation2_authoritative/) are recorded with both
the prompt name and the resolved path so the mapping is auditable.

Writes: simulation-results-ct2i/S0_INPUT_AND_HASH_MANIFEST.csv
No real-data file is read, opened, or modified.
"""
from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "simulation-results-ct2i" / "S0_INPUT_AND_HASH_MANIFEST.csv"

BASELINE = "7f6b62035951df7d032d0a3eab04cb3c9b0328b4"

# (prompt_name, resolved_relative_path, role, required)
INPUTS = [
    ("CT2I_STUDENT_SIMULATION_ONLY_EXPERIMENT_PLAN.md",
     "CT2I_STUDENT_SIMULATION_ONLY_EXPERIMENT_PLAN.md",
     "authoritative_scientific_specification", "required"),
    ("CT2I_STUDENT_SIMULATION_EXECUTION_PROMPT.md",
     "CT2I_STUDENT_SIMULATION_EXECUTION_PROMPT.md",
     "execution_prompt", "required"),
    ("ct2i_main_revised_clean.tex",
     "manuscript_reference/ct2i_main_revised_clean.tex",
     "main_manuscript_READ_ONLY", "required"),
    ("ct2i_main_revised_clean.pdf",
     "manuscript_reference/ct2i_main_revised_clean.pdf",
     "main_manuscript_READ_ONLY", "required"),
    ("ct2i_supp_revised_clean.tex",
     "manuscript_reference/ct2i_supp_revised_clean.tex",
     "supplement_READ_ONLY", "required"),
    ("ct2i_supp_revised_clean.pdf",
     "manuscript_reference/ct2i_supp_revised_clean.pdf",
     "supplement_READ_ONLY", "required"),
    ("CT2I_SIMULATION_PLACEHOLDER_REGISTER.csv",
     "manuscript_reference/CT2I_SIMULATION_PLACEHOLDER_REGISTER.csv",
     "combined_placeholder_register", "required"),
    ("20_SIMULATION_PROTOCOLS_AND_SUMMARY.md",
     "simulation2_authoritative/20_SIMULATION_PROTOCOLS_AND_SUMMARY.md",
     "stage2_authoritative_summary_READ_ONLY", "required"),
    ("21_SIMULATION_RESULTS.csv",
     "simulation2_authoritative/21_SIMULATION_RESULTS.csv",
     "stage2_authoritative_raw_results_READ_ONLY", "required"),
    ("simulation_protocols.yaml",
     "simulation2_authoritative/simulation_protocols.yaml",
     "stage2_frozen_protocol_READ_ONLY", "required"),
    ("configs/simulation_protocols.yaml",
     "configs/simulation_protocols.yaml",
     "stage2_frozen_protocol_repo_copy", "required"),
    ("configs/pilot_cpu_frozen.yaml",
     "configs/pilot_cpu_frozen.yaml",
     "stage2_frozen_cpu_matrix_context", "supporting"),
    ("MAIN_SIMULATION_PLACEHOLDER_REGISTER.csv",
     "MAIN_SIMULATION_PLACEHOLDER_REGISTER.csv",
     "fallback_placeholder_register_not_needed", "fallback"),
    ("HANDOFF_SHA256SUMS.txt",
     "HANDOFF_SHA256SUMS.txt",
     "supplied_handoff_checksums", "supporting"),
    ("requirements.lock.txt",
     "requirements.lock.txt",
     "environment_lock", "supporting"),
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True).stdout.strip()


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for prompt_name, rel, role, req in INPUTS:
        p = REPO / rel
        if p.is_file():
            rows.append({
                "prompt_input_name": prompt_name,
                "resolved_path": rel,
                "role": role,
                "requirement": req,
                "present": "YES",
                "size_bytes": p.stat().st_size,
                "sha256": sha256_file(p),
                "notes": "",
            })
        else:
            rows.append({
                "prompt_input_name": prompt_name,
                "resolved_path": rel,
                "role": role,
                "requirement": req,
                "present": "NO",
                "size_bytes": "",
                "sha256": "",
                "notes": ("combined register present, fallback not required"
                          if req == "fallback" else "MISSING"),
            })

    # repository / commit facts
    head = git("rev-parse", "HEAD")
    baseline_type = git("cat-file", "-t", BASELINE)
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    dirty = git("status", "--porcelain")
    for key, val, note in [
        ("REPOSITORY_ORIGIN", git("remote", "get-url", "origin"), "active repository"),
        ("REQUIRED_BASELINE_COMMIT", BASELINE,
         f"object type={baseline_type or 'ABSENT'}"),
        ("BASELINE_PRESENT_IN_ACTIVE_REPO", "YES" if baseline_type == "commit" else "NO", ""),
        ("WORKING_BRANCH", branch, "created from the required baseline"),
        ("BRANCH_MERGE_BASE_IS_BASELINE",
         "YES" if git("merge-base", "HEAD", BASELINE) == BASELINE else "NO", ""),
        ("HEAD_AT_MANIFEST_TIME", head, ""),
        ("WORKTREE_CLEAN_AT_BRANCH_CREATION", "YES" if not dirty else "NO",
         "dirty entries are Phase S0 outputs only"),
        ("HISTORICAL_REPOSITORY", "https://github.com/cph354001/cT2I",
         "READ-ONLY; not cloned, not modified, not required for Phase S0"),
        ("REAL_DATA_FILES_TOUCHED", "0", "no real dataset/model/image was read or written"),
    ]:
        rows.append({"prompt_input_name": key, "resolved_path": val, "role": "repository_fact",
                     "requirement": "verification", "present": "", "size_bytes": "",
                     "sha256": "", "notes": note})

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["prompt_input_name", "resolved_path", "role",
                                          "requirement", "present", "size_bytes",
                                          "sha256", "notes"])
        w.writeheader()
        w.writerows(rows)

    missing = [r for r in rows if r["present"] == "NO" and r["requirement"] == "required"]
    print(f"wrote {OUT.relative_to(REPO)}  rows={len(rows)}  missing_required={len(missing)}")
    for r in missing:
        print("  MISSING REQUIRED:", r["resolved_path"])
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
