"""HOMALS (homogeneity analysis by alternating least squares), r=2, with a
defensible out-of-sample transform (contract 10.4; Amendment B.7).

Implementation: classical Gifi ALS on the indicator superset of the fitted
rows. Object scores S (n x r) centered and normalized S'S = n I; category
quantifications are per-variable conditional means of object scores, updated
alternately. Canonicalization: components ordered by decreasing explained
variance proxy (quantification norm), sign fixed so each component's largest-
absolute quantification is positive; deterministic ALS init from SVD of the
centered indicator matrix (no randomness).

Out-of-sample transform: a NEW row's per-variable code is the FITTED category
quantification of its level (lookup), i.e. z_j(new) = Z_j[level]; unseen level
-> zero vector (the origin, the weighted mean of fitted quantifications).
This is the standard Gifi treatment of category points as the representation.
No refitting at transform time. NOT an MCA substitution: iterated ALS on
indicators with normalization on object scores.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .base import Encoder

R_DIM = 2
MAX_ITER = 200
TOL = 1e-8


class HomalsEncoder(Encoder):
    name = "homals"

    def fit(self, X, y=None):
        n, m = X.shape
        # indicator blocks
        levels = {c: sorted(X[c].astype(str).unique()) for c in X.columns}
        blocks, index = [], {}
        for c in X.columns:
            idx = {v: i for i, v in enumerate(levels[c])}
            G = np.zeros((n, len(levels[c])))
            G[np.arange(n), X[c].astype(str).map(idx).to_numpy()] = 1.0
            blocks.append(G)
            index[c] = idx
        Gs = blocks
        # deterministic init: SVD of centered concatenated indicators
        Gcat = np.hstack(Gs)
        Gc = Gcat - Gcat.mean(axis=0)
        U, s, _ = np.linalg.svd(Gc, full_matrices=False)
        S = U[:, :R_DIM] * np.sqrt(n)
        prev = np.inf
        for _ in range(MAX_ITER):
            Zs = []
            for G in Gs:
                D = G.sum(axis=0)
                Z = (G.T @ S) / np.maximum(D, 1.0)[:, None]
                Zs.append(Z)
            S_new = np.mean([G @ Z for G, Z in zip(Gs, Zs)], axis=0)
            S_new -= S_new.mean(axis=0)
            # orthonormalize: S'S = n I (Gram-Schmidt via SVD)
            Us, ss, Vt = np.linalg.svd(S_new, full_matrices=False)
            S_new = Us @ Vt * np.sqrt(n)
            loss = float(np.mean([np.sum((S_new - G @ Z) ** 2) for G, Z in zip(Gs, Zs)]))
            if abs(prev - loss) < TOL * max(prev, 1.0):
                S = S_new
                break
            S, prev = S_new, loss
        # final quantifications + canonicalization
        self.quant_ = {}
        norms = np.zeros(R_DIM)
        for c, G in zip(X.columns, Gs):
            D = G.sum(axis=0)
            Z = (G.T @ S) / np.maximum(D, 1.0)[:, None]
            self.quant_[c] = Z
            norms += (Z ** 2).sum(axis=0)
        order = np.argsort(-norms)
        for c in X.columns:
            Z = self.quant_[c][:, order]
            self.quant_[c] = Z
        # sign canonicalization per component over all variables
        allq = np.vstack([self.quant_[c] for c in X.columns])
        signs = np.sign(allq[np.abs(allq).argmax(axis=0), np.arange(R_DIM)])
        signs[signs == 0] = 1.0
        for c in X.columns:
            self.quant_[c] = self.quant_[c] * signs
        self.index_ = index
        self.columns_ = list(X.columns)
        return self

    def transform(self, X):
        outs = []
        for c in self.columns_:
            idx = self.index_[c]
            Z = self.quant_[c]
            block = np.zeros((len(X), R_DIM))
            for r, s in enumerate(X[c].astype(str)):
                i = idx.get(s)
                if i is not None:
                    block[r] = Z[i]  # unseen -> zero vector (origin)
            outs.append(block)
        return np.hstack(outs)

    def state_summary(self):
        return {"r": R_DIM, "levels": {c: len(i) for c, i in self.index_.items()}}
