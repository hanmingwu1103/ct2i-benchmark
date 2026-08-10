"""Measured CPU microbenchmark (§16): representative operations, resource
accounting, written to _tmp/microbenchmark_rows.csv for the frozen matrix."""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import psutil

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO.parent / "audit-ct2i" / "02-pilot"
sys.path.insert(0, str(REPO / "src"))

from ct2i_benchmark.runners import load_dataset, load_folds  # noqa: E402
from ct2i_benchmark.pipeline import encode_foldsafe  # noqa: E402
from ct2i_benchmark.layouts.layouts import IGTDReimpl, BIERenderer, BarGraphRenderer, resize_to_diag  # noqa: E402
from ct2i_benchmark.readers.pca_mlp import PcaMlpReader  # noqa: E402
from ct2i_benchmark.models.wrappers import REGISTRY as MODELS  # noqa: E402

rows = []
proc = psutil.Process()


def bench(bid, op, ds, n, p, px, fn):
    cpu0 = proc.cpu_times()
    t0 = time.perf_counter()
    status, out_bytes = "SUCCESS", 0
    try:
        out = fn()
        if hasattr(out, "nbytes"):
            out_bytes = int(out.nbytes)
    except Exception as e:  # noqa: BLE001
        status = f"FAILED:{type(e).__name__}"
    el = time.perf_counter() - t0
    cpu1 = proc.cpu_times()
    cu, cs = cpu1.user - cpu0.user, cpu1.system - cpu0.system
    rows.append({"benchmark_id": bid, "operation": op, "dataset_id": ds,
                 "n_rows": n, "n_features": p, "native_pixels": px,
                 "configuration_id": f"micro:{op}", "threads": proc.num_threads(),
                 "elapsed_s": round(el, 3), "cpu_user_s": round(cu, 3),
                 "cpu_system_s": round(cs, 3),
                 "cpu_core_hours": round((cu + cs) / 3600, 6),
                 "peak_rss_mb": round(proc.memory_info().rss / 2**20, 1),
                 "output_bytes": out_bytes, "status": status, "notes": ""})
    print(f"{bid:28s} {status:10s} {el:8.2f}s")


for ds in ["tictactoe", "mushroom", "bace"]:
    X, y, g = load_dataset(ds)
    folds = load_folds(ds, AUDIT)
    fold = folds[0]
    n, p = len(X), X.shape[1]
    ef_label = encode_foldsafe(X, y, g, fold, "label")
    d = ef_label.Z_inner_train.shape[1]
    bench(f"MB-{ds}-enc-target", "target_oof_encode", ds, n, p, 0,
          lambda: encode_foldsafe(X, y, g, fold, "target").Z_outer_test)
    bench(f"MB-{ds}-enc-hash", "hash_column_encode", ds, n, p, 0,
          lambda: encode_foldsafe(X, y, g, fold, "hash_column").Z_outer_test)
    lay = IGTDReimpl(max_step=2000, seed=7)
    bench(f"MB-{ds}-igtd-fit", "igtd_fit_transform", ds, n, d, d,
          lambda: lay.fit(ef_label.Z_inner_train).transform(ef_label.Z_inner_train))
    bench(f"MB-{ds}-bie", "bie_render", ds, n, d, d * 32,
          lambda: BIERenderer().transform(ef_label.Z_inner_train))
    if d * d <= 262_144:
        bench(f"MB-{ds}-bargraph", "bargraph_render", ds, n, d, d * d,
              lambda: BarGraphRenderer().transform(ef_label.Z_inner_train))
    img = resize_to_diag(lay.fit(ef_label.Z_inner_train).transform(ef_label.Z_inner_train))
    bench(f"MB-{ds}-pca_mlp", "pca_mlp_fit", ds, len(img), 64 * 64, 64 * 64,
          lambda: PcaMlpReader(seed=1).fit(img, y[fold.inner_train_ids])
          .predict_proba(img[:10]))
    Zo, yo = ef_label.Z_outer_train, y[fold.train_ids]
    bench(f"MB-{ds}-lightgbm", "lightgbm_fit", ds, len(Zo), Zo.shape[1], 0,
          lambda: MODELS["lightgbm"]().fit(Zo, yo).predict_proba(Zo[:10]))
    bench(f"MB-{ds}-direct_mlp", "direct_mlp_fit", ds, len(Zo), Zo.shape[1], 0,
          lambda: MODELS["direct_mlp"]().fit(Zo, yo).predict_proba(Zo[:10]))
    bench(f"MB-{ds}-tabm", "tabm_fit", ds, len(Zo), Zo.shape[1], 0,
          lambda: MODELS["tabm"]().fit(Zo, yo).predict_proba(Zo[:10]))
    bench(f"MB-{ds}-tabicl", "tabicl_v2_call", ds, len(Zo), Zo.shape[1], 0,
          lambda: MODELS["tabicl_v2"]().fit(Zo, yo).predict_proba(Zo[:10]))

# ResNet-18 smoke timing (already run in smoke; repeat for the record)
X, y, g = load_dataset("tictactoe")
folds = load_folds("tictactoe", AUDIT)
ef = encode_foldsafe(X, y, g, folds[0], "label")
img = resize_to_diag(IGTDReimpl(max_step=200, seed=7)
                     .fit(ef.Z_inner_train).transform(ef.Z_inner_train))
from ct2i_benchmark.readers.resnet18_smoke import resnet18_cpu_smoke  # noqa: E402
bench("MB-resnet18-smoke", "resnet18_cpu_smoke", "tictactoe", 8, 64 * 64, 224 * 224,
      lambda: np.array([resnet18_cpu_smoke(img[:8], y[folds[0].inner_train_ids][:8])["elapsed_s"]]))

pd.DataFrame(rows).to_csv(AUDIT / "_tmp" / "microbenchmark_rows.csv", index=False)
print("MICROBENCHMARK DONE")
