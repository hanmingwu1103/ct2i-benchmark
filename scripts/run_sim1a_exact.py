"""Phase S1 step 2: Simulation 1A — exact theorem checks. SIMULATION ONLY.

96 DGP conditions x 11 encoder configurations x 100 replicates = 105,600 exact
cells, every one computed by full enumeration of the state space. No sampling,
no learner fitting, no real data.

Per (block, replicate, Delta_eta) the DGP parameters and eta are built ONCE and
all 11 encoders are evaluated against them, which is both faster and the reason
the encoder contrast is exactly paired.

Writes raw replicate-level rows to
  simulation-results-ct2i/raw/sim1a_replicates.csv
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from ct2i_benchmark.simulations import sim1_core as C          # noqa: E402
from ct2i_benchmark.simulations import sim1_design as D        # noqa: E402
from ct2i_benchmark.statuses import Status                     # noqa: E402

OUT = REPO / "simulation-results-ct2i" / "raw" / "sim1a_replicates.csv"
FIELDS = ["scenario_id", "replicate", "seed", "component", "M", "K", "marginal",
          "tau", "interaction_count", "delta_eta", "encoder", "bucket_width",
          "learner", "metric", "risk_x", "risk_z", "risk_learner",
          "theoretical_gap", "estimated_gap", "representation_loss",
          "learner_shortfall", "mcse", "fiber_count", "merged_fiber_count",
          "merged_fiber_mass", "max_fiber_posterior_spread", "collision_count",
          "occupied_buckets", "n_cells", "exact_or_mc", "theoretical_gap_status",
          "status", "warning", "notes"]


def hash_diagnostics(M: int, K: int, B: int, column_aware: bool) -> tuple[int, int]:
    """(collision_count, occupied_buckets) for the population token set."""
    bk = C._hash_buckets(M, K, B, column_aware)
    tokens = bk.size if column_aware else K       # shared-value: K distinct tokens
    used = len(np.unique(bk)) if column_aware else len(np.unique(bk[0]))
    return int(tokens - used), int(used)


def main(limit: int | None = None) -> int:
    scen = D.scenarios_1a()
    if limit:
        scen = scen[:limit]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    n_rows = n_fail = 0

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for si, s in enumerate(scen, 1):
            f = s.factors
            M, K, de = f["M"], f["K"], f["delta_eta"]
            configs = D.encoder_configs("A", M, K)
            for rep, seed in enumerate(s.seeds, 1):
                # ---- build the DGP once for this (block, replicate, Delta) ----
                try:
                    prm = C.draw_params(M, K, f["marginal"], f["tau"], f["n_int"],
                                        de, seed)
                    cells = C.enumerate_cells(K, prm.d_active)
                    p_cell = C.cell_probabilities(cells, prm.p_marg)
                    eta = C.impose_delta_eta(cells, p_cell,
                                             C.eta_raw(cells, prm), de)
                except Exception as e:                       # noqa: BLE001
                    for enc, B, _lab in configs:
                        for metric in ("logloss", "brier"):
                            row = {k: None for k in FIELDS}
                            row.update(scenario_id=s.scenario_id, replicate=rep,
                                       seed=seed, component="1A", M=M, K=K,
                                       marginal=f["marginal"], tau=f["tau"],
                                       interaction_count=f["n_int"], delta_eta=de,
                                       encoder=enc, bucket_width=B,
                                       learner="bayes_z_oracle", metric=metric,
                                       exact_or_mc="exact",
                                       status=Status.NUMERICAL_FAILURE.value,
                                       notes=str(e)[:150])
                            w.writerow(row); n_rows += 1; n_fail += 1
                    continue

                for enc, B, _lab in configs:
                    try:
                        fid = C.population_fibers(enc, cells, prm, B)
                        rep_d = C.exact_gap_report(fid, p_cell, eta)
                        coll, occ = (hash_diagnostics(M, K, B, enc == "hash_column")
                                     if enc in D.HASH_ENC else (None, None))
                        status, note = Status.SUCCESS.value, ""
                    except Exception as e:                   # noqa: BLE001
                        rep_d, coll, occ = None, None, None
                        status, note = Status.NUMERICAL_FAILURE.value, str(e)[:150]

                    for metric in ("logloss", "brier"):
                        row = {k: None for k in FIELDS}
                        row.update(scenario_id=s.scenario_id, replicate=rep,
                                   seed=seed, component="1A", M=M, K=K,
                                   marginal=f["marginal"], tau=f["tau"],
                                   interaction_count=f["n_int"], delta_eta=de,
                                   encoder=enc, bucket_width=B,
                                   learner="bayes_z_oracle", metric=metric,
                                   collision_count=coll, occupied_buckets=occ,
                                   exact_or_mc="exact", status=status, notes=note)
                        if rep_d is not None:
                            g = rep_d[f"gap_{metric}"]
                            row.update(
                                risk_x=rep_d[f"risk_x_{metric}"],
                                risk_z=rep_d[f"risk_z_{metric}"],
                                # the oracle predicts ebar(z): its risk IS risk_z,
                                # so the learner shortfall is exactly zero here
                                risk_learner=rep_d[f"risk_z_{metric}"],
                                theoretical_gap=rep_d[f"theoretical_gap_{metric}"],
                                estimated_gap=g,
                                representation_loss=g,
                                learner_shortfall=0.0,
                                mcse=0.0,
                                fiber_count=rep_d["fiber_count"],
                                merged_fiber_count=rep_d["merged_fiber_count"],
                                merged_fiber_mass=rep_d["merged_fiber_mass"],
                                max_fiber_posterior_spread=rep_d["max_fiber_posterior_spread"],
                                n_cells=rep_d["n_cells"] if "n_cells" in rep_d else len(cells),
                                theoretical_gap_status="IDENTIFIED_EXACT",
                            )
                        else:
                            n_fail += 1
                        w.writerow(row); n_rows += 1
            if si % 12 == 0 or si == len(scen):
                el = time.perf_counter() - t0
                print(f"  scenario {si}/{len(scen)}  rows={n_rows:,}  "
                      f"elapsed={el:.0f}s", flush=True)

    el = time.perf_counter() - t0
    print(f"\nSIM 1A DONE  rows={n_rows:,}  failures={n_fail}  "
          f"elapsed={el:.0f}s  core-hours={el/3600:.3f}")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1]) if len(sys.argv) > 1 else None))
