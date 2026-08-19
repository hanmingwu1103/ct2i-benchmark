"""Phase A0 step 6: timing and memory microbenchmark for the dense-signal addendum.

SIMULATION ONLY. PREFLIGHT ONLY. THIS SCRIPT PRODUCES A TIMING PROBE, NEVER AN
ADDENDUM RESULT. Its per-cell rows are written to a scratch path OUTSIDE
`simulation-results-ct2i/` and are discarded; only CPU seconds, peak RSS and
bytes-per-row are retained. No file it writes is a package artefact and none of
it may be summarised, plotted, or reported as a dense-signal finding.

Two measurement layers:

  units  M1-M8 unit-cost probes at d = 3 and d = 5 on the same host and in the
         same process, so the per-operation ratio is measured rather than
         assumed.
  e2e    ONE whole scenario end-to-end at a given d, run through a probe copy of
         the 1B scenario loop that takes `d_active` as a PARAMETER, so the d = 5
         and d = 3 arms are timed on byte-identical code and the ratio cannot be
         contaminated by an implementation difference. `run_sim1b_finite.py` is
         NOT executed; it is imported only for `ebar_coordinatewise`.

The extrapolation anchor is measured, not projected: the identically shaped
d = 3 twin (M=5, K=4; 48 scenarios, 182,400 rows) cost 5.931 core-hours,
computed as `df[(df.M==5)&(df.K==4)].cpu_seconds.sum()/3600` from the frozen
05b parquet. The microbenchmark's only job is the d = 5 / d = 3 COST RATIO.

Usage:
  s0a_addendum_microbenchmark.py units
  s0a_addendum_microbenchmark.py e2e <d_active> <n_train> <replicates>
                                     [<marginal> <tau> <n_int> <delta_eta>]
"""
from __future__ import annotations

import csv
import os
import platform
import resource
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import psutil

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from ct2i_benchmark.simulations import sim1_core as CORE       # noqa: E402
from ct2i_benchmark.simulations import sim1_design as DES      # noqa: E402
from ct2i_benchmark.simulations import sim1_finite as FIN      # noqa: E402

import run_sim1b_finite as RUNNER                              # noqa: E402  (ebar only)

OUT = REPO / "simulation-results-ct2i" / "S0A_ADDENDUM_MICROBENCHMARK_ROWS.csv"
SCRATCH = Path(os.environ.get(
    "A0_SCRATCH",
    "/private/tmp/claude-501/-Users-Eric-Desktop-114----code-result/"
    "e234d5a4-799b-49a4-b4f1-9d19ec0e4653/scratchpad/a0"))
PROC = psutil.Process()

M_ADD, K_ADD = 5, 4
N_EVAL = DES.N_EVAL
REPEATS = 3
COLS = [f"v{j}" for j in range(M_ADD)]

# addendum seed rule (mirrors 01A_ADDENDUM_PROTOCOL_FREEZE.yaml)
SEED_BASE_1BD = 2_000_000_000
OOF_BASE_1BD = 91_211


def addendum_seed(block, replicate):
    import hashlib
    h = int.from_bytes(
        hashlib.blake2b(repr(tuple(block)).encode(), digest_size=4).digest(), "little")
    return SEED_BASE_1BD + 1000 * (h % 1_000_000) + int(replicate)


def peak_rss_mb() -> float:
    ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return ru / 2 ** 20 if sys.platform == "darwin" else ru / 1024


