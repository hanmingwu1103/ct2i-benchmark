"""Typed run statuses (Stage 1 vocabulary + Stage 2 additions per 01_AMENDMENTS)."""
from __future__ import annotations

from enum import Enum


class Status(str, Enum):
    SUCCESS = "SUCCESS"
    SKIPPED_INELIGIBLE = "SKIPPED_INELIGIBLE"
    PREPROCESSING_FAILURE = "PREPROCESSING_FAILURE"
    ENCODING_FAILURE = "ENCODING_FAILURE"
    LAYOUT_FAILURE = "LAYOUT_FAILURE"
    IMAGE_RENDER_FAILURE = "IMAGE_RENDER_FAILURE"
    TRAINING_FAILURE = "TRAINING_FAILURE"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    TIMEOUT = "TIMEOUT"
    NUMERICAL_FAILURE = "NUMERICAL_FAILURE"
    METRIC_UNDEFINED = "METRIC_UNDEFINED"
    INTERRUPTED = "INTERRUPTED"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"
    # Stage 2 additions (01_AMENDMENTS B.1)
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    MODEL_ACCESS_NOT_AUTHORIZED = "MODEL_ACCESS_NOT_AUTHORIZED"


FAILURE_STATUSES = frozenset(
    s for s in Status if s not in (Status.SUCCESS, Status.SKIPPED_INELIGIBLE)
)


def is_success(status: str | Status) -> bool:
    return Status(status) is Status.SUCCESS


def metrics_allowed(status: str | Status) -> bool:
    """Metrics may be stored only for SUCCESS runs; all failures carry nulls."""
    return is_success(status)
