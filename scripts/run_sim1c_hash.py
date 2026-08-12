"""Phase S1 step 3: Simulation 1C — shared-value hash collapse. SIMULATION ONLY.

Two arms:

  exact   closed-form population risks and gaps for the shared-value hash, plus
          reachable-encoding counts, occupied buckets and collision counts for
          both hash encoders. No sampling.
  finite  binary records drawn and fitted learners evaluated on the encoded
          representation, streamed over the evaluation sample.

Usage:  run_sim1c_hash.py [exact|finite|both] [limit]

Writes  simulation-results-ct2i/raw/sim1c_exact.csv
        simulation-results-ct2i/raw/sim1c_finite.csv
"""
from __future__ import annotations

import csv
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from ct2i_benchmark.simulations import sim1_binary as B        # noqa: E402
from ct2i_benchmark.simulations import sim1_design as D        # noqa: E402
from ct2i_benchmark.simulations import sim1_finite as F        # noqa: E402
from ct2i_benchmark.statuses import Status                     # noqa: E402

RAW = REPO / "simulation-results-ct2i" / "raw"
EXACT_FIELDS = ["scenario_id", "replicate", "seed", "component", "M",
                "activation_rate", "target_mechanism", "tau", "encoder",
                "bucket_width", "width_label", "metric", "risk_x", "risk_z",
                "theoretical_gap", "estimated_gap", "representation_loss",
                "identity_error", "mcse", "fiber_count", "reachable_encodings",
                "occupied_buckets", "collision_count",
                "max_fiber_posterior_spread", "active_block_injective",
                "exact_or_mc", "theoretical_gap_status", "status", "notes"]
FINITE_FIELDS = ["scenario_id", "replicate", "seed", "component", "M",
                 "activation_rate", "target_mechanism", "n_train", "encoder",
                 "bucket_width", "width_label", "learner", "metric",
                 "risk_x", "risk_z", "risk_learner", "representation_loss",
                 "learner_shortfall", "total_excess_risk", "mcse",
                 "roc_auc", "pr_auc", "occupied_buckets", "collision_count",
                 "theoretical_gap_status", "status", "notes"]


def sample_binary(M, q, target, tau, n, seed, eta_pat=None):
    """Draw n binary records and their exact eta."""
    rng = np.random.default_rng(seed)
    Xb = (rng.random((n, M)) < q).astype(np.int8)
    if target == "hamming_weight":
        eta = B.hamming_weight_eta(M, q, tau)[Xb.sum(axis=1)]
    else:
        idx = Xb[:, :B.S_ACTIVE] @ (2 ** np.arange(B.S_ACTIVE - 1, -1, -1))
        eta = eta_pat[idx]
    y = (rng.random(n) < eta).astype(np.int8)
    X = pd.DataFrame(Xb.astype(str), columns=[f"v{j}" for j in range(M)])
    return X, y, eta


def run_exact(scen, writer):
    n = 0
    seen = set()
    for s in scen:
        f = s.factors
        M, q, tgt = f["M"], f["activation_rate"], f["target_mechanism"]
        key = (M, q, tgt)
        if key in seen:            # n_train does not affect the exact arm
            continue
        seen.add(key)
        widths = D.bucket_widths(M, 2)
        for rep, seed in enumerate(s.seeds, 1):
            for lab, Bw in widths.items():
                try:
                    r = B.exact_1c_shared_value(M=M, q=q, tau=D.TAU_1C,
                                                target=tgt, B=Bw, seed=seed)
                    ca = B.column_aware_diagnostics(M, Bw)
                    inj = B.column_aware_active_block_injective(M, Bw)
                    st, note = Status.SUCCESS.value, ""
                except Exception as e:                        # noqa: BLE001
                    r, ca, inj = None, None, None
                    st, note = Status.NUMERICAL_FAILURE.value, str(e)[:150]

                for enc in ("hash_shared", "hash_column"):
                    for metric in ("logloss", "brier"):
                        row = {k: None for k in EXACT_FIELDS}
                        row.update(scenario_id=s.scenario_id, replicate=rep,
                                   seed=seed, component="1C", M=M,
                                   activation_rate=q, target_mechanism=tgt,
                                   tau=D.TAU_1C, encoder=enc, bucket_width=Bw,
                                   width_label=lab, metric=metric,
                                   exact_or_mc="exact", status=st, notes=note)
                        if r is not None:
                            row.update(occupied_buckets=ca["occupied_buckets"],
                                       collision_count=ca["collision_count"],
                                       active_block_injective=bool(inj))
                            if enc == "hash_shared":
                                g = r[f"gap_{metric}"]
                                row.update(
                                    risk_x=r[f"risk_x_{metric}"],
                                    risk_z=r[f"risk_z_{metric}"],
                                    theoretical_gap=r[f"theoretical_gap_{metric}"],
                                    estimated_gap=g, representation_loss=g,
                                    identity_error=r[f"identity_error_{metric}"],
                                    mcse=0.0, fiber_count=r["fiber_count"],
                                    reachable_encodings=r["reachable_encodings"],
                                    max_fiber_posterior_spread=r["max_fiber_posterior_spread"],
                                    theoretical_gap_status="IDENTIFIED_EXACT")
                            else:
                                # column-aware fibers mix all M coordinates:
                                # the population gap is not identified here
                                row.update(theoretical_gap_status="NOT_IDENTIFIED")
                        writer.writerow(row); n += 1
    return n


