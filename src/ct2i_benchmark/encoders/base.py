"""Encoder base contracts (code-grade contract 10.4).

Frozen conventions:
- Category-string normalization: values are used as exact Python strings after
  pandas `.astype(str)`; no case-folding or stripping (source strings are
  already canonical for the pilot datasets).
- Missing values arrive as the explicit string category produced upstream
  (e.g. "?" for Mushroom stalk-root). No encoder treats it specially.
- Unseen level at transform: encoder-specific frozen fallback (see subclasses).
- Rare levels: no pooling in Stage 2 (sensitivity option deferred to Stage 3).
- All encoders are fit(X[, y]) -> self; transform(X) -> float64 ndarray.
- Supervised encoders additionally implement fit_transform_oof(...) via the
  cross-fitting engine in pipeline.py (never inside the encoder itself).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class Encoder:
    name: str = "base"
    supervised: bool = False

    def fit(self, X: pd.DataFrame, y: np.ndarray | None = None) -> "Encoder":
        raise NotImplementedError

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError

    def state_summary(self) -> dict:
        """JSON-able fitted-state summary for artifact hashing."""
        raise NotImplementedError


class MinMaxScaler01:
    """Min-Max to [0,1] fitted on training-side codes only; transform clips."""

    def fit(self, Z: np.ndarray) -> "MinMaxScaler01":
        self.lo_ = Z.min(axis=0)
        self.hi_ = Z.max(axis=0)
        self.span_ = np.where(self.hi_ > self.lo_, self.hi_ - self.lo_, 1.0)
        self.const_ = self.hi_ <= self.lo_
        return self

    def transform(self, Z: np.ndarray) -> np.ndarray:
        out = (Z - self.lo_) / self.span_
        out = np.clip(out, 0.0, 1.0)
        out[:, self.const_] = 0.0
        return out

    def state_summary(self) -> dict:
        return {"lo": self.lo_.tolist(), "hi": self.hi_.tolist()}
