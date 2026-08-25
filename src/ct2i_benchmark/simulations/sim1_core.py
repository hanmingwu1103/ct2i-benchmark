"""Simulation 1 core: DGP, exact Bayes risks, fiber algebra, population encoders.

This module implements the *population / exact-enumeration* arm of Simulation 1.
Everything here is deterministic given the seed and involves no learner fitting.

Mathematics (frozen; see simulation-results-ct2i/S0_IMPLEMENTATION_SPEC.md):

  X = (X_1,...,X_M), coordinates independent, X_j ~ p_marg on {0,...,K-1}.
  Only the first d coordinates ("active block") carry signal; d = M for
  Simulation 1A, d = min(M, 3) for Simulation 1B.

  raw linear predictor
      g(x) = tau * ( sum_{j in A} a_j(x_j) + sum_{(j,l) in P} b_{jl}(x_j, x_l) )
  with a_j p-centred and b_{jl} p-double-centred, so every term has mean zero.
      eta_raw(x) = logistic(g(x))

  Within-fiber spread is then imposed EXACTLY on the fibers of the designed
  merge map phi_D (coordinate 0: k -> k//2; all other coordinates identity):

      eta(x) = 0.20 + 0.60 * m(f(x)) + (Delta_eta / 2) * s(x)

  where m(f) = p-weighted mean of eta_raw over fiber f, and s(x) in [-1, 1] is
  the rank shape: cells of a fiber f are ordered by (eta_raw, cell) ascending
  and receive s = -1 + 2i/(r-1); singleton fibers get s = 0.

  Consequences, all exact and asserted in code:
    * eta in [0.05, 0.95] always, so no clipping ever occurs;
    * every phi_D fiber with r >= 2 has max(eta) - min(eta) = Delta_eta EXACTLY,
      which is what makes `Delta_eta` a controlled quantity rather than a
      descriptive one;
    * Delta_eta = 0  =>  eta constant on every phi_D fiber (lossless merge);
    * Delta_eta > 0  =>  strictly positive representation gap for phi_D;
    * injective encoders have zero gap for every Delta_eta.

Risk conventions (frozen, matching Stage 2): natural logarithms (nats) and the
one-coordinate Brier loss (y - p)^2.

  R_log(X) = E[ H(eta(X)) ],           H(q) = -q ln q - (1-q) ln(1-q)
  R_bri(X) = E[ eta(X)(1 - eta(X)) ]
  R_log(Z) = E[ H(ebar(Z)) ],          ebar(z) = E[eta(X) | Z = z]
  R_bri(Z) = E[ ebar(Z)(1 - ebar(Z)) ]

Theorem identities checked by this module:

  R_log(Z) - R_log(X) = I(Y; X | Z)
  R_bri(Z) - R_bri(X) = E[ Var{eta(X) | Z} ]

Both right-hand sides are computed through STRUCTURALLY INDEPENDENT code paths
(a per-cell KL sum and a per-fiber variance sum respectively), never by
re-using the risk difference, so the identity check is a real check.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np

from ..hashing import bucket_of

# ---------------------------------------------------------------------------
# Frozen constants
# ---------------------------------------------------------------------------

ETA_BASE_LO = 0.20          # affine squash of fiber means -> [0.20, 0.80]
ETA_BASE_SPAN = 0.60
DELTA_ETA_MAX = 0.30        # largest frozen Delta_eta level
ETA_LO = ETA_BASE_LO - DELTA_ETA_MAX / 2.0                   # 0.05
ETA_HI = ETA_BASE_LO + ETA_BASE_SPAN + DELTA_ETA_MAX / 2.0   # 0.95

ZIPF_S = 1.2                # "Zipf-like" marginal exponent
HASH_SEED = 20260810        # retained verbatim from the baseline repo
KEY_SCALE = 10 ** 12        # float -> int key quantisation for fiber grouping


# ---------------------------------------------------------------------------
# Marginals and cell enumeration
# ---------------------------------------------------------------------------

def marginal_pmf(K: int, kind: str) -> np.ndarray:
    """Category marginal on {0,...,K-1}. 'uniform' or 'zipf' (s = 1.2)."""
    if kind == "uniform":
        p = np.full(K, 1.0 / K)
    elif kind == "zipf":
        p = (np.arange(1, K + 1, dtype=float)) ** (-ZIPF_S)
        p /= p.sum()
    else:
        raise ValueError(f"unknown marginal {kind!r}")
    return p


def enumerate_cells(K: int, d: int) -> np.ndarray:
    """All K**d cells of the active block, lexicographic. Shape (K**d, d)."""
    grids = np.meshgrid(*([np.arange(K)] * d), indexing="ij")
    return np.stack([g.ravel() for g in grids], axis=1).astype(np.int64)


def cell_probabilities(cells: np.ndarray, p_marg: np.ndarray) -> np.ndarray:
    """p(x) = prod_j p_marg(x_j) for the active block (coordinates independent)."""
    return np.prod(p_marg[cells], axis=1)


# ---------------------------------------------------------------------------
# DGP parameters
# ---------------------------------------------------------------------------

@dataclass
class DGPParams:
    M: int
    K: int
    d_active: int
    marginal: str
    tau: float
    n_int: int
    delta_eta: float
    seed: int
    p_marg: np.ndarray = field(repr=False)
    a: np.ndarray = field(repr=False)                 # (d, K) p-centred
    pairs: tuple = ()
    b: tuple = field(default=(), repr=False)          # per pair, (K, K) double-centred


def interaction_pairs(d: int, n_int: int) -> tuple:
    """First n_int pairs of the lexicographic enumeration of {(j,l): j<l<d}."""
    allp = [(j, l) for j in range(d) for l in range(j + 1, d)]
    if n_int > len(allp):
        raise ValueError(f"requested {n_int} interaction pairs but only "
                         f"{len(allp)} exist for d={d}")
    return tuple(allp[:n_int])


def draw_params(M: int, K: int, marginal: str, tau: float, n_int: int,
                delta_eta: float, seed: int, d_active: int | None = None) -> DGPParams:
    """Draw one DGP parameter set. Seeded and fully reproducible."""
    d = M if d_active is None else min(M, d_active)
    rng = np.random.default_rng(seed)
    p = marginal_pmf(K, marginal)

    a = rng.standard_normal((d, K))
    a -= (a * p[None, :]).sum(axis=1, keepdims=True)      # p-centre each variable

    pairs = interaction_pairs(d, n_int)
    bs = []
    for _ in pairs:
        b = rng.standard_normal((K, K))
        row = p @ b                # average over first index  -> length K
        col = b @ p                # average over second index -> length K
        grand = float(p @ b @ p)
        bs.append(b - row[None, :] - col[:, None] + grand)   # double p-centred

    return DGPParams(M=M, K=K, d_active=d, marginal=marginal, tau=tau,
                     n_int=n_int, delta_eta=delta_eta, seed=seed,
                     p_marg=p, a=a, pairs=pairs, b=tuple(bs))


def eta_raw(cells: np.ndarray, prm: DGPParams) -> np.ndarray:
    """logistic(g(x)) on the active block; beta0 = 0."""
    d = prm.d_active
    g = prm.a[np.arange(d)[None, :], cells[:, :d]].sum(axis=1)
    for (j, l), b in zip(prm.pairs, prm.b):
        g = g + b[cells[:, j], cells[:, l]]
    return 1.0 / (1.0 + np.exp(-prm.tau * g))


# ---------------------------------------------------------------------------
# Fiber algebra
# ---------------------------------------------------------------------------

def group_ids(codes: np.ndarray) -> np.ndarray:
    """Map rows of an integer code matrix to contiguous fiber ids."""
    codes = np.atleast_2d(codes)
    if codes.shape[0] == 1 and codes.ndim == 2 and codes.shape[1] != 1:
        codes = codes.reshape(-1, codes.shape[-1])
    _, inv = np.unique(codes, axis=0, return_inverse=True)
    return np.asarray(inv).ravel()


def partition_fingerprint(fid: np.ndarray) -> str:
    """Canonical digest of the CELL -> FIBER PARTITION induced by `fid`.

    Fibers are relabelled in order of FIRST APPEARANCE -- equivalently, sorted
    by their smallest cell index -- and the relabelled sequence is hashed
    together with its length.  Two id vectors therefore produce the same
    digest if and only if they induce the SAME partition of the cells: a pure
    relabelling of the fibers leaves it unchanged, while a permutation of the
    cell -> fiber assignment, or a swap of one cell between two fibers,
    changes it.

    WHY THIS EXISTS.  `fiber_count` -- and the whole multiset of fiber sizes --
    is INVARIANT under both of those defects, and the production-versus-
    reference gap comparison is blind to them as well because both
    implementations are handed the same `fid`.  The stored Monte-Carlo
    representation loss does move, but only by the size of the induced change
    in the population gap, which for a small assignment defect can sit under
    the Monte-Carlo noise floor.  This digest is the exact, tolerance-free
    detector for that class.

    Deliberately does NOT call `group_ids`, `hash_codes`, `quantize` or
    `np.unique`: it must share no code with the construction helpers whose
    defects it exists to detect.
    """
    seen: dict[int, int] = {}
    h = hashlib.blake2b(digest_size=16)
    flat = np.asarray(fid).ravel().tolist()
    h.update(b"ct2i-partition-v1:")
    h.update(len(flat).to_bytes(8, "little"))
    for v in flat:
        v = int(v)
        lab = seen.get(v)
        if lab is None:
            lab = len(seen)
            seen[v] = lab
        h.update(lab.to_bytes(8, "little"))
    return h.hexdigest()


def quantize(v: np.ndarray) -> np.ndarray:
    """Float codes -> exact integer keys (fiber identity must be exact)."""
    return np.rint(np.asarray(v, float) * KEY_SCALE).astype(np.int64)


def designed_merge_ids(cells: np.ndarray) -> np.ndarray:
    """phi_D: coordinate 0 -> k//2, all other coordinates identity."""
    z = cells.copy()
    z[:, 0] = z[:, 0] // 2
    return group_ids(z)


