import numpy as np
import pandas as pd
import pytest

from ct2i_benchmark.splitting.outer import duplicate_groups, make_folds


@pytest.fixture(scope="session")
def toy():
    """Small deterministic categorical dataset with duplicates and both classes."""
    rng = np.random.default_rng(1234)
    n = 240
    X = pd.DataFrame({
        "a": rng.choice(list("wxyz"), n),
        "b": rng.choice(list("mnop"), n),
        "c": rng.choice(["0", "1"], n),
        "d": rng.choice(list("abcdefg"), n),
    })
    logits = (X["a"].map({"w": .8, "x": -.4, "y": .1, "z": -.9}).astype(float)
              + X["c"].map({"0": -.5, "1": .5}).astype(float))
    y = (rng.random(n) < 1 / (1 + np.exp(-logits))).to_numpy().astype(np.int8)
    if y.sum() < 10 or y.sum() > n - 10:  # safety, deterministic seed keeps it balanced
        y[:20] = 1; y[20:40] = 0
    g = duplicate_groups(X)
    folds = make_folds(y, g, n_outer=5, seed_fold=42, seed_inner=421)
    return X, y, g, folds
