"""Phase S1 step 4: Simulation 1B — finite-sample encoding and learner study.

SIMULATION ONLY. Option B (fractional) per S1_AUTHORIZATION_AND_DECISIONS.md:
all 288 DGP scenarios and all 13 encoder configurations run with the Bayes-on-Z
oracle and logistic regression; LightGBM and the MLP run on a representative
encoder subset at one bucket width.

Population Bayes-on-Z, per the frozen per-cell identification rule:

  coordinate-wise encoders  eta depends only on the active block and these
                            encoders act per coordinate, so the fibers over the
                            active block are enumerable and ebar(z) is EXACT.
                            For the sample-fitted encoders this is exact
                            CONDITIONAL on the fitted mapping, which is the
                            frozen convention.
  hash encoders             fibers mix all M coordinates. Exact when the full
                            space enumerates (K**M <= 1e6, i.e. M=5 with K in
                            {4,12}); otherwise NOT_IDENTIFIED, and BOTH
                            representation_loss and learner_shortfall are NULL
                            because both require R_Bayes(Z). Only
                            total_excess_risk survives there.

Real CPU time is accounted per scenario (resource.getrusage in the worker) so
the resource report rests on measurement rather than another projection.

Usage: run_sim1b_finite.py [limit]        env: S1_WORKERS (default 8)
"""
from __future__ import annotations

import os
import resource
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from ct2i_benchmark.simulations import sim1_core as C          # noqa: E402
from ct2i_benchmark.simulations import sim1_design as D        # noqa: E402
from ct2i_benchmark.simulations import sim1_finite as F        # noqa: E402
from ct2i_benchmark.statuses import Status                     # noqa: E402

RAW = REPO / "simulation-results-ct2i" / "raw"
FIELDS = ["scenario_id", "replicate", "seed", "component", "M", "K", "marginal",
          "tau", "interaction_count", "delta_eta", "n_train", "n_test",
          "encoder", "bucket_width", "width_label", "learner", "metric",
          "risk_x", "risk_z", "risk_learner", "theoretical_gap", "estimated_gap",
          "representation_loss", "learner_shortfall", "total_excess_risk",
          "mcse", "roc_auc", "pr_auc", "fiber_count", "collision_count",
          "occupied_buckets", "exact_or_mc", "theoretical_gap_status",
          "cpu_seconds", "status", "warning", "notes"]


# per-worker caches: one worker handles one scenario, so these are shared by
# that scenario's 50 replicates and cleared when the process exits
_SPACE: dict = {}
_FIBER: dict = {}


def _space_cache(K, M, prm):
    """(full cells, cell probabilities, active-block index) for the full space."""
    key = (K, M, prm.marginal)
    if key not in _SPACE:
        full = C.enumerate_cells(K, M)
        p_full = C.cell_probabilities(full, prm.p_marg)
        ids = np.zeros(len(full), dtype=np.int64)
        for j in range(prm.d_active):
            ids = ids * K + full[:, j]
        _SPACE[key] = (full, p_full, ids)
    return _SPACE[key]


def _fiber_cache(K, M, Bw, column_aware, full):
    """Hash fiber partition of the full space; independent of the DGP draw."""
    key = (K, M, Bw, column_aware)
    if key not in _FIBER:
        _FIBER[key] = C.group_ids(C.hash_codes(full, K, Bw, column_aware))
    return _FIBER[key]


