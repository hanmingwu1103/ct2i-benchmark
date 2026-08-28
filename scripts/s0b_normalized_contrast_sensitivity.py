"""Phase A0.1 / D16: how far does the NORMALIZED d=5 minus d=3 contrast move

TERMINAL STATUS (2026-08-25)
----------------------------
The dense-signal M = 5, K = 4, d = 5 addendum was PERMANENTLY DISCONTINUED
BEFORE EXECUTION by the advisor.  addendum_run = false;
addendum_status = TERMINATED_BEFORE_EXECUTION; full addendum cells run: 0;
Phase A1 will never run.  Nothing here is pending, planned or awaiting
approval.  This script is retained ONLY as design-audit provenance; nothing it
measures is a study result.  Decision record:
simulation-results-ct2i/DENSE_ADDENDUM_DECISION.md
when a competent implementer resolves what D16 leaves unsaid?

WHY THIS EXISTS
---------------
Three A0.1 documents state the normalized (signal-normalized) d = 5 minus d = 3
log-loss contrast three different ways, while the RAW contrast reproduces
closely across the same attempts.  An instability confined to the normalized
scale is a specification problem, not an arithmetic one: `relative_log_gap` is
a RATIO, and averaging a ratio is not the same as taking the ratio of averages.
D16 (`01B_ADDENDUM_ADVISOR_RULINGS.yaml`) inherits its aggregation rule from
01A `contrast.aggregation` -- "Replicates are averaged WITHIN scenario first;
the scenario-pair difference is the observation" -- which is unambiguous for a
LINEAR quantity and ambiguous for a ratio.  Neither D14, D16, nor 01A says at
which level the division happens, nor which denominator normalizes a
DIFFERENCE of two arms that have two different denominators.

This script enumerates the defensible resolutions, computes the primary
statistic under each, and prints one table so the advisor can see exactly how
much his choice moves the answer.  Every number in
`simulation-results-ct2i/S0B_NORMALIZED_CONTRAST_SENSITIVITY.md` comes from
here, and that document names the command beside each number.

THE ESTIMAND
------------
D14 freezes
    relative_log_gap   = (R_log*(Z)   - R_log*(X))   / (H(Y) - R_log*(X))
    relative_brier_gap = (R_Brier*(Z) - R_Brier*(X)) / Var{eta(X)}
Both are functions of the exact 1024-state cell law alone: the production
runner computes them from `sim1_core.exact_gap_report` and
`population_signal_scales` with no learner, no training sample and no
evaluation sample (`scripts/run_sim1b_dense_addendum.py`, the `pop`/`rel`
block).  The primary statistics of D16 E1a and E1b are therefore computable
EXACTLY without A1, which is what made this sensitivity analysis possible
without executing a single addendum cell -- and, in the event, what made the
sign instability visible in time to stop the arm being run at all.

The d = 3 partner arm is RECOMPUTED here from its frozen seed rule
(`sim1_core.dgp_block_seed("1B", ...)`) through the identical population path,
because the frozen d = 3 parquet stores Monte-Carlo risks and no normalized
quantity: D14's estimand is not readable off any frozen artefact.  That
recomputation is itself one of the choices this script exposes.

THE AXES OF UNDERSPECIFICATION
------------------------------
  ratio level   where the division happens: per replicate (mean of ratios), per
                scenario after averaging replicates (ratio of means), or once
                per block after pooling; or the contrast normalized by a single
                common denominator (the d = 3 arm's, or the two-arm mean).
  delta_eta     the block key excludes delta_eta, so a block mean averages the
                three delta_eta levels -- but D16 never says whether the
                average is of RATIOS or inside the ratio, and never says
                whether the primary is pooled over delta_eta or reported per
                level.
  bucket width  E1a collapses B0/B1/B2, E1b averages B0 and B1.  Both are
                shown to be immaterial to the ESTIMATE (the denominator does
                not depend on the encoder, so mean-of-normalized equals
                normalized-of-mean, and hash_shared's three widths induce one
                partition); including B2 in E1b is NOT immaterial.
  inference     which unit carries the SE: 8 block means with 7 df (D13), the
                48 scenario pairs, or the 400 draws (block as a fixed effect).
                This moves t, never the estimate.

WHAT THIS SCRIPT DOES NOT DO
----------------------------
  ZERO addendum cells: population algebra only, no learner fitted, nothing
  written into the results package.  There is no default output path; `--out`
  must be given explicitly and may not point inside the package.

Usage:
  s0b_normalized_contrast_sensitivity.py [--reps N] [--clause E1a|E1b|both]
                                         [--out FILE.json]
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "simulation-results-ct2i"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from ct2i_benchmark.simulations import sim1_core as CORE  # noqa: E402
import run_sim1b_dense_addendum as RUN  # noqa: E402

M, K, D_ADD = RUN.M_ADD, RUN.K_ADD, RUN.D_ADD
MARGINALS, TAUS, N_INTS = ("uniform", "zipf"), (0.5, 1.5), (0, 3)
DELTAS = (0.0, 0.1, 0.3)
N_TRAINS = (500, 5000)                # population quantities are n_train-free
BLOCKS = list(itertools.product(MARGINALS, TAUS, N_INTS))
FULL = CORE.enumerate_cells(K, M)
# the 6 hash configurations D16 E1a / E1b speak about
CFG = {"hash_shared_B0": (False, 10), "hash_shared_B1": (False, 20),
       "hash_shared_B2": (False, 40), "hash_column_B0": (True, 10),
       "hash_column_B1": (True, 20), "hash_column_B2": (True, 40)}
_FID: dict = {}


def fid_for(column_aware: bool, width: int) -> np.ndarray:
    key = (column_aware, width)
    if key not in _FID:
        _FID[key] = CORE.group_ids(CORE.hash_codes(FULL, K, width, column_aware))
    return _FID[key]


def arm_seed(marg, tau, n_int, d, rep) -> int:
    """d = 5: the addendum runner's rule. d = 3: the frozen twin's rule."""
    if d == D_ADD:
        return RUN.addendum_seed(RUN.addendum_block(marg, tau, n_int), rep)
    return CORE.dgp_block_seed("1B", (M, K, marg, tau, n_int), rep)


def cell_law(marg, tau, n_int, delta, d, seed):
    """(p_cell, eta) on the FULL 4**5 space for an arm with d active columns."""
    prm = CORE.draw_params(M, K, marg, tau, n_int, delta, seed, d_active=d)
    act = CORE.enumerate_cells(K, d)
    pa = CORE.cell_probabilities(act, prm.p_marg)
    ea = CORE.impose_delta_eta(act, pa, CORE.eta_raw(act, prm), delta)
    pf = CORE.cell_probabilities(FULL, prm.p_marg)
    ids = np.zeros(len(FULL), dtype=np.int64)
    for j in range(d):
        ids = ids * K + FULL[:, j]
    return pf, ea[ids]


def numerators_and_denominators(p, eta) -> dict:
    """Raw gaps per configuration, plus the two D14 denominators."""
    rl_x = float((p * CORE._binary_entropy(eta)).sum())
    rb_x = float((p * eta * (1.0 - eta)).sum())
    p_y = float((p * eta).sum())
    h_y = float(CORE._binary_entropy(np.array([p_y]))[0])
    out = {"den_log": h_y - rl_x, "den_bri": p_y * (1.0 - p_y) - rb_x}
    for name, (ca, width) in CFG.items():
        fid = fid_for(ca, width)
        n_f = int(fid.max()) + 1
        mass = np.bincount(fid, weights=p, minlength=n_f)
        ws = np.bincount(fid, weights=p * eta, minlength=n_f)
        eb = np.where(mass > 0, ws / np.where(mass > 0, mass, 1.0), 0.0)
        out["num_log_" + name] = float((mass * CORE._binary_entropy(eb)).sum()) - rl_x
        out["num_bri_" + name] = float((mass * eb * (1.0 - eb)).sum()) - rb_x
    return out


def build(n_rep: int) -> dict:
    """cube[(block_index, delta_index, rep, d)] -> numerators/denominators."""
    cube = {}
    for bi, (marg, tau, ni) in enumerate(BLOCKS):
        for ei, de in enumerate(DELTAS):
            for r in range(1, n_rep + 1):
                for d in (D_ADD, 3):
                    p, eta = cell_law(marg, tau, ni, de, d,
                                      arm_seed(marg, tau, ni, d, r))
                    cube[(bi, ei, r, d)] = numerators_and_denominators(p, eta)
    return cube


# ---------------------------------------------------------------------------
# aggregation variants: each returns the 8 block-level contrast values
# ---------------------------------------------------------------------------

def _num(cube, bi, ei, r, d, keys, kind) -> float:
    return float(np.mean([cube[(bi, ei, r, d)][f"num_{kind}_{k}"] for k in keys]))


def _den(cube, bi, ei, r, d, kind) -> float:
    return cube[(bi, ei, r, d)]["den_log" if kind == "log" else "den_bri"]


def block_values(cube, n_rep, keys, variant, kind="log",
                 deltas=range(len(DELTAS))) -> np.ndarray:
    """The 8 block-level contrast values under one aggregation variant."""
    reps = range(1, n_rep + 1)
    out = []
    for bi in range(len(BLOCKS)):
        per_delta = []
        for ei in deltas:
            n5 = np.array([_num(cube, bi, ei, r, D_ADD, keys, kind) for r in reps])
            n3 = np.array([_num(cube, bi, ei, r, 3, keys, kind) for r in reps])
            q5 = np.array([_den(cube, bi, ei, r, D_ADD, kind) for r in reps])
            q3 = np.array([_den(cube, bi, ei, r, 3, kind) for r in reps])
            if variant == "mean_of_ratios":
                per_delta.append((n5 / q5).mean() - (n3 / q3).mean())
            elif variant == "ratio_of_means_scenario":
                per_delta.append(n5.mean() / q5.mean() - n3.mean() / q3.mean())
            elif variant == "common_den_d3":
                per_delta.append(((n5 - n3) / q3).mean())
            elif variant == "common_den_mean":
                per_delta.append(((n5 - n3) / (0.5 * (q5 + q3))).mean())
            elif variant == "raw":
                per_delta.append(n5.mean() - n3.mean())
            elif variant == "ratio_of_means_block":
                per_delta.append((n5.mean(), q5.mean(), n3.mean(), q3.mean()))
            else:
                raise ValueError(variant)
        if variant == "ratio_of_means_block":
            a = np.array(per_delta)
            out.append(a[:, 0].mean() / a[:, 1].mean()
                       - a[:, 2].mean() / a[:, 3].mean())
        else:
            out.append(float(np.mean(per_delta)))
    return np.array(out, dtype=float)


def draw_values(cube, n_rep, keys, kind="log") -> np.ndarray:
    """Per-(block, replicate) mean-of-ratios contrast: the 8 x n_rep draw units.

    The two arms use disjoint seeds (01A seeds.disjointness,
    pairing_level: condition_not_replicate), so the replicate index is a
    bookkeeping pair, not a matched pair; the mean is identical to the
    unpaired difference of arm means and only the SE differs.
    """
    reps = range(1, n_rep + 1)
    rows = []
    for bi in range(len(BLOCKS)):
        for r in reps:
            v5 = np.mean([_num(cube, bi, ei, r, D_ADD, keys, kind)
                          / _den(cube, bi, ei, r, D_ADD, kind)
                          for ei in range(len(DELTAS))])
            v3 = np.mean([_num(cube, bi, ei, r, 3, keys, kind)
                          / _den(cube, bi, ei, r, 3, kind)
                          for ei in range(len(DELTAS))])
            rows.append((bi, v5 - v3))
    return np.array([r[1] for r in rows]), np.array([r[0] for r in rows])


def scenario_values(cube, n_rep, keys, kind="log") -> np.ndarray:
    """The 48 scenario-pair values (3 delta_eta x 2 n_train x 8 blocks).

    n_train does not enter any population quantity, so the two n_train levels
    of a (block, delta_eta) pair are literal duplicates -- 01A
    contrast.uncertainty.duplicate_pairs_disclosure. They are materialised here
    exactly as 01A's "48 scenario pairs" wording implies, which is why the
    48-pair SE is optimistic by construction.
    """
    reps = range(1, n_rep + 1)
    vals = []
    for bi in range(len(BLOCKS)):
        for ei in range(len(DELTAS)):
            v5 = np.mean([_num(cube, bi, ei, r, D_ADD, keys, kind)
                          / _den(cube, bi, ei, r, D_ADD, kind) for r in reps])
            v3 = np.mean([_num(cube, bi, ei, r, 3, keys, kind)
                          / _den(cube, bi, ei, r, 3, kind) for r in reps])
            vals.extend([v5 - v3] * len(N_TRAINS))
    return np.array(vals)


def frozen_d3_block_values(cube, n_rep, keys) -> np.ndarray:
    """A6: the d = 3 arm's NUMERATOR taken from the frozen twin, not recomputed.

    The frozen parquet stores a MONTE-CARLO `representation_loss` and no
    normalizer, so D14's ratio cannot be read off it: the only way to use the
    frozen arm at all is to pair its stored numerator with a RECOMPUTED exact
    denominator. That hybrid is a defensible reading of "use the frozen partner
    arm", and comparing it against the fully recomputed A1 measures what the
    recomputation costs.
    """
    import pandas as pd
    p = PKG / "05b_SIM1B_REPLICATE_RESULTS.parquet"
    d = pd.read_parquet(p)
    enc = "hash_shared" if keys[0].startswith("hash_shared") else "hash_column"
    widths = sorted({k.split("_")[-1] for k in keys})
    q = d[(d.M == M) & (d.K == K) & (d.metric == "logloss")
          & (d.learner == "bayes_z_oracle") & (d.status == "SUCCESS")
          & (d.encoder == enc) & (d.width_label.isin(widths))]
    g = q.groupby(["marginal", "tau", "interaction_count", "delta_eta",
                   "replicate"]).representation_loss.mean()
    reps = range(1, n_rep + 1)
    out = []
    for bi, (marg, tau, ni) in enumerate(BLOCKS):
        per_delta = []
        for ei, de in enumerate(DELTAS):
            v5 = np.mean([_num(cube, bi, ei, r, D_ADD, keys, "log")
                          / _den(cube, bi, ei, r, D_ADD, "log") for r in reps])
            v3 = np.mean([float(g.loc[(marg, tau, ni, de, r)])
                          / _den(cube, bi, ei, r, 3, "log") for r in reps])
            per_delta.append(v5 - v3)
        out.append(float(np.mean(per_delta)))
    return np.array(out)


def t_block(v: np.ndarray) -> tuple[float, float, float, int]:
    est = float(v.mean())
    se = float(v.std(ddof=1) / np.sqrt(len(v)))
    t = est / se
    return est, se, t, int((v > 0).sum())


# ---------------------------------------------------------------------------

CLAUSE_KEYS = {
    "E1a": ("hash_shared collapsed (B0)", ["hash_shared_B0"]),
    "E1b": ("hash_column narrow width mean(B0,B1)",
            ["hash_column_B0", "hash_column_B1"]),
}

VARIANTS = [
    ("A1 mean-of-ratios, replicates then delta_eta (as first published)",
     "mean_of_ratios", None),
    ("A2 ratio-of-means within scenario (average numerator and denominator "
     "over replicates first)", "ratio_of_means_scenario", None),
    ("A3 ratio-of-means within block (pool replicates AND delta_eta)",
     "ratio_of_means_block", None),
    ("A4 contrast over the d=3 denominator ((n5-n3)/q3)", "common_den_d3", None),
    ("A5 contrast over the two-arm mean denominator", "common_den_mean", None),
    ("A1@delta=0.0 only", "mean_of_ratios", [0]),
    ("A1@delta=0.1 only", "mean_of_ratios", [1]),
    ("A1@delta=0.3 only", "mean_of_ratios", [2]),
]


def run(n_rep: int, clauses: list[str]) -> dict:
    print("NORMALIZED CONTRAST SENSITIVITY -- zero addendum cells, "
          "zero package writes")
    print(f"repo        : {REPO}")
    print(f"interpreter : {sys.executable}")
    print(f"replicates  : {n_rep} per block per arm; blocks: {len(BLOCKS)}; "
          f"delta_eta: {list(DELTAS)}")
    cube = build(n_rep)
    res: dict = {"n_rep": n_rep}

    # --- width-collapse premises -------------------------------------------
    mx_shared, mx_col = 0.0, 0.0
    for (bi, ei, r, d), v in cube.items():
        q = v["den_log"]
        s0, s1, s2 = (v["num_log_hash_shared_B0"] / q,
                      v["num_log_hash_shared_B1"] / q,
                      v["num_log_hash_shared_B2"] / q)
        mx_shared = max(mx_shared, abs(s0 - s1), abs(s0 - s2))
        mx_col = max(mx_col, abs(v["num_log_hash_column_B0"] / q
                                 - v["num_log_hash_column_B1"] / q))
    res["max_abs_width_diff_hash_shared"] = mx_shared
    res["max_abs_width_diff_hash_column_B0_B1"] = mx_col
    print(f"\n[width premises]  max |rel_log(B0) - rel_log(B1 or B2)| "
          f"hash_shared = {mx_shared:.3e}   (D16 E1a's collapse premise)")
    print(f"[width premises]  max |rel_log(B0) - rel_log(B1)| "
          f"hash_column = {mx_col:.3e}   (E1b's widths are NOT degenerate)")
    tol = RUN.worker_tolerance()
    dmin = min(v["den_log"] for v in cube.values())
    bmin = min(v["den_bri"] for v in cube.values())
    res["min_den_log"], res["min_den_brier"], res["tolerance"] = dmin, bmin, tol
    print(f"[NOT_IDENTIFIED]  min denominator: log {dmin:.4g}, "
          f"Brier {bmin:.4g}; D14 tolerance {tol:.1e} -> "
          f"{'no' if min(dmin, bmin) > tol else 'SOME'} cell is NOT_IDENTIFIED")

    for clause in clauses:
        label, keys = CLAUSE_KEYS[clause]
        print(f"\n=== {clause}: {label} ===")
        print(f"  {'aggregation choice':<62} {'estimate':>10} {'SE':>9} "
              f"{'t':>7} {'q<.05?':>7} {'blk>0':>6}")
        rows = []
        for name, variant, deltas in VARIANTS:
            ds = range(len(DELTAS)) if deltas is None else deltas
            v = block_values(cube, n_rep, keys, variant, "log", ds)
            est, se, t, pos = t_block(v)
            p1 = float(stats.t.sf(t, df=len(v) - 1))
            print(f"  {name:<62} {est:>+10.5f} {se:>9.5f} {t:>+7.2f} "
                  f"{'yes' if p1 < 0.05 else 'no':>7} {pos:>4}/8")
            rows.append(dict(choice=name, variant=variant,
                             deltas=list(ds), estimate=est, se=se, t=t,
                             one_sided_p=p1, blocks_positive=pos,
                             block_values=[float(x) for x in v]))
        v6 = frozen_d3_block_values(cube, n_rep, keys)
        est6, se6, t6, pos6 = t_block(v6)
        name6 = ("A6 d=3 numerator READ from the frozen twin (Monte Carlo) "
                 "with exact denominator")
        print(f"  {name6:<62} {est6:>+10.5f} {se6:>9.5f} {t6:>+7.2f} "
              f"{'':>7} {pos6:>4}/8")
        rows.append(dict(choice=name6, variant="frozen_d3_numerator",
                         estimate=est6, se=se6, t=t6, blocks_positive=pos6,
                         block_values=[float(x) for x in v6]))
        # width sensitivity for E1b, and the Brier companion
        if clause == "E1b":
            for extra_name, extra_keys in (
                    ("A1 with B0 only", ["hash_column_B0"]),
                    ("A1 with mean(B0,B1,B2)",
                     ["hash_column_B0", "hash_column_B1", "hash_column_B2"]),
                    ("A1 with B2 only", ["hash_column_B2"])):
                v = block_values(cube, n_rep, extra_keys, "mean_of_ratios")
                est, se, t, pos = t_block(v)
                print(f"  {extra_name:<62} {est:>+10.5f} {se:>9.5f} "
                      f"{t:>+7.2f} {'':>7} {pos:>4}/8")
                rows.append(dict(choice=extra_name, variant="mean_of_ratios",
                                 estimate=est, se=se, t=t, blocks_positive=pos))
        # raw contrast and normalized Brier under the reference aggregation
        vr = block_values(cube, n_rep, keys, "raw", "log")
        est_r, se_r, t_r, pos_r = t_block(vr)
        vb = block_values(cube, n_rep, keys, "mean_of_ratios", "bri")
        est_b, se_b, t_b, pos_b = t_block(vb)
        raw_label = "RAW log-loss contrast (linear: ratio-order-free)"
        print(f"  {raw_label:<62} {est_r:>+10.5f} {se_r:>9.5f} "
              f"{t_r:>+7.2f} {'':>7} {pos_r:>4}/8")
        print(f"  {'NORMALIZED Brier contrast (A1 aggregation)':<62} "
              f"{est_b:>+10.5f} {se_b:>9.5f} {t_b:>+7.2f} {'':>7} {pos_b:>4}/8")
        rows.append(dict(choice="RAW log-loss contrast", variant="raw",
                         estimate=est_r, se=se_r, t=t_r, blocks_positive=pos_r))
        rows.append(dict(choice="NORMALIZED Brier contrast",
                         variant="mean_of_ratios_brier", estimate=est_b,
                         se=se_b, t=t_b, blocks_positive=pos_b))

        # inference-unit sensitivity, estimate held at A1
        v = block_values(cube, n_rep, keys, "mean_of_ratios")
        est, se, t, pos = t_block(v)
        dv, dblk = draw_values(cube, n_rep, keys)
        # block as a fixed effect: SE of the grand mean of block means from the
        # within-block draw variance
        per_block_var = np.array([dv[dblk == b].var(ddof=1)
                                  for b in range(len(BLOCKS))])
        se_draw = float(np.sqrt((per_block_var / n_rep).mean() / len(BLOCKS)))
        sv = scenario_values(cube, n_rep, keys)
        se_scen = float(sv.std(ddof=1) / np.sqrt(len(sv)))
        print(f"\n  inference unit (estimate fixed at {est:+.5f}, "
              f"aggregation A1):")
        print(f"    8 block means, 7 df (D13)          SE={se:.5f}  "
              f"t={est / se:+.2f}")
        print(f"    48 scenario pairs, 47 df (01A)     SE={se_scen:.5f}  "
              f"t={est / se_scen:+.2f}   (n_train duplicates included)")
        print(f"    400 draws, block fixed, 392 df     SE={se_draw:.5f}  "
              f"t={est / se_draw:+.2f}")
        # D14 requires interaction_pairs = 0 and = 3 to be reported separately;
        # neither D14 nor D16 says whether the PRIMARY is the pooled mean or a
        # per-stratum statistic, so both are printed.
        strata = {}
        print("  per-stratum (D14 mandatory disclosure, aggregation A1):")
        for sname, idx in (("interaction_pairs=0", [0, 2, 4, 6]),
                           ("interaction_pairs=3", [1, 3, 5, 7])):
            sv2 = v[idx]
            e2 = float(sv2.mean())
            s2 = float(sv2.std(ddof=1) / np.sqrt(len(sv2)))
            strata[sname] = dict(estimate=e2, se=s2, t=e2 / s2,
                                 blocks_positive=int((sv2 > 0).sum()))
            print(f"    {sname:<22} est={e2:+.5f}  SE={s2:.5f}  "
                  f"t={e2 / s2:+.2f}  blocks>0: {int((sv2 > 0).sum())}/4")
        res[clause] = dict(rows=rows, se_block=se, se_scenario=se_scen,
                           se_draw=se_draw, estimate_A1=est,
                           block_values_A1=[float(x) for x in v],
                           strata=strata)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reps", type=int, default=50,
                    help="replicates per block per arm (frozen design: 50)")
    ap.add_argument("--clause", default="both", choices=["E1a", "E1b", "both"])
    ap.add_argument("--out", type=Path, default=None,
                    help="OPTIONAL json summary path; there is NO default "
                         "output file and it may not be inside the results "
                         "package")
    args = ap.parse_args(argv)
    if args.out is not None and PKG in args.out.resolve().parents:
        ap.error("refusing to write a probe summary into the results package")
    clauses = ["E1a", "E1b"] if args.clause == "both" else [args.clause]
    res = run(args.reps, clauses)
    if args.out is not None:
        args.out.write_text(json.dumps(res, indent=2, default=str))
        print(f"\n[wrote] {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
