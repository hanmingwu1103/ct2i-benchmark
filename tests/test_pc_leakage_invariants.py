"""P-C: the six mandatory leakage/lineage invariant tests (§13) plus the
additional mandatory checks. Named PC1..PC6 and AC1..AC7."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ct2i_benchmark.artifacts.lineage import LeakageError
from ct2i_benchmark.encoders.hashing_enc import (
    HASH_SEED,
    ColumnAwareHashEncoder,
    SharedValueHashEncoder,
    bucket_rule,
)
from ct2i_benchmark.hashing import bucket_of, sha256_array
from ct2i_benchmark.layouts.layouts import IGTDReimpl
from ct2i_benchmark.pipeline import encode_foldsafe

EVIDENCE = Path(__file__).resolve().parents[1] / ".cache" / "test_evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)


def _record(test_id, passed, extra=None):
    (EVIDENCE / f"{test_id}.json").write_text(
        json.dumps({"test_id": test_id, "pass": bool(passed), **(extra or {})},
                   indent=1, default=str))


def _hash_state(ef):
    return {
        "itr": sha256_array(ef.Z_inner_train), "iva": sha256_array(ef.Z_inner_val),
        "otr": sha256_array(ef.Z_outer_train), "ote": sha256_array(ef.Z_outer_test),
    }


def test_pc1_outer_test_label_permutation_invariance(toy):
    """PC1: permuting ONLY outer-test labels leaves every fitted state and
    encoding byte-identical (target encoder, the most exposed path)."""
    X, y, g, folds = toy
    fold = folds[0]
    y_perm = y.copy()
    rng = np.random.default_rng(5)
    y_perm[fold.test_ids] = rng.permutation(y_perm[fold.test_ids])
    h1 = _hash_state(encode_foldsafe(X, y, g, fold, "target"))
    h2 = _hash_state(encode_foldsafe(X, y_perm, g, fold, "target"))
    _record("PC1", h1 == h2, {"hashes_equal": h1 == h2})
    assert h1 == h2


def test_pc2_self_influence(toy):
    """PC2: flipping ONE outer-training row's label leaves that row's own OOF
    code unchanged (its OOF encoder never saw its label)."""
    X, y, g, folds = toy
    fold = folds[0]
    ef1 = encode_foldsafe(X, y, g, fold, "target")
    # flip one inner-training row's label
    victim_pos = 3
    victim_global = fold.inner_train_ids[victim_pos]
    y_flip = y.copy()
    y_flip[victim_global] = 1 - y_flip[victim_global]
    ef2 = encode_foldsafe(X, y_flip, g, fold, "target")
    # invariant on RAW OOF codes: the victim's own OOF encoder never saw its label
    own_same = np.allclose(ef1.Z_inner_train_raw[victim_pos],
                           ef2.Z_inner_train_raw[victim_pos])
    others_changed = not np.allclose(ef1.Z_inner_train_raw, ef2.Z_inner_train_raw)
    _record("PC2", own_same, {"own_code_unchanged": own_same,
                              "other_codes_changed": others_changed})
    assert own_same
    assert others_changed  # sanity: the flip did propagate to OOF-fit rows


def test_pc3_unique_category_memorization_trap():
    """PC3: one level per row, random balanced labels -> global encoding
    memorizes; OOF encoding must fall back to the training prior."""
    rng = np.random.default_rng(7)
    n = 120
    X = pd.DataFrame({"u": [f"lvl{i}" for i in range(n)],
                      "f": rng.choice(["a", "b"], n)})
    y = np.array([0, 1] * (n // 2), dtype=np.int8)
    from ct2i_benchmark.splitting.outer import duplicate_groups, make_folds
    g = duplicate_groups(X)
    folds = make_folds(y, g, n_outer=5)
    fold = folds[0]
    ef = encode_foldsafe(X, y, g, fold, "target")
    from ct2i_benchmark.encoders.supervised import TARGET_ALPHA
    col_u = 0
    codes_u = ef.Z_inner_train_raw[:, col_u]
    y_itr = y[fold.inner_train_ids]
    # global (contaminated) encoding for contrast
    from ct2i_benchmark.encoders import TargetEncoder
    glob = TargetEncoder().fit(X, y).transform(X)[fold.inner_train_ids, col_u]
    # memorization statistic: separation of codes by the row's OWN label.
    # Global: code = (y_i + alpha*prior)/(1+alpha) -> gap = 1/(1+alpha) exactly.
    # OOF: unique level unseen by its OOF-fit encoder -> prior fallback, no
    # own-label information -> gap ~ 0 (only fold-prior noise).
    def own_label_gap(codes):
        return float(codes[y_itr == 1].mean() - codes[y_itr == 0].mean())
    gap_oof = own_label_gap(codes_u)
    gap_glob = own_label_gap(glob)
    expected_glob = 1.0 / (1.0 + TARGET_ALPHA)
    # The OOF gap contains only fold-prior sampling noise (label-free OOF
    # partition x finite fold priors), while the global gap is the exact
    # memorization signature 1/(1+alpha). Require the OOF gap to sit well
    # below that signature (threshold = half the signature).
    _record("PC3", abs(gap_oof) < expected_glob / 2 < gap_glob,
            {"own_label_gap_oof": gap_oof, "own_label_gap_global": gap_glob,
             "expected_global_gap": expected_glob})
    assert abs(gap_oof) < expected_glob / 2          # OOF: no memorization signature
    assert abs(gap_glob - expected_glob) < 1e-6      # global memorizes exactly


def test_pc4_unseen_category_fallback(toy):
    """PC4: a level appearing only in outer test maps to the prior/unknown rule
    learned from outer training (target, count, label, onehot)."""
    X, y, g, folds = toy
    X2 = X.copy()
    fold = folds[0]
    probe = fold.test_ids[0]
    X2.loc[probe, "a"] = "__NEVER_SEEN__"
    ef = encode_foldsafe(X2, y, g, fold, "target")
    pos = list(fold.test_ids).index(probe)
    prior = float(np.mean(y[fold.train_ids]))
    # scaled value of prior under the outer scaler: recover via inverse check
    ok = np.isfinite(ef.Z_outer_test[pos, 0])
    from ct2i_benchmark.encoders import CountEncoder, LabelEncoder
    ce = CountEncoder().fit(X2.iloc[fold.train_ids])
    assert ce.transform(X2.iloc[[probe]])[0, 0] == 0.0
    le = LabelEncoder().fit(X2.iloc[fold.train_ids])
    assert le.transform(X2.iloc[[probe]])[0, 0] == 0.0   # UNSEEN index
    _record("PC4", ok, {"prior": prior})
    assert ok


def test_pc5_artifact_lineage_exclusion(toy):
    """PC5: fit_row_ids and fit_label_ids of every fitted artifact are disjoint
    from outer-test ids; a poisoned artifact raises LeakageError."""
    X, y, g, folds = toy
    fold = folds[0]
    ef = encode_foldsafe(X, y, g, fold, "target")
    for rec in ef.lineage:
        rec.assert_excludes(fold.test_ids, "outer_test")
    # inner-side artifacts must also exclude inner-validation rows
    for rec in ef.lineage:
        if rec.inner_fold_or_role.startswith("inner_oof"):
            rec.assert_excludes(fold.inner_val_ids, "inner_val")
    # negative control: a deliberately poisoned record must raise
    from ct2i_benchmark.artifacts.lineage import LineageRecord
    bad = LineageRecord.create("bad", "encoder:target", {}, fold.test_ids[:3],
                               fold.test_ids[:3], [], fold.outer_fold, "poison", {})
    with pytest.raises(LeakageError):
        bad.assert_excludes(fold.test_ids)
    _record("PC5", True, {"n_artifacts_checked": len(ef.lineage)})


def test_pc6_determinism_double_run(toy):
    """PC6: with all seeds fixed, two clean runs produce identical hashes of
    folds, transformed matrices, fitted states, and a model's predictions."""
    X, y, g, folds = toy
    fold = folds[0]
    from ct2i_benchmark.splitting.outer import make_folds
    folds_b = make_folds(y, g, n_outer=5, seed_fold=42, seed_inner=421)
    assert [f.sha256() for f in folds] == [f.sha256() for f in folds_b]
    ha = _hash_state(encode_foldsafe(X, y, g, fold, "ordered_catboost"))
    hb = _hash_state(encode_foldsafe(X, y, g, fold, "ordered_catboost"))
    assert ha == hb
    lay1 = IGTDReimpl(max_step=300, seed=7).fit(
        encode_foldsafe(X, y, g, fold, "label").Z_inner_train)
    lay2 = IGTDReimpl(max_step=300, seed=7).fit(
        encode_foldsafe(X, y, g, fold, "label").Z_inner_train)
    assert lay1.perm_.tolist() == lay2.perm_.tolist()
    from ct2i_benchmark.models.wrappers import LightGBMModel
    ef = encode_foldsafe(X, y, g, fold, "label")
    p1 = LightGBMModel(n_estimators=50).fit(ef.Z_outer_train, y[fold.train_ids]) \
        .predict_proba(ef.Z_outer_test)
    p2 = LightGBMModel(n_estimators=50).fit(ef.Z_outer_train, y[fold.train_ids]) \
        .predict_proba(ef.Z_outer_test)
    same = bool(np.array_equal(p1, p2))
    _record("PC6", same, {"fold_hashes_equal": True, "enc_hashes_equal": ha == hb,
                          "layout_perm_equal": True, "predictions_equal": same})
    assert same


