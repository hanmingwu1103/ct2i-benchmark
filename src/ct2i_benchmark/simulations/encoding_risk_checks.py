"""Simulation 1 implementation-validation checks (§20). NOT the full sweep.

DGP: M categorical variables, explicit finite joint distribution, known
posterior eta(x). Bayes risks computed by exact enumeration over the joint
support; encoded-representation Bayes risks by exact aggregation over encoder
fibers. Checks 1-8 of the reissued protocol.
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd


def make_dgp(M=3, K=4, seed=11, within_fiber_spread=0.3, merge_map=None):
    """Finite DGP: X uniform over K^M cells; eta from a seeded logistic-style
    table. merge_map: optional dict cell->fiber used to CONSTRUCT posteriors
    constant (spread=0) or varying (spread>0) within fibers of a target
    encoder."""
    rng = np.random.default_rng(seed)
    cells = list(itertools.product(range(K), repeat=M))
    n_cells = len(cells)
    p_cell = np.full(n_cells, 1.0 / n_cells)
    if merge_map is None:
        eta = rng.uniform(0.1, 0.9, n_cells)
    else:
        fibers = sorted(set(merge_map.values()))
        base = {f: rng.uniform(0.15, 0.85) for f in fibers}
        eta = np.array([
            np.clip(base[merge_map[c]] +
                    (rng.uniform(-within_fiber_spread, within_fiber_spread)
                     if within_fiber_spread > 0 else 0.0), 0.01, 0.99)
            for c in cells])
    return cells, p_cell, eta


def bayes_risks(p_cell, eta):
    """Exact Bayes log-loss (nats) and one-coordinate Brier risk on X."""
    eta = np.asarray(eta)
    h = -(eta * np.log(eta) + (1 - eta) * np.log(1 - eta))
    return float((p_cell * h).sum()), float((p_cell * eta * (1 - eta)).sum())


def encoded_bayes_risks(cells, p_cell, eta, encode_fn):
    """Exact Bayes risks on Z = encode_fn(cell) by fiber aggregation."""
    fibers: dict = {}
    for i, c in enumerate(cells):
        z = encode_fn(c)
        fibers.setdefault(z, []).append(i)
    rl = rb = 0.0
    for idx in fibers.values():
        w = p_cell[idx].sum()
        e = float((p_cell[idx] * eta[idx]).sum() / w)
        rl += w * -(e * np.log(e) + (1 - e) * np.log(1 - e)) if 0 < e < 1 else 0.0
        rb += w * e * (1 - e)
    return float(rl), float(rb)


def theoretical_gaps(cells, p_cell, eta, encode_fn):
    """I(Y;X|Z) (nats) and E[Var(eta|Z)] computed exactly."""
    rl_x, rb_x = bayes_risks(p_cell, eta)
    rl_z, rb_z = encoded_bayes_risks(cells, p_cell, eta, encode_fn)
    return rl_z - rl_x, rb_z - rb_x


def shared_value_hash_range(M: int, distinct_buckets: bool) -> int:
    """Reachable encodings of {0,1}^M under bare-value hashing (Stage 1
    proposition): M+1 if buckets distinct, else 1."""
    reachable = set()
    for w in range(M + 1):
        if distinct_buckets:
            reachable.add((w, M - w))
        else:
            reachable.add((M,))
    return len(reachable)


def sample_dataset(cells, p_cell, eta, n, seed):
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(cells), size=n, p=p_cell)
    X = pd.DataFrame([cells[i] for i in idx]).astype(str)
    X.columns = [f"v{j}" for j in range(X.shape[1])]
    y = (rng.random(n) < eta[idx]).astype(np.int8)
    return X, y, idx
