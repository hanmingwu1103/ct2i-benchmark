"""Frozen CPU pilot (P-D-CPU, §17) + reconstructed global-vs-fold-safe
comparison (P-A, §18). Runs ONLY the matrix in configs/pilot_cpu_frozen.yaml."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO.parent / "audit-ct2i" / "02-pilot"
sys.path.insert(0, str(REPO / "src"))

from ct2i_benchmark.runners import (load_dataset, load_folds, run_image_cell,  # noqa: E402
                                    run_tabular_cell, onehot_eligible)
from ct2i_benchmark.artifacts.lineage import code_commit  # noqa: E402
from ct2i_benchmark.artifacts.store import ArtifactStore  # noqa: E402
from ct2i_benchmark.evaluation.selection import Candidate, select  # noqa: E402

CFG = yaml.safe_load((REPO / "configs" / "pilot_cpu_frozen.yaml").read_text())
COMMIT = code_commit(str(REPO))
store = ArtifactStore(AUDIT / "artifacts")
t_start = time.perf_counter()

cells, results = [], []
COMPLEXITY = {"logistic": 1, "pca_mlp": 3, "direct_mlp": 3, "lightgbm": 2,
              "xgboost": 2, "catboost_native": 2, "tabm": 4, "tabicl_v2": 5,
              "tabpfn_3": 5}


def cell_id(ds, fold, branch, enc, lay, model, seed):
    return f"{ds}|f{fold}|{branch}|{enc}|{lay}|{model}|s{seed}"


for ds in CFG["datasets"]:
    X, y, g = load_dataset(ds)
    folds = load_folds(ds, AUDIT)
    for fold in folds:
        # eligibility from INNER-TRAINING cardinalities only (never touches
        # inner-validation or outer-test content — Codex re-review finding)
        oh_ok = onehot_eligible(X, fold.inner_train_ids)
        # ---- image branch ----
        for enc in CFG["image"]["encoders"]:
            if enc == "onehot" and not oh_ok:
                for lay in CFG["image"]["layouts"]:
                    for seed in CFG["image"]["seeds"]:
                        cells.append({"cell_id": cell_id(ds, fold.outer_fold, "image", enc, lay, "pca_mlp", seed),
                                      "eligible": False, "eligibility_rule": "onehot_width_cap",
                                      "status": "SKIPPED_INELIGIBLE"})
                continue
            for lay in CFG["image"]["layouts"]:
                for seed in CFG["image"]["seeds"]:
                    cid = cell_id(ds, fold.outer_fold, "image", enc, lay, "pca_mlp", seed)
                    rec = run_image_cell(X, y, g, fold, enc, lay, seed, COMMIT,
                                         timeout_s=CFG["timeouts"]["image_cell_s"])
                    rec.update(cell_id=cid, dataset_id=ds, branch="image",
                               configuration_id=f"{enc}|{lay}|pca_mlp|default")
                    results.append(rec)
                    cells.append({"cell_id": cid, "eligible": True,
                                  "eligibility_rule": "frozen_matrix",
                                  "status": rec["status"]})
        # ---- representation-controlled branch ----
        for enc in CFG["representation"]["encoders"]:
            if enc == "onehot" and not oh_ok:
                for model in CFG["representation"]["models"]:
                    for seed in (CFG["representation"]["mlp_seeds"] if model == "direct_mlp" else [5]):
                        cells.append({"cell_id": cell_id(ds, fold.outer_fold, "representation", enc, "none", model, seed),
                                      "eligible": False, "eligibility_rule": "onehot_width_cap",
                                      "status": "SKIPPED_INELIGIBLE"})
                continue
            for model in CFG["representation"]["models"]:
                seeds = CFG["representation"]["mlp_seeds"] if model == "direct_mlp" else [5]
                for seed in seeds:
                    cid = cell_id(ds, fold.outer_fold, "representation", enc, "none", model, seed)
                    rec = run_tabular_cell(X, y, g, fold, enc, model, seed, COMMIT,
                                           timeout_s=CFG["timeouts"]["tabular_cell_s"])
                    rec.update(cell_id=cid, dataset_id=ds, branch="representation",
                               configuration_id=f"{enc}|{model}|default")
                    results.append(rec)
                    cells.append({"cell_id": cid, "eligible": True,
                                  "eligibility_rule": "frozen_matrix",
                                  "status": rec["status"]})
        # ---- best-practice branch ----
        for spec in CFG["best_practice"]["models"]:
            model, enc, seeds = spec["model"], spec.get("encoder"), spec.get("seeds", [5])
            for seed in seeds:
                cid = cell_id(ds, fold.outer_fold, "best_practice", enc or "raw", "none", model, seed)
                if model in CFG.get("unavailable_models", {}):
                    cells.append({"cell_id": cid, "eligible": False,
                                  "eligibility_rule": "model_access",
                                  "status": CFG["unavailable_models"][model]})
                    continue
                rec = run_tabular_cell(X, y, g, fold, enc, model, seed, COMMIT,
                                       timeout_s=CFG["timeouts"]["foundation_cell_s"])
                rec.update(cell_id=cid, dataset_id=ds, branch="best_practice",
                           configuration_id=f"{enc or 'raw'}|{model}|fixed")
                results.append(rec)
                cells.append({"cell_id": cid, "eligible": True,
                              "eligibility_rule": "frozen_matrix",
                              "status": rec["status"]})
    print(f"{ds}: done ({time.perf_counter()-t_start:.0f}s elapsed)", flush=True)

# persist raw results + predictions
for rec in results:
    scores = rec.pop("y_score_test", None)
    if scores is not None:
        ds = rec["dataset_id"]
        fold_ids = json.loads((AUDIT / "splits" / f"{ds}_folds.json").read_text())
        te = fold_ids["folds"][rec["outer_fold"]]["test_ids"]
        Xd, yd, _ = load_dataset(ds)
        store.save_predictions(rec["cell_id"].replace("|", "_"), te, yd[te], scores)
        rec["prediction_artifact"] = f"pred_{rec['cell_id'].replace('|','_')}.parquet"
    store.append("pilot_runs", {**rec, "code_commit": COMMIT})

pd.DataFrame(cells).to_csv(AUDIT / "_tmp" / "pilot_cells_raw.csv", index=False)

# ---- per-(dataset, fold, branch) selection on INNER results only ----
# Candidate inputs are exclusively inner-phase quantities (inner_auc,
# complexity, inner_elapsed_s, inner_status); outer refit failures are handled
# AFTER ranking via the frozen next-ranked fallback (contract 10.6).
sel_rows = []
df = pd.DataFrame([r for r in results])
from ct2i_benchmark.evaluation.selection import rank_candidates  # noqa: E402
for (ds, fold, branch), grp in df.groupby(["dataset_id", "outer_fold", "branch"]):
    cands = [Candidate(r["cell_id"], r["inner_auc"],
                       COMPLEXITY.get(r["reader_or_model"], 3),
                       r["inner_elapsed_s"] if r["inner_elapsed_s"] is not None else 0.0,
                       r["inner_status"] if r["inner_status"] is not None else "TRAINING_FAILURE")
             for _, r in grp.iterrows()]
    ranked = rank_candidates(cands)
    top, tie = select(cands)
    if top is None:
        sel_rows.append({"dataset_id": ds, "outer_fold": fold, "policy_branch": branch,
                         "candidate_count": len(cands), "status": "TRAINING_FAILURE"})
        continue
    # refit fallback: walk ranked candidates until one whose OUTER refit
    # succeeded; count fallbacks (selection itself never read outer results)
    fallbacks = 0
    chosen = None
    for cand in ranked:
        row = grp[grp.cell_id == cand.config_id].iloc[0]
        if row["status"] == "SUCCESS":
            chosen, top, tie2 = row, cand, tie
            break
        fallbacks += 1
    if chosen is None:
        sel_rows.append({"dataset_id": ds, "outer_fold": fold, "policy_branch": branch,
                         "candidate_count": len(cands),
                         "status": "TRAINING_FAILURE",
                         "notes": f"all {len(ranked)} ranked candidates failed outer refit"})
        continue
    r = chosen
    m = r["metrics"] or {}
    sel_rows.append({
        "dataset_id": ds, "outer_fold": fold, "policy_branch": branch,
        "candidate_count": len(cands), "selected_cell_id": top.config_id,
        "selected_config_id": r["configuration_id"], "tie_break_used": tie,
        "inner_primary_metric": top.inner_metric,
        "outer_auc": m.get("auc"), "outer_pr_auc": m.get("pr_auc"),
        "outer_logloss": m.get("logloss"), "outer_brier": m.get("brier"),
        "outer_balanced_accuracy": m.get("balanced_accuracy"),
        "outer_f1_valsel": m.get("f1_valsel"),
        "outer_calibration_slope": m.get("calibration_slope"),
        "outer_calibration_intercept": m.get("calibration_intercept"),
        "status": r["status"],
        "selection_churn_key": r["configuration_id"],
        "notes": f"refit_fallbacks={fallbacks}" if fallbacks else "",
    })
pd.DataFrame(sel_rows).to_csv(AUDIT / "_tmp" / "policy_selection_rows.csv", index=False)
el = time.perf_counter() - t_start
print(f"PILOT DONE in {el/60:.1f} min; cells={len(cells)} results={len(results)}")
