"""Phase S1 step 7: Simulation 1 tables, generated from frozen raw output.

SIMULATION ONLY. Columns follow 01_PROTOCOL_FREEZE.yaml exactly.

  TabS1  simulation design and factor levels, reflecting the design ACTUALLY
         EXECUTED (read back from the raw output, not from the plan), with the
         mandated d = 3 disclosure for Simulation 1B.
  TabS2  theorem-identity and implementation acceptance summary, one row per
         criterion A1-A15, including the criteria that could not be evaluated.
  TabS3  the prespecified contrasts C1-C11 with uncertainty. Scenario is the
         unit of analysis, contrasts are paired within (block, replicate), and
         deterministic exact contrasts carry no p-value.

Each table is written as CSV and as a LaTeX booktabs fragment.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
OUTD = REPO / "simulation-results-ct2i"
RAW = OUTD / "raw"
TABD = OUTD / "11_SIM1_TABLES"
FREEZE = OUTD / "01_PROTOCOL_FREEZE.yaml"


def load(n):
    p = RAW / n
    return pd.read_csv(p, low_memory=False) if p.exists() else None


def write(df: pd.DataFrame, name: str, caption: str):
    TABD.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABD / f"{name}.csv", index=False)
    try:
        tex = df.to_latex(index=False, escape=True, float_format="%.5g",
                          caption=caption, label=f"tab:{name.lower()}")
    except Exception:                                          # noqa: BLE001
        tex = df.to_latex(index=False, escape=True, float_format="%.5g")
    (TABD / f"{name}.tex").write_text(tex, encoding="utf-8")
    print(f"  wrote {name}.csv / .tex  ({len(df)} rows)")


def tab_s1(a1, c_ex, c_fi, b):
    rows = []
    for d, comp, note in ((a1, "1A", "exact enumeration; d = M (all coordinates active)"),
                          (c_ex, "1C exact", "closed form; d = 5 named coordinates"),
                          (c_fi, "1C finite", "d = 5 named coordinates"),
                          (b, "1B", "d = 3 in EVERY cell: M varies the number of "
                                    "pure-noise columns only, so the design does NOT "
                                    "test dense high-cardinality signal")):
        if d is None:
            rows.append(dict(component=comp, status="NOT RUN", notes=note))
            continue
        g = d[d.status == "SUCCESS"]

        def lv(c):
            return ("" if c not in g.columns
                    else ", ".join(str(x) for x in sorted(g[c].dropna().unique())[:8]))
        rows.append(dict(
            component=comp, M=lv("M"), K=lv("K"), marginal=lv("marginal"),
            tau=lv("tau"), interaction_count=lv("interaction_count"),
            delta_eta=lv("delta_eta"), n_train=lv("n_train"), n_test=lv("n_test"),
            activation_rate=lv("activation_rate"),
            target_mechanism=lv("target_mechanism"),
            encoder=lv("encoder"), bucket_width=lv("bucket_width"),
            learner=lv("learner"),
            scenarios=g.scenario_id.nunique(),
            replicate_count=(int(g.replicate.max()) if "replicate" in g else ""),
            rows=len(g), status="EXECUTED", notes=note))
    write(pd.DataFrame(rows), "TabS1",
          "Simulation design and factor levels as executed.")


def tab_s2():
    p = OUTD / "07_SIM1_ACCEPTANCE_REPORT.json"
    if not p.exists():
        print("  TabS2 skipped: acceptance report not built yet")
        return
    rep = json.loads(p.read_text(encoding="utf-8"))
    frz = yaml.safe_load(open(FREEZE, encoding="utf-8"))["acceptance_criteria"]
    got = {c["criterion_id"]: c for c in rep["criteria"]}
    rows = []
    for cid in sorted(frz):
        c = got.get(cid)
        if c is None:
            rows.append(dict(criterion_id=cid,
                             criterion_description=frz[cid]["description"],
                             maximum_error="", tolerance="",
                             **{"pass": "NOT EVALUATED"},
                             notes="requires an arm not yet complete"))
        else:
            rows.append(dict(criterion_id=cid,
                             criterion_description=c["criterion_description"],
                             maximum_error=c["maximum_error"],
                             tolerance=c["tolerance"],
                             **{"pass": {True: "PASS", False: "FAIL",
                                         None: "NOT EVALUATED"}[c["pass"]]},
                             notes=c.get("notes", "")))
    # A7 verification-scope disclosure required by the S0 review (m2)
    for r in rows:
        if r["criterion_id"] == "A7":
            r["notes"] = ((r["notes"] + "; ") if r["notes"] else "") + \
                "verified by brute-force enumeration at M <= 14; asserted by the " \
                "Stage 1 proposition at M in {50, 200, 1000}"
    write(pd.DataFrame(rows), "TabS2",
          "Theorem-identity and implementation acceptance summary.")


def paired(d, sel_a, sel_b, value="representation_loss", keys=None):
    """Scenario-level paired differences between two selections.

    `keys` identifies the DGP draw the two arms must share. For encoder
    contrasts that is (scenario_id, replicate). For contrasts ACROSS a factor
    that is itself part of the scenario id -- Delta_eta in C5, n_train in
    C6-C8 -- pairing on scenario_id would find no overlap at all, because each
    level is its own scenario. Those contrasts pair on `seed`, which is exactly
    what the frozen block seeding makes shareable: both arms of a within-DGP
    contrast are drawn from one parameter set, so an identical seed identifies
    the same draw.
    """
    keys = keys or ["scenario_id", "replicate"]
    A = d[sel_a].groupby(keys)[value].mean()
    B = d[sel_b].groupby(keys)[value].mean()
    j = pd.concat([A.rename("a"), B.rename("b")], axis=1).dropna()
    if j.empty:
        return None
    j["diff"] = j["a"] - j["b"]
    lvl = "scenario_id" if "scenario_id" in j.index.names else j.index.names[0]
    return j.groupby(level=lvl)["diff"].mean()


def tab_s3(a1, b):
    cfg = yaml.safe_load(open(FREEZE, encoding="utf-8"))
    direction = cfg["multiplicity"]["directionality"]
    family = set(cfg["multiplicity"]["family_members"])
    rows = []

    def add(cid, ea, eb, learner, metric, s, exact, note=""):
        if s is None or len(s) < 2:
            rows.append(dict(contrast_id=cid, encoder_a=ea, encoder_b=eb,
                             learner=learner, metric=metric, n_scenarios=0,
                             estimate=None, ci_low=None, ci_high=None, mcse=None,
                             p_raw=None, p_bh=None, in_bh_family=cid in family,
                             notes=(note + " unavailable").strip()))
            return
        m, sd, n = s.mean(), s.std(ddof=1), len(s)
        se = sd / np.sqrt(n)
        if exact:
            p = None
            note = (note + " exact arm: deterministic, no p-value").strip()
        else:
            d1 = direction.get(cid, "two-sided")
            t = m / se if se > 0 else np.inf
            if "greater" in d1:
                p = stats.t.sf(t, n - 1)
            elif "less" in d1:
                p = stats.t.cdf(t, n - 1)
            else:
                p = 2 * stats.t.sf(abs(t), n - 1)
        rows.append(dict(contrast_id=cid, encoder_a=ea, encoder_b=eb,
                         learner=learner, metric=metric, n_scenarios=n,
                         estimate=m, ci_low=m - 1.96 * se, ci_high=m + 1.96 * se,
                         mcse=se, p_raw=p, p_bh=None,
                         in_bh_family=cid in family, notes=note))

    # exact-arm contrasts (1A): deterministic, reported without p-values
    if a1 is not None:
        g = a1[(a1.status == "SUCCESS") & (a1.metric == "logloss")]
        add("C1", "onehot", "hash_shared", "bayes_z_oracle", "logloss",
            paired(g, g.encoder == "onehot", g.encoder == "hash_shared"), True,
            "1A exact.")
        add("C2", "hash_column", "hash_shared", "bayes_z_oracle", "logloss",
            paired(g, g.encoder == "hash_column", g.encoder == "hash_shared"), True,
            "1A exact.")
        add("C3", "onehot", "count_pop", "bayes_z_oracle", "logloss",
            paired(g, g.encoder == "onehot", g.encoder == "count_pop"), True,
            "1A exact.")
        dm = g[g.encoder == "designed_merge"]
        add("C5", "designed_merge d=0.3", "designed_merge d=0", "bayes_z_oracle",
            "logloss", paired(dm, dm.delta_eta == 0.3, dm.delta_eta == 0.0,
                              keys=["seed"]), True,
            "1A exact; construction identity, excluded from the BH family.")

    # finite-sample contrasts (1B)
    if b is not None:
        g = b[(b.status == "SUCCESS") & (b.metric == "logloss")]
        add("C4", "target", "onehot", "bayes_z_oracle", "logloss",
            paired(g[g.learner == "bayes_z_oracle"],
                   g[g.learner == "bayes_z_oracle"].encoder == "target",
                   g[g.learner == "bayes_z_oracle"].encoder == "onehot"), False,
            "1B.")
        for cid, lrn in (("C6", "lightgbm"), ("C7", "mlp"), ("C8", "logistic")):
            gl = g[g.learner == lrn]
            add(cid, f"n_train=5000", "n_train=500", lrn, "logloss",
                paired(gl, gl.n_train == 5000, gl.n_train == 500,
                       value="learner_shortfall", keys=["seed", "encoder"]),
                False, "1B; H5.")
        # H6: coefficient of variation of representation loss, Zipf vs uniform
        for cid, enc in (("C9", "target"), ("C10", "woe"),
                         ("C11", "ordered_catboost_sim")):
            ge = g[(g.encoder == enc) & (g.K == 50)
                   & (g.learner == "bayes_z_oracle")]
            if ge.empty:
                add(cid, f"{enc} Zipf CV", "uniform CV", "bayes_z_oracle",
                    "logloss", None, False, "1B; H6.")
                continue
            # H6 compares marginals, and `marginal` is itself part of the
            # scenario id, so grouping by scenario_id leaves one column empty
            # and the pivot drops everything (the same trap as C5). The
            # marginal is the treatment here, so the arms cannot share a seed;
            # instead they are MATCHED on every other factor and the
            # across-replicate coefficient of variation is compared within each
            # matched cell.
            block = ["M", "K", "tau", "interaction_count", "delta_eta", "n_train"]
            cv = (ge.groupby(block + ["marginal"]).representation_loss
                  .agg(["mean", "std"]))
            cv["cv"] = cv["std"] / cv["mean"].replace(0, np.nan)
            w = cv.reset_index().pivot_table(index=block, columns="marginal",
                                             values="cv")
            s = ((w["zipf"] - w["uniform"]).dropna()
                 if {"zipf", "uniform"} <= set(w.columns) else None)
            if s is not None:
                s = s.reset_index(drop=True)
            add(cid, f"{enc} Zipf CV", "uniform CV", "bayes_z_oracle", "logloss",
                s, False, "1B; H6 coefficient of variation.")

    df = pd.DataFrame(rows)
    # Benjamini-Hochberg over the stochastic family members only
    m = df[(df.in_bh_family) & df.p_raw.notna()]
    if len(m):
        p = m.p_raw.to_numpy()
        order = np.argsort(p)
        adj = np.empty_like(p)
        n = len(p)
        prev = 1.0
        for rank in range(n - 1, -1, -1):
            i = order[rank]
            prev = min(prev, p[i] * n / (rank + 1))
            adj[i] = prev
        df.loc[m.index, "p_bh"] = adj
    write(df, "TabS3", "Prespecified finite-sample contrasts with uncertainty.")


def main() -> int:
    a1 = load("sim1a_replicates.csv")
    c_ex, c_fi = load("sim1c_exact.csv"), load("sim1c_finite.csv")
    b = load("sim1b_replicates.csv")
    print("arms:", {"1A": a1 is not None, "1C_exact": c_ex is not None,
                    "1C_finite": c_fi is not None, "1B": b is not None})
    tab_s1(a1, c_ex, c_fi, b)
    tab_s2()
    tab_s3(a1, b)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