# ---------------------------------------------------------------------------
# eta construction with exactly controlled within-fiber spread
# ---------------------------------------------------------------------------

def impose_delta_eta(cells: np.ndarray, p_cell: np.ndarray, e_raw: np.ndarray,
                     delta_eta: float) -> np.ndarray:
    """eta = 0.20 + 0.60*m(f) + (Delta/2)*s, with s the rank shape in [-1,1].

    Within every designed-merge fiber of size r >= 2 the resulting posterior
    range equals `delta_eta` exactly.
    """
    fid = designed_merge_ids(cells)
    n_f = int(fid.max()) + 1

    mass = np.bincount(fid, weights=p_cell, minlength=n_f)
    wsum = np.bincount(fid, weights=p_cell * e_raw, minlength=n_f)
    with np.errstate(invalid="ignore", divide="ignore"):
        m = np.where(mass > 0, wsum / np.where(mass > 0, mass, 1.0), 0.0)

    # rank shape: order each fiber by (eta_raw, cell) ascending
    order = np.lexsort((*[cells[:, j] for j in range(cells.shape[1] - 1, -1, -1)],
                        e_raw, fid))
    s = np.zeros(len(cells))
    start = 0
    fid_sorted = fid[order]
    while start < len(order):
        stop = start + 1
        while stop < len(order) and fid_sorted[stop] == fid_sorted[start]:
            stop += 1
        r = stop - start
        if r >= 2:
            s[order[start:stop]] = -1.0 + 2.0 * np.arange(r) / (r - 1)
        start = stop

    eta = ETA_BASE_LO + ETA_BASE_SPAN * m[fid] + (delta_eta / 2.0) * s
    if not (eta.min() >= ETA_LO - 1e-12 and eta.max() <= ETA_HI + 1e-12):
        raise AssertionError(
            f"eta escaped the no-clipping band [{ETA_LO}, {ETA_HI}]: "
            f"observed [{eta.min()}, {eta.max()}]")
    return eta