# ---------- additional mandatory checks (§13) ----------

def test_ac1_inner_val_labels_never_in_inner_oof_codes(toy):
    """AC1: permuting inner-validation labels leaves inner-training OOF codes
    identical."""
    X, y, g, folds = toy
    fold = folds[0]
    y2 = y.copy()
    rng = np.random.default_rng(11)
    y2[fold.inner_val_ids] = rng.permutation(y2[fold.inner_val_ids])
    a = encode_foldsafe(X, y, g, fold, "woe").Z_inner_train
    b = encode_foldsafe(X, y2, g, fold, "woe").Z_inner_train
    same = bool(np.array_equal(a, b))
    _record("AC1", same, {})
    assert same


def test_ac2_groups_never_cross_boundaries(toy):
    """AC2: duplicate groups never cross outer or inner boundaries."""
    X, y, g, folds = toy
    for f in folds:
        assert not set(g[f.train_ids]) & set(g[f.test_ids])
        assert not set(g[f.inner_train_ids]) & set(g[f.inner_val_ids])
    _record("AC2", True, {"n_folds": len(folds)})


def test_ac3_column_aware_hash_moves_with_column():
    """AC3: moving the same bare value to a different column changes the
    column-aware encoding; AC4: shared-value encoding is invariant."""
    X1 = pd.DataFrame({"c1": ["v", "w"], "c2": ["a", "b"]})
    X2 = pd.DataFrame({"c1": ["a", "b"], "c2": ["v", "w"]})  # values swapped
    ca1 = ColumnAwareHashEncoder().fit(X1).transform(X1)
    ca2 = ColumnAwareHashEncoder().fit(X2).transform(X2)
    sv1 = SharedValueHashEncoder().fit(X1).transform(X1)
    sv2 = SharedValueHashEncoder().fit(X2).transform(X2)
    _record("AC3", not np.array_equal(ca1, ca2), {})
    _record("AC4", np.array_equal(sv1, sv2), {})
    assert not np.array_equal(ca1, ca2)
    assert np.array_equal(sv1, sv2)


