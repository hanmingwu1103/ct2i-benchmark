"""Phase S0 step 10: full-cell count and CPU core-hour / disk projection.

Composes the MEASURED per-cell costs in S0_CELL_COST_ROWS.csv over the exact
frozen factor grid in 01_PROTOCOL_FREEZE.yaml. Every (M, K) combination in the
design was measured directly, so no interpolation across state-space size is
involved. Costs for the unmeasured factors (marginal, tau, interaction_pairs,
delta_eta) are treated as cost-neutral: they change the numbers a cell
computes, not the amount of work, and the probe confirms cost is driven by
encoded width, n_train and learner.

Writes: simulation-results-ct2i/S0_RESOURCE_ESTIMATE.csv
"""
from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
COSTS = REPO / "simulation-results-ct2i" / "S0_CELL_COST_ROWS.csv"
MICRO = REPO / "simulation-results-ct2i" / "S0_MICROBENCHMARK_ROWS.csv"
OUT = REPO / "simulation-results-ct2i" / "S0_RESOURCE_ESTIMATE.csv"

CEILING_CORE_HOURS = 80.0
CEILING_DISK_GB = 20.0
MAX_WORKERS = 8

# ---- frozen factor grid -----------------------------------------------------
MK = [(5, 4), (5, 12), (5, 50), (20, 4), (20, 12), (20, 50)]
N_TRAIN = [500, 5000]
MARGINALS, TAUS, N_INT, DELTAS = 2, 2, 2, 3
COST_NEUTRAL = MARGINALS * TAUS * N_INT * DELTAS      # 24 DGP variants per (M,K)
REPS_1B = 50
LEARNERS = ["logistic", "lightgbm", "mlp"]

# encoder configurations: hash encoders are swept over 3 bucket widths
ENCODER_CONFIGS = {
    "label": 1, "onehot": 1, "count": 1,
    "hash_column": 3, "hash_shared": 3,
    "target": 1, "woe": 1, "ordered_catboost_sim": 1, "homals": 1,
}
HEAVY_SUBSET = ["label", "onehot", "count", "hash_column", "hash_shared", "target"]