def max_fiber_spread(fid: np.ndarray, p_cell: np.ndarray, eta: np.ndarray,
                     min_mass: float = 0.0) -> float:
    """Largest within-fiber posterior range over fibers with positive mass."""
    out = 0.0
    for f in np.unique(fid):
        sel = fid == f
        if p_cell[sel].sum() <= min_mass:
            continue
        out = max(out, float(eta[sel].max() - eta[sel].min()))
    return out


# ---------------------------------------------------------------------------
# Exact Bayes risks and the two theorem identities
# ---------------------------------------------------------------------------

def _binary_entropy(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, float)
    out = np.zeros_like(q)
    ok = (q > 0.0) & (q < 1.0)
    out[ok] = -(q[ok] * np.log(q[ok]) + (1 - q[ok]) * np.log1p(-q[ok]))
    return out


def bayes_risks_x(p_cell: np.ndarray, eta: np.ndarray) -> tuple[float, float]:
    """Exact Bayes log-loss (nats) and one-coordinate Brier risk using X."""
    return (float((p_cell * _binary_entropy(eta)).sum()),
            float((p_cell * eta * (1.0 - eta)).sum()))


def fiber_posteriors(fid: np.ndarray, p_cell: np.ndarray, eta: np.ndarray):
    """Per-fiber mass P(f) and posterior ebar(f) = E[eta | Z = f]."""
    n_f = int(fid.max()) + 1
    mass = np.bincount(fid, weights=p_cell, minlength=n_f)
    wsum = np.bincount(fid, weights=p_cell * eta, minlength=n_f)
    ebar = np.where(mass > 0, wsum / np.where(mass > 0, mass, 1.0), 0.0)
    return mass, ebar


