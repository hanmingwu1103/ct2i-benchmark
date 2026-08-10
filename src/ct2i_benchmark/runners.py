"""Stage 2 execution runners: smoke, microbenchmark, frozen CPU pilot,
reconstructed global-vs-fold-safe comparison, simulations.

All runs are CPU-only, seeded, typed, and lineage-tracked. Cell execution is
shared between the pilot and the P-A comparison.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import psutil

from .evaluation.metrics import compute_metrics, select_threshold
from .layouts.layouts import MAX_NATIVE_PIXELS, resize_to_diag
from .layouts.layouts import REGISTRY as LAYOUTS
from .models.wrappers import REGISTRY as MODELS
from .pipeline import encode_foldsafe, encode_global, run_protected
from .readers.pca_mlp import PcaMlpReader
from .statuses import Status

REPO = Path(__file__).resolve().parents[2]
CACHE = REPO / ".cache"
ONEHOT_WIDTH_CAP = 1500  # encoded columns; training-side cardinalities only


def load_dataset(ds: str):
    X = pd.read_parquet(CACHE / "processed" / f"{ds}_X.parquet")
    y = np.load(CACHE / "processed" / f"{ds}_y.npy")
    g = np.load(CACHE / "processed" / f"{ds}_groups.npy")
    return X, y, g


def load_folds(ds: str, audit: Path):
    doc = json.loads((audit / "splits" / f"{ds}_folds.json").read_text())
    from .splitting.outer import FoldSpec
    return [FoldSpec(f["outer_fold"], np.array(f["train_ids"]), np.array(f["test_ids"]),
                     np.array(f["inner_train_ids"]), np.array(f["inner_val_ids"]))
            for f in doc["folds"]]


def onehot_eligible(X, train_ids):
    width = sum(X.iloc[train_ids][c].nunique() + 1 for c in X.columns)
    return width <= ONEHOT_WIDTH_CAP


def _mem_mb():
    return psutil.Process().memory_info().rss / 2**20


def run_image_cell(X, y, g, fold, encoder, layout_name, seed, commit,
                   protocol="foldsafe", timeout_s=900):
    """One image-branch cell: encode -> layout -> render 64x64 -> PCA+MLP.
    Returns run dict (typed)."""
    t0 = time.perf_counter()
    rec = {"encoder": encoder, "layout": layout_name, "reader_or_model": "pca_mlp",
           "seed": seed, "outer_fold": fold.outer_fold, "protocol": protocol,
           "stage_of_failure": None, "exception_class": None,
           "inner_auc": None, "metrics": None, "threshold": None}
    step = run_protected(
        lambda: encode_foldsafe(X, y, g, fold, encoder, commit=commit)
        if protocol == "foldsafe" else None,
        Status.ENCODING_FAILURE, timeout_s=timeout_s)
    if protocol == "global":
        step = run_protected(lambda: encode_global(X, y, fold, encoder),
                             Status.ENCODING_FAILURE, timeout_s=timeout_s)
    if step.status != "SUCCESS":
        rec.update(status=step.status, stage_of_failure="encoding",
                   exception_class=step.exception_class,
                   elapsed_s=time.perf_counter() - t0, peak_rss_mb=_mem_mb())
        return rec
    if protocol == "foldsafe":
        ef = step.value
        Zi, Zv, Zo, Zt = ef.Z_inner_train, ef.Z_inner_val, ef.Z_outer_train, ef.Z_outer_test
    else:
        Zi, Zv, Zo, Zt = step.value

    d = Zi.shape[1]
    lay_cls = LAYOUTS[layout_name]
    lay = lay_cls() if layout_name != "igtd_reimpl" else lay_cls(max_step=2000, seed=7)
    native_px = lay.native_pixels(d)
    if native_px > MAX_NATIVE_PIXELS:
        rec.update(status=Status.SKIPPED_INELIGIBLE.value,
                   stage_of_failure="layout_eligibility",
                   notes=f"native_pixels={native_px}>cap",
                   elapsed_s=time.perf_counter() - t0, peak_rss_mb=_mem_mb())
        return rec

    def _fit_render():
        if protocol == "foldsafe":
            lay.fit(Zi)                      # training-side ONLY
            img_i, img_v = lay.transform(Zi), lay.transform(Zv)
            lay_o = (lay_cls() if layout_name != "igtd_reimpl"
                     else lay_cls(max_step=2000, seed=7)).fit(Zo)
            img_o, img_t = lay_o.transform(Zo), lay_o.transform(Zt)
        else:                                # RECONSTRUCTED-CONTAMINATED
            lay.fit(np.vstack([Zo, Zt]))     # complete matrix, images once
            img_i, img_v = lay.transform(Zi), lay.transform(Zv)
            img_o, img_t = lay.transform(Zo), lay.transform(Zt)
        return tuple(resize_to_diag(m) for m in (img_i, img_v, img_o, img_t))

    step = run_protected(_fit_render, Status.LAYOUT_FAILURE, timeout_s=timeout_s)
    if step.status != "SUCCESS":
        rec.update(status=step.status, stage_of_failure="layout_fit",
                   exception_class=step.exception_class,
                   elapsed_s=time.perf_counter() - t0, peak_rss_mb=_mem_mb())
        return rec
    di, dv, do, dt = step.value

    def _train_eval():
        r = PcaMlpReader(seed=seed)
        r.fit(di, y[fold.inner_train_ids])
        s_val = r.predict_proba(dv)
        from sklearn.metrics import roc_auc_score
        inner_auc = (roc_auc_score(y[fold.inner_val_ids], s_val)
                     if len(np.unique(y[fold.inner_val_ids])) > 1 else None)
        thr = select_threshold(y[fold.inner_val_ids], s_val)
        r2 = PcaMlpReader(seed=seed)
        r2.fit(do, y[fold.train_ids])
        s_test = r2.predict_proba(dt)
        return inner_auc, thr, s_test

    step = run_protected(_train_eval, Status.TRAINING_FAILURE, timeout_s=timeout_s)
    if step.status != "SUCCESS":
        rec.update(status=step.status, stage_of_failure="reader_fit",
                   exception_class=step.exception_class,
                   elapsed_s=time.perf_counter() - t0, peak_rss_mb=_mem_mb())
        return rec
    inner_auc, thr, s_test = step.value
    m, mstatus = compute_metrics(y[fold.test_ids], s_test, thr)
    rec.update(status=mstatus, inner_auc=inner_auc, threshold=thr, metrics=m,
               y_score_test=s_test.tolist(), elapsed_s=time.perf_counter() - t0,
               peak_rss_mb=_mem_mb())
    return rec


def run_tabular_cell(X, y, g, fold, encoder, model_name, seed, commit,
                     protocol="foldsafe", model_kwargs=None, timeout_s=600):
    """One tabular cell. encoder=None + catboost_native -> raw categorical."""
    t0 = time.perf_counter()
    rec = {"encoder": encoder or "raw", "layout": "none",
           "reader_or_model": model_name, "seed": seed,
           "outer_fold": fold.outer_fold, "protocol": protocol,
           "stage_of_failure": None, "exception_class": None,
           "inner_auc": None, "metrics": None, "threshold": None}
    if model_name == "catboost_native":
        Xi, Xv = X.iloc[fold.inner_train_ids], X.iloc[fold.inner_val_ids]
        Xo, Xt = X.iloc[fold.train_ids], X.iloc[fold.test_ids]
    else:
        if protocol == "foldsafe":
            step = run_protected(lambda: encode_foldsafe(X, y, g, fold, encoder,
                                                         commit=commit),
                                 Status.ENCODING_FAILURE, timeout_s=timeout_s)
        else:
            step = run_protected(lambda: encode_global(X, y, fold, encoder),
                                 Status.ENCODING_FAILURE, timeout_s=timeout_s)
        if step.status != "SUCCESS":
            rec.update(status=step.status, stage_of_failure="encoding",
                       exception_class=step.exception_class,
                       elapsed_s=time.perf_counter() - t0, peak_rss_mb=_mem_mb())
            return rec
        if protocol == "foldsafe":
            ef = step.value
            Xi, Xv, Xo, Xt = ef.Z_inner_train, ef.Z_inner_val, ef.Z_outer_train, ef.Z_outer_test
        else:
            Xi, Xv, Xo, Xt = step.value

    def _train_eval():
        kw = dict(model_kwargs or {})
        if "seed" in MODELS[model_name].__init__.__code__.co_varnames:
            kw.setdefault("seed", seed)
        m1 = MODELS[model_name](**kw)
        m1.fit(Xi, y[fold.inner_train_ids])
        s_val = m1.predict_proba(Xv)
        from sklearn.metrics import roc_auc_score
        inner_auc = (roc_auc_score(y[fold.inner_val_ids], s_val)
                     if len(np.unique(y[fold.inner_val_ids])) > 1 else None)
        thr = select_threshold(y[fold.inner_val_ids], s_val)
        m2 = MODELS[model_name](**kw)
        m2.fit(Xo, y[fold.train_ids])
        s_test = m2.predict_proba(Xt)
        return inner_auc, thr, s_test

    step = run_protected(_train_eval, Status.TRAINING_FAILURE, timeout_s=timeout_s)
    if step.status != "SUCCESS":
        rec.update(status=step.status, stage_of_failure="model_fit",
                   exception_class=step.exception_class,
                   elapsed_s=time.perf_counter() - t0, peak_rss_mb=_mem_mb())
        return rec
    inner_auc, thr, s_test = step.value
    m, mstatus = compute_metrics(y[fold.test_ids], s_test, thr)
    rec.update(status=mstatus, inner_auc=inner_auc, threshold=thr, metrics=m,
               y_score_test=s_test.tolist(), elapsed_s=time.perf_counter() - t0,
               peak_rss_mb=_mem_mb())
    return rec


def dispatch(args):
    raise SystemExit("Use scripts/*.py entry points in Stage 2")
