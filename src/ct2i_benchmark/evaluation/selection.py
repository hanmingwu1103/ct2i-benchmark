"""Inner-validation candidate selection with the frozen tie-break order
(contract 10.6): (1) higher inner primary metric; (2) lower predeclared
complexity key; (3) lower measured inner fit time (only if complexity ties);
(4) lexicographically smaller config id. Refit-failure fallback: next-ranked
candidate; if all fail -> TRAINING_FAILURE for the policy cell."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Candidate:
    config_id: str
    inner_metric: float | None
    complexity_key: float
    fit_time_s: float
    status: str


def rank_candidates(cands: list[Candidate]) -> list[Candidate]:
    ok = [c for c in cands if c.status == "SUCCESS" and c.inner_metric is not None]
    return sorted(ok, key=lambda c: (-c.inner_metric, c.complexity_key,
                                     c.fit_time_s, c.config_id))


def select(cands: list[Candidate]) -> tuple[Candidate | None, str]:
    ranked = rank_candidates(cands)
    if not ranked:
        return None, "TRAINING_FAILURE"
    top = ranked[0]
    tie = [c for c in ranked if c.inner_metric == top.inner_metric]
    tie_break = "none" if len(tie) == 1 else (
        "complexity" if len({c.complexity_key for c in tie}) > 1 else (
            "fit_time" if len({c.fit_time_s for c in tie}) > 1 else "config_id"))
    return top, tie_break


# Outer statuses that mean "the refit itself succeeded" and therefore CANNOT
# remove a ranked candidate from fallback consideration. METRIC_UNDEFINED
# arises from outer-test label composition (single-class fold) — letting it
# skip a candidate would leak outer-test label information into which policy
# is deployed (final-audit P1 finding, closed here).
REFIT_OK_STATUSES = frozenset({"SUCCESS", "METRIC_UNDEFINED"})


def select_with_fallback(cands: list[Candidate], refit_status_of: dict[str, str]):
    """Rank on inner-only quantities; walk the ranking, skipping ONLY
    candidates whose outer REFIT failed (never ones whose outer metric is
    undefined). Returns (chosen_config_id, tie_break, n_fallbacks) or
    (None, 'TRAINING_FAILURE', n) when every ranked candidate's refit failed."""
    ranked = rank_candidates(cands)
    if not ranked:
        return None, "TRAINING_FAILURE", 0
    _, tie_break = select(cands)
    fallbacks = 0
    for cand in ranked:
        if refit_status_of.get(cand.config_id) in REFIT_OK_STATUSES:
            return cand.config_id, tie_break, fallbacks
        fallbacks += 1
    return None, "TRAINING_FAILURE", fallbacks