def bayes_risks_z(fid: np.ndarray, p_cell: np.ndarray, eta: np.ndarray) -> tuple[float, float]:
    """Exact Bayes risks using Z, by aggregation over encoder fibers."""
    mass, ebar = fiber_posteriors(fid, p_cell, eta)
    return (float((mass * _binary_entropy(ebar)).sum()),
            float((mass * ebar * (1.0 - ebar)).sum()))


def conditional_mutual_information(fid: np.ndarray, p_cell: np.ndarray,
                                   eta: np.ndarray) -> float:
    """I(Y; X | Z) in nats, by a per-cell KL sum.

    Structurally independent of the risk difference: this sums
    p(x) * KL( Bern(eta(x)) || Bern(ebar(z(x))) ) over cells, rather than
    differencing two entropies.
    """
    _, ebar = fiber_posteriors(fid, p_cell, eta)
    e = eta
    q = ebar[fid]
    ok = (p_cell > 0) & (e > 0) & (e < 1) & (q > 0) & (q < 1)
    kl = np.zeros_like(e)
    kl[ok] = (e[ok] * np.log(e[ok] / q[ok])
              + (1 - e[ok]) * np.log((1 - e[ok]) / (1 - q[ok])))
    return float((p_cell * kl).sum())


def expected_conditional_variance(fid: np.ndarray, p_cell: np.ndarray,
                                  eta: np.ndarray) -> float:
    """E[ Var{eta(X) | Z} ], by a per-fiber weighted variance sum.

    Structurally independent of the Brier risk difference.
    """
    mass, ebar = fiber_posteriors(fid, p_cell, eta)
    dev2 = (eta - ebar[fid]) ** 2
    n_f = len(mass)
    within = np.bincount(fid, weights=p_cell * dev2, minlength=n_f)
    return float(within.sum())


