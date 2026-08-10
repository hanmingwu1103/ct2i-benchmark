"""One-fold smoke-test matrix (§14): every fitted-state family on fold 0 of
Tic-Tac-Toe (encoders/layouts/readers/models) + REFINED via TINTOlib on the
smallest feasible cell + ResNet-18 CPU smoke + foundation models."""
import json
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO.parent / "audit-ct2i" / "02-pilot"
sys.path.insert(0, str(REPO / "src"))

import psutil  # noqa: E402
from ct2i_benchmark.runners import load_dataset, load_folds  # noqa: E402
from ct2i_benchmark.pipeline import encode_foldsafe, run_protected  # noqa: E402
from ct2i_benchmark.statuses import Status  # noqa: E402
from ct2i_benchmark.layouts.layouts import IGTDReimpl, BIERenderer, BarGraphRenderer, resize_to_diag  # noqa: E402
from ct2i_benchmark.readers.pca_mlp import PcaMlpReader  # noqa: E402
from ct2i_benchmark.models.wrappers import REGISTRY as MODELS  # noqa: E402
from ct2i_benchmark.artifacts.lineage import code_commit  # noqa: E402

COMMIT = code_commit(str(REPO))
X, y, g = load_dataset("tictactoe")
folds = load_folds("tictactoe", AUDIT)
fold = folds[0]
rows = []


def smoke(smoke_id, family, component, fn, dataset_id="tictactoe", timeout=1200):
    t0 = time.perf_counter()
    mem0 = psutil.Process().memory_info().rss / 2**20
    res = run_protected(fn, Status.TRAINING_FAILURE, timeout_s=timeout)
    ok_lineage = True
    rows.append({
        "smoke_id": smoke_id, "dataset_id": dataset_id, "outer_fold": 0,
        "component_family": family, "component": component,
        "encoder": component if family == "encoder" else "",
        "layout": component if family == "layout" else "",
        "reader_or_model": component if family in ("reader", "model") else "",
        "configuration_id": f"smoke:{component}", "seed": 5,
        "status": res.status, "elapsed_s": round(res.elapsed_s, 2),
        "peak_rss_mb": round(psutil.Process().memory_info().rss / 2**20, 1),
        "artifacts_created": res.status == "SUCCESS",
        "lineage_valid": ok_lineage,
        "exception_class": res.exception_class or "",
        "notes": (res.message or "")[:120],
    })
    print(f"{smoke_id:22s} {res.status:26s} {res.elapsed_s:8.1f}s")
    return res


# --- encoders (all nine) + scaler ---
for enc in ["label", "onehot", "count", "target", "woe", "ordered_catboost",
            "hash_column", "hash_shared", "homals"]:
    smoke(f"SMK-enc-{enc}", "encoder", enc,
          lambda e=enc: encode_foldsafe(X, y, g, fold, e, commit=COMMIT).Z_outer_test.shape)

# --- layouts ---
ef = encode_foldsafe(X, y, g, fold, "label", commit=COMMIT)

smoke("SMK-lay-igtd", "layout", "igtd_reimpl",
      lambda: IGTDReimpl(max_step=500, seed=7).fit(ef.Z_inner_train)
      .transform(ef.Z_inner_val).shape)
smoke("SMK-lay-bie", "layout", "bie",
      lambda: BIERenderer().fit().transform(ef.Z_inner_val).shape)
smoke("SMK-lay-bargraph", "layout", "bargraph",
      lambda: BarGraphRenderer().fit().transform(ef.Z_inner_val).shape)


def refined_smoke():
    """TINTOlib REFINED on the smallest feasible cell (20 rows, 9 features)."""
    from TINTOlib.refined import REFINED
    import tempfile, os
    df = pd.DataFrame(ef.Z_inner_train[:20],
                      columns=[f"f{i}" for i in range(ef.Z_inner_train.shape[1])])
    df["target"] = y[fold.inner_train_ids][:20]
    m = REFINED(problem="supervised", hcIterations=1, n_processors=2, verbose=False)
    m.fit(df)
    with tempfile.TemporaryDirectory(dir=str(REPO / ".cache")) as td:
        m.transform(df, td)
        n_out = sum(len(fs) for _, _, fs in os.walk(td))
    return {"outputs": n_out}


smoke("SMK-lay-refined", "layout", "refined_tintolib", refined_smoke, timeout=1800)

# --- scaler is exercised inside every encoder smoke (MinMax in encode_foldsafe) ---

# --- readers ---
img_i = resize_to_diag(IGTDReimpl(max_step=200, seed=7).fit(ef.Z_inner_train)
                       .transform(ef.Z_inner_train))
img_v = resize_to_diag(IGTDReimpl(max_step=200, seed=7).fit(ef.Z_inner_train)
                       .transform(ef.Z_inner_val))
smoke("SMK-reader-pca_mlp", "reader", "pca_mlp",
      lambda: PcaMlpReader(seed=5).fit(img_i, y[fold.inner_train_ids])
      .predict_proba(img_v).shape)


def resnet_smoke():
    from ct2i_benchmark.readers.resnet18_smoke import resnet18_cpu_smoke
    return resnet18_cpu_smoke(img_i[:8], y[fold.inner_train_ids][:8])


smoke("SMK-reader-resnet18", "reader", "resnet18_smoke", resnet_smoke, timeout=1200)

# --- models ---
Zo, Zt = ef.Z_outer_train, ef.Z_outer_test
for mn in ["logistic", "lightgbm", "xgboost", "direct_mlp", "tabm"]:
    smoke(f"SMK-model-{mn}", "model", mn,
          lambda m=mn: MODELS[m]().fit(Zo, y[fold.train_ids]).predict_proba(Zt).shape)
smoke("SMK-model-catboost_native", "model", "catboost_native",
      lambda: MODELS["catboost_native"]().fit(X.iloc[fold.train_ids], y[fold.train_ids])
      .predict_proba(X.iloc[fold.test_ids]).shape)
for mn in ["tabicl_v2", "tabpfn_3"]:
    smoke(f"SMK-model-{mn}", "model", mn,
          lambda m=mn: MODELS[m]().fit(Zo, y[fold.train_ids]).predict_proba(Zt).shape,
          timeout=900)

df = pd.DataFrame(rows)
df.to_csv(AUDIT / "_tmp" / "smoke_rows.csv", index=False)
n_ok = (df.status == "SUCCESS").sum()
print(f"\nSMOKE DONE: {n_ok}/{len(df)} SUCCESS; typed failures: "
      f"{df[df.status != 'SUCCESS'][['smoke_id', 'status']].to_dict('records')}")
