"""Shared parallel driver for the Simulation 1 finite-sample arms.

One worker process per scenario. Scenarios are independent by construction —
each draws its own DGP from its own block seed — so there is no cross-scenario
state and results are identical to a serial run. Rows are returned to the parent
and written by it, so the output file has a single writer and a deterministic
order (scenarios are re-sorted by scenario_id before writing).

Worker count is capped for memory: at M = 1000 an evaluation chunk is about
320 MB, so 8 workers plus training data would crowd a 16 GB host. The cap is
applied per scenario size rather than globally.

LightGBM is configured with n_jobs=1 in the frozen learner settings, so process
parallelism does not oversubscribe cores.
"""
from __future__ import annotations

import csv
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# keep BLAS single-threaded inside workers; parallelism is at the process level
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")


def workers_for(max_workers: int, heavy: bool) -> int:
    """Fewer workers for memory-heavy scenarios."""
    return max(1, min(max_workers, 4 if heavy else max_workers))


def run_parallel(scenarios, worker_fn, out_path, fields, max_workers=8,
                 heavy_key=None, label="run", checkpoint=True,
                 failure_rows=None):
    """Execute worker_fn(scenario) -> list[dict] across processes.

    heavy_key(scenario) -> bool marks memory-heavy scenarios, which are run in a
    second pass with a reduced worker count rather than mixed with light ones.

    WORKER / POOL FAILURE (reconciliation C2). `fu.result()` raises when a
    worker dies: a spawn or import error, an OOM kill, `BrokenProcessPool`. The
    parent used to record `results[scenario_id] = []` and write a header-only
    part file, so every attempted cell of that scenario disappeared with no
    typed row anywhere, the run still exited 0, and a restart SKIPPED the
    scenario because its part file existed.

      failure_rows(scenario, exc) -> list[dict]
          OPT-IN, and the only behaviour change. When supplied, a dead worker's
          cells are materialised by the caller as typed failure rows and those
          rows -- never an empty list -- are what is checkpointed. If the
          provider itself raises, or returns nothing, the run FAILS LOUDLY
          instead of silently retaining a gap.

    `failure_rows=None` keeps the inherited behaviour byte for byte, so the two
    existing callers (`run_sim1b_finite.py`, `run_sim1c_hash.py`, whose frozen
    output is already on disk) are unaffected.

    CHECKPOINTING. Each scenario's rows are written to their own part file the
    moment that scenario finishes, and scenarios whose part file already exists
    are skipped on restart. An eight-hour run must not lose everything to a
    laptop sleeping, a pool worker dying, or a reboot -- which is exactly what
    happened on the first attempt: macOS slept, the ProcessPoolExecutor's
    workers were killed, and the parent hung forever on futures that could
    never resolve, having completed 8 of 288 scenarios with nothing on disk.
    """
    import pathlib
    parts = pathlib.Path(str(out_path).replace(".csv", "_parts"))
    parts.mkdir(parents=True, exist_ok=True)

    def part_of(s):
        return parts / f"{s.scenario_id}.csv"

    if checkpoint:
        pending = [s for s in scenarios if not part_of(s).exists()]
        skipped = len(scenarios) - len(pending)
        if skipped:
            print(f"  [{label}] resuming: {skipped} scenarios already on disk, "
                  f"{len(pending)} to run", flush=True)
        scenarios = pending

    light = [s for s in scenarios if not (heavy_key and heavy_key(s))]
    heavy = [s for s in scenarios if heavy_key and heavy_key(s)]
    results: dict[str, list] = {}
    t0 = time.perf_counter()
    done = 0
    total = len(scenarios)

    for batch, nw in ((light, max_workers), (heavy, workers_for(max_workers, True))):
        if not batch:
            continue
        with ProcessPoolExecutor(max_workers=nw) as ex:
            futs = {ex.submit(worker_fn, s): s for s in batch}
            for fu in as_completed(futs):
                s = futs[fu]
                try:
                    results[s.scenario_id] = fu.result()
                except BaseException as e:                   # noqa: BLE001
                    print(f"  !! {s.scenario_id} FAILED: {type(e).__name__}: "
                          f"{str(e)[:120]}", flush=True)
                    if failure_rows is None:
                        if not isinstance(e, Exception):
                            raise
                        results[s.scenario_id] = []          # inherited path
                    else:
                        try:
                            made = list(failure_rows(s, e))
                        except BaseException as inner:       # noqa: BLE001
                            raise RuntimeError(
                                f"{s.scenario_id}: the worker failed with "
                                f"{type(e).__name__}: {str(e)[:120]} and the "
                                f"typed-failure-row provider itself raised "
                                f"{type(inner).__name__}: {str(inner)[:120]}; "
                                f"attempted cells cannot be accounted for and "
                                f"this run is not retainable") from inner
                        if not made:
                            raise RuntimeError(
                                f"{s.scenario_id}: the worker failed with "
                                f"{type(e).__name__}: {str(e)[:120]} and the "
                                f"typed-failure-row provider returned NO rows; "
                                f"an empty checkpoint would silently delete "
                                f"every attempted cell of this scenario")
                        print(f"     -> {len(made):,} typed failure rows "
                              f"materialised for its attempted cells",
                              flush=True)
                        results[s.scenario_id] = made
                if checkpoint:                       # persist immediately
                    with open(part_of(s), "w", newline="", encoding="utf-8") as pf:
                        pw = csv.DictWriter(pf, fieldnames=fields)
                        pw.writeheader()
                        pw.writerows(results[s.scenario_id])
                done += 1
                el = time.perf_counter() - t0
                rate = done / max(el, 1e-9)
                eta = (total - done) / rate if rate > 0 else float("nan")
                print(f"  [{label}] {done}/{total} scenarios  "
                      f"elapsed={el/60:.1f}m  eta={eta/60:.1f}m  "
                      f"(workers={nw})", flush=True)

    # merge every part file on disk, not just this session's results, so a
    # resumed run still produces the complete output
    n = 0
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for pf in sorted(parts.glob("*.csv")):
            with open(pf, newline="", encoding="utf-8") as f2:
                for row in csv.DictReader(f2):
                    w.writerow(row)
                    n += 1
    el = time.perf_counter() - t0
    print(f"[{label}] DONE rows={n:,} wall={el/60:.1f}m "
          f"core-hours~{el*max_workers/3600:.2f} (upper bound)")
    return n
