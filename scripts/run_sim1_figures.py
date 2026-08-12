"""Phase S1 step 7: Simulation 1 figures, generated from frozen raw output.

SIMULATION ONLY. Panels follow 01_PROTOCOL_FREEZE.yaml exactly; nothing is
selected for favourability and no panel is added or dropped here.

Two disclosure rules carried in from the S0 review are enforced in the drawing
code, not left to the caption writer:

  * every series is labelled EXACT or EMPIRICAL, so a reader cannot mistake an
    estimated finite-sample curve for an identified population quantity;
  * where a quantity is structurally unavailable (column-aware hash
    representation loss), the series is omitted from the loss axis and the
    absence is annotated on the panel rather than left blank.

Writes 10_SIM1_FIGURES/{FigS1,FigS2,FigS3,FigS4}.{pdf,svg}
       08_SIM1_FIGURE_DATA.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402
import pandas as pd                      # noqa: E402
import yaml                              # noqa: E402

REPO = Path(__file__).resolve().parents[1]
OUTD = REPO / "simulation-results-ct2i"
RAW = OUTD / "raw"
FIGD = OUTD / "10_SIM1_FIGURES"
FREEZE = OUTD / "01_PROTOCOL_FREEZE.yaml"

STYLE = yaml.safe_load(open(FREEZE, encoding="utf-8"))["figures"]["style"]
PAL = STYLE["palette_hex"]
plt.rcParams.update({"font.size": STYLE["font_size_pt"], "axes.linewidth": 0.6,
                     "xtick.labelsize": 7, "ytick.labelsize": 7,
                     "legend.fontsize": 6, "axes.titlesize": 8,
                     "savefig.bbox": "tight", "figure.dpi": 200,
                     "savefig.dpi": 400})
SINGLE, DOUBLE = STYLE["single_column_in"], STYLE["double_column_in"]


def load(n):
    p = RAW / n
    return pd.read_csv(p, low_memory=False) if p.exists() else None


def save(fig, name):
    FIGD.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "svg"):
        fig.savefig(FIGD / f"{name}.{ext}")
    plt.close(fig)
    print(f"  wrote {name}.pdf / .svg")


def col(i):
    return PAL[i % len(PAL)]


def fig_s1(a1, c_ex, b, keep):
    """Estimated versus theoretical gaps. Exact arms in one panel; 1B where identified."""
    fig, ax = plt.subplots(1, 3, figsize=(DOUBLE, 2.4))
    ex = []
    for d, lab in ((a1, "1A"), (c_ex, "1C")):
        if d is None:
            continue
        g = d[(d.status == "SUCCESS")]
        if lab == "1C":
            g = g[g.encoder == "hash_shared"]
        ex.append(g.assign(arm=lab))
    if ex:
        E = pd.concat(ex)
        for i, (m, gm) in enumerate(E.groupby("metric")):
            x = pd.to_numeric(gm.theoretical_gap, errors="coerce")
            y = pd.to_numeric(gm.estimated_gap, errors="coerce")
            # rasterise the point cloud, keep axes/text vector: 373k vector points
            # made a 31 MB SVG, which is unusable as a publication asset
            ax[0].scatter(x, y, s=3, alpha=.35, color=col(i),
                          label=f"{m} (EXACT)", rasterized=True)
        lim = [0, max(1e-6, np.nanmax(pd.to_numeric(E.theoretical_gap, errors="coerce")))]
        ax[0].plot(lim, lim, "k--", lw=.7, label="y = x")
        ax[0].set(xlabel="theoretical gap", ylabel="estimated gap",
                  title="(a) exact arms (1A, 1C)")
        ax[0].legend(frameon=False)
        keep.append(E.assign(panel="FigS1a"))

    for j, m in enumerate(("logloss", "brier")):
        A = ax[j + 1]
        if b is not None:
            g = b[(b.status == "SUCCESS") & (b.metric == m)
                  & (b.theoretical_gap_status == "IDENTIFIED_EXACT")
                  & (b.learner == "bayes_z_oracle")]
            if len(g):
                x = pd.to_numeric(g.theoretical_gap, errors="coerce")
                y = pd.to_numeric(g.estimated_gap, errors="coerce")
                A.errorbar(x, y, yerr=pd.to_numeric(g.mcse, errors="coerce"),
                           fmt="o", ms=2, lw=.4, alpha=.4, color=col(j),
                           label=f"1B {m} (EMPIRICAL)", rasterized=True)
                lim = [0, max(1e-6, np.nanmax(x))]
                A.plot(lim, lim, "k--", lw=.7)
                keep.append(g.assign(panel=f"FigS1{'bc'[j]}"))
                A.legend(frameon=False)
        else:
            A.text(.5, .5, "Simulation 1B\nnot yet available", ha="center",
                   va="center", transform=A.transAxes, color="grey")
        A.set(xlabel="theoretical gap", ylabel="estimated gap",
              title=f"({'bc'[j]}) 1B {m}, identified cells")
    save(fig, "FigS1")


def fig_s2(a1, keep):
    """Representation loss versus within-fiber posterior spread (1A exact arm)."""
    if a1 is None:
        return
    fig, ax = plt.subplots(1, 2, figsize=(DOUBLE, 2.4), sharey=False)
    for j, marg in enumerate(("uniform", "zipf")):
        A = ax[j]
        g = a1[(a1.status == "SUCCESS") & (a1.metric == "logloss")
               & (a1.marginal == marg)]
        for i, (enc, ge) in enumerate(g.groupby("encoder")):
            t = ge.groupby("delta_eta").representation_loss.agg(["mean", "min", "max"])
            A.plot(t.index, t["mean"], "o-", ms=3, lw=1, color=col(i), label=enc)
            A.fill_between(t.index, t["min"], t["max"], color=col(i), alpha=.12)
            keep.append(ge.assign(panel=f"FigS2{'ab'[j]}"))
        A.set(xlabel=r"$\Delta_\eta$ (within-fiber posterior range)",
              ylabel="representation loss (nats)" if j == 0 else "",
              title=f"({'ab'[j]}) {marg} marginal — EXACT")
        if j == 1:
            A.legend(frameon=False, ncol=2)
    fig.text(.5, -.06, "band = min-max across the 96 DGP conditions "
             "(exact cells have mcse = 0, so this is NOT a confidence interval)",
             ha="center", fontsize=6, color="grey")
    save(fig, "FigS2")


def fig_s3(c_ex, c_fi, keep):
    """Shared-value versus column-aware hashing as binary width M grows."""
    if c_ex is None:
        return
    rates = sorted(c_ex.activation_rate.unique())
    fig, ax = plt.subplots(2, len(rates), figsize=(DOUBLE, 4.2), sharex=True)
    for r, tgt in enumerate(("position_specific", "hamming_weight")):
        for c, q in enumerate(rates):
            A = ax[r, c]
            g = c_ex[(c_ex.status == "SUCCESS") & (c_ex.encoder == "hash_shared")
                     & (c_ex.metric == "logloss") & (c_ex.target_mechanism == tgt)
                     & (c_ex.activation_rate == q)]
            t = g.groupby("M").representation_loss.mean()
            A.plot(t.index, t.values, "o-", ms=3, lw=1, color=col(1),
                   label="shared-value hash (EXACT)")
            A.axhline(0, color=col(2), lw=1, ls="-",
                      label="injective ref: label/onehot/count (EXACT, = 0)")
            A.set_xscale("log")
            A.set_title(f"{tgt.replace('_',' ')}, q = {q}", fontsize=7)
            if c == 0:
                A.set_ylabel("representation loss (nats)")
            if r == 1:
                A.set_xlabel("binary width M")
            keep.append(g.assign(panel=f"FigS3_r{r}c{c}"))
            if r == 0 and c == 0:
                A.legend(frameon=False, loc="lower right")
    fig.text(.5, -.02, "column-aware hash is omitted from this axis: its population "
             "representation loss is NOT IDENTIFIED. Its comparison appears on the "
             "ROC-AUC panel below.", ha="center", fontsize=6, color="grey")
    save(fig, "FigS3")

    if c_fi is not None:
        fig, ax = plt.subplots(1, 2, figsize=(DOUBLE, 2.4), sharey=True)
        for r, tgt in enumerate(("position_specific", "hamming_weight")):
            A = ax[r]
            g = c_fi[(c_fi.status == "SUCCESS") & (c_fi.metric == "logloss")
                     & (c_fi.target_mechanism == tgt)]
            for i, (enc, ge) in enumerate(g.groupby("encoder")):
                t = ge.groupby("M").roc_auc.mean()
                A.plot(t.index, t.values, "o-", ms=3, lw=1, color=col(i),
                       label=f"{enc} (EMPIRICAL)")
                keep.append(ge.assign(panel=f"FigS3auc_{tgt}"))
            A.axhline(.5, color="grey", lw=.6, ls=":")
            A.set(xscale="log", xlabel="binary width M",
                  title=f"{tgt.replace('_',' ')} — ROC-AUC")
            if r == 0:
                A.set_ylabel("ROC-AUC")
                A.legend(frameon=False)
        save(fig, "FigS3_auc")


def fig_s4(b, keep):
    """Representation loss and learner shortfall by n_train and learner."""
    if b is None:
        return
    fig, ax = plt.subplots(1, 2, figsize=(DOUBLE, 2.6))
    g = b[(b.status == "SUCCESS") & (b.metric == "logloss")]

    A = ax[0]
    ident = g[g.theoretical_gap_status == "IDENTIFIED_EXACT"]
    encs = sorted(ident.encoder.unique())
    for i, nt in enumerate(sorted(g.n_train.unique())):
        sub = ident[ident.n_train == nt]
        m = [sub[sub.encoder == e].representation_loss.mean() for e in encs]
        se = [sub[sub.encoder == e].representation_loss.sem() for e in encs]
        A.errorbar(np.arange(len(encs)) + (i - .5) * .18, m, yerr=se, fmt="o",
                   ms=4, lw=1, color=col(i), label=f"n_train = {nt}")
    A.set_xticks(np.arange(len(encs)))
    A.set_xticklabels(encs, rotation=45, ha="right")
    A.set(ylabel="representation loss (nats)", title="(a) representation loss")
    A.legend(frameon=False)
    n_unid = int((g.theoretical_gap_status == "NOT_IDENTIFIED").sum())
    if n_unid:
        A.text(.02, .95, f"{n_unid:,} rows omitted:\npopulation gap NOT IDENTIFIED",
               transform=A.transAxes, fontsize=5.5, va="top", color="grey")

    A = ax[1]
    lrn = sorted(x for x in g.learner.unique() if x != "bayes_z_oracle")
    for i, nt in enumerate(sorted(g.n_train.unique())):
        sub = g[g.n_train == nt]
        m = [sub[sub.learner == l].learner_shortfall.mean() for l in lrn]
        se = [sub[sub.learner == l].learner_shortfall.sem() for l in lrn]
        A.errorbar(np.arange(len(lrn)) + (i - .5) * .18, m, yerr=se, fmt="s",
                   ms=4, lw=1, color=col(i), label=f"n_train = {nt}")
    A.set_xticks(np.arange(len(lrn)))
    A.set_xticklabels(lrn, rotation=45, ha="right")
    A.set(ylabel="learner shortfall (nats)", title="(b) learner shortfall")
    A.legend(frameon=False)
    keep.append(g.assign(panel="FigS4"))
    fig.text(.5, -.16, "d = 3 signal coordinates in EVERY 1B cell: M varies the number "
             "of pure-noise columns only. Representation loss and learner shortfall "
             "are never combined.", ha="center", fontsize=6, color="grey")
    save(fig, "FigS4")


def main() -> int:
    a1, c_ex, c_fi = load("sim1a_replicates.csv"), load("sim1c_exact.csv"), \
        load("sim1c_finite.csv")
    b = load("sim1b_replicates.csv")
    print("arms:", {"1A": a1 is not None, "1C_exact": c_ex is not None,
                    "1C_finite": c_fi is not None, "1B": b is not None})
    keep: list = []
    fig_s1(a1, c_ex, b, keep)
    fig_s2(a1, keep)
    fig_s3(c_ex, c_fi, keep)
    fig_s4(b, keep)
    if keep:
        cols = ["panel", "scenario_id", "replicate", "encoder", "learner", "metric",
                "M", "K", "delta_eta", "n_train", "marginal", "activation_rate",
                "target_mechanism", "bucket_width", "representation_loss",
                "learner_shortfall", "estimated_gap", "theoretical_gap", "mcse",
                "roc_auc", "theoretical_gap_status", "exact_or_mc"]
        D = pd.concat(keep, ignore_index=True)
        D = D[[c for c in cols if c in D.columns]]
        D.to_csv(OUTD / "08_SIM1_FIGURE_DATA.csv", index=False)
        print(f"wrote 08_SIM1_FIGURE_DATA.csv ({len(D):,} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