def exact_gap_report(fid: np.ndarray, p_cell: np.ndarray, eta: np.ndarray) -> dict:
    """Both gaps, both independent theoretical values, and the identity errors."""
    rl_x, rb_x = bayes_risks_x(p_cell, eta)
    rl_z, rb_z = bayes_risks_z(fid, p_cell, eta)
    cmi = conditional_mutual_information(fid, p_cell, eta)
    evar = expected_conditional_variance(fid, p_cell, eta)
    mass, _ = fiber_posteriors(fid, p_cell, eta)
    sizes = np.bincount(fid, minlength=len(mass))
    merged = (sizes >= 2) & (mass > 0)
    return {
        "risk_x_logloss": rl_x, "risk_z_logloss": rl_z,
        "risk_x_brier": rb_x, "risk_z_brier": rb_z,
        "gap_logloss": rl_z - rl_x, "gap_brier": rb_z - rb_x,
        "theoretical_gap_logloss": cmi, "theoretical_gap_brier": evar,
        "identity_error_logloss": abs((rl_z - rl_x) - cmi),
        "identity_error_brier": abs((rb_z - rb_x) - evar),
        "fiber_count": int(len(mass)),
        "merged_fiber_count": int(merged.sum()),
        "merged_fiber_mass": float(mass[merged].sum()),
        "max_fiber_posterior_spread": max_fiber_spread(fid, p_cell, eta),
    }


def reference_gap_report(fid, p_cell, eta) -> dict:
    """Deliberately slow, dependency-free reference implementation.

    Raised by the Codex S0 review: the fast path computes both sides of each
    identity from the SAME `fiber_posteriors` aggregation, so a defect in fiber
    grouping, masses, or conditional means could make both sides agree
    incorrectly. Structural separation of the two formulas is not the same as
    independence of the two implementations.

    This function shares no code with the fast path: pure-Python dict grouping,
    `math` rather than numpy reductions, no bincount, no `fiber_posteriors`.
    A property test asserts the two agree across the whole grid, so a shared
    aggregation bug would have to be reproduced independently here to escape
    detection.
    """
    import math
    from collections import defaultdict

    groups: dict[int, list[int]] = defaultdict(list)
    for i, f in enumerate(fid):
        groups[int(f)].append(i)

    r_log_x = r_bri_x = 0.0
    for i in range(len(p_cell)):
        p, e = float(p_cell[i]), float(eta[i])
        if p <= 0.0:
            continue
        if 0.0 < e < 1.0:
            r_log_x += p * (-(e * math.log(e) + (1.0 - e) * math.log(1.0 - e)))
        r_bri_x += p * e * (1.0 - e)

    r_log_z = r_bri_z = cmi = evar = 0.0
    for idx in groups.values():
        mass = sum(float(p_cell[i]) for i in idx)
        if mass <= 0.0:
            continue
        ebar = sum(float(p_cell[i]) * float(eta[i]) for i in idx) / mass
        if 0.0 < ebar < 1.0:
            r_log_z += mass * (-(ebar * math.log(ebar)
                                 + (1.0 - ebar) * math.log(1.0 - ebar)))
        r_bri_z += mass * ebar * (1.0 - ebar)
        for i in idx:
            p, e = float(p_cell[i]), float(eta[i])
            if p <= 0.0:
                continue
            if 0.0 < e < 1.0 and 0.0 < ebar < 1.0:
                cmi += p * (e * math.log(e / ebar)
                            + (1.0 - e) * math.log((1.0 - e) / (1.0 - ebar)))
            evar += p * (e - ebar) ** 2

    return {
        "risk_x_logloss": r_log_x, "risk_z_logloss": r_log_z,
        "risk_x_brier": r_bri_x, "risk_z_brier": r_bri_z,
        "gap_logloss": r_log_z - r_log_x, "gap_brier": r_bri_z - r_bri_x,
        "theoretical_gap_logloss": cmi, "theoretical_gap_brier": evar,
        "identity_error_logloss": abs((r_log_z - r_log_x) - cmi),
        "identity_error_brier": abs((r_bri_z - r_bri_x) - evar),
    }


# ---------------------------------------------------------------------------
# Population encoders: cell array -> fiber ids
# ---------------------------------------------------------------------------