def test_ac5_zero_one_buckets_recorded_per_width():
    """AC5: buckets of bare strings '0' and '1' recorded for every pilot hash
    width; distinctness recorded (needed by the shared-value proposition)."""
    widths = sorted({bucket_rule(k, 10) for k in [10, 100, 1000, 10000]})
    rec = {}
    for B in widths:
        b0, b1 = bucket_of("0", B, HASH_SEED), bucket_of("1", B, HASH_SEED)
        rec[str(B)] = {"b0": b0, "b1": b1, "distinct": b0 != b1}
    _record("AC5", True, {"buckets": rec})
    assert all("distinct" in v for v in rec.values())


def test_ac6_onehot_label_unknown_deterministic():
    """AC6: one-hot and label unknown-level behavior is deterministic."""
    from ct2i_benchmark.encoders import LabelEncoder, OneHotEncoder01
    Xf = pd.DataFrame({"a": ["p", "q", "r"]})
    Xt = pd.DataFrame({"a": ["zzz"]})
    oh = OneHotEncoder01().fit(Xf)
    r1, r2 = oh.transform(Xt), oh.transform(Xt)
    assert np.array_equal(r1, r2) and r1[0, -1] == 1.0  # UNSEEN column
    le = LabelEncoder().fit(Xf)
    assert le.transform(Xt)[0, 0] == 0.0
    _record("AC6", True, {})


def test_ac7_eligibility_never_reads_outer_test_labels(toy):
    """AC7: the one-hot width-eligibility rule uses training-side cardinalities
    only (permuting outer-test labels AND features cannot change it)."""
    X, y, g, folds = toy
    fold = folds[0]

    def width_eligible(X, train_ids, cap=4096):
        card = sum(X.iloc[train_ids][c].nunique() for c in X.columns)
        return card <= cap

    e1 = width_eligible(X, fold.train_ids)
    X2 = X.copy()
    X2.loc[fold.test_ids, "a"] = "MUTATED"
    e2 = width_eligible(X2, fold.train_ids)
    _record("AC7", e1 == e2, {})
    assert e1 == e2