def ebar_coordinatewise(mapping, tab, prm):
    """Exact ebar per active-block cell under a coordinate-wise fitted mapping.

    Every non-hash encoder here (label, one-hot, count, target, WoE, ordered
    CatBoost, HOMALS) maps a cell coordinate-by-coordinate: the code contributed
    by column j depends only on that column's level. The active-block fiber is
    therefore the PRODUCT of the per-coordinate level partitions, so it can be
    obtained by encoding the K distinct levels of each active coordinate rather
    than all K**d cells.

    That matters a lot: at M=20, K=50 the direct route encodes 125,000 cells and
    one-hot returns a 125,000 x 1020 matrix -- about 1 GB, rebuilt for every
    encoder and every replicate. This route encodes d*K = 150 rows instead.
    Output is identical, and a property test asserts that on a small case.
    """
    import pandas as pd
    d, K, M = prm.d_active, prm.K, prm.M
    cols = [f"v{j}" for j in range(M)]

    # probe: for active coordinate j, vary its level over 0..K-1 and hold the
    # others at level 0, so the varying part of the code isolates column j
    per_coord = []
    for j in range(d):
        probe = pd.DataFrame({c: ["0"] * K for c in cols})
        probe[f"v{j}"] = [str(k) for k in range(K)]
        Zc = mapping.transform(probe)
        # group levels of column j that produce an identical code row
        per_coord.append(C.group_ids(C.quantize(Zc)))

    # combine per-coordinate group ids into the product partition
    fid = np.zeros(len(tab.cells), dtype=np.int64)
    for j in range(d):
        g = per_coord[j]
        fid = fid * (int(g.max()) + 1) + g[tab.cells[:, j]]
    fid = C.group_ids(fid.reshape(-1, 1))

    mass, ebar = C.fiber_posteriors(fid, tab.p_cell, tab.eta)
    return ebar[fid], fid


