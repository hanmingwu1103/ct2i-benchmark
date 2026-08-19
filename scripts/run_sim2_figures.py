"""Phase S1 step 7: Simulation 2 figure, summary table and acceptance report.

SIMULATION ONLY. The Stage 2 scientific design is frozen; this only renders and
summarises the reproduction in 12_SIM2_RESULTS.csv.

Three panels, per 01_PROTOCOL_FREEZE.yaml figures.Sim2Figure:
  A  oracle optimism versus K with the sigma*sqrt(2 ln K) bound
  B  validation regret and winner instability versus K
  C  K=72 minus K=8 oracle advantage across sigma

Writes 14_SIM2_ACCEPTANCE_REPORT.json, 15_SIM2_FIGURE_DATA.csv,
       16_SIM2_FIGURE.pdf (+ .svg), 17_SIM2_SUMMARY_TABLE.csv
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
from matplotlib.ticker import (FormatStrFormatter,  # noqa: E402
                               NullFormatter)
import numpy as np                       # noqa: E402
import pandas as pd                      # noqa: E402
import yaml                              # noqa: E402

REPO = Path(__file__).resolve().parents[1]
OUTD = REPO / "simulation-results-ct2i"
FREEZE = OUTD / "01_PROTOCOL_FREEZE.yaml"

CFG = yaml.safe_load(open(FREEZE, encoding="utf-8"))
STYLE = CFG["figures"]["style"]
PAL = STYLE["palette_hex"]
plt.rcParams.update({"font.size": STYLE["font_size_pt"], "axes.linewidth": .6,
                     "xtick.labelsize": 7, "ytick.labelsize": 7,
                     "legend.fontsize": 6, "axes.titlesize": 8,
                     "savefig.bbox": "tight", "figure.dpi": 200,
                     "savefig.dpi": 400})


def main() -> int:
    src = OUTD / "12_SIM2_RESULTS.csv"
    if not src.exists():
        print("12_SIM2_RESULTS.csv missing; run run_sim2_reproduce.py first")
        return 1
    d = pd.read_csv(src)
    d["value"] = pd.to_numeric(d["value"], errors="coerce")
    par = d.parameter_json.map(json.loads)
    for k in ("K", "sigma", "rho", "regime"):
        d[k] = par.map(lambda p, k=k: p.get(k))

    panel = d[(d.selection_rule_or_encoder == "panel") & (d.regime == "all_equal")]
    asym = d[d.metric == "oracle_advantage_large_minus_small"].copy()

    fig, ax = plt.subplots(1, 3, figsize=(STYLE["double_column_in"], 2.4))
    # Phase R: panel B now carries a right-hand axis, so the panels need more
    # horizontal room or its label collides with panel C's y-label.
    fig.subplots_adjust(wspace=.85)

    # ---- A: oracle optimism vs K, with the sub-Gaussian bound ----
    A = ax[0]
    for i, sg in enumerate(sorted(panel.sigma.dropna().unique())):
        g = panel[(panel.sigma == sg) & (panel.rho == 0.0)
                  & (panel.metric == "oracle_optimism_mean")].sort_values("K")
        A.plot(g.K, g.value, "o-", ms=3, lw=1, color=PAL[i],
               label=f"observed, $\\sigma$={sg:g}")
        b = panel[(panel.sigma == sg) & (panel.rho == 0.0)
                  & (panel.metric == "oracle_optimism_mean")].sort_values("K")
        A.plot(b.K, pd.to_numeric(b.theoretical_value, errors="coerce"), "--",
               lw=.8, color=PAL[i], alpha=.6)
    A.set(xscale="log", xlabel="candidate count K",
          ylabel="oracle optimism", title="(A) optimism vs bound ($\\rho$=0)")
    A.legend(frameon=False, loc="upper left")
    A.text(.97, .03, "dashed = $\\sigma\\sqrt{2\\ln K}$ bound", transform=A.transAxes,
           fontsize=5.5, va="bottom", ha="right", color="grey")

    # ---- B: validation regret and winner instability vs K ----
    # Phase R: the two series differ by orders of magnitude and previously shared
    # one unlabelled axis, which made the panel unreadable. Each series now owns
    # a labelled axis (regret left, instability right) and one combined legend
    # sits outside the data region.
    B = ax[1]
    B2 = B.twinx()
    handles = []
    for i, (m, lab, axis, unit) in enumerate((
            ("regret_mean", "validation regret (left)", B, "regret"),
            ("winner_instability", "winner instability (right)", B2,
             "instability (prob.)"))):
        g = (panel[(panel.metric == m) & (panel.rho == 0.0)]
             .groupby("K").value.mean().sort_index())
        style = "o-" if i == 0 else "s--"
        h, = axis.plot(g.index, g.values, style, ms=3, lw=1, color=PAL[i + 2],
                       label=lab)
        axis.set_ylabel(unit, color=PAL[i + 2], fontsize=7)
        axis.tick_params(axis="y", colors=PAL[i + 2])
        handles.append(h)
    B.set(xscale="log", xlabel="candidate count K", title="(B) regret and instability")
    B.legend(handles, [h.get_label() for h in handles], loc="upper center",
             bbox_to_anchor=(.5, -.33), frameon=False, ncol=1)

    # ---- C: K=72 minus K=8 oracle advantage ----
    C = ax[2]
    asym["sigma"] = asym.parameter_json.map(lambda s: json.loads(s)["sigma"])
    g = asym.groupby("sigma").value.mean().sort_index()
    tg = CFG["simulation_2"]["validation_targets"]["k72_minus_k8_oracle_advantage"]
    frozen = [tg.get(f"sigma_{s:g}", tg.get(f"sigma_{s:.3f}")) for s in g.index]
    C.plot(g.index, g.values, "o-", ms=4, lw=1, color=PAL[1], label="reproduced")
    C.plot(g.index, frozen, "x--", ms=5, lw=.8, color="k", label="frozen Stage 2")
    C.set(xscale="log", xlabel="$\\sigma$", ylabel="K=72 minus K=8 advantage",
          title="(C) asymmetric candidate sets")
    # Phase R: a log x-axis over sigma in {0.005, 0.010, 0.030} produced
    # matplotlib's default minor-tick labels, i.e. malformed sigma ticks. Pin the
    # three evaluated sigma values as the only labelled ticks.
    C.set_xticks(list(g.index))
    C.xaxis.set_major_formatter(FormatStrFormatter("%.3f"))
    C.xaxis.set_minor_locator(plt.NullLocator())
    C.xaxis.set_minor_formatter(NullFormatter())
    C.legend(frameon=False)

    for ext in ("pdf", "svg"):
        fig.savefig(OUTD / f"16_SIM2_FIGURE.{ext}")
    plt.close(fig)

    keep = pd.concat([panel.assign(panel="A/B"), asym.assign(panel="C")])
    keep[["panel", "scenario_id", "K", "sigma", "rho", "regime", "metric",
          "value", "theoretical_value", "mcse"]].to_csv(
        OUTD / "15_SIM2_FIGURE_DATA.csv", index=False)

    # ---- summary table and acceptance ----
    tgt = CFG["simulation_2"]["validation_targets"]
    bias = d[d.metric == "reporting_bias_mean"].value.abs().max()
    ratio = d[d.metric == "oracle_bound_ratio"].value.max()
    rows = [
        dict(criterion="C1 honest independent-test reporting is unbiased",
             maximum_observed_value=bias,
             theoretical_bound_or_tolerance=tgt["max_abs_honest_independent_test_reporting_bias"],
             **{"pass": bool(abs(bias - tgt["max_abs_honest_independent_test_reporting_bias"]) <= 1.5e-4)}),
        dict(criterion="C2 oracle optimism within the sub-Gaussian bound",
             maximum_observed_value=ratio,
             theoretical_bound_or_tolerance=tgt["max_observed_over_theoretical_oracle_bound_ratio"],
             **{"pass": bool(ratio <= 1.0)}),
    ]
    for s in sorted(g.index):
        f = tgt["k72_minus_k8_oracle_advantage"].get(
            f"sigma_{s:g}", tgt["k72_minus_k8_oracle_advantage"].get(f"sigma_{s:.3f}"))
        rows.append(dict(criterion=f"C6 K=72 minus K=8 oracle advantage, sigma={s:g}",
                         maximum_observed_value=float(g.loc[s]),
                         theoretical_bound_or_tolerance=f,
                         **{"pass": bool(abs(g.loc[s] - f) <= max(.15 * s, 1e-3))}))
    tab = pd.DataFrame(rows)
    tab.to_csv(OUTD / "17_SIM2_SUMMARY_TABLE.csv", index=False)
    (OUTD / "14_SIM2_ACCEPTANCE_REPORT.json").write_text(
        json.dumps(dict(source="reproduction of the frozen Stage 2 design",
                        n_rows=len(d), criteria=rows,
                        n_passed=int(tab["pass"].sum()),
                        n_total=len(tab),
                        note="design frozen by Stage 2 and not changed; a "
                             "mismatch would be reported, not tuned away"),
                   indent=2), encoding="utf-8")
    print(tab.to_string(index=False))
    print(f"\n{int(tab['pass'].sum())}/{len(tab)} Simulation 2 criteria reproduced")
    print("wrote 14_SIM2_ACCEPTANCE_REPORT.json, 15_SIM2_FIGURE_DATA.csv, "
          "16_SIM2_FIGURE.pdf/.svg, 17_SIM2_SUMMARY_TABLE.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
