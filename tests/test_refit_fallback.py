"""Final-audit P1 fix: the refit fallback must never consult outer-test-label-
dependent statuses. METRIC_UNDEFINED (single-class outer fold) keeps the
candidate; only genuine refit failures advance the fallback."""
from ct2i_benchmark.evaluation.selection import Candidate, select_with_fallback


def _cands():
    return [Candidate("a", 0.90, 1, 1.0, "SUCCESS"),
            Candidate("b", 0.85, 1, 1.0, "SUCCESS"),
            Candidate("c", 0.80, 1, 1.0, "SUCCESS")]


def test_metric_undefined_does_not_trigger_fallback():
    chosen, _, n = select_with_fallback(_cands(), {"a": "METRIC_UNDEFINED",
                                                   "b": "SUCCESS", "c": "SUCCESS"})
    assert chosen == "a" and n == 0     # outer-label composition cannot demote


def test_refit_failure_triggers_fallback():
    chosen, _, n = select_with_fallback(_cands(), {"a": "TRAINING_FAILURE",
                                                   "b": "SUCCESS", "c": "SUCCESS"})
    assert chosen == "b" and n == 1


def test_all_refits_failed():
    chosen, status, n = select_with_fallback(_cands(), {"a": "TIMEOUT",
                                                        "b": "TRAINING_FAILURE",
                                                        "c": "RESOURCE_LIMIT"})
    assert chosen is None and status == "TRAINING_FAILURE" and n == 3


def test_inner_failed_candidates_never_ranked():
    cands = _cands() + [Candidate("d", 0.99, 1, 1.0, "TRAINING_FAILURE")]
    chosen, _, _ = select_with_fallback(cands, {k: "SUCCESS" for k in "abcd"})
    assert chosen == "a"                # d's inner failure excludes it despite 0.99
