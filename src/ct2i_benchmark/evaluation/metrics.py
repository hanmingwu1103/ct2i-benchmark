"""Outer-test metric computation (17.5) with METRIC_UNDEFINED discipline."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
                             brier_score_loss, f1_score, log_loss, roc_auc_score)

from ..statuses import Status


def compute_metrics(y_true, y_score, threshold: float | None) -> tuple[dict, str]:
    """Returns (metrics dict with None for undefined entries, status).

    Status is METRIC_UNDEFINED only when the PRIMARY metric (AUC) is undefined
    (single-class test fold). Individual undefined secondary metrics are None
    without failing the run."""
    y_true = np.asarray(y_true, int)
    y_score = np.asarray(y_score, float)
    if len(np.unique(y_true)) < 2:
        return ({m: None for m in ["auc", "pr_auc", "logloss", "brier",
                                    "balanced_accuracy", "f1_valsel",
                                    "calibration_slope", "calibration_intercept"]},
                Status.METRIC_UNDEFINED.value)
    eps = 1e-12
    p = np.clip(y_score, eps, 1 - eps)
    out = {
        "auc": float(roc_auc_score(y_true, y_score)),
        "pr_auc": float(average_precision_score(y_true, y_score)),
        "logloss": float(log_loss(y_true, p)),
        "brier": float(brier_score_loss(y_true, y_score)),
    }
    thr = 0.5 if threshold is None else float(threshold)
    y_hat = (y_score >= thr).astype(int)
    out["balanced_accuracy"] = float(balanced_accuracy_score(y_true, y_hat))
    out["f1_valsel"] = float(f1_score(y_true, y_hat, zero_division=0))
    slope, intercept = _calibration(y_true, p)
    out["calibration_slope"] = slope
    out["calibration_intercept"] = intercept
    return out, Status.SUCCESS.value


def _calibration(y_true, p):
    """Logistic recalibration slope/intercept on logits; None when the solver
    cannot estimate (near-separation / tiny fold)."""
    logit = np.log(p / (1 - p))
    if np.ptp(logit) < 1e-9:
        return None, None
    try:
        from sklearn.linear_model import LogisticRegression
        lr = LogisticRegression(penalty=None, max_iter=1000)
        lr.fit(logit.reshape(-1, 1), y_true)
        return float(lr.coef_[0][0]), float(lr.intercept_[0])
    except Exception:
        return None, None


def select_threshold(y_val, s_val) -> float:
    """Validation-selected F1 threshold over the grid of observed scores
    (deterministic; midpoints of sorted unique scores)."""
    from sklearn.metrics import f1_score
    y_val = np.asarray(y_val, int)
    s = np.asarray(s_val, float)
    uniq = np.unique(s)
    if len(uniq) == 1 or len(np.unique(y_val)) < 2:
        return 0.5
    cands = (uniq[:-1] + uniq[1:]) / 2
    if len(cands) > 200:
        cands = cands[np.linspace(0, len(cands) - 1, 200).astype(int)]
    f1s = [f1_score(y_val, (s >= t).astype(int), zero_division=0) for t in cands]
    return float(cands[int(np.argmax(f1s))])
