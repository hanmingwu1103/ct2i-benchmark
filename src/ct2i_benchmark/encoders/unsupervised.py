"""Label-free encoders: Label, One-Hot, Count (contract 10.4).

Split into per-concept classes; re-exported by thin modules label.py etc. to
keep the architecture's conceptual separation visible.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .base import Encoder

UNSEEN = "__UNSEEN__"


class LabelEncoder(Encoder):
    """Integer index per level, vocabulary fitted on training rows; unseen ->
    reserved index 0 (UNSEEN bucket fitted into the vocabulary)."""
    name = "label"

    def fit(self, X, y=None):
        self.vocab_ = {}
        for c in X.columns:
            levels = sorted(X[c].astype(str).unique())
            self.vocab_[c] = {UNSEEN: 0, **{v: i + 1 for i, v in enumerate(levels)}}
        return self

    def transform(self, X):
        cols = []
        for c in X.columns:
            v = self.vocab_[c]
            cols.append(X[c].astype(str).map(lambda s, v=v: v.get(s, 0)).to_numpy(float))
        return np.column_stack(cols)

    def state_summary(self):
        return {c: len(v) for c, v in self.vocab_.items()}


class OneHotEncoder01(Encoder):
    """Binary indicator per fitted level + one UNSEEN column per variable.
    Width-eligibility guard is applied OUTSIDE (pipeline) using training-side
    cardinalities only."""
    name = "onehot"

    def fit(self, X, y=None):
        self.levels_ = {c: sorted(X[c].astype(str).unique()) for c in X.columns}
        return self

    def transform(self, X):
        blocks = []
        for c in X.columns:
            lv = self.levels_[c]
            index = {v: i for i, v in enumerate(lv)}
            block = np.zeros((len(X), len(lv) + 1))
            for r, s in enumerate(X[c].astype(str)):
                block[r, index.get(s, len(lv))] = 1.0  # last col = UNSEEN
            blocks.append(block)
        return np.hstack(blocks)

    def state_summary(self):
        return {c: len(v) for c, v in self.levels_.items()}


class CountEncoder(Encoder):
    """Relative frequency of the level among FITTED rows; unseen -> 0.0.
    Denominator = number of fitted rows (frozen)."""
    name = "count"

    def fit(self, X, y=None):
        self.freq_ = {}
        n = len(X)
        for c in X.columns:
            vc = X[c].astype(str).value_counts()
            self.freq_[c] = (vc / n).to_dict()
        return self

    def transform(self, X):
        cols = []
        for c in X.columns:
            f = self.freq_[c]
            cols.append(X[c].astype(str).map(lambda s, f=f: f.get(s, 0.0)).to_numpy(float))
        return np.column_stack(cols)

    def state_summary(self):
        return {c: len(f) for c, f in self.freq_.items()}
