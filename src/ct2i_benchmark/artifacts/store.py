"""JSON-lines artifact store for run records, lineage records, and predictions."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np


def _clean(obj):
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        return None if math.isnan(v) else v
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


class ArtifactStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def append(self, kind: str, record: dict) -> None:
        path = self.root / f"{kind}.jsonl"
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(_clean(record), sort_keys=True) + "\n")

    def read_all(self, kind: str) -> list[dict]:
        path = self.root / f"{kind}.jsonl"
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def write_json(self, name: str, obj) -> Path:
        path = self.root / name
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_clean(obj), f, indent=1, sort_keys=True)
        return path

    def save_predictions(self, run_id: str, row_ids, y_true, y_score) -> Path:
        """Parquet prediction record (round-trip exact for nulls/ids)."""
        import pandas as pd
        df = pd.DataFrame({
            "run_id": run_id,
            "row_id": np.asarray(row_ids, dtype=np.int64),
            "y_true": np.asarray(y_true, dtype=np.int8),
            "y_score": np.asarray(y_score, dtype=np.float64),
        })
        path = self.root / f"pred_{run_id}.parquet"
        df.to_parquet(path, index=False)
        return path