def append_rows(rows: list[dict]) -> None:
    fields = ["layer", "operation", "d_active", "configuration", "repeats",
              "median_elapsed_s", "cpu_s", "peak_rss_mb", "output_bytes",
              "status", "notes"]
    new = not OUT.exists()
    with open(OUT, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


# ---------------------------------------------------------------------------
# units: M1 - M8
# ---------------------------------------------------------------------------

def bench(rows, op, d, config, fn, repeats=REPEATS, notes=""):
    times, status, nbytes = [], "SUCCESS", 0
    c0 = PROC.cpu_times()
    for _ in range(repeats):
        t0 = time.perf_counter()
        try:
            out = fn()
            if hasattr(out, "nbytes"):
                nbytes = int(out.nbytes)
        except Exception as e:                                   # noqa: BLE001
            status = f"FAILED:{type(e).__name__}"
            notes = (notes + " " + str(e)[:120]).strip()
            times.append(float("nan"))
            break
        times.append(time.perf_counter() - t0)
    c1 = PROC.cpu_times()
    med = float(np.median(times))
    rows.append(dict(layer="unit", operation=op, d_active=d, configuration=config,
                     repeats=repeats, median_elapsed_s=round(med, 6),
                     cpu_s=round((c1.user - c0.user) + (c1.system - c0.system), 6),
                     peak_rss_mb=round(peak_rss_mb(), 1), output_bytes=nbytes,
                     status=status, notes=notes))
    return med


def run_units() -> None:
    rows: list[dict] = []
    rows.append(dict(layer="env", operation="host", d_active="",
                     configuration=f"{platform.platform()} py{platform.python_version()} "
                                   f"cores={os.cpu_count()}",
                     repeats=0, median_elapsed_s=0, cpu_s=0,
                     peak_rss_mb=round(peak_rss_mb(), 1), output_bytes=0,
                     status="SUCCESS", notes="A0 timing probe; not an addendum result"))
    for d in (3, 5):
        blk = (M_ADD, K_ADD, "zipf", 1.5, 3)
        seed = addendum_seed(blk, 1)
        prm = CORE.draw_params(M_ADD, K_ADD, "zipf", 1.5, 3, 0.3, seed, d_active=d)
        tab = FIN.build_eta_table(prm)

        # M1 parameter draw + eta table
        bench(rows, "M1_draw_params_plus_eta_table", d, f"d{d}",
              lambda: FIN.build_eta_table(
                  CORE.draw_params(M_ADD, K_ADD, "zipf", 1.5, 3, 0.3, seed, d_active=d)),
              notes=f"eta table cells = K**d = {K_ADD ** d}")

        # M2 sampling
        for n in (5000, N_EVAL):
            bench(rows, "M2_sample_records", d, f"d{d}_n{n}",
                  lambda n=n: FIN.sample_records(prm, tab, n, seed + 100_000)[1])

        Xtr, ytr, _ = FIN.sample_records(prm, tab, 5000, seed + 100_000)
        Xtr500 = Xtr.iloc[:500].reset_index(drop=True)
        ytr500 = ytr[:500]
        Xev, _, eta_ev = FIN.sample_records(prm, tab, N_EVAL, seed + 200_000)

        # M5 encoder fit (oof + full fit), M3 ebar probe
        for enc in ["label", "onehot", "count", "target", "woe",
                    "ordered_catboost_sim", "homals"]:
            for Xs, ys, lab in ((Xtr500, ytr500, "n500"), (Xtr, ytr, "n5000")):
                bench(rows, "M5_oof_plus_full_fit", d, f"d{d}_{enc}_{lab}",
                      lambda enc=enc, Xs=Xs, ys=ys: (
                          FIN.oof_train_codes(Xs, ys, enc, OOF_BASE_1BD + 17),
                          FIN.full_fit_mapping(Xs, ys, enc)), repeats=1)
            mp = FIN.full_fit_mapping(Xtr, ytr, enc)
            bench(rows, "M3_ebar_coordinatewise", d, f"d{d}_{enc}",
                  lambda mp=mp: RUNNER.ebar_coordinatewise(mp, tab, prm)[0],
                  notes=f"probe rows = d*K = {d * K_ADD}")

        # M4 hash exact path over the full space (depends on M,K only)
        full = CORE.enumerate_cells(K_ADD, M_ADD)
        p_full = CORE.cell_probabilities(full, prm.p_marg)
        ids = np.zeros(len(full), dtype=np.int64)
        for j in range(prm.d_active):
            ids = ids * K_ADD + full[:, j]
        eta_full = tab.eta[ids]
        for Bw in (10, 20, 40):
            for ca in (True, False):
                bench(rows, "M4_hash_full_space_fibers", d,
                      f"d{d}_B{Bw}_{'col' if ca else 'shared'}",
                      lambda Bw=Bw, ca=ca: CORE.fiber_posteriors(
                          CORE.group_ids(CORE.hash_codes(full, K_ADD, Bw, ca)),
                          p_full, eta_full)[1],
                      notes="full space = K**M = 1024, independent of d")

        # M6 learner fit on encoded Z
        for enc, Bw in (("onehot", None), ("hash_column", 20)):
            if Bw is None:
                Ztr = FIN.oof_train_codes(Xtr, ytr, enc, OOF_BASE_1BD + 17)
                mp = FIN.full_fit_mapping(Xtr, ytr, enc)
            else:
                mp = FIN.make_sim_hash(True, Bw).fit(Xtr)
                Ztr = mp.transform(Xtr)
            for lrn in ("logistic", "lightgbm", "mlp"):
                bench(rows, "M6_learner_fit", d, f"d{d}_{enc}_{lrn}_n5000",
                      lambda lrn=lrn, Ztr=Ztr: FIN.make_learner(lrn, seed=seed).fit(Ztr, ytr),
                      repeats=1)
            model = FIN.make_learner("logistic", seed=seed).fit(Ztr, ytr)
            # M7 chunked evaluation prediction
            bench(rows, "M7_predict_proba_chunked_multi", d, f"d{d}_{enc}_n_eval50000",
                  lambda mp=mp, model=model: FIN.predict_proba_chunked_multi(
                      mp, {"logistic": model}, Xev)["logistic"], repeats=1)

        # M8 peak RSS after the whole d-block
        rows.append(dict(layer="unit", operation="M8_peak_rss_after_block", d_active=d,
                         configuration=f"d{d}", repeats=0, median_elapsed_s=0,
                         cpu_s=0, peak_rss_mb=round(peak_rss_mb(), 1),
                         output_bytes=0, status="SUCCESS",
                         notes="single-process probe; multiply by 8 workers for the envelope"))
    append_rows(rows)
    print(f"units: wrote {len(rows)} rows to {OUT}")


# ---------------------------------------------------------------------------
# e2e: ONE whole scenario, d_active parameterised. TIMING PROBE ONLY.
# ---------------------------------------------------------------------------

def probe_scenario(d_active: int, marginal: str, tau: float, n_int: int,
                   delta_eta: float, n_train: int, replicates: int,
                   scenario_id: str):
    """A probe copy of the 1B scenario loop with `d_active` as a parameter.

    Byte-identical work at d=3 and d=5 apart from `d_active` itself, which is
    the whole point: the ratio it yields is a measurement of the d effect and
    nothing else. Local caches, so no state leaks between d levels.
    """
    from sklearn.metrics import average_precision_score, roc_auc_score

    ru0 = resource.getrusage(resource.RUSAGE_SELF)
    t0 = time.perf_counter()
    M, K = M_ADD, K_ADD
    blk = (M, K, marginal, tau, n_int)
    hash_exact = CORE.hash_gap_identified(M, K)
    space_cache: dict = {}
    fiber_cache: dict = {}
    rows = []

    for rep in range(1, replicates + 1):
        seed = addendum_seed(blk, rep)
        prm = CORE.draw_params(M, K, marginal, tau, n_int, delta_eta, seed,
                               d_active=d_active)
        tab = FIN.build_eta_table(prm)
        Xbig, ybig, _ = FIN.sample_records(prm, tab, 5000, seed + 100_000)
        Xtr = Xbig.iloc[:n_train].reset_index(drop=True)
        ytr = ybig[:n_train]
        Xev, yev, eta_ev = FIN.sample_records(prm, tab, N_EVAL, seed + 200_000)
        ev_cell = tab.cell_ids(Xev.iloc[:, :prm.d_active].to_numpy().astype(np.int64))
        Xn = Xev.to_numpy().astype(np.int64)
        ev_key = np.zeros(len(Xev), dtype=np.int64)
        for j in range(M):
            ev_key = ev_key * K + Xn[:, j]

        if "full" not in space_cache:
            full = CORE.enumerate_cells(K, M)
            space_cache["full"] = (full, CORE.cell_probabilities(full, prm.p_marg))
        full, p_full = space_cache["full"]
        idsf = np.zeros(len(full), dtype=np.int64)
        for j in range(prm.d_active):
            idsf = idsf * K + full[:, j]

        for enc, Bw, lab in DES.encoder_configs("B", M, K):
            lrns = DES.learners_for(enc, lab)
            if enc in DES.HASH_ENC:
                mp = FIN.make_sim_hash(enc == "hash_column", Bw).fit(Xtr)
                Ztr = mp.transform(Xtr)
                key = (Bw, enc == "hash_column")
                if key not in fiber_cache:
                    fiber_cache[key] = CORE.group_ids(
                        CORE.hash_codes(full, K, Bw, enc == "hash_column"))
                fid_full = fiber_cache[key]
                _m, eb = CORE.fiber_posteriors(fid_full, p_full, tab.eta[idsf])
                ebar_ev = eb[fid_full][ev_key]
            else:
                Ztr = FIN.oof_train_codes(Xtr, ytr, enc, OOF_BASE_1BD + 17 * rep)
                mp = FIN.full_fit_mapping(Xtr, ytr, enc)
                eb_cells, _ = RUNNER.ebar_coordinatewise(mp, tab, prm)
                ebar_ev = eb_cells[ev_cell]

            models = {}
            for lrn in lrns:
                if lrn == "bayes_z_oracle":
                    continue
                models[lrn] = FIN.make_learner(lrn, seed=seed).fit(Ztr, ytr)
            preds = FIN.predict_proba_chunked_multi(mp, models, Xev) if models else {}
            preds["bayes_z_oracle"] = ebar_ev

            for lrn, p in preds.items():
                for metric in ("logloss", "brier"):
                    fn = FIN.rb_logloss if metric == "logloss" else FIN.rb_brier
                    dd = FIN.decompose(eta_ev, ebar_ev, p, metric)
                    row = dict(scenario_id=scenario_id, replicate=rep, seed=seed,
                               d_active=d_active, M=M, K=K, marginal=marginal,
                               tau=tau, interaction_count=n_int, delta_eta=delta_eta,
                               n_train=n_train, n_test=N_EVAL, encoder=enc,
                               bucket_width=Bw, width_label=lab, learner=lrn,
                               metric=metric,
                               risk_x=float(fn(eta_ev, eta_ev).mean()),
                               risk_z=dd["risk_z"], risk_learner=dd["risk_learner"],
                               representation_loss=dd["representation_loss"],
                               learner_shortfall=dd["learner_shortfall"],
                               total_excess_risk=dd["total_excess_risk"],
                               mcse=dd["mcse"], roc_auc=None, pr_auc=None,
                               theoretical_gap_status="IDENTIFIED_EXACT",
                               status="TIMING_PROBE_NOT_A_RESULT")
                    if metric == "logloss" and len(np.unique(yev)) > 1:
                        row["roc_auc"] = float(roc_auc_score(yev, p))
                        row["pr_auc"] = float(average_precision_score(yev, p))
                    rows.append(row)

    ru1 = resource.getrusage(resource.RUSAGE_SELF)
    cpu = (ru1.ru_utime - ru0.ru_utime) + (ru1.ru_stime - ru0.ru_stime)
    return rows, cpu, time.perf_counter() - t0, peak_rss_mb(), hash_exact


def run_e2e(d_active: int, n_train: int, replicates: int,
            marginal: str = "zipf", tau: float = 1.5, n_int: int = 3,
            delta_eta: float = 0.3) -> None:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    sid = f"PROBE-d{d_active}-n{n_train}-{marginal}-t{tau}-i{n_int}-de{delta_eta}"
    rows, cpu, wall, rss, _ = probe_scenario(
        d_active, marginal, tau, n_int, delta_eta, n_train, replicates, sid)
    df = pd.DataFrame(rows)
    csv_path = SCRATCH / f"TIMING_PROBE_ONLY_{sid}.csv"
    pq_path = SCRATCH / f"TIMING_PROBE_ONLY_{sid}.parquet"
    df.to_csv(csv_path, index=False)
    df.to_parquet(pq_path, index=False)
    per_rep = cpu / replicates
    append_rows([dict(
        layer="e2e", operation="whole_scenario_probe", d_active=d_active,
        configuration=(f"{marginal}_tau{tau}_nint{n_int}_delta{delta_eta}"
                       f"_n{n_train}_reps{replicates}"),
        repeats=replicates, median_elapsed_s=round(wall, 3), cpu_s=round(cpu, 3),
        peak_rss_mb=round(rss, 1),
        output_bytes=csv_path.stat().st_size, status="SUCCESS",
        notes=(f"rows={len(df)}; cpu_s_per_replicate={per_rep:.3f}; "
               f"cpu_s_per_50rep_scenario={per_rep * 50:.1f}; "
               f"csv_bytes_per_row={csv_path.stat().st_size / len(df):.1f}; "
               f"parquet_bytes_per_row={pq_path.stat().st_size / len(df):.1f}; "
               f"TIMING PROBE ONLY - scratch output, not an addendum result"))])
    print(f"e2e d={d_active} n_train={n_train} reps={replicates}: "
          f"cpu={cpu:.1f}s wall={wall:.1f}s rows={len(df)} "
          f"cpu_per_rep={per_rep:.3f}s -> per-50rep-scenario {per_rep * 50:.1f}s "
          f"rss={rss:.0f}MB")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    if sys.argv[1] == "units":
        run_units()
    elif sys.argv[1] == "e2e":
        extra = sys.argv[5:]
        if extra:
            run_e2e(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]),
                    extra[0], float(extra[1]), int(extra[2]), float(extra[3]))
        else:
            run_e2e(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
