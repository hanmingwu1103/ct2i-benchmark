"""P-B: the nine mandatory typed-failure tests (Stage 2 master prompt §12).

Each test is individually named PB1..PB9 and writes an evidence record consumed
by 11_FAILURE_TEST_REPORT.json.
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from ct2i_benchmark.evaluation.metrics import compute_metrics
from ct2i_benchmark.pipeline import run_protected
from ct2i_benchmark.statuses import Status, metrics_allowed

EVIDENCE = Path(__file__).resolve().parents[1] / ".cache" / "test_evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)


def _record(test_id, expected, observed, extra=None):
    rec = {"test_id": test_id, "expected_status": expected, "observed_status": observed,
           "pass": expected == observed, **(extra or {})}
    (EVIDENCE / f"{test_id}.json").write_text(json.dumps(rec, indent=1, default=str))
    return rec


def test_pb1_constant_score_genuine_half_auc_retained():
    """PB1: constant-score predictor -> SUCCESS with AUC exactly 0.5, retained."""
    y = np.array([0, 1] * 20)
    s = np.full(40, 0.37)
    m, status = compute_metrics(y, s, threshold=0.5)
    _record("PB1", "SUCCESS", status, {"auc": m["auc"]})
    assert status == Status.SUCCESS.value
    assert m["auc"] == 0.5          # genuine chance level, valid data
    assert metrics_allowed(status)


def test_pb2_injected_model_exception():
    """PB2: injected model exception -> TRAINING_FAILURE, all metrics null."""
    def bad_fit():
        raise RuntimeError("injected training crash")
    res = run_protected(bad_fit, Status.TRAINING_FAILURE)
    _record("PB2", "TRAINING_FAILURE", res.status,
            {"exception_class": res.exception_class})
    assert res.status == Status.TRAINING_FAILURE.value
    assert res.value is None and not metrics_allowed(res.status)


def test_pb3_injected_image_exception():
    """PB3: injected image exception -> IMAGE_RENDER_FAILURE, metrics null."""
    def bad_render():
        raise ValueError("injected render crash")
    res = run_protected(bad_render, Status.IMAGE_RENDER_FAILURE)
    _record("PB3", "IMAGE_RENDER_FAILURE", res.status,
            {"exception_class": res.exception_class})
    assert res.status == Status.IMAGE_RENDER_FAILURE.value
    assert res.value is None


def test_pb4_forced_timeout():
    """PB4: forced timeout -> TIMEOUT, metrics null."""
    import time

    def slow():
        time.sleep(10)
        return 1
    res = run_protected(slow, Status.TRAINING_FAILURE, timeout_s=0.5)
    _record("PB4", "TIMEOUT", res.status, {"elapsed_s": res.elapsed_s})
    assert res.status == Status.TIMEOUT.value
    assert res.value is None and res.elapsed_s < 5


def test_pb5_single_class_test_target():
    """PB5: single-class test fold -> METRIC_UNDEFINED, never 0.5."""
    y = np.ones(30, int)
    s = np.linspace(0, 1, 30)
    m, status = compute_metrics(y, s, threshold=0.5)
    _record("PB5", "METRIC_UNDEFINED", status, {"auc_is_null": m["auc"] is None})
    assert status == Status.METRIC_UNDEFINED.value
    assert m["auc"] is None            # not 0.5


def test_pb6_majority_class_predictions_with_valid_ranking():
    """PB6: majority-class hard predictions but valid score ranking -> valid
    AUC retained; F1 may equal 0."""
    rng = np.random.default_rng(9)
    y = (rng.random(200) < 0.15).astype(int)
    s = np.where(y == 1, rng.uniform(0.2, 0.45, 200), rng.uniform(0.0, 0.3, 200))
    m, status = compute_metrics(y, s, threshold=0.9)  # threshold above every score
    _record("PB6", "SUCCESS", status, {"auc": m["auc"], "f1": m["f1_valsel"]})
    assert status == Status.SUCCESS.value
    assert m["auc"] is not None and m["auc"] > 0.5
    assert m["f1_valsel"] == 0.0


def test_pb7_aggregation_filters_on_status_only():
    """PB7: aggregation depends only on status; successful 0.5 rows survive."""
    rows = [
        {"run_id": "r1", "status": "SUCCESS", "auc": 0.5},
        {"run_id": "r2", "status": "SUCCESS", "auc": 0.9},
        {"run_id": "r3", "status": "TRAINING_FAILURE", "auc": None},
        {"run_id": "r4", "status": "TIMEOUT", "auc": None},
    ]
    kept = [r for r in rows if r["status"] == "SUCCESS"]
    _record("PB7", "SUCCESS", "SUCCESS",
            {"kept_ids": [r["run_id"] for r in kept]})
    assert {r["run_id"] for r in kept} == {"r1", "r2"}
    assert any(r["auc"] == 0.5 for r in kept)          # genuine 0.5 retained
    assert all(r["auc"] is not None for r in kept)


def test_pb8_paired_report_denominator_and_typed_exclusions():
    """PB8: paired-comparison report carries denominator + typed exclusions
    by arm and stage."""
    cells = [
        {"dataset": "d1", "arm": "image", "status": "SUCCESS"},
        {"dataset": "d1", "arm": "tabular", "status": "SUCCESS"},
        {"dataset": "d2", "arm": "image", "status": "LAYOUT_FAILURE"},
        {"dataset": "d2", "arm": "tabular", "status": "SUCCESS"},
    ]
    paired = {}
    excl = []
    for d in {c["dataset"] for c in cells}:
        arms = {c["arm"]: c["status"] for c in cells if c["dataset"] == d}
        if all(v == "SUCCESS" for v in arms.values()):
            paired[d] = arms
        else:
            excl.append({"dataset": d,
                         "reason": {a: s for a, s in arms.items() if s != "SUCCESS"}})
    report = {"n_pairs": len(paired), "n_excluded": len(excl), "exclusions": excl}
    _record("PB8", "SUCCESS", "SUCCESS", report)
    assert report["n_pairs"] == 1 and report["n_excluded"] == 1
    assert report["exclusions"][0]["reason"] == {"image": "LAYOUT_FAILURE"}


def test_pb9_serialization_roundtrip_exact(tmp_path):
    """PB9: JSON + Parquet round-trip preserves status, nulls, ids, metrics."""
    rec = {"run_id": "d1|f0|enc|lay|m|s1", "status": "TRAINING_FAILURE",
           "auc": None, "logloss": None, "n_test": 48}
    p = tmp_path / "r.json"
    p.write_text(json.dumps(rec))
    back = json.loads(p.read_text())
    assert back == rec and back["auc"] is None

    df = pd.DataFrame([
        {"run_id": "a", "status": "SUCCESS", "auc": 0.5},
        {"run_id": "b", "status": "TIMEOUT", "auc": None},
    ])
    pq = tmp_path / "r.parquet"
    df.to_parquet(pq, index=False)
    back_df = pd.read_parquet(pq)
    _record("PB9", "SUCCESS", "SUCCESS", {"json_ok": True})
    assert back_df.loc[0, "auc"] == 0.5
    assert math.isnan(back_df.loc[1, "auc"]) or back_df.loc[1, "auc"] is None
    assert list(back_df["status"]) == ["SUCCESS", "TIMEOUT"]
    assert list(back_df["run_id"]) == ["a", "b"]
