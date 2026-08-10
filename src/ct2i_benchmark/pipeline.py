"""Fold-safe execution engine (code-grade contract §10).

encode_foldsafe() implements 10.3 exactly:
  inner candidate evaluation:
    1-4. supervised encoders are OOF-cross-fitted on inner-training rows;
    5.   an inner-training-fitted mapping transforms inner-validation;
    6.   scaler fitted only on (OOF) inner-training codes;
    7.   fitted layout fitted only on scaled inner-training codes;
    8.   inner-validation transformed without refitting.
  after selection:
    OOF codes on the full outer-training fold; full outer-training mapping for
    outer test; scaler/layout on outer-training artifacts only; refit selected
    model; evaluate outer test once.

encode_global() reconstructs the CONTAMINATED Stage 1 protocol for P-A only
(encoder/scaler/layout fitted on ALL rows; images generated once). It is
clearly labelled and never used by the pilot's primary path.

run_protected() wraps any step with typed-status capture and a soft timeout
(thread-executor with abandonment; documented limitation: the abandoned
worker thread may continue until process exit, but its outputs are discarded
and its status is TIMEOUT).
"""
from __future__ import annotations

import time
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutTimeout
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .artifacts.lineage import LineageRecord
from .encoders import REGISTRY as ENC_REGISTRY, SUPERVISED, MinMaxScaler01
from .splitting.outer import oof_folds
from .statuses import Status


@dataclass
class EncodedFold:
    """Fold-safe encoded matrices + lineage for one (dataset, fold, encoder)."""
    Z_inner_train: np.ndarray
    Z_inner_val: np.ndarray
    Z_outer_train: np.ndarray
    Z_outer_test: np.ndarray
    lineage: list


def encode_foldsafe(X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, fold,
                    encoder_name: str, seed_oof: int = 4211, commit="UNCOMMITTED",
                    encoder_kwargs=None) -> EncodedFold:
    enc_cls = ENC_REGISTRY[encoder_name]
    kw = encoder_kwargs or {}
    lineage = []
    itr, iva = fold.inner_train_ids, fold.inner_val_ids
    otr, ote = fold.train_ids, fold.test_ids
    supervised = encoder_name in SUPERVISED

    def _fit_enc(row_ids, label_ids, role):
        enc = enc_cls(**kw)
        if supervised:
            enc.fit(X.iloc[row_ids], y[row_ids])
        else:
            enc.fit(X.iloc[row_ids])
        lineage.append(LineageRecord.create(
            artifact_id=f"enc|{encoder_name}|f{fold.outer_fold}|{role}",
            artifact_type=f"encoder:{encoder_name}",
            config=kw, fit_row_ids=row_ids,
            fit_label_ids=label_ids if supervised else [],
            transform_row_ids=[], outer_fold=fold.outer_fold, role=role,
            seed_set={"oof": seed_oof}, commit=commit))
        return enc

    if supervised:
        # --- inner: OOF codes for inner-training rows ---
        Z_itr = np.zeros((len(itr), 0))
        oof = oof_folds(itr, y, groups, seed=seed_oof)
        parts = {}
        width = None
        for k_i, (fit_l, hold_l) in enumerate(oof):
            enc_k = _fit_enc(itr[fit_l], itr[fit_l], f"inner_oof{k_i}")
            codes = enc_k.transform(X.iloc[itr[hold_l]])
            width = codes.shape[1]
            for pos, li in enumerate(hold_l):
                parts[li] = codes[pos]
        Z_itr = np.vstack([parts[i] for i in range(len(itr))])
        # --- inner-val: mapping fitted on ALL inner-training rows ---
        enc_it = _fit_enc(itr, itr, "inner_map")
        Z_iva = enc_it.transform(X.iloc[iva])
        # --- outer: OOF codes on the complete outer-training fold ---
        oof_o = oof_folds(otr, y, groups, seed=seed_oof + 7)
        parts_o = {}
        for k_i, (fit_l, hold_l) in enumerate(oof_o):
            enc_k = _fit_enc(otr[fit_l], otr[fit_l], f"outer_oof{k_i}")
            codes = enc_k.transform(X.iloc[otr[hold_l]])
            for pos, li in enumerate(hold_l):
                parts_o[li] = codes[pos]
        Z_otr = np.vstack([parts_o[i] for i in range(len(otr))])
        enc_full = _fit_enc(otr, otr, "outer_map")
        Z_ote = enc_full.transform(X.iloc[ote])
    else:
        enc_i = _fit_enc(itr, [], "inner_fit")
        Z_itr = enc_i.transform(X.iloc[itr])
        Z_iva = enc_i.transform(X.iloc[iva])
        enc_o = _fit_enc(otr, [], "outer_fit")
        Z_otr = enc_o.transform(X.iloc[otr])
        Z_ote = enc_o.transform(X.iloc[ote])

    # --- scaler: fitted on (OOF) training-side codes only ---
    sc_i = MinMaxScaler01().fit(Z_itr)
    sc_o = MinMaxScaler01().fit(Z_otr)
    lineage.append(LineageRecord.create(
        artifact_id=f"scaler|{encoder_name}|f{fold.outer_fold}|inner",
        artifact_type="scaler:minmax", config={}, fit_row_ids=itr, fit_label_ids=[],
        transform_row_ids=iva, outer_fold=fold.outer_fold, role="inner",
        seed_set={}, commit=commit))
    lineage.append(LineageRecord.create(
        artifact_id=f"scaler|{encoder_name}|f{fold.outer_fold}|outer",
        artifact_type="scaler:minmax", config={}, fit_row_ids=otr, fit_label_ids=[],
        transform_row_ids=ote, outer_fold=fold.outer_fold, role="outer",
        seed_set={}, commit=commit))
    return EncodedFold(sc_i.transform(Z_itr), sc_i.transform(Z_iva),
                       sc_o.transform(Z_otr), sc_o.transform(Z_ote), lineage)


