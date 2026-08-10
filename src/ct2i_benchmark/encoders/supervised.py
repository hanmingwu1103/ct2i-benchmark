"""Supervised encoders: Target, WoE, ordered CatBoost-style (contract 10.4).

Frozen constants:
- TARGET_SMOOTHING alpha = 20.0; prior = mean of FITTED labels only; unseen
  level at transform -> prior.
- WOE pseudocount = 0.5 added to each class count of a level, with the class
  totals correspondingly augmented by 0.5 * K_c (K_c = fitted level count of
  the column), so class-conditional probabilities are properly normalized;
  clip at +/- 5.0; unseen level at transform -> 0.0 (neutral evidence — the
  frozen contract; NOT the prior).
- ORDERED_CATBOOST: n_permutations = 4, seeds = perm_seed + {0..3}, prior
  weight alpha = 1.0; code for row i under one permutation uses strictly
  preceding rows (own label NEVER in own code); final code = mean over
  permutations; `fitted_codes_` is the training-side representation consumed
  by the pipeline (operational path). Mapping for NEW rows = smoothed
  per-level target mean over ALL fitted rows (standard CatBoost inference);
  unseen level -> prior.

Target/WoE are OOF-cross-fitted by pipeline.encode_foldsafe; ordered-CatBoost
is its own cross-fitting scheme and uses fitted_codes_ directly. The P-C tests
verify both paths.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .base import Encoder

TARGET_ALPHA = 20.0
WOE_PSEUDO = 0.5
WOE_CLIP = 5.0
OCB_PERMS = 4
OCB_ALPHA = 1.0


class TargetEncoder(Encoder):
    name = "target"
    supervised = True

    def fit(self, X, y=None):
        assert y is not None
        y = np.asarray(y, float)
        self.prior_ = float(y.mean())
        self.map_ = {}
        for c in X.columns:
            df = pd.DataFrame({"v": X[c].astype(str), "y": y})
            g = df.groupby("v")["y"].agg(["sum", "size"])
            self.map_[c] = (
                (g["sum"] + TARGET_ALPHA * self.prior_) / (g["size"] + TARGET_ALPHA)
            ).to_dict()
        return self

    def transform(self, X):
        cols = []
        for c in X.columns:
            m = self.map_[c]
            cols.append(X[c].astype(str).map(lambda s, m=m: m.get(s, self.prior_)).to_numpy(float))
        return np.column_stack(cols)

    def state_summary(self):
        return {"prior": self.prior_, "levels": {c: len(m) for c, m in self.map_.items()}}


class WoEEncoder(Encoder):
    name = "woe"
    supervised = True

    def fit(self, X, y=None):
        assert y is not None
        y = np.asarray(y, int)
        n1, n0 = max(int(y.sum()), 0), max(int((1 - y).sum()), 0)
        self.map_ = {}
        for c in X.columns:
            df = pd.DataFrame({"v": X[c].astype(str), "y": y})
            g = df.groupby("v")["y"].agg(["sum", "size"])
            k_c = len(g)  # class totals augmented by pseudo*K_c: proper normalization
            pos = g["sum"] + WOE_PSEUDO
            neg = (g["size"] - g["sum"]) + WOE_PSEUDO
            woe = np.log((pos / (n1 + WOE_PSEUDO * k_c)) / (neg / (n0 + WOE_PSEUDO * k_c)))
            self.map_[c] = woe.clip(-WOE_CLIP, WOE_CLIP).to_dict()
        return self

    def transform(self, X):
        cols = []
        for c in X.columns:
            m = self.map_[c]
            cols.append(X[c].astype(str).map(lambda s, m=m: m.get(s, 0.0)).to_numpy(float))
        return np.column_stack(cols)

    def state_summary(self):
        return {"levels": {c: len(m) for c, m in self.map_.items()}}


class OrderedCatBoostEncoder(Encoder):
    name = "ordered_catboost"
    supervised = True

    def __init__(self, perm_seed: int = 977):
        self.perm_seed = perm_seed

    def fit(self, X, y=None):
        assert y is not None
        y = np.asarray(y, float)
        n = len(y)
        self.prior_ = float(y.mean())
        self.fitted_codes_ = np.zeros((n, X.shape[1]))
        for j, c in enumerate(X.columns):
            v = X[c].astype(str).to_numpy()
            acc = np.zeros(n)
            for p in range(OCB_PERMS):
                rng = np.random.default_rng(self.perm_seed + p)
                order = rng.permutation(n)
                run_sum: dict[str, float] = {}
                run_cnt: dict[str, int] = {}
                codes = np.empty(n)
                for pos_i, i in enumerate(order):
                    s = v[i]
                    cnt = run_cnt.get(s, 0)
                    ssum = run_sum.get(s, 0.0)
                    codes[i] = (ssum + OCB_ALPHA * self.prior_) / (cnt + OCB_ALPHA)
                    run_cnt[s] = cnt + 1
                    run_sum[s] = ssum + y[i]
                acc += codes
            self.fitted_codes_[:, j] = acc / OCB_PERMS
        # inference mapping for new rows: full-fit smoothed level means
        self.map_ = {}
        for c in X.columns:
            df = pd.DataFrame({"v": X[c].astype(str), "y": y})
            g = df.groupby("v")["y"].agg(["sum", "size"])
            self.map_[c] = (
                (g["sum"] + OCB_ALPHA * self.prior_) / (g["size"] + OCB_ALPHA)
            ).to_dict()
        self._fit_index = None  # set by engine when fitted_codes are used in-place
        return self

    def transform(self, X):
        cols = []
        for c in X.columns:
            m = self.map_[c]
            cols.append(X[c].astype(str).map(lambda s, m=m: m.get(s, self.prior_)).to_numpy(float))
        return np.column_stack(cols)

    def state_summary(self):
        return {"prior": self.prior_, "perm_seed": self.perm_seed, "n_perms": OCB_PERMS,
                "levels": {c: len(m) for c, m in self.map_.items()}}
