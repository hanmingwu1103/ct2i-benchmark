"""Deterministic hashing utilities.

- sha256_* : content hashes for files, arrays, and JSON-able objects.
- stable_token_hash : seeded, process-independent token hash (blake2b) used by
  the hash encoders. Python's built-in hash() is salted per process and MUST
  NOT be used (code-grade contract 10.4).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_array(arr: np.ndarray) -> str:
    a = np.ascontiguousarray(arr)
    h = hashlib.sha256()
    h.update(str(a.dtype).encode())
    h.update(str(a.shape).encode())
    h.update(a.tobytes())
    return h.hexdigest()


def sha256_obj(obj) -> str:
    """Canonical-JSON hash of a JSON-able object (sorted keys, no whitespace)."""
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def sha256_int_ids(ids) -> str:
    """Deterministic hash of a sequence of integer row ids (sorted)."""
    arr = np.sort(np.asarray(list(ids), dtype=np.int64))
    return sha256_array(arr)


def stable_token_hash(token: str, seed: int = 0) -> int:
    """Seeded 64-bit stable hash of a string token (blake2b keyed)."""
    key = seed.to_bytes(8, "little", signed=False)
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8, key=key).digest()
    return int.from_bytes(digest, "little")


def bucket_of(token: str, n_buckets: int, seed: int = 0) -> int:
    return stable_token_hash(token, seed) % n_buckets
