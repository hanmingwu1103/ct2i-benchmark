"""Hash encoders (contract 10.4).

- Column-aware (primary): token = f"{column_name}={value}"; per-record counts
  over B shared buckets via the seeded stable hash; signs DISABLED (unsigned
  counting, matching the shared-value ablation's construction so the ONLY
  difference is column identity in the token).
- Shared-value ablation: token = bare value string only (reproduces the
  Stage 1 pathological encoder).
- Bucket-width rule (frozen, from the manuscript's rule on the fitted
  training cardinality K_tot): B = 16 if K_tot<50; 32 if <500; 64 if <5000;
  else min(M, 1024).
- Stateless given (columns, B, seed): fit() only computes B from training-side
  cardinalities (One... no label use). The bare-string bucket map for "0"/"1"
  is recorded for every width (P-C additional check).
"""
from __future__ import annotations

import numpy as np

from ..hashing import bucket_of
from .base import Encoder

HASH_SEED = 20260810


def bucket_rule(k_tot: int, m: int) -> int:
    if k_tot < 50:
        return 16
    if k_tot < 500:
        return 32
    if k_tot < 5000:
        return 64
    return min(m, 1024)


class _HashBase(Encoder):
    column_aware: bool

    def fit(self, X, y=None):
        k_tot = int(sum(X[c].astype(str).nunique() for c in X.columns))
        self.n_buckets_ = bucket_rule(k_tot, X.shape[1])
        self.columns_ = list(X.columns)
        self.zero_one_buckets_ = {
            "0": bucket_of("0", self.n_buckets_, HASH_SEED),
            "1": bucket_of("1", self.n_buckets_, HASH_SEED),
        }
        return self

    def _token(self, col: str, val: str) -> str:
        return f"{col}={val}" if self.column_aware else val

    def transform(self, X):
        out = np.zeros((len(X), self.n_buckets_))
        for c in self.columns_:
            vals = X[c].astype(str).to_numpy()
            for r, s in enumerate(vals):
                out[r, bucket_of(self._token(c, s), self.n_buckets_, HASH_SEED)] += 1.0
        return out

    def state_summary(self):
        return {"B": self.n_buckets_, "seed": HASH_SEED,
                "column_aware": self.column_aware,
                "zero_one_buckets": self.zero_one_buckets_}


class ColumnAwareHashEncoder(_HashBase):
    name = "hash_column"
    column_aware = True


class SharedValueHashEncoder(_HashBase):
    name = "hash_shared"
    column_aware = False
