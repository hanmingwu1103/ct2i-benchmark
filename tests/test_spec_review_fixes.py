"""Regression tests for the spec-review (Codex run 1) findings that were fixed
before the pilot. Each test names the finding it closes."""
import time

import numpy as np
import pandas as pd

from ct2i_benchmark.encoders import OrderedCatBoostEncoder
from ct2i_benchmark.layouts.layouts import IGTDReimpl
from ct2i_benchmark.pipeline import encode_foldsafe, run_protected
from ct2i_benchmark.splitting.outer import duplicate_groups, union_groups
from ct2i_benchmark.statuses import Status


def test_igtd_semantics():
    """Finding 4: transform must place feature perm_[i] AT cell i, matching the
    objective's fr[perm,perm] reading."""
    rng = np.random.default_rng(3)
    Z = rng.random((30, 6))
    lay = IGTDReimpl(max_step=100, seed=7).fit(Z)
    img = lay.transform(Z)
    flat = img.reshape(30, -1)
    for cell in range(6):
        assert np.allclose(flat[:, cell], Z[:, lay.perm_[cell]])


def test_ordered_catboost_operational(toy):
    """Finding 3: the ordered statistic must be the operational training-side
    representation — changing perm_seed must change the pipeline matrices."""
    X, y, g, folds = toy
    fold = folds[0]
    a = encode_foldsafe(X, y, g, fold, "ordered_catboost",
                        encoder_kwargs={"perm_seed": 977})
    b = encode_foldsafe(X, y, g, fold, "ordered_catboost",
                        encoder_kwargs={"perm_seed": 1234})
    assert not np.allclose(a.Z_inner_train_raw, b.Z_inner_train_raw)
    # Self-influence: a row's own label never enters its ordered statistic
    # directly (strictly-preceding rows only), but it DOES enter the smoothing
    # prior (mean of all fitted labels) — an O(1/n) channel that is exactly
    # the "leakage-attenuated, not leakage-free" characterization from
    # Stage 1. Assert the bound, not exact invariance (exact zero
    # self-influence is the property of the OOF-cross-fitted encoders, PC2).
    victim_pos = 3
    victim_global = fold.inner_train_ids[victim_pos]
    y2 = y.copy(); y2[victim_global] = 1 - y2[victim_global]
    c = encode_foldsafe(X, y2, g, fold, "ordered_catboost",
                        encoder_kwargs={"perm_seed": 977})
    n_itr = len(fold.inner_train_ids)
    own_shift = np.abs(a.Z_inner_train_raw[victim_pos]
                       - c.Z_inner_train_raw[victim_pos]).max()
    assert own_shift <= 2.0 / n_itr  # prior-channel bound only


def test_timeout_returns_promptly():
    """Finding PB4: run_protected must RETURN within ~timeout, not block on the
    abandoned worker."""
    t0 = time.perf_counter()
    res = run_protected(lambda: time.sleep(5) or 1, Status.TRAINING_FAILURE,
                        timeout_s=0.3)
    wall = time.perf_counter() - t0
    assert res.status == Status.TIMEOUT.value
    assert wall < 2.0  # promptly, not after the 5s sleep


def test_union_groups_bace_style():
    """Finding 1: rows identical under ANY constraint share a component."""
    scaffold = np.array([0, 0, 1, 2, 3])
    dup = np.array([0, 1, 1, 2, 3])  # rows 1,2 identical features, diff scaffolds
    comp = union_groups(scaffold, dup)
    assert comp[0] == comp[1] == comp[2]      # merged through both constraints
    assert comp[3] != comp[0] and comp[4] != comp[3]


def test_duplicate_groups_separator_safe():
    """Finding 1: rows containing the separator must not collide."""
    X = pd.DataFrame({"a": ["x|1", "x"], "b": ["y", "1|y"]})
    g = duplicate_groups(X)
    assert g[0] != g[1]


def test_hash_token_escaping():
    """Finding 3 (hash): column-aware tokens are length-prefixed unambiguous."""
    from ct2i_benchmark.encoders.hashing_enc import ColumnAwareHashEncoder
    X1 = pd.DataFrame({"a=b": ["c"]})
    X2 = pd.DataFrame({"a": ["b=c"]})
    e1 = ColumnAwareHashEncoder().fit(X1)
    e2 = ColumnAwareHashEncoder().fit(X2)
    assert e1._token("a=b", "c") != e2._token("a", "b=c")


def test_label_sentinel_no_collision():
    """Finding 3 (label): a literal '__UNSEEN__' level must not collide with
    the reserved unknown index."""
    from ct2i_benchmark.encoders import LabelEncoder
    Xf = pd.DataFrame({"a": ["__UNSEEN__", "b"]})
    le = LabelEncoder().fit(Xf)
    codes = le.transform(Xf)
    assert codes[0, 0] != 0.0                # real level, not the unknown bucket
    assert le.transform(pd.DataFrame({"a": ["zz"]}))[0, 0] == 0.0


def test_selection_ignores_outer_metrics():
    """Finding 2/5: candidate selection must be invariant to outer results —
    it reads inner metrics only."""
    from ct2i_benchmark.evaluation.selection import Candidate, select
    cands = [Candidate("a", 0.80, 1, 1.0, "SUCCESS"),
             Candidate("b", 0.85, 2, 1.0, "SUCCESS")]
    top1, _ = select(cands)
    # "outer results" do not exist in the Candidate schema at all — the type
    # system enforces the capability boundary at the selection layer.
    assert top1.config_id == "b"
    assert not hasattr(top1, "outer_metric")


def test_onehot_eligibility_production(toy):
    """Finding AC7: the PRODUCTION eligibility function must ignore outer-test
    content."""
    from ct2i_benchmark.runners import onehot_eligible
    X, y, g, folds = toy
    fold = folds[0]
    e1 = onehot_eligible(X, fold.train_ids)
    X2 = X.copy()
    X2.loc[fold.test_ids, "a"] = "MUTATED_LEVEL"
    assert onehot_eligible(X2, fold.train_ids) == e1
