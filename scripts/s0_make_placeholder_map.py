"""Phase S0 step 3: map every manuscript simulation placeholder to a required output.

Two placeholder populations are merged:

  (a) the combined register  manuscript_reference/CT2I_SIMULATION_PLACEHOLDER_REGISTER.csv
      (13 rows: SIM1-*, SIM2-*, REPO-01);
  (b) the literal \\SimPending{...} anchors actually present in the manuscript
      sources (7 anchors in the main text; 0 in the supplement).

Anchors in (b) that are not register ids are added as separate rows, because
they are distinct insertion points the advisor must fill. Register rows whose
id does not appear literally in the .tex are flagged
`anchor_present_in_tex=NO (register-only)` — these are supplement insertion
points named by the register but not yet stubbed in the working supplement.

The manuscripts are opened READ-ONLY (parsed, never written).

Writes: simulation-results-ct2i/S0_PLACEHOLDER_OUTPUT_MAP.csv
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REGISTER = REPO / "manuscript_reference" / "CT2I_SIMULATION_PLACEHOLDER_REGISTER.csv"
MAIN_TEX = REPO / "manuscript_reference" / "ct2i_main_revised_clean.tex"
SUPP_TEX = REPO / "manuscript_reference" / "ct2i_supp_revised_clean.tex"
OUT = REPO / "simulation-results-ct2i" / "S0_PLACEHOLDER_OUTPUT_MAP.csv"

# Manuscript-only \SimPending anchors (not register ids) and their bindings.
# Each is bound to the SAME frozen numeric artifacts as its register sibling;
# the advisor writes the prose, the student supplies only the values.
EXTRA_ANCHORS = {
    "SIM-ABS-01": dict(
        alias_of="SIM1-RESULT-01",
        producing_outputs="07_SIM1_ACCEPTANCE_REPORT.json; 06_SIM1_SUMMARY.csv",
        producing_script="scripts/run_sim1_summarize.py",
        required_columns="criterion_id; criterion_pass; mean_abs_identity_error; mean_gap",
        blocking="YES",
        note=("Abstract one-sentence Simulation 1 conclusion. Student supplies the "
              "validated pass/fail and max identity error ONLY; advisor writes the sentence."),
    ),
    "SIM-FIG-01": dict(
        alias_of="SIM1-FIG-01",
        producing_outputs="10_SIM1_FIGURES/FigS1_identity.pdf; 08_SIM1_FIGURE_DATA.csv",
        producing_script="scripts/run_sim1_figures.py",
        required_columns="scenario_id; encoder; metric; estimated_gap; theoretical_gap; mcse",
        blocking="YES",
        note=("Main-text Simulation 1 figure float (fig:sim1). Frozen panel plan "
              "= Figure S1 panels a-d; see 01_PROTOCOL_FREEZE.yaml figures.FigS1."),
    ),
    "SIM-FIG-02": dict(
        alias_of="SIM2-FIG-01",
        producing_outputs="16_SIM2_FIGURE.pdf; 15_SIM2_FIGURE_DATA.csv",
        producing_script="scripts/run_sim2_figures.py",
        required_columns="K; sigma; rho; regime; metric; value; theoretical_value; mcse",
        blocking="YES",
        note=("Main-text Simulation 2 figure float (fig:sim2). Numbers are already "
              "final in the Stage 2 authoritative output; only rendering is permitted."),
    ),
    "SIM-DISC-01": dict(
        alias_of="SIM1-RESULT-02",
        producing_outputs="06_SIM1_SUMMARY.csv; 09_SIM1_TABLE_DATA.csv; 20_RESULT_HANDOFF_MEMO.md",
        producing_script="scripts/run_sim1_summarize.py",
        required_columns="encoder; learner; metric; representation_loss; learner_shortfall; ci_low; ci_high",
        blocking="YES",
        note=("Discussion paragraph integrating Simulation 1 encoding-loss findings. "
              "ADVISOR-WRITTEN PROSE; student supplies contrasts with uncertainty only."),
    ),
    "SIM-CONCL-01": dict(
        alias_of="SIM1-RESULT-01",
        producing_outputs="07_SIM1_ACCEPTANCE_REPORT.json",
        producing_script="scripts/run_sim1_summarize.py",
        required_columns="criterion_id; criterion_description; maximum_error; tolerance; pass",
        blocking="YES",
        note=("Conclusions one-sentence Simulation 1 statement. ADVISOR-WRITTEN PROSE."),
    ),
}

# Register id -> producing script (the frozen generator that must emit the numbers).
PRODUCER = {
    "SIM1-RESULT-01": "scripts/run_sim1a_exact.py -> scripts/run_sim1_summarize.py",
    "SIM1-RESULT-02": "scripts/run_sim1b_finite.py -> scripts/run_sim1_summarize.py",
    "SIM1-RESULT-03": "scripts/run_sim1c_hash.py -> scripts/run_sim1_summarize.py",
    "SIM1-FIG-01": "scripts/run_sim1_figures.py (FigS1)",
    "SIM1-FIG-02": "scripts/run_sim1_figures.py (FigS2)",
    "SIM1-FIG-03": "scripts/run_sim1_figures.py (FigS3)",
    "SIM1-FIG-04": "scripts/run_sim1_figures.py (FigS4)",
    "SIM1-TAB-01": "scripts/run_sim1_tables.py (TabS1)",
    "SIM1-TAB-02": "scripts/run_sim1_tables.py (TabS2)",
    "SIM1-TAB-03": "scripts/run_sim1_tables.py (TabS3)",
    "SIM2-FIG-01": "scripts/run_sim2_figures.py",
    "SIM2-TAB-01": "scripts/run_sim2_tables.py",
    "REPO-01": "scripts/s0_env_commit.py -> 02_ENVIRONMENT_AND_COMMIT.json",
}

# Which phase produces it.
PHASE = {
    "SIM1-RESULT-01": "S1.2 (Sim 1A exact)",
    "SIM1-RESULT-02": "S1.4 (Sim 1B finite-sample)",
    "SIM1-RESULT-03": "S1.3 (Sim 1C hash collapse)",
    "SIM1-FIG-01": "S1.7 (figures)",
    "SIM1-FIG-02": "S1.7 (figures)",
    "SIM1-FIG-03": "S1.7 (figures)",
    "SIM1-FIG-04": "S1.7 (figures)",
    "SIM1-TAB-01": "S1.7 (tables)",
    "SIM1-TAB-02": "S1.7 (tables)",
    "SIM1-TAB-03": "S1.7 (tables)",
    "SIM2-FIG-01": "S1.5 (Sim 2 regeneration)",
    "SIM2-TAB-01": "S1.5 (Sim 2 regeneration)",
    "REPO-01": "S1.8 (packaging)",
}

FIELDS = ["placeholder_id", "source", "manuscript_file", "anchor_present_in_tex",
          "tex_line", "alias_of", "producing_phase", "producing_script",
          "required_output_files", "required_columns", "blocking_for_submission",
          "student_supplies", "advisor_writes", "notes"]


def find_anchors(path: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for m in re.finditer(r"\\SimPending\{([A-Z0-9\-]+):", line):
            out.setdefault(m.group(1), i)
    return out


def main() -> int:
    main_anchors = find_anchors(MAIN_TEX)
    supp_anchors = find_anchors(SUPP_TEX)

    rows = []
    seen = set()
    # the supplied register carries a UTF-8 BOM; utf-8-sig strips it so the
    # first field name is `placeholder_id`, not `﻿placeholder_id`
    with open(REGISTER, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            pid = (r.get("placeholder_id") or "").strip()
            if not pid:
                continue
            seen.add(pid)
            line = main_anchors.get(pid) or supp_anchors.get(pid)
            rows.append({
                "placeholder_id": pid,
                "source": "register",
                "manuscript_file": r["manuscript_file"],
                "anchor_present_in_tex": "YES" if line else "NO (register-only)",
                "tex_line": line or "",
                "alias_of": "",
                "producing_phase": PHASE.get(pid, ""),
                "producing_script": PRODUCER.get(pid, ""),
                "required_output_files": r["required_student_file"],
                "required_columns": r["required_columns"],
                "blocking_for_submission": r["blocking_for_submission"],
                "student_supplies": "validated numeric values / figure / table files",
                "advisor_writes": "all interpretive prose",
                "notes": r["notes"],
            })

    for pid, spec in EXTRA_ANCHORS.items():
        line = main_anchors.get(pid) or supp_anchors.get(pid)
        rows.append({
            "placeholder_id": pid,
            "source": "manuscript \\SimPending anchor",
            "manuscript_file": ("ct2i_main_revised_clean.tex" if pid in main_anchors
                                else "ct2i_supp_revised_clean.tex" if pid in supp_anchors
                                else "NOT FOUND"),
            "anchor_present_in_tex": "YES" if line else "NO",
            "tex_line": line or "",
            "alias_of": spec["alias_of"],
            "producing_phase": PHASE.get(spec["alias_of"], ""),
            "producing_script": spec["producing_script"],
            "required_output_files": spec["producing_outputs"],
            "required_columns": spec["required_columns"],
            "blocking_for_submission": spec["blocking"],
            "student_supplies": "validated numeric values / figure file",
            "advisor_writes": "all interpretive prose",
            "notes": spec["note"],
        })

    rows.sort(key=lambda r: (r["placeholder_id"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    unmapped = [r for r in rows if not r["producing_script"]]
    orphan = [a for a in list(main_anchors) + list(supp_anchors)
              if a not in seen and a not in EXTRA_ANCHORS]
    print(f"wrote {OUT.relative_to(REPO)}")
    print(f"  register rows      : {len(seen)}")
    print(f"  tex anchors (main) : {len(main_anchors)}  {sorted(main_anchors)}")
    print(f"  tex anchors (supp) : {len(supp_anchors)}")
    print(f"  total placeholders : {len(rows)}")
    print(f"  mapped to an output: {len(rows) - len(unmapped)}/{len(rows)}")
    print(f"  unmapped tex anchors: {orphan}")
    return 1 if (unmapped or orphan) else 0


if __name__ == "__main__":
    raise SystemExit(main())