def scenario_worker(s):
    """All rows for ONE 1B scenario, in its own process."""
    ru0 = resource.getrusage(resource.RUSAGE_SELF)
    rows = []
    f = s.factors
    M, K, de, n_tr = f["M"], f["K"], f["delta_eta"], f["n_train"]
    n_test = D.N_EVAL
    hash_exact = C.hash_gap_identified(M, K)

    for rep, seed in enumerate(s.seeds, 1):
        try:
            prm = C.draw_params(M, K, f["marginal"], f["tau"], f["n_int"], de,
                                seed, d_active=D.D_ACTIVE_1B)
            tab = F.build_eta_table(prm)
            # nested training sizes: n=500 is the first 500 rows of the n=5000 draw
            Xbig, ybig, _ = F.sample_records(prm, tab, 5000, seed + 100_000)
            Xtr, ytr = Xbig.iloc[:n_tr].reset_index(drop=True), ybig[:n_tr]
            Xev, yev, eta_ev = F.sample_records(prm, tab, n_test, seed + 200_000)
            ev_cell = tab.cell_ids(
                Xev.iloc[:, :prm.d_active].to_numpy().astype(np.int64))
            ev_key = None
            if hash_exact:                     # full-space index of each eval row
                Xn = Xev.to_numpy().astype(np.int64)
                ev_key = np.zeros(len(Xev), dtype=np.int64)
                for j in range(M):
                    ev_key = ev_key * K + Xn[:, j]
        except Exception as e:                                  # noqa: BLE001
            continue

        for enc, Bw, lab in D.encoder_configs("B", M, K):
            lrns = D.learners_for(enc, lab)
            base = dict(scenario_id=s.scenario_id, replicate=rep, seed=seed,
                        component="1B", M=M, K=K, marginal=f["marginal"],
                        tau=f["tau"], interaction_count=f["n_int"], delta_eta=de,
                        n_train=n_tr, n_test=n_test, encoder=enc,
                        bucket_width=Bw, width_label=lab, exact_or_mc="mc")
            try:
                # ---- fit encoder ----
                if enc in D.HASH_ENC:
                    mp = F.make_sim_hash(enc == "hash_column", Bw).fit(Xtr)
                    Ztr = mp.transform(Xtr)
                else:
                    Ztr = F.oof_train_codes(Xtr, ytr, enc, 4211 + 17 * rep)
                    mp = F.full_fit_mapping(Xtr, ytr, enc)

                # ---- population ebar on the evaluation rows ----
                gap_status, ebar_ev, fib = "NOT_IDENTIFIED", None, None
                if enc in D.HASH_ENC:
                    if hash_exact:
                        # The full-space enumeration, its cell probabilities,
                        # the active-block index and the hash fiber partition
                        # depend only on (M, K, marginal, B, column_aware) --
                        # NOT on the replicate. Recomputing them per replicate
                        # was pure waste: at M=5, K=12 that is a 248,832-row
                        # enumeration repeated 50 times per hash config. Only
                        # eta_full varies with the DGP draw.
                        full, p_full, ids = _space_cache(K, M, prm)
                        fid_full = _fiber_cache(K, M, Bw, enc == "hash_column",
                                                full)
                        eta_full = tab.eta[ids]
                        _m, eb = C.fiber_posteriors(fid_full, p_full, eta_full)
                        ebar_ev = eb[fid_full][ev_key]
                        fib = int(eb.size)
                        gap_status = "IDENTIFIED_EXACT"
                else:
                    eb_cells, fid_cells = ebar_coordinatewise(mp, tab, prm)
                    ebar_ev = eb_cells[ev_cell]
                    fib = int(len(np.unique(fid_cells)))
                    gap_status = "IDENTIFIED_EXACT"

                # ---- fit learners, predict evaluation sample once ----
                models = {}
                for lrn in lrns:
                    if lrn == "bayes_z_oracle":
                        continue
                    mo = F.make_learner(lrn, seed=seed)
                    mo.fit(Ztr, ytr)
                    models[lrn] = mo
                preds = F.predict_proba_chunked_multi(mp, models, Xev) if models else {}
                if "bayes_z_oracle" in lrns and ebar_ev is not None:
                    preds["bayes_z_oracle"] = ebar_ev

                two_class = len(np.unique(yev)) > 1
                for lrn, p in preds.items():
                    for metric in ("logloss", "brier"):
                        row = {k: None for k in FIELDS}
                        row.update(base, learner=lrn, metric=metric,
                                   fiber_count=fib,
                                   theoretical_gap_status=gap_status,
                                   status=Status.SUCCESS.value)
                        fn = F.rb_logloss if metric == "logloss" else F.rb_brier
                        r_x = float(fn(eta_ev, eta_ev).mean())
                        r_l = float(fn(eta_ev, p).mean())
                        row.update(risk_x=r_x, risk_learner=r_l,
                                   total_excess_risk=r_l - r_x)
                        if ebar_ev is not None:
                            d = F.decompose(eta_ev, ebar_ev, p, metric)
                            row.update(risk_z=d["risk_z"],
                                       representation_loss=d["representation_loss"],
                                       learner_shortfall=d["learner_shortfall"],
                                       estimated_gap=d["representation_loss"],
                                       theoretical_gap=d["representation_loss"],
                                       mcse=d["mcse"])
                        if metric == "logloss":
                            if two_class:
                                from sklearn.metrics import (average_precision_score,
                                                             roc_auc_score)
                                row["roc_auc"] = float(roc_auc_score(yev, p))
                                row["pr_auc"] = float(average_precision_score(yev, p))
                            else:
                                row["status"] = Status.METRIC_UNDEFINED.value
                        rows.append(row)
            except Exception as e:                              # noqa: BLE001
                for lrn in lrns:
                    for metric in ("logloss", "brier"):
                        row = {k: None for k in FIELDS}
                        row.update(base, learner=lrn, metric=metric,
                                   status=Status.TRAINING_FAILURE.value,
                                   notes=f"{type(e).__name__}: {str(e)[:120]}")
                        rows.append(row)

    ru1 = resource.getrusage(resource.RUSAGE_SELF)
    cpu = (ru1.ru_utime - ru0.ru_utime) + (ru1.ru_stime - ru0.ru_stime)
    for r in rows:
        r["cpu_seconds"] = round(cpu / max(len(rows), 1), 6)
    return rows


def main() -> int:
    from _s1_parallel import run_parallel
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    scen = D.scenarios_1b()
    todo = scen[:limit] if limit else scen
    RAW.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    n = run_parallel(todo, scenario_worker, RAW / "sim1b_replicates.csv", FIELDS,
                     max_workers=int(os.environ.get("S1_WORKERS", 8)),
                     heavy_key=lambda s: s.factors["K"] >= 50 and s.factors["M"] >= 20,
                     label="1B")
    print(f"SIM 1B wall={(time.perf_counter()-t0)/60:.1f}m rows={n:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