def finite_worker(s):
    """All rows for ONE scenario. Runs in its own process; no shared state."""
    rows = []
    if True:
        f = s.factors
        M, q, tgt, n_tr = (f["M"], f["activation_rate"],
                           f["target_mechanism"], f["n_train"])
        widths = D.bucket_widths(M, 2)
        for rep, seed in enumerate(s.seeds, 1):
            ep = (B.position_specific_eta(q, D.TAU_1C, seed)
                  if tgt == "position_specific" else None)  # noqa: F841
            Xtr, ytr, _ = sample_binary(M, q, tgt, D.TAU_1C, n_tr, seed + 1, ep)
            Xev, yev, eta_ev = sample_binary(M, q, tgt, D.TAU_1C,
                                             D.N_EVAL, seed + 2, ep)
            for enc, Bw, lab in D.encoder_configs("C", M, 2):
                lrns = [l for l in D.learners_for(enc, lab) if l != "bayes_z_oracle"]
                base = dict(scenario_id=s.scenario_id, replicate=rep, seed=seed,
                            component="1C", M=M, activation_rate=q,
                            target_mechanism=tgt, n_train=n_tr, encoder=enc,
                            bucket_width=Bw, width_label=lab,
                            theoretical_gap_status=(
                                "IDENTIFIED_EXACT" if enc == "hash_shared"
                                else "NOT_IDENTIFIED"))
                try:
                    # encode + fit every learner of this encoder, then predict
                    # the evaluation sample ONCE for all of them
                    if enc in D.HASH_ENC:
                        mp = F.make_sim_hash(enc == "hash_column", Bw).fit(Xtr)
                        Ztr = mp.transform(Xtr)
                    else:
                        Ztr = F.oof_train_codes(Xtr, ytr, enc, 4211 + 17 * rep)
                        mp = F.full_fit_mapping(Xtr, ytr, enc)
                    models = {}
                    for lrn in lrns:
                        mo = F.make_learner(lrn, seed=seed)
                        mo.fit(Ztr, ytr)
                        models[lrn] = mo
                    preds = F.predict_proba_chunked_multi(mp, models, Xev)
                    two_class = len(np.unique(yev)) > 1
                    for lrn, p in preds.items():
                        for metric in ("logloss", "brier"):
                            d = F.decompose(eta_ev, eta_ev, p, metric)
                            r2 = {k: None for k in FINITE_FIELDS}
                            r2.update(base, learner=lrn, metric=metric,
                                      risk_x=d["risk_x"], risk_z=d["risk_z"],
                                      risk_learner=d["risk_learner"],
                                      learner_shortfall=d["learner_shortfall"],
                                      total_excess_risk=d["total_excess_risk"],
                                      mcse=d["mcse"], status=Status.SUCCESS.value)
                            if metric == "logloss" and two_class:
                                from sklearn.metrics import (average_precision_score,
                                                             roc_auc_score)
                                r2["roc_auc"] = float(roc_auc_score(yev, p))
                                r2["pr_auc"] = float(average_precision_score(yev, p))
                            elif metric == "logloss":
                                r2["status"] = Status.METRIC_UNDEFINED.value
                            rows.append(r2)
                except Exception as e:                         # noqa: BLE001
                    for lrn in lrns:
                        for metric in ("logloss", "brier"):
                            r2 = {k: None for k in FINITE_FIELDS}
                            r2.update(base, learner=lrn, metric=metric,
                                      status=Status.TRAINING_FAILURE.value,
                                      notes=str(e)[:150])
                            rows.append(r2)
    return rows


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    scen = D.scenarios_1c()
    RAW.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()

    if mode in ("exact", "both"):
        with open(RAW / "sim1c_exact.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=EXACT_FIELDS); w.writeheader()
            n = run_exact(scen, w)
        print(f"SIM 1C EXACT DONE rows={n:,} elapsed={time.perf_counter()-t0:.0f}s")

    if mode in ("finite", "both"):
        from _s1_parallel import run_parallel
        todo = scen[:limit] if limit else scen
        run_parallel(todo, finite_worker, RAW / "sim1c_finite.csv",
                     FINITE_FIELDS, max_workers=int(os.environ.get("S1_WORKERS", 8)),
                     heavy_key=lambda s: s.factors["M"] >= 200, label="1C finite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
