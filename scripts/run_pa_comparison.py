"""P-A (§18): reconstructed global-vs-fold-safe comparison on the frozen
paired subset. Identical rows, folds, seeds, candidates, readers."""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO.parent / "audit-ct2i" / "02-pilot"
sys.path.insert(0, str(REPO / "src"))

from ct2i_benchmark.runners import load_dataset, load_folds, run_image_cell, run_tabular_cell  # noqa: E402
from ct2i_benchmark.artifacts.lineage import code_commit  # noqa: E402

CFG = yaml.safe_load((REPO / "configs" / "pilot_cpu_frozen.yaml").read_text())["pa_comparison"]
COMMIT = code_commit(str(REPO))
rows = []
t0 = time.perf_counter()

for ds in CFG["datasets"]:
    X, y, g = load_dataset(ds)
    folds = load_folds(ds, AUDIT)
    for fold in folds[:CFG["n_folds"]]:
        for enc in CFG["encoders"]:
            for lay in CFG["layouts"]:
                cell = {}
                for proto in ["global", "foldsafe"]:
                    img = run_image_cell(X, y, g, fold, enc, lay, CFG["seed"],
                                         COMMIT, protocol=proto,
                                         timeout_s=CFG["timeout_s"])
                    tab = run_tabular_cell(X, y, g, fold, enc, "lightgbm",
                                           CFG["seed"], COMMIT, protocol=proto,
                                           timeout_s=CFG["timeout_s"])
                    cell[proto] = (img, tab)
                gi, gt = cell["global"]
                si, st = cell["foldsafe"]
                ok = all(r["status"] == "SUCCESS" for r in (gi, gt, si, st))
                a = {k: (r["metrics"]["auc"] if r["status"] == "SUCCESS" else None)
                     for k, r in [("global_image_auc", gi), ("global_tabular_auc", gt),
                                  ("safe_image_auc", si), ("safe_tabular_auc", st)]}
                rows.append({
                    "dataset_id": ds, "outer_fold": fold.outer_fold, "seed": CFG["seed"],
                    "encoder": enc, "layout": lay, "image_reader": "pca_mlp",
                    "tabular_model": "lightgbm", **a,
                    "b_model_image": (a["global_image_auc"] - a["safe_image_auc"]) if ok else None,
                    "b_model_tabular": (a["global_tabular_auc"] - a["safe_tabular_auc"]) if ok else None,
                    "b_delta": ((a["global_image_auc"] - a["global_tabular_auc"])
                                - (a["safe_image_auc"] - a["safe_tabular_auc"])) if ok else None,
                    "reconstruction_scope": "RECONSTRUCTED-CONTAMINATED-PROTOCOL (original code absent)",
                    "status": "SUCCESS" if ok else "PARTIAL_FAILURE",
                    "notes": "" if ok else str({k: r["status"] for k, r in
                                                [("gi", gi), ("gt", gt), ("si", si), ("st", st)]
                                                if r["status"] != "SUCCESS"}),
                })
        print(f"P-A {ds} fold {fold.outer_fold} done ({time.perf_counter()-t0:.0f}s)",
              flush=True)

pd.DataFrame(rows).to_csv(AUDIT / "_tmp" / "pa_rows.csv", index=False)
d = pd.DataFrame(rows)
ok = d[d.status == "SUCCESS"]
print(f"P-A DONE: {len(ok)}/{len(d)} paired cells; "
      f"median b_delta={ok.b_delta.median():.4f} range=({ok.b_delta.min():.4f},"
      f"{ok.b_delta.max():.4f})")
