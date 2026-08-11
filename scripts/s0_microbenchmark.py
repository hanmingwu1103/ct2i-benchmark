"""Phase S0 step 9: small timing and memory microbenchmark. SIMULATION ONLY.

Measures the unit cost of every operation the Phase S1 run is built from, at
the frozen factor levels, then step 10 composes those unit costs into a
full-cell count and a CPU core-hour / disk projection.

This script touches no real dataset, no real-data model, and no image. It only
imports the simulation modules and fits learners on synthetic draws.

Writes: simulation-results-ct2i/S0_MICROBENCHMARK_ROWS.csv
"""
from __future__ import annotations

import csv
import platform
import resource
import sys
import time
from pathlib import Path

import numpy as np
import psutil

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from ct2i_benchmark.simulations import sim1_binary as B1C      # noqa: E402
from ct2i_benchmark.simulations import sim1_core as CORE       # noqa: E402
from ct2i_benchmark.simulations import sim1_finite as FIN      # noqa: E402

OUT = REPO / "simulation-results-ct2i" / "S0_MICROBENCHMARK_ROWS.csv"
PROC = psutil.Process()
ROWS: list[dict] = []

# Deliberately small: this is a unit-cost probe, not a pilot run.
N_EVAL_PROBE = 50_000
REPEATS = 3


def peak_rss_mb() -> float:
    ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS reports bytes, Linux reports kilobytes
    return ru / 2 ** 20 if sys.platform == "darwin" else ru / 1024


def bench(op: str, component: str, config: str, fn, repeats: int = REPEATS,
          notes: str = "") -> float:
    """Time fn `repeats` times, record the MEDIAN, return it in seconds."""
    times, status, out_bytes = [], "SUCCESS", 0
    for _ in range(repeats):
        c0, t0 = PROC.cpu_times(), time.perf_counter()
        try:
            out = fn()
            if hasattr(out, "nbytes"):
                out_bytes = int(out.nbytes)
        except Exception as e:  # noqa: BLE001
            status = f"FAILED:{type(e).__name__}"
            times.append(float("nan"))
            notes = (notes + " " + str(e)[:120]).strip()
            break
        el = time.perf_counter() - t0
        c1 = PROC.cpu_times()
        times.append(el)
        cpu = (c1.user - c0.user) + (c1.system - c0.system)
    med = float(np.median(times))
    ROWS.append({
        "operation": op, "component": component, "configuration": config,
        "repeats": repeats, "median_elapsed_s": round(med, 6),
        "cpu_s_last_rep": round(cpu, 6) if status == "SUCCESS" else "",
        "peak_rss_mb": round(peak_rss_mb(), 1),
        "output_bytes": out_bytes, "status": status, "notes": notes,
    })
    print(f"  {op:38s} {config:26s} {med*1000:10.2f} ms  {status}")
    return med


print("=" * 78)
print("Phase S0 microbenchmark  (SIMULATION ONLY - no real data touched)")
print("=" * 78)

# ---------------------------------------------------------------------------
# 1A: exact enumeration cost, per (M, K) and encoder
# ---------------------------------------------------------------------------
print("\n[1A] exact enumeration")
for (M, K) in [(3, 3), (3, 4), (5, 3), (5, 4)]:
    for enc, B in [("designed_merge", None), ("count_pop", None),
                   ("hash_column", 2 * M * K), ("hash_shared", 2 * M * K)]:
        bench("sim1a_exact_cell", "1A", f"M{M}_K{K}_{enc}",
              lambda M=M, K=K, enc=enc, B=B: CORE.exact_scenario(
                  M=M, K=K, marginal="zipf", tau=1.5, n_int=2,
                  delta_eta=0.3, seed=101, encoder=enc, B=B))

# ---------------------------------------------------------------------------
# 1B: DGP table, sampling, encoding, learner fits
# ---------------------------------------------------------------------------
print("\n[1B] eta table construction (once per scenario x replicate)")
tables = {}
for (M, K) in [(5, 4), (20, 12), (20, 50)]:
    prm = CORE.draw_params(M=M, K=K, marginal="zipf", tau=1.5, n_int=3,
                           delta_eta=0.3, seed=201, d_active=3)
    tables[(M, K)] = (prm, FIN.build_eta_table(prm))
    bench("sim1b_eta_table", "1B", f"M{M}_K{K}",
          lambda prm=prm: FIN.build_eta_table(prm), repeats=2)

print("\n[1B] record sampling")
for (M, K), (prm, tab) in tables.items():
    for n in (500, 5000, N_EVAL_PROBE):
        bench("sim1b_sample_records", "1B", f"M{M}_K{K}_n{n}",
              lambda prm=prm, tab=tab, n=n: FIN.sample_records(prm, tab, n, 777)[1])

