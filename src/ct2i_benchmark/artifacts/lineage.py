"""Fitted-artifact lineage records (code-grade contract 10.7).

Every fitted state (encoder, scaler, layout, PCA, reader, model) must carry a
lineage record proving which rows and labels it saw. Raw row ids stay private;
their deterministic hashes and counts are exposed for validation.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

from ..hashing import sha256_int_ids, sha256_obj

_EMPTY_HASH = sha256_int_ids([])


def code_commit(repo_root: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", repo_root, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return "UNCOMMITTED"


@dataclass
class LineageRecord:
    artifact_id: str
    artifact_type: str
    parent_artifact_ids: list[str]
    code_commit: str
    config_hash: str
    fit_row_ids_hash: str
    fit_label_ids_hash: str  # hash of rows whose LABELS were consumed at fit
    transform_row_ids_hash: str
    outer_fold: int
    inner_fold_or_role: str
    seed_set: dict
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sha256: str = ""
    # private (not serialized into reports, but kept for in-process validation)
    _fit_row_ids: frozenset = field(default_factory=frozenset, repr=False)
    _fit_label_ids: frozenset = field(default_factory=frozenset, repr=False)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("_fit_row_ids"); d.pop("_fit_label_ids")
        return d

    @classmethod
    def create(cls, artifact_id, artifact_type, config, fit_row_ids, fit_label_ids,
               transform_row_ids, outer_fold, role, seed_set, parents=(), commit="UNCOMMITTED",
               state_hash=""):
        return cls(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            parent_artifact_ids=list(parents),
            code_commit=commit,
            config_hash=sha256_obj(config),
            fit_row_ids_hash=sha256_int_ids(fit_row_ids) if len(fit_row_ids) else _EMPTY_HASH,
            fit_label_ids_hash=sha256_int_ids(fit_label_ids) if len(fit_label_ids) else _EMPTY_HASH,
            transform_row_ids_hash=sha256_int_ids(transform_row_ids) if len(transform_row_ids) else _EMPTY_HASH,
            outer_fold=outer_fold,
            inner_fold_or_role=role,
            seed_set=dict(seed_set),
            sha256=state_hash,
            _fit_row_ids=frozenset(int(i) for i in fit_row_ids),
            _fit_label_ids=frozenset(int(i) for i in fit_label_ids),
        )

    def assert_excludes(self, forbidden_ids, what: str = "outer_test") -> None:
        """P-C invariant 5: fit rows/labels must not intersect forbidden ids."""
        forbidden = frozenset(int(i) for i in forbidden_ids)
        row_overlap = self._fit_row_ids & forbidden
        lab_overlap = self._fit_label_ids & forbidden
        if row_overlap or lab_overlap:
            raise LeakageError(
                f"artifact {self.artifact_id} ({self.artifact_type}): "
                f"{len(row_overlap)} fit-row / {len(lab_overlap)} fit-label ids "
                f"intersect {what}"
            )


class LeakageError(RuntimeError):
    """Raised when a lineage invariant is violated. Always fatal."""
