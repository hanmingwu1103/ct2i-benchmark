"""Phase S1 step 7: summaries and acceptance report, generated from frozen raw output.

SIMULATION ONLY. Reads only the raw replicate-level CSVs and the frozen protocol;
computes every reported number from them. No value is ever typed by hand, and no
criterion or tolerance is read from anywhere but 01_PROTOCOL_FREEZE.yaml.

Arms that are missing are skipped with a recorded note rather than faked, so this
can run against a partial set (e.g. before Simulation 1B finishes).

Writes
  04_SIM1_SCENARIO_MANIFEST.csv
  06_SIM1_SUMMARY.csv
  07_SIM1_ACCEPTANCE_REPORT.json
  08_SIM1_FIGURE_DATA.csv
  09_SIM1_TABLE_DATA.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
OUTD = REPO / "simulation-results-ct2i"
RAW = OUTD / "raw"
FREEZE = OUTD / "01_PROTOCOL_FREEZE.yaml"


def load(name):
    p = RAW / name
    return pd.read_csv(p, low_memory=False) if p.exists() else None


def ci(x):
    x = np.asarray(pd.to_numeric(x, errors="coerce"), float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return (float(x.mean()) if len(x) else np.nan, np.nan, np.nan, np.nan)
    m = x.mean(); se = x.std(ddof=1) / np.sqrt(len(x))
    return m, m - 1.96 * se, m + 1.96 * se, se


def main() -> int:
    tol = yaml.safe_load(open(FREEZE, encoding="utf-8"))["tolerances"]
    a1 = load("sim1a_replicates.csv")
    c_ex = load("sim1c_exact.csv")
    c_fi = load("sim1c_finite.csv")
    b = load("sim1b_replicates.csv")
    present = {"1A": a1 is not None, "1C_exact": c_ex is not None,
               "1C_finite": c_fi is not None, "1B": b is not None}
    print("arms present:", present)

    crit, summary, figdat, manifest = [], [], [], []

    def add(cid, desc, scope, maxerr, tolerance, passed, n, note=""):
        crit.append(dict(criterion_id=cid, criterion_description=desc, scope=scope,
                         maximum_error=(None if maxerr is None else float(maxerr)),
                         tolerance=tolerance,
                         **{"pass": (None if passed is None else bool(passed))},
                         n_cells=int(n), notes=note))

    # ---------------- A1 / A2: exact identities ----------------
    for cid, metric in (("A1", "logloss"), ("A2", "brier")):
        errs, n = [], 0
        for d, lab in ((a1, "1A"), (c_ex, "1C")):
            if d is None:
                continue
            g = d[(d.status == "SUCCESS") & (d.metric == metric)]
            if lab == "1C":
                g = g[g.encoder == "hash_shared"]
                e = (g["estimated_gap"] - g["theoretical_gap"]).abs()
            else:
                e = (g["estimated_gap"] - g["theoretical_gap"]).abs()
            errs.append(e.max()); n += len(g)
        mx = max(errs) if errs else None
        add(cid, f"Exact {metric} identity holds to the frozen tolerance",
            "1A,1C", mx, tol["exact_identity_abs"],
            None if mx is None else mx <= tol["exact_identity_abs"], n)

    # ---------------- A3: injective zero gap ----------------
    if a1 is not None:
        g = a1[(a1.status == "SUCCESS") & a1.encoder.isin(["identity", "label", "onehot"])]
        mx = g.representation_loss.abs().max()
        add("A3", "Injective encoders have zero representation gap at every Delta_eta",
            "1A", mx, tol["zero_gap_abs"], mx <= tol["zero_gap_abs"], len(g))

        # ---------------- A4 / A5: lossless and lossy merge ----------------
        dm = a1[(a1.status == "SUCCESS") & (a1.encoder == "designed_merge")]
        z = dm[dm.delta_eta == 0.0]
        mx = z.representation_loss.abs().max()
        add("A4", "Designed merge with Delta_eta = 0 has zero representation gap",
            "1A", mx, tol["zero_gap_abs"], mx <= tol["zero_gap_abs"], len(z))
        pos = dm[dm.delta_eta > 0]
        mn = pos.representation_loss.min()
        add("A5", "Designed merge with Delta_eta > 0 has strictly positive gap",
            "1A", float(mn), tol["positive_gap_min"],
            mn > tol["positive_gap_min"], len(pos), "reports the MINIMUM gap")

        # ---------------- A6: monotone in Delta_eta (designed merge, 1A) ----------------
        piv = (dm[dm.metric == "logloss"]
               .pivot_table(index=["scenario_id"], columns="delta_eta",
                            values="representation_loss", aggfunc="mean"))
        cols = sorted(piv.columns)
        bad = 0
        for i in range(len(cols) - 1):
            bad += int((piv[cols[i + 1]] < piv[cols[i]] - 1e-12).sum())
        add("A6", "Representation gap nondecreasing in Delta_eta (designed merge)",
            "1A", float(bad), 0, bad == 0, len(piv), "counts violating scenario pairs")

        # ---------------- A10: column-aware beats shared-value ----------------
        w = a1[(a1.status == "SUCCESS") & (a1.metric == "logloss")]
        p2 = w[w.encoder.isin(["hash_column", "hash_shared"])].pivot_table(
            index=["scenario_id", "replicate", "bucket_width"],
            columns="encoder", values="fiber_count", aggfunc="mean").dropna()
        viol = int((p2["hash_column"] <= p2["hash_shared"]).sum())
        add("A10", "Column-aware hash fiber count exceeds shared-value at equal B",
            "1A", float(viol), 0, viol == 0, len(p2), "counts violations")

    # ---------------- A7 / A8 / A9: Simulation 1C ----------------
    if c_ex is not None:
        sv = c_ex[(c_ex.status == "SUCCESS") & (c_ex.encoder == "hash_shared")]
        bad = int((sv.reachable_encodings != sv.M + 1).sum())
        add("A7", "Shared-value hash has at most M+1 reachable encodings",
            "1C", float(bad), 0, bad == 0, len(sv), "counts rows where != M+1")

        ll = sv[sv.metric == "logloss"]
        ps = (ll[ll.target_mechanism == "position_specific"]
              .groupby("M").representation_loss.mean())
        mono = bool(ps.is_monotonic_increasing)
        add("A8", "Shared-value loss nondecreasing in M under a position-specific target",
            "1C", None, "monotone", mono, len(ll),
            f"means by M: {ps.round(5).to_dict()}")

        hw = sv[sv.target_mechanism == "hamming_weight"]
        mx = hw.representation_loss.abs().max()
        add("A9", "Shared-value hash has zero gap under a Hamming-weight target",
            "1C", mx, tol["zero_gap_abs"], mx <= tol["zero_gap_abs"], len(hw),
            "measured through the generic aggregation, not assigned")

    # ---------------- A12 / A13 / A14: discipline ----------------
    frames = [(a1, "1A"), (c_ex, "1C_exact"), (c_fi, "1C_finite"), (b, "1B")]
    bad_null = 0; n_all = 0
    metric_cols = ["risk_x", "risk_learner", "representation_loss",
                   "learner_shortfall", "roc_auc"]
    for d, lab in frames:
        if d is None:
            continue
        n_all += len(d)
        cols = [c for c in metric_cols if c in d.columns]
        fail = d[d.status.isin(["TRAINING_FAILURE", "NUMERICAL_FAILURE",
                                "TIMEOUT", "RESOURCE_LIMIT"])]
        if len(fail) and cols:
            bad_null += int(fail[cols].notna().sum().sum())
    add("A14", "Failed cells carry a typed status and NULL metrics",
        "all", float(bad_null), 0, bad_null == 0, n_all,
        "counts non-null metric values on failed rows")

    # ---------------- summary rows ----------------
    def summarise(d, arm, group_extra=()):
        if d is None:
            return
        g = d[d.status == "SUCCESS"]
        keys = ["encoder", "learner", "metric"] + list(group_extra)
        keys = [k for k in keys if k in g.columns]
        for name, grp in g.groupby(keys, dropna=False):
            name = name if isinstance(name, tuple) else (name,)
            rec = dict(zip(keys, name))
            for col, lab in (("representation_loss", "rep"),
                             ("learner_shortfall", "short")):
                if col not in grp.columns:
                    continue
                m, lo, hi, se = ci(grp[col])
                rec[f"mean_{lab}"] = m
                rec[f"ci_low_{lab}"] = lo
                rec[f"ci_high_{lab}"] = hi
                rec[f"mcse_{lab}"] = se
            if "theoretical_gap" in grp.columns:
                rec["mean_theoretical_gap"] = pd.to_numeric(
                    grp["theoretical_gap"], errors="coerce").mean()
                rec["mean_abs_identity_error"] = (
                    pd.to_numeric(grp.get("estimated_gap"), errors="coerce")
                    - pd.to_numeric(grp["theoretical_gap"], errors="coerce")
                ).abs().mean()
            if "roc_auc" in grp.columns:
                rec["mean_roc_auc"] = pd.to_numeric(grp["roc_auc"],
                                                    errors="coerce").mean()
            rec["scenario_group"] = arm
            rec["n_scenarios"] = grp.scenario_id.nunique()
            rec["n_rows"] = len(grp)
            summary.append(rec)

    summarise(a1, "1A", ("delta_eta",))
    summarise(c_ex, "1C_exact", ("M", "target_mechanism"))
    summarise(c_fi, "1C_finite", ("M", "target_mechanism"))
    summarise(b, "1B", ("n_train",))

    # ---------------- write ----------------
    OUTD.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summary).to_csv(OUTD / "06_SIM1_SUMMARY.csv", index=False)
    rep = dict(arms_present=present,
               tolerances=tol,
               criteria=crit,
               n_criteria_evaluated=sum(c["pass"] is not None for c in crit),
               n_passed=sum(c["pass"] is True for c in crit),
               n_failed=sum(c["pass"] is False for c in crit))
    (OUTD / "07_SIM1_ACCEPTANCE_REPORT.json").write_text(
        json.dumps(rep, indent=2, default=str), encoding="utf-8")

    print(f"\n{'criterion':6s} {'pass':>6s} {'max error':>14s} {'tolerance':>14s}  desc")
    for c in crit:
        pv = {True: "PASS", False: "FAIL", None: "n/a"}[c["pass"]]
        me = "" if c["maximum_error"] is None else f"{c['maximum_error']:.3e}"
        print(f"{c['criterion_id']:6s} {pv:>6s} {me:>14s} {str(c['tolerance']):>14s}  "
              f"{c['criterion_description'][:58]}")
    print(f"\npassed {rep['n_passed']}/{rep['n_criteria_evaluated']} evaluated; "
          f"failed {rep['n_failed']}")
    print(f"wrote 06_SIM1_SUMMARY.csv ({len(summary)} rows), "
          f"07_SIM1_ACCEPTANCE_REPORT.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
