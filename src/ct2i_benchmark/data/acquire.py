"""Scripted acquisition of the four pilot datasets from canonical sources.

Raw files are cached under <repo>/.cache/raw/ (never committed). Every download
records URL, timestamp, sha256, and row/feature counts into the acquisition
manifest. Targets are frozen source-semantic definitions (data/targets.py) —
never sample-majority coding.
"""
from __future__ import annotations

import gzip
import io
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from ..hashing import sha256_file, sha256_array

SOURCES = {
    "tictactoe": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/tic-tac-toe/tic-tac-toe.data",
        "canonical_source": "UCI ML Repository: Tic-Tac-Toe Endgame",
        "license": "CC BY 4.0 (UCI)",
        "target_name": "outcome",
        "positive": "positive",  # win for x — source-defined
    },
    "mushroom": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/mushroom/agaricus-lepiota.data",
        "canonical_source": "UCI ML Repository: Mushroom (agaricus-lepiota)",
        "license": "CC BY 4.0 (UCI)",
        "target_name": "class",
        "positive": "p",  # poisonous — source-defined
    },
    "bace": {
        "url": "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/bace.csv",
        "canonical_source": "MoleculeNet/DeepChem dataset bucket: bace.csv",
        "license": "MoleculeNet research distribution",
        "target_name": "Class",
        "positive": 1,  # BACE-1 inhibitor — source-defined
    },
    "parity5_plus_5": {
        "url": "https://github.com/EpistasisLab/pmlb/raw/master/datasets/parity5%2B5/parity5%2B5.tsv.gz",
        "canonical_source": "PMLB (EpistasisLab): parity5+5",
        "license": "MIT (PMLB)",
        "target_name": "target",
        "positive": 1,  # native concept label
    },
}

TTT_COLS = [f"sq{i}" for i in range(1, 10)] + ["outcome"]
MUSHROOM_COLS = [
    "class", "cap-shape", "cap-surface", "cap-color", "bruises", "odor",
    "gill-attachment", "gill-spacing", "gill-size", "gill-color", "stalk-shape",
    "stalk-root", "stalk-surface-above-ring", "stalk-surface-below-ring",
    "stalk-color-above-ring", "stalk-color-below-ring", "veil-type", "veil-color",
    "ring-number", "ring-type", "spore-print-color", "population", "habitat",
]


@dataclass
class AcquisitionRecord:
    dataset_id: str
    canonical_source: str
    source_url_or_id: str
    license: str
    download_time: str
    raw_path_private: str
    raw_sha256: str
    n_raw: int
    p_raw: int
    target_name: str
    target_levels: str
    processed_n: int
    processed_p: int
    processed_sha256: str
    status: str
    notes: str = ""

    def to_dict(self):
        return asdict(self)


def _download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "ct2i-benchmark/0.2 (research)"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest


def acquire(dataset_id: str, cache_dir: str | Path):
    """Download raw file, build processed (X_cat DataFrame, y int8) with frozen target.

    Returns (X: DataFrame of string categories, y: np.int8 array, extras: dict,
    record: AcquisitionRecord).
    """
    spec = SOURCES[dataset_id]
    cache = Path(cache_dir)
    raw_path = cache / "raw" / f"{dataset_id}{Path(spec['url'].split('?')[0]).suffix or '.data'}"
    if not raw_path.exists():
        _download(spec["url"], raw_path)
    raw_sha = sha256_file(raw_path)
    extras: dict = {}

    if dataset_id == "tictactoe":
        df = pd.read_csv(raw_path, header=None, names=TTT_COLS, dtype=str)
        y = (df["outcome"] == spec["positive"]).to_numpy(dtype=np.int8)
        X = df.drop(columns=["outcome"]).astype(str)
        levels = ",".join(sorted(df["outcome"].unique()))
    elif dataset_id == "mushroom":
        df = pd.read_csv(raw_path, header=None, names=MUSHROOM_COLS, dtype=str)
        y = (df["class"] == spec["positive"]).to_numpy(dtype=np.int8)
        X = df.drop(columns=["class"]).astype(str)
        # frozen missing policy: '?' is an explicit category level (kept as-is)
        levels = ",".join(sorted(df["class"].unique()))
    elif dataset_id == "bace":
        df = pd.read_csv(raw_path)
        from .molecular import morgan_fingerprints, scaffold_groups, canonical_smiles
        smiles = df["mol"].astype(str).tolist()
        canon = canonical_smiles(smiles)
        fps = morgan_fingerprints(canon, n_bits=1024, radius=2)  # all 1024 bits retained
        y = df["Class"].astype(int).to_numpy(dtype=np.int8)
        X = pd.DataFrame(fps.astype(np.uint8).astype(str),
                         columns=[f"fp{i:04d}" for i in range(fps.shape[1])])
        extras["scaffold_groups"] = scaffold_groups(canon)
        extras["smiles_canonical"] = canon
        extras["source_row_id"] = df.index.to_numpy()
        levels = "0,1"
    elif dataset_id == "parity5_plus_5":
        with gzip.open(raw_path, "rb") as f:
            df = pd.read_csv(io.BytesIO(f.read()), sep="\t")
        y = df["target"].astype(int).to_numpy(dtype=np.int8)
        X = df.drop(columns=["target"]).astype(int).astype(str)
        levels = "0,1"
    else:
        raise KeyError(dataset_id)

    processed_sha = sha256_array(
        np.concatenate([np.frombuffer(X.to_csv(index=False).encode(), dtype=np.uint8),
                        y.astype(np.uint8)])
    )
    rec = AcquisitionRecord(
        dataset_id=dataset_id,
        canonical_source=spec["canonical_source"],
        source_url_or_id=spec["url"],
        license=spec["license"],
        download_time=datetime.now(timezone.utc).isoformat(),
        raw_path_private=str(raw_path.name),
        raw_sha256=raw_sha,
        n_raw=len(df),
        p_raw=df.shape[1],
        target_name=spec["target_name"],
        target_levels=levels,
        processed_n=len(X),
        processed_p=X.shape[1],
        processed_sha256=processed_sha,
        status="SUCCESS",
        notes="stress-test dataset (deliberate), not metadata-representative"
        if dataset_id == "parity5_plus_5" else "",
    )
    return X, y, extras, rec
