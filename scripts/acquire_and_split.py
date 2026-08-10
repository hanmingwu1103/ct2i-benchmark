"""Pass B: acquire the four pilot datasets, build duplicate/scaffold groups,
create and persist deterministic folds, and write manifests."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO.parent / "audit-ct2i" / "02-pilot"
sys.path.insert(0, str(REPO / "src"))

from ct2i_benchmark.data.acquire import acquire  # noqa: E402
from ct2i_benchmark.splitting.outer import (duplicate_groups, make_folds,  # noqa: E402
                                            conflicting_label_groups)
from ct2i_benchmark.hashing import sha256_obj  # noqa: E402

SEED_FOLD, SEED_INNER = 42, 421
acq_rows, split_rows = [], []

for ds in ["tictactoe", "mushroom", "bace", "parity5_plus_5"]:
    X, y, extras, rec = acquire(ds, REPO / ".cache")
    if ds == "bace":
        groups = extras["scaffold_groups"]
        group_type = "bemis_murcko_scaffold"
    else:
        groups = duplicate_groups(X)
        group_type = "exact_feature_duplicate"
    n_conflict = conflicting_label_groups(groups, y)
    folds = make_folds(y, groups, n_outer=5, seed_fold=SEED_FOLD, seed_inner=SEED_INNER)
    # persist processed data + folds
    ddir = REPO / ".cache" / "processed"
    ddir.mkdir(parents=True, exist_ok=True)
    X.to_parquet(ddir / f"{ds}_X.parquet")
    np.save(ddir / f"{ds}_y.npy", y)
    np.save(ddir / f"{ds}_groups.npy", groups)
    fold_doc = []
    for f in folds:
        fold_doc.append({
            "outer_fold": f.outer_fold,
            "train_ids": f.train_ids.tolist(), "test_ids": f.test_ids.tolist(),
            "inner_train_ids": f.inner_train_ids.tolist(),
            "inner_val_ids": f.inner_val_ids.tolist(), "sha256": f.sha256(),
        })
        def cc(ids):
            vals = np.bincount(y[ids], minlength=2)
            return f"{int(vals[0])}|{int(vals[1])}"
        split_rows.append({
            "dataset_id": ds, "outer_fold": f.outer_fold,
            "splitter": "StratifiedGroupKFold+group_holdout",
            "seed": f"{SEED_FOLD}/{SEED_INNER}", "group_type": group_type,
            "n_groups": int(len(np.unique(groups))),
            "n_train": len(f.train_ids), "n_inner_train": len(f.inner_train_ids),
            "n_inner_val": len(f.inner_val_ids), "n_test": len(f.test_ids),
            "train_class_counts": cc(f.train_ids),
            "inner_train_class_counts": cc(f.inner_train_ids),
            "inner_val_class_counts": cc(f.inner_val_ids),
            "test_class_counts": cc(f.test_ids),
            "train_test_group_overlap": len(set(groups[f.train_ids]) & set(groups[f.test_ids])),
            "inner_group_overlap": len(set(groups[f.inner_train_ids]) & set(groups[f.inner_val_ids])),
            "duplicate_conflicts": n_conflict,
            "split_artifact": f"splits/{ds}_folds.json",
            "split_sha256": f.sha256(), "status": "SUCCESS", "notes": "",
        })
    (AUDIT / "splits").mkdir(parents=True, exist_ok=True)
    (AUDIT / "splits" / f"{ds}_folds.json").write_text(json.dumps(
        {"dataset": ds, "seed_fold": SEED_FOLD, "seed_inner": SEED_INNER,
         "group_type": group_type, "folds": fold_doc}, indent=1))
    row = rec.to_dict()
    row["preprocessing_config_hash"] = sha256_obj(
        {"seed_fold": SEED_FOLD, "group_type": group_type, "missing": "explicit-category"})
    row["redistribution_allowed"] = "no-raw-in-repo"
    acq_rows.append(row)
    print(f"{ds}: n={rec.processed_n} p={rec.processed_p} groups={len(np.unique(groups))} "
          f"conflicts={n_conflict} folds=5 raw_sha={rec.raw_sha256[:12]}")

pd.DataFrame(acq_rows).to_csv(AUDIT / "_tmp" / "acquisition_rows.csv", index=False)
pd.DataFrame(split_rows).to_csv(AUDIT / "_tmp" / "split_rows.csv", index=False)
print("MANIFESTS WRITTEN")
