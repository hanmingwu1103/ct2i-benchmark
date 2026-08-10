"""Deterministic group-aware stratified splits (code-grade contract 10.1/10.2).

- Outer: 5-fold StratifiedGroupKFold (groups = duplicate groups or scaffolds).
- Inner: one group-aware stratified 80/20 split of the outer-training rows.
- OOF: deterministic group-aware folds of the inner-training rows for
  supervised-encoder cross-fitting.
Splits are created BEFORE any learned preprocessing and persisted with hashes.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from ..hashing import sha256_array


def duplicate_groups(X: pd.DataFrame) -> np.ndarray:
    """Exact-feature duplicate groups: identical canonical feature rows share a
    group id. Label-free by construction (labels never consulted)."""
    keys = X.astype(str).agg("\x1f".join, axis=1)
    codes, _ = pd.factorize(keys, sort=True)
    return codes.astype(np.int64)


def conflicting_label_groups(groups: np.ndarray, y: np.ndarray) -> int:
    """Count duplicate groups whose members carry conflicting labels (reported,
    never deleted)."""
    df = pd.DataFrame({"g": groups, "y": y})
    n_lab = df.groupby("g")["y"].nunique()
    return int((n_lab > 1).sum())


@dataclass
class FoldSpec:
    outer_fold: int
    train_ids: np.ndarray
    test_ids: np.ndarray
    inner_train_ids: np.ndarray
    inner_val_ids: np.ndarray

    def sha256(self) -> str:
        return sha256_array(np.concatenate([
            np.sort(self.train_ids), [-1], np.sort(self.test_ids), [-2],
            np.sort(self.inner_train_ids), [-3], np.sort(self.inner_val_ids)]).astype(np.int64))


def make_folds(y: np.ndarray, groups: np.ndarray, n_outer: int = 5,
               seed_fold: int = 42, seed_inner: int = 421, inner_frac: float = 0.2):
    """Deterministic outer folds + one inner group-aware stratified split each."""
    y = np.asarray(y)
    groups = np.asarray(groups)
    idx = np.arange(len(y))
    sgkf = StratifiedGroupKFold(n_splits=n_outer, shuffle=True, random_state=seed_fold)
    folds: list[FoldSpec] = []
    for k, (tr, te) in enumerate(sgkf.split(idx, y, groups)):
        itr, iva = _inner_split(tr, y[tr], groups[tr], seed_inner + k, inner_frac)
        folds.append(FoldSpec(k, idx[tr], idx[te], idx[tr][itr], idx[tr][iva]))
    _assert_no_group_overlap(folds, groups)
    return folds


def _inner_split(local_idx, y_tr, g_tr, seed, frac):
    """Group-aware stratified holdout: greedy assignment of groups to the
    validation side, deterministic under the seed."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({"i": np.arange(len(local_idx)), "y": y_tr, "g": g_tr})
    gsum = df.groupby("g").agg(n=("i", "size"), pos=("y", "sum"))
    order = rng.permutation(gsum.index.to_numpy())
    target_n = frac * len(df)
    target_pos = frac * df["y"].sum()
    val_groups, got_n, got_pos = [], 0, 0
    for g in order:
        n, pos = int(gsum.loc[g, "n"]), int(gsum.loc[g, "pos"])
        if got_n + n <= target_n * 1.25 and got_n < target_n:
            take = (got_pos < target_pos) or (pos == 0)
            if take:
                val_groups.append(g); got_n += n; got_pos += pos
    val_set = set(val_groups)
    mask_val = df["g"].isin(val_set).to_numpy()
    if mask_val.sum() == 0 or mask_val.sum() == len(df):
        raise ValueError("degenerate inner split")
    # both classes must appear on both sides where possible
    if y_tr[~mask_val].sum() == 0 or y_tr[mask_val].sum() == 0:
        # deterministic fallback: move the smallest positive-containing group
        pos_groups = gsum[gsum["pos"] > 0].sort_values("n").index
        for g in pos_groups:
            flip = df["g"].eq(g).to_numpy()
            if y_tr[mask_val | flip].sum() > 0 and y_tr[~(mask_val | flip)].sum() > 0:
                mask_val = mask_val | flip
                break
    return np.where(~mask_val)[0], np.where(mask_val)[0]


def oof_folds(inner_train_ids: np.ndarray, y: np.ndarray, groups: np.ndarray,
              k: int = 5, seed: int = 4211):
    """Deterministic LABEL-FREE group-aware OOF folds for supervised-encoder
    cross-fitting. The partition is a function of (row ids, groups, seed) ONLY:
    stratifying the OOF partition on labels would make the partition itself
    label-dependent and break the self-influence invariant (P-C test 2).
    Groups are seed-shuffled and round-robin assigned to k folds.
    Returns list of (fit_local_idx, holdout_local_idx)."""
    ids = np.asarray(inner_train_ids)
    g_l = groups[ids]
    uniq = np.unique(g_l)
    k_eff = max(2, min(k, len(uniq)))
    rng = np.random.default_rng(seed)
    order = rng.permutation(uniq)
    fold_of_group = {g: i % k_eff for i, g in enumerate(order)}
    assign = np.array([fold_of_group[g] for g in g_l])
    out = []
    for f in range(k_eff):
        hold = np.where(assign == f)[0]
        fit = np.where(assign != f)[0]
        if len(hold) and len(fit):
            out.append((fit, hold))
    return out


def _assert_no_group_overlap(folds, groups):
    for f in folds:
        tr_g = set(groups[f.train_ids]); te_g = set(groups[f.test_ids])
        if tr_g & te_g:
            raise AssertionError(f"outer fold {f.outer_fold}: group overlap train/test")
        itr_g = set(groups[f.inner_train_ids]); iva_g = set(groups[f.inner_val_ids])
        if itr_g & iva_g:
            raise AssertionError(f"outer fold {f.outer_fold}: group overlap inner")
