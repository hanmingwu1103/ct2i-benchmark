"""Phase S0 step 9b: end-to-end cost of ONE Simulation 1B cell, as Phase S1
will actually execute it (streaming evaluation, no full wide matrix).

A "cell" is one (scenario, replicate, encoder, learner) unit:
    OOF training codes -> learner fit -> chunked encode+predict over n_eval
    -> Rao-Blackwellised risk decomposition.

Measured at the corners of the frozen factor grid so the projection in
S0_RESOURCE_ESTIMATE.csv rests on observed costs, not guesses.

SIMULATION ONLY. No real dataset, model, or image is touched.

Writes: simulation-results-ct2i/S0_CELL_COST_ROWS.csv
"""
from __future__ import annotations

import csv
import resource
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from ct2i_benchmark.simulations import sim1_core as CORE       # noqa: E402
from ct2i_benchmark.simulations import sim1_finite as FIN      # noqa: E402

OUT = REPO / "simulation-results-ct2i" / "S0_CELL_COST_ROWS.csv"
N_EVAL = 50_000
ROWS: list[dict] = []


def peak_mb() -> float:
    ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return ru / 2 ** 20 if sys.platform == "darwin" else ru / 1024


# Every (M, K) combination in the frozen grid, so the projection in
# S0_RESOURCE_ESTIMATE.csv needs no interpolation across state-space size.
CORNERS = [(5, 4), (5, 12), (5, 50), (20, 4), (20, 12), (20, 50)]
ENCODERS = ["label", "onehot", "count", "hash_column", "hash_shared",
            "target", "woe", "ordered_catboost_sim", "homals"]
LEARNERS = ["logistic", "lightgbm", "mlp"]

print("=" * 92)
print("Phase S0 per-cell cost probe (SIMULATION ONLY)")
print(f"{'M,K':>8} {'n_tr':>6} {'encoder':>20} {'learner':>9} "
      f"{'enc_s':>8} {'fit_s':>8} {'eval_s':>8} {'cell_s':>8} {'width':>6}")
print("-" * 92)

for (M, K) in CORNERS:
    prm = CORE.draw_params(M=M, K=K, marginal="zipf", tau=1.5, n_int=3,
                           delta_eta=0.3, seed=201, d_active=3)
    t0 = time.perf_counter()
    tab = FIN.build_eta_table(prm)
    t_table = time.perf_counter() - t0

    Xev, _, eta_ev = FIN.sample_records(prm, tab, N_EVAL, 902)
    widths = FIN.bucket_widths(M, K)

    for n_train in (500, 5000):
        Xtr, ytr, _ = FIN.sample_records(prm, tab, n_train, 901)
        for enc in ENCODERS:
            # encoder fit + OOF training codes
            t0 = time.perf_counter()
            if enc in ("hash_column", "hash_shared"):
                mapping = FIN.make_sim_hash(enc == "hash_column", widths["B1"]).fit(Xtr)
                Ztr = mapping.transform(Xtr)
            else:
                Ztr = FIN.oof_train_codes(Xtr, ytr, enc, 4211)
                mapping = FIN.full_fit_mapping(Xtr, ytr, enc)
            t_enc = time.perf_counter() - t0
            width = Ztr.shape[1]

            for lrn in LEARNERS:
                t0 = time.perf_counter()
                model = FIN.make_learner(lrn, seed=7)
                model.fit(Ztr, ytr)
                t_fit = time.perf_counter() - t0

                t0 = time.perf_counter()
                p = FIN.predict_proba_chunked(mapping, model, Xev)
                d = FIN.decompose(eta_ev, eta_ev, p, "logloss")
                t_eval = time.perf_counter() - t0

                cell = t_enc / len(LEARNERS) + t_fit + t_eval
                ROWS.append({
                    "M": M, "K": K, "n_train": n_train, "encoder": enc,
                    "learner": lrn, "encoded_width": width,
                    "eta_table_s": round(t_table, 6),
                    "encode_s": round(t_enc, 4), "fit_s": round(t_fit, 4),
                    "eval_s": round(t_eval, 4), "cell_s": round(cell, 4),
                    "peak_rss_mb": round(peak_mb(), 1),
                    "learner_shortfall_sanity": round(d["learner_shortfall"], 6),
                    "status": "SUCCESS",
                })
                print(f"{M:3d},{K:<4d} {n_train:6d} {enc:>20} {lrn:>9} "
                      f"{t_enc:8.3f} {t_fit:8.3f} {t_eval:8.3f} {cell:8.3f} {width:6d}")

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(ROWS[0].keys()))
    w.writeheader()
    w.writerows(ROWS)

cs = np.array([r["cell_s"] for r in ROWS])
print("-" * 92)
print(f"wrote {OUT.relative_to(REPO)}  rows={len(ROWS)}")
print(f"cell_s: min {cs.min():.3f}  median {np.median(cs):.3f}  "
      f"mean {cs.mean():.3f}  max {cs.max():.3f}")
print(f"peak RSS: {peak_mb():.1f} MB")