print("\n[1B] encoder fit + transform  (train OOF codes, then eval transform)")
enc_widths = {}
for (M, K), (prm, tab) in tables.items():
    for n_train in (500, 5000):
        Xtr, ytr, _ = FIN.sample_records(prm, tab, n_train, 811)
        Xev, _, _ = FIN.sample_records(prm, tab, N_EVAL_PROBE, 812)
        for enc in ["label", "onehot", "count", "hash_column", "hash_shared",
                    "target", "woe", "ordered_catboost_sim", "homals"]:
            cfg = f"M{M}_K{K}_n{n_train}_{enc}"
            bench("sim1b_oof_train_codes", "1B", cfg,
                  lambda X=Xtr, y=ytr, e=enc: FIN.oof_train_codes(X, y, e, 4211),
                  repeats=2)
            try:
                mapping = FIN.full_fit_mapping(Xtr, ytr, enc)
                bench("sim1b_eval_transform", "1B", cfg,
                      lambda m=mapping, X=Xev: m.transform(X), repeats=2)
                enc_widths[cfg] = int(mapping.transform(Xev.iloc[:5]).shape[1])
            except Exception as e:  # noqa: BLE001
                ROWS.append({"operation": "sim1b_eval_transform", "component": "1B",
                             "configuration": cfg, "repeats": 0,
                             "median_elapsed_s": "", "cpu_s_last_rep": "",
                             "peak_rss_mb": round(peak_rss_mb(), 1),
                             "output_bytes": 0, "status": f"FAILED:{type(e).__name__}",
                             "notes": str(e)[:150]})

print("\n[1B] learner fit + predict on the evaluation sample")
for (M, K), (prm, tab) in [((20, 50), tables[(20, 50)])]:
    Xtr, ytr, _ = FIN.sample_records(prm, tab, 5000, 821)
    Xev, _, _ = FIN.sample_records(prm, tab, N_EVAL_PROBE, 822)
    for enc, width_label in [("label", "narrow"), ("onehot", "wide")]:
        mapping = FIN.full_fit_mapping(Xtr, ytr, enc)
        Ztr = FIN.oof_train_codes(Xtr, ytr, enc, 4211)
        Zev = mapping.transform(Xev)
        for n_train in (500, 5000):
            Zt, yt = Ztr[:n_train], ytr[:n_train]
            for lname in ("logistic", "lightgbm", "mlp"):
                cfg = f"{enc}({width_label},d={Ztr.shape[1]})_n{n_train}_{lname}"

                def _fit_predict(Zt=Zt, yt=yt, Zev=Zev, lname=lname):
                    m = FIN.make_learner(lname, seed=7)
                    m.fit(Zt, yt)
                    return m.predict_proba(Zev)[:, 1]
                bench("sim1b_learner_fit_predict", "1B", cfg, _fit_predict, repeats=2)

# ---------------------------------------------------------------------------
# 1C: exact closed form and binary diagnostics
# ---------------------------------------------------------------------------
print("\n[1C] exact closed form and hash diagnostics")
for M in (10, 50, 200, 1000):
    for tgt in ("position_specific", "hamming_weight"):
        bench("sim1c_exact_shared_value", "1C", f"M{M}_{tgt}",
              lambda M=M, t=tgt: B1C.exact_1c_shared_value(
                  M=M, q=0.20, tau=1.5, target=t, B=2 * M, seed=401))
    bench("sim1c_column_aware_diagnostics", "1C", f"M{M}",
          lambda M=M: B1C.column_aware_diagnostics(M, 2 * M))
    bench("sim1c_column_aware_injectivity", "1C", f"M{M}",
          lambda M=M: B1C.column_aware_active_block_injective(M, 2 * M))

# ---------------------------------------------------------------------------
# Write rows
# ---------------------------------------------------------------------------
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["operation", "component", "configuration",
                                      "repeats", "median_elapsed_s",
                                      "cpu_s_last_rep", "peak_rss_mb",
                                      "output_bytes", "status", "notes"])
    w.writeheader()
    w.writerows(ROWS)

print("\n" + "=" * 78)
print(f"wrote {OUT.relative_to(REPO)}   rows={len(ROWS)}")
print(f"peak RSS this process: {peak_rss_mb():.1f} MB")
print(f"platform: {platform.platform()}  python {platform.python_version()}")
print(f"logical cores: {psutil.cpu_count()}  physical: {psutil.cpu_count(logical=False)}")
failed = [r for r in ROWS if r["status"] != "SUCCESS"]
print(f"failed probes: {len(failed)}")
for r in failed:
    print("  ", r["operation"], r["configuration"], r["status"], r["notes"][:80])