# 1A and 1C
REPS_1A, REPS_1C = 100, 50
MK_1A = [(3, 3), (3, 4), (5, 3), (5, 4)]
ENC_1A = 11          # 5 non-hash + 2 hash x 3 widths
DGP_1A_PER_MK = 2 * 2 * 2 * 3        # marginal x tau x n_int x delta
M_1C = [10, 50, 200, 1000]
Q_1C, TGT_1C = 3, 2
ENC_1C = 9


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    cost_rows = read(COSTS)
    micro = read(MICRO)

    # measured median cell cost, keyed by (M, K, n_train, encoder, learner)
    cell = defaultdict(list)
    for r in cost_rows:
        key = (int(r["M"]), int(r["K"]), int(r["n_train"]), r["encoder"], r["learner"])
        cell[key].append(float(r["cell_s"]))
    cell = {k: statistics.median(v) for k, v in cell.items()}

    micro_med = defaultdict(list)
    for r in micro:
        if r["status"] == "SUCCESS" and r["median_elapsed_s"]:
            micro_med[(r["operation"], r["configuration"])].append(
                float(r["median_elapsed_s"]))
    micro_med = {k: statistics.median(v) for k, v in micro_med.items()}

    rows = []

    # ---------------- Simulation 1A ----------------
    a_costs = [v for (op, cfg), v in micro_med.items() if op == "sim1a_exact_cell"]
    a_mean = statistics.mean(a_costs)
    a_cells = len(MK_1A) * DGP_1A_PER_MK * ENC_1A * REPS_1A
    a_hours = a_cells * a_mean / 3600
    rows.append(dict(component="1A", variant="exact_enumeration",
                     cells=a_cells, mean_cell_s=round(a_mean, 6),
                     serial_core_hours=round(a_hours, 3),
                     wall_hours_at_8_workers=round(a_hours / MAX_WORKERS, 3),
                     disk_gb=0.02,
                     basis="measured sim1a_exact_cell median over 4 (M,K) x 4 encoders"))

    # ---------------- Simulation 1B ----------------
    for variant, heavy in [("full_factorial", None), ("fractional_proposed", HEAVY_SUBSET)]:
        total_s, n_cells = 0.0, 0
        for (M, K) in MK:
            for n_tr in N_TRAIN:
                for enc, n_widths in ENCODER_CONFIGS.items():
                    for lrn in LEARNERS:
                        if heavy is not None and lrn in ("lightgbm", "mlp") \
                           and enc not in heavy:
                            continue
                        # the fractional variant runs heavy learners at ONE width
                        widths = 1 if (heavy is not None
                                       and lrn in ("lightgbm", "mlp")) else n_widths
                        c = cell.get((M, K, n_tr, enc, lrn))
                        if c is None:
                            continue
                        k = widths * COST_NEUTRAL * REPS_1B
                        total_s += c * k
                        n_cells += k
        hours = total_s / 3600
        rows.append(dict(component="1B", variant=variant, cells=n_cells,
                         mean_cell_s=round(total_s / max(n_cells, 1), 6),
                         serial_core_hours=round(hours, 2),
                         wall_hours_at_8_workers=round(hours / MAX_WORKERS, 2),
                         disk_gb=round(n_cells * 400 / 1e9, 3),
                         basis="measured cell_s median at every (M,K,n_train,encoder,learner)"))

    # ---------------- Simulation 1C ----------------
    c_exact = [v for (op, cfg), v in micro_med.items()
               if op == "sim1c_exact_shared_value"]
    c_exact_mean = statistics.mean(c_exact)
    c_exact_cells = len(M_1C) * Q_1C * TGT_1C * REPS_1C
    # finite-sample arm reuses the 1B per-cell cost profile at comparable width
    c_finite_proxy = statistics.median(
        [v for (M, K, n, e, l), v in cell.items()
         if e in ("onehot", "hash_column", "hash_shared", "label", "count")])
    c_finite_cells = len(M_1C) * Q_1C * TGT_1C * len(N_TRAIN) * ENC_1C * REPS_1C * len(LEARNERS)
    c_hours = (c_exact_cells * c_exact_mean + c_finite_cells * c_finite_proxy) / 3600
    rows.append(dict(component="1C", variant="exact_plus_finite_sample",
                     cells=c_exact_cells + c_finite_cells,
                     mean_cell_s=round(c_finite_proxy, 6),
                     serial_core_hours=round(c_hours, 2),
                     wall_hours_at_8_workers=round(c_hours / MAX_WORKERS, 2),
                     disk_gb=round((c_exact_cells + c_finite_cells) * 400 / 1e9, 3),
                     basis="measured sim1c exact closed form + 1B cell-cost proxy for the finite arm"))

    # ---------------- Simulation 2 ----------------
    rows.append(dict(component="2", variant="reproduction_from_frozen_protocol",
                     cells=1459, mean_cell_s=0.35,
                     serial_core_hours=0.15,
                     wall_hours_at_8_workers=0.02, disk_gb=0.01,
                     basis="Stage 2 authoritative run is 1,459 vectorised scenario rows at R=10,000"))

    # ---------------- Totals ----------------
    # snapshot the component rows first, so a TOTAL never counts another TOTAL
    base_rows = list(rows)
    for variant in ("full_factorial", "fractional_proposed"):
        sel = [r for r in base_rows if r["component"] != "1B"
               or r["variant"] == variant]
        h = sum(r["serial_core_hours"] for r in sel)
        d = sum(r["disk_gb"] for r in sel)
        rows.append(dict(
            component="TOTAL", variant=variant,
            cells=sum(r["cells"] for r in sel),
            mean_cell_s="",
            serial_core_hours=round(h, 2),
            wall_hours_at_8_workers=round(h / MAX_WORKERS, 2),
            disk_gb=round(d, 3),
            basis=(f"ceiling {CEILING_CORE_HOURS} core-hours / {CEILING_DISK_GB} GB; "
                   f"{'WITHIN' if h <= CEILING_CORE_HOURS else 'EXCEEDS'} CPU ceiling; "
                   f"{'WITHIN' if d <= CEILING_DISK_GB else 'EXCEEDS'} disk ceiling")))

    rows.append(dict(component="CEILING", variant="advisor_limit", cells="",
                     mean_cell_s="", serial_core_hours=CEILING_CORE_HOURS,
                     wall_hours_at_8_workers=CEILING_CORE_HOURS / MAX_WORKERS,
                     disk_gb=CEILING_DISK_GB,
                     basis="GPU hours 0; parallel workers 8; no silent design reduction"))
    rows.append(dict(component="PEAK_MEMORY", variant="measured", cells="",
                     mean_cell_s="", serial_core_hours="", wall_hours_at_8_workers="",
                     disk_gb="",
                     basis="806 MB peak RSS per worker with chunked evaluation "
                           "(EVAL_CHUNK=10000); 8 workers => about 6.5 GB, "
                           "within the 16 GB host"))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"wrote {OUT.relative_to(REPO)}\n")
    hdr = f"{'component':12s} {'variant':32s} {'cells':>10s} {'core-h':>9s} {'wall-h/8':>9s} {'disk GB':>8s}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        if r["component"] == "PEAK_MEMORY":
            continue
        print(f"{r['component']:12s} {r['variant']:32s} {str(r['cells']):>10s} "
              f"{str(r['serial_core_hours']):>9s} {str(r['wall_hours_at_8_workers']):>9s} "
              f"{str(r['disk_gb']):>8s}")
    print()
    for r in rows:
        if r["component"] == "TOTAL":
            print(f"  {r['variant']}: {r['basis']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
