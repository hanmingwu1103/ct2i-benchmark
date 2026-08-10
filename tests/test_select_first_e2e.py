"""End-to-end production proof of select-first behavior (Codex re-review
blocker 2/7): running the PRODUCTION cell runners over a candidate grid and
selecting with the PRODUCTION selection path must yield an identical selected
candidate and identical inner scores when outer-test labels are permuted.
Outer metrics may change; the selection may not."""
import numpy as np

from ct2i_benchmark.evaluation.selection import Candidate, rank_candidates
from ct2i_benchmark.runners import run_image_cell, run_tabular_cell, onehot_eligible


def _run_grid(X, y, g, fold):
    recs = []
    for enc in ["label", "target"]:
        r = run_image_cell(X, y, g, fold, enc, "bie", 1042, "TEST", timeout_s=300)
        r["cell_id"] = f"img|{enc}"
        recs.append(r)
        r = run_tabular_cell(X, y, g, fold, enc, "lightgbm", 5, "TEST",
                             model_kwargs={"n_estimators": 40}, timeout_s=300)
        r["cell_id"] = f"tab|{enc}"
        recs.append(r)
    return recs


def _select(recs):
    cands = [Candidate(r["cell_id"], r["inner_auc"], 2,
                       r["inner_elapsed_s"] or 0.0,
                       r["inner_status"] or "TRAINING_FAILURE") for r in recs]
    ranked = rank_candidates(cands)
    return ranked[0].config_id if ranked else None, \
        {c.config_id: c.inner_metric for c in cands}


def test_select_first_outer_label_invariance(toy):
    X, y, g, folds = toy
    fold = folds[1]
    recs_a = _run_grid(X, y, g, fold)
    sel_a, inner_a = _select(recs_a)

    y_perm = y.copy()
    rng = np.random.default_rng(99)
    y_perm[fold.test_ids] = rng.permutation(y_perm[fold.test_ids])
    recs_b = _run_grid(X, y_perm, g, fold)
    sel_b, inner_b = _select(recs_b)

    assert sel_a == sel_b                     # selection unchanged
    assert inner_a == inner_b                 # inner scores identical
    # sanity: the permutation was real (some outer metric moved)
    moved = any(
        (ra["metrics"] or {}).get("auc") != (rb["metrics"] or {}).get("auc")
        for ra, rb in zip(recs_a, recs_b)
        if ra["status"] == "SUCCESS" and rb["status"] == "SUCCESS")
    assert moved


def test_eligibility_inner_train_only(toy):
    """Blocker 3/7: the production eligibility gate reads inner-training rows
    only — mutating inner-validation OR outer-test features cannot change it."""
    X, y, g, folds = toy
    fold = folds[0]
    base = onehot_eligible(X, fold.inner_train_ids)
    X_mut = X.copy()
    X_mut.loc[fold.inner_val_ids, "a"] = "MUT_IVAL"
    X_mut.loc[fold.test_ids, "b"] = "MUT_TEST"
    assert onehot_eligible(X_mut, fold.inner_train_ids) == base