def _hash_buckets(n_cols: int, K: int, B: int, column_aware: bool,
                  col_names: list[str] | None = None) -> np.ndarray:
    """Bucket index for every (column, level). Shape (n_cols, K).

    Tokens are byte-identical to the baseline repo's hash encoders:
      column-aware : f"{len(col)}:{col}={val}"   (length-prefixed, unambiguous)
      shared-value : the bare value string
    Counting is UNSIGNED, so column identity in the token is the only
    difference between the two encoders.
    """
    names = col_names or [f"v{j}" for j in range(n_cols)]
    out = np.empty((n_cols, K), dtype=np.int64)
    for j in range(n_cols):
        for k in range(K):
            tok = f"{len(names[j])}:{names[j]}={k}" if column_aware else f"{k}"
            out[j, k] = bucket_of(tok, B, HASH_SEED)
    return out


def hash_codes(cells: np.ndarray, K: int, B: int, column_aware: bool) -> np.ndarray:
    """Per-record unsigned bucket-count vector. Shape (n_cells, B)."""
    n, n_cols = cells.shape
    bk = _hash_buckets(n_cols, K, B, column_aware)
    out = np.zeros((n, B), dtype=np.int64)
    for j in range(n_cols):
        np.add.at(out, (np.arange(n), bk[j, cells[:, j]]), 1)
    return out


def population_fibers(name: str, cells: np.ndarray, prm: DGPParams,
                      B: int | None = None) -> np.ndarray:
    """Fiber ids induced by a deterministic population encoder.

    identity / label / onehot  are injective controls (identical fibers).
    designed_merge             is the non-injective theoretical control.
    count_pop                  maps a level to its TRUE marginal probability,
                               so it collapses levels of equal probability
                               (total collapse under a uniform marginal,
                               injective under Zipf).
    hash_column / hash_shared  use the frozen blake2b bucketing above.
    """
    if name in ("identity", "label", "onehot"):
        return group_ids(cells)
    if name == "designed_merge":
        return designed_merge_ids(cells)
    if name == "count_pop":
        return group_ids(quantize(prm.p_marg[cells]))
    if name in ("hash_column", "hash_shared"):
        if B is None:
            raise ValueError("bucket width B is required for hash encoders")
        return group_ids(hash_codes(cells, prm.K, B, name == "hash_column"))
    raise ValueError(f"unknown population encoder {name!r}")


INJECTIVE_CONTROLS = ("identity", "label", "onehot")
POPULATION_ENCODERS = ("identity", "label", "onehot", "designed_merge",
                       "count_pop", "hash_column", "hash_shared")


# ---------------------------------------------------------------------------
# Seed blocks: pairing for within-DGP contrasts
# ---------------------------------------------------------------------------

SEED_BASE = {"1A": 100_000, "1B": 200_000, "1B_data": 300_000,
             "1C": 400_000, "1C_data": 600_000}

# Factors that are CONTRASTED within a DGP draw and must therefore be excluded
# from the seed key, so both arms of the contrast share one parameter draw.
CONTRASTED_FACTORS = {
    "1A": ("delta_eta",),
    "1B": ("delta_eta", "n_train"),
    "1C": ("M", "n_train"),
}


def dgp_block_seed(component: str, block: tuple, replicate: int) -> int:
    """Seed for the DGP parameter draw, keyed on a block that EXCLUDES the
    contrasted factors.

    Raised by the S0 design review (BLOCKER B1). The original rule keyed the
    seed on a scenario index that *contained* the contrasted factor, so the two
    arms of every within-DGP contrast (A6, A8, C5-C8) were drawn from DIFFERENT
    parameter sets. The comparison was then unpaired by construction and the
    between-draw variance swamped the effect: acceptance criterion A8
    ("shared-value loss nondecreasing in M") failed 15/15 measured replicates
    under the unpaired rule and 0/15 under the paired rule. Since the freeze
    forbids retuning a failed criterion, that would have produced an
    unfixable spurious failure in Phase S1.

    `block` must contain only the NON-contrasted factors, in a fixed order.
    A property test asserts the parameter draw is identical across the levels
    of each contrasted factor within a block.
    """
    if component not in SEED_BASE:
        raise ValueError(f"unknown component {component!r}")
    h = int.from_bytes(
        hashlib.blake2b(repr(tuple(block)).encode(), digest_size=4).digest(),
        "little")
    return SEED_BASE[component] + 1000 * (h % 1_000_000) + int(replicate)