def encode_global(X: pd.DataFrame, y: np.ndarray, fold, encoder_name: str,
                  encoder_kwargs=None):
    """RECONSTRUCTED CONTAMINATED PROTOCOL (P-A arm 1 only): encoder + scaler
    fitted on ALL rows (labels included for supervised encoders), then rows are
    sliced by fold. Never used in the pilot's primary path."""
    enc_cls = ENC_REGISTRY[encoder_name]
    enc = enc_cls(**(encoder_kwargs or {}))
    if encoder_name in SUPERVISED:
        enc.fit(X, y)
    else:
        enc.fit(X)
    Z_all = enc.transform(X)
    sc = MinMaxScaler01().fit(Z_all)
    Z = sc.transform(Z_all)
    return (Z[fold.inner_train_ids], Z[fold.inner_val_ids],
            Z[fold.train_ids], Z[fold.test_ids])


@dataclass
class StepResult:
    status: str
    value: object = None
    elapsed_s: float = 0.0
    exception_class: str | None = None
    message: str | None = None


_EXC_STATUS = {
    "MemoryError": Status.RESOURCE_LIMIT,
    "FloatingPointError": Status.NUMERICAL_FAILURE,
    "KeyboardInterrupt": Status.INTERRUPTED,
    "ImportError": Status.DEPENDENCY_UNAVAILABLE,
    "ModuleNotFoundError": Status.DEPENDENCY_UNAVAILABLE,
}


def run_protected(fn, stage_status: Status, timeout_s: float | None = None,
                  *args, **kwargs) -> StepResult:
    """Execute fn with typed-status capture and a soft timeout."""
    t0 = time.perf_counter()
    try:
        if timeout_s is None:
            value = fn(*args, **kwargs)
        else:
            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(fn, *args, **kwargs)
                try:
                    value = fut.result(timeout=timeout_s)
                except FutTimeout:
                    fut.cancel()
                    return StepResult(Status.TIMEOUT.value,
                                      elapsed_s=time.perf_counter() - t0)
        result = np.asarray(value, dtype=object) if False else value
        # NaN/Inf guard for numeric outputs
        if isinstance(value, np.ndarray) and value.dtype.kind == "f" \
                and not np.isfinite(value).all():
            return StepResult(Status.NUMERICAL_FAILURE.value,
                              elapsed_s=time.perf_counter() - t0,
                              exception_class="NonFiniteOutput")
        return StepResult(Status.SUCCESS.value, result, time.perf_counter() - t0)
    except Exception as e:  # noqa: BLE001 — typed capture is the point
        status = _EXC_STATUS.get(type(e).__name__, stage_status)
        return StepResult(status.value, None, time.perf_counter() - t0,
                          type(e).__name__, _sanitize(str(e)))


def _sanitize(msg: str, limit: int = 300) -> str:
    import re
    msg = re.sub(r"[A-Za-z]:\\\\?[^\s'\"]+", "<path>", msg)
    return msg[:limit]


def format_exception(e: BaseException) -> str:
    return _sanitize("".join(traceback.format_exception_only(type(e), e)))