# ---------------------------------------------------------------------------
# Per-cell identification of the population gap (Simulation 1B)
# ---------------------------------------------------------------------------

ENUM_CAP = 1_000_000        # frozen: largest full state space we will enumerate


def hash_gap_identified(M: int, K: int, cap: int = ENUM_CAP) -> bool:
    """True when the FULL state space K**M is small enough to enumerate.

    Raised by the S0 design review (BLOCKER B2). The blanket declaration that
    hash-encoder population gaps are NOT_IDENTIFIED in Simulation 1B was
    over-broad: it is true at M=20, K=50, but false at M=5, K=4, where the
    whole space is 1024 cells and the exact gap computes in about 5 ms. The
    status is therefore decided per cell rather than per encoder.
    """
    try:
        return K ** M <= cap
    except OverflowError:
        return False


def exact_full_space_gap(prm: DGPParams, encoder: str, B: int | None,
                         delta_eta: float) -> dict:
    """Exact gap over the FULL K**M space, for encoders that mix all coordinates.

    eta depends only on the active block, but a hashed record's bucket-count
    vector sums over every coordinate, so the fibers must be built on the full
    space. Callers must check `hash_gap_identified` first.
    """
    if not hash_gap_identified(prm.M, prm.K):
        raise ValueError(f"state space {prm.K}**{prm.M} exceeds ENUM_CAP={ENUM_CAP}")
    full = enumerate_cells(prm.K, prm.M)
    p_full = cell_probabilities(full, prm.p_marg)

    # eta is a function of the active block only; look it up per full cell
    active = full[:, :prm.d_active]
    act_cells = enumerate_cells(prm.K, prm.d_active)
    p_act = cell_probabilities(act_cells, prm.p_marg)
    eta_act = impose_delta_eta(act_cells, p_act, eta_raw(act_cells, prm), delta_eta)
    ids = np.zeros(len(active), dtype=np.int64)
    for j in range(prm.d_active):
        ids = ids * prm.K + active[:, j]
    eta_full = eta_act[ids]

    if encoder in ("hash_column", "hash_shared"):
        if B is None:
            raise ValueError("bucket width B is required for hash encoders")
        fid = group_ids(hash_codes(full, prm.K, B, encoder == "hash_column"))
    else:
        fid = population_fibers(encoder, full, prm, B)

    rep = exact_gap_report(fid, p_full, eta_full)
    rep.update(n_cells=int(len(full)), exact_or_mc="exact", mcse=0.0,
               theoretical_gap_status="IDENTIFIED_EXACT")
    return rep


# ---------------------------------------------------------------------------
# One assembled exact scenario
# ---------------------------------------------------------------------------

def exact_scenario(M: int, K: int, marginal: str, tau: float, n_int: int,
                   delta_eta: float, seed: int, encoder: str,
                   B: int | None = None, d_active: int | None = None) -> dict:
    """Build the DGP, impose Delta_eta, and evaluate one encoder exactly."""
    prm = draw_params(M, K, marginal, tau, n_int, delta_eta, seed, d_active)
    cells = enumerate_cells(K, prm.d_active)
    p_cell = cell_probabilities(cells, prm.p_marg)
    eta = impose_delta_eta(cells, p_cell, eta_raw(cells, prm), delta_eta)
    fid = population_fibers(encoder, cells, prm, B)
    rep = exact_gap_report(fid, p_cell, eta)
    rep.update(M=M, K=K, marginal=marginal, tau=tau, interaction_count=n_int,
               delta_eta=delta_eta, seed=seed, encoder=encoder,
               bucket_width=(B if B is not None else ""),
               d_active=prm.d_active, n_cells=int(len(cells)),
               exact_or_mc="exact", mcse=0.0)
    return rep
