"""Simulation 1C: shared-value hash collapse on wide binary data (exact).

Design: M binary coordinates, X_j ~ Bernoulli(q) iid. Two target mechanisms:

  position-specific  eta depends on the first S = 5 named coordinates
                     (main effects + 2 interactions among them);
  hamming-weight     eta depends only on w = sum_j X_j.

Why this arm can be evaluated EXACTLY rather than by Monte Carlo:

  For binary records the shared-value hash sees only the bare tokens "0" and
  "1". A record with w ones contributes w to bucket b1 = bucket("1") and M - w
  to bucket b0 = bucket("0"). Hence

      b0 != b1  ->  Z is a bijection of w, giving exactly M + 1 reachable
                    encodings (the Stage 1 proposition);
      b0 == b1  ->  Z[b0] = M for every record, giving exactly 1.

  So the encoder's fibers are indexed by w, and every population quantity
  reduces to a sum over w = 0,...,M. The conditional law of the S signal
  coordinates given w is hypergeometric: the number a of active coordinates
  among the first S satisfies a | w ~ Hypergeom(M, w, S), and given a the
  active subset is uniform over the C(S, a) patterns. Both facts are exact,
  so ebar(w) and Var(eta | w) are exact.

  Under a hamming-weight target eta is itself a function of w, so the gap is
  exactly zero: shared-value hashing is adequate there. That is the
  overgeneralisation guard required by the plan.

Column-aware hashing does not admit the same reduction (its fibers mix all M
coordinates), so its population gap is reported as NOT_IDENTIFIED; what is
established exactly for it is the absence of the deterministic Hamming-weight
collapse -- its reachable-encoding count and its injectivity on the active
block are both computed here.
"""
from __future__ import annotations

import itertools

import numpy as np
from scipy.stats import binom, hypergeom

from ..hashing import bucket_of
from .sim1_core import (
    HASH_SEED,
    _binary_entropy,
    group_ids,
)

S_ACTIVE = 5                 # named signal coordinates for the position target
N_INT_PAIRS_1C = 2           # interactions among the active coordinates
ETA_LO_1C, ETA_SPAN_1C = 0.05, 0.90     # squash keeps eta in [0.05, 0.95]


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------

def position_specific_eta(q: float, tau: float, seed: int) -> np.ndarray:
    """eta for each of the 2**S patterns of the active coordinates."""
    rng = np.random.default_rng(seed)
    pats = np.array(list(itertools.product([0, 1], repeat=S_ACTIVE)), dtype=np.int64)
    c = rng.standard_normal(S_ACTIVE)
    pairs = [(j, l) for j in range(S_ACTIVE) for l in range(j + 1, S_ACTIVE)][:N_INT_PAIRS_1C]
    d = rng.standard_normal(len(pairs))
    g = pats @ c
    for (j, l), dv in zip(pairs, d):
        g = g + dv * pats[:, j] * pats[:, l]
    # q-WEIGHTED centring: patterns are not equiprobable when q != 0.5, so an
    # unweighted mean over the 32 patterns would let marginal prevalence drift
    # with the activation rate, confounding the activation-rate factor with a
    # prevalence shift. (S0 design review, MINOR m6.)
    a = pats.sum(axis=1)
    p_pat = q ** a * (1.0 - q) ** (S_ACTIVE - a)
    g = g - float((p_pat * g).sum())
    return ETA_LO_1C + ETA_SPAN_1C / (1.0 + np.exp(-tau * g))


def hamming_weight_eta(M: int, q: float, tau: float) -> np.ndarray:
    """eta for each w = 0,...,M under the Hamming-weight target."""
    w = np.arange(M + 1, dtype=float)
    z = (w - M * q) / np.sqrt(max(M * q * (1.0 - q), 1e-12))
    return ETA_LO_1C + ETA_SPAN_1C / (1.0 + np.exp(-tau * z))


# ---------------------------------------------------------------------------
# Shared-value hash structure on binary data
# ---------------------------------------------------------------------------

def shared_value_zero_one_buckets(B: int) -> tuple[int, int]:
    """Buckets of the bare tokens "0" and "1" under the frozen hash."""
    return bucket_of("0", B, HASH_SEED), bucket_of("1", B, HASH_SEED)


def shared_value_reachable(M: int, B: int) -> int:
    """Number of reachable shared-value encodings of {0,1}**M: M+1, or 1."""
    b0, b1 = shared_value_zero_one_buckets(B)
    return M + 1 if b0 != b1 else 1


def shared_value_reachable_bruteforce(M: int, B: int) -> int:
    """Same count obtained by enumerating all 2**M records (small M only)."""
    if M > 16:
        raise ValueError("brute force is restricted to M <= 16")
    b0, b1 = shared_value_zero_one_buckets(B)
    seen = set()
    for rec in itertools.product([0, 1], repeat=M):
        z = np.zeros(B, dtype=np.int64)
        for v in rec:
            z[b1 if v else b0] += 1
        seen.add(tuple(z.tolist()))
    return len(seen)


def column_aware_active_block_injective(M: int, B: int) -> bool:
    """True iff the 2**S active-block patterns get distinct partial encodings.

    This is the exact statement that column-aware hashing does NOT collapse
    position-specific information the way shared-value hashing does; any
    residual loss is collision-driven, not a deterministic Hamming-weight
    identification.
    """
    names = [f"v{j}" for j in range(M)]
    bk = np.array([[bucket_of(f"{len(names[j])}:{names[j]}={k}", B, HASH_SEED)
                    for k in (0, 1)] for j in range(S_ACTIVE)])
    pats = np.array(list(itertools.product([0, 1], repeat=S_ACTIVE)), dtype=np.int64)
    codes = np.zeros((len(pats), B), dtype=np.int64)
    for j in range(S_ACTIVE):
        np.add.at(codes, (np.arange(len(pats)), bk[j, pats[:, j]]), 1)
    return len(np.unique(group_ids(codes))) == len(pats)


def column_aware_diagnostics(M: int, B: int) -> dict:
    """Occupied buckets and token collisions for the full column-aware map."""
    names = [f"v{j}" for j in range(M)]
    buckets = [bucket_of(f"{len(names[j])}:{names[j]}={k}", B, HASH_SEED)
               for j in range(M) for k in (0, 1)]
    occ = len(set(buckets))
    return {"n_tokens": len(buckets), "occupied_buckets": occ,
            "collision_count": len(buckets) - occ}


# ---------------------------------------------------------------------------
# Exact population evaluation of one 1C cell
# ---------------------------------------------------------------------------

def _pattern_moments_by_active_count(eta_pat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Mean of eta and of eta**2 over patterns grouped by active count a."""
    pats = np.array(list(itertools.product([0, 1], repeat=S_ACTIVE)), dtype=np.int64)
    a = pats.sum(axis=1)
    m1 = np.array([eta_pat[a == k].mean() for k in range(S_ACTIVE + 1)])
    m2 = np.array([(eta_pat[a == k] ** 2).mean() for k in range(S_ACTIVE + 1)])
    return m1, m2


def exact_1c_shared_value(M: int, q: float, tau: float, target: str, B: int,
                          seed: int) -> dict:
    """Exact population risks and gaps for the shared-value hash.

    Returns the same identity-check fields as sim1_core.exact_gap_report so the
    two arms are directly comparable.
    """
    w = np.arange(M + 1)
    p_w = binom.pmf(w, M, q)
    b0, b1 = shared_value_zero_one_buckets(B)
    collapsed = (b0 == b1)

    if target == "hamming_weight":
        eta_w = hamming_weight_eta(M, q, tau)
        risk_x_log = float((p_w * _binary_entropy(eta_w)).sum())
        risk_x_bri = float((p_w * eta_w * (1 - eta_w)).sum())

        # The zero gap under this target must EMERGE from the aggregation, not
        # be assigned. An earlier version set (risk_z, cmi, evar) = (risk_x, 0, 0)
        # on the non-collapsed branch, which made acceptance criterion A9 -- the
        # guard against overgeneralising the shared-value failure -- a tautology
        # that a genuine fiber-logic bug would have passed. Both branches now go
        # through the same generic fiber aggregation as the position-specific
        # arm, so A9 is measured. (Design review S0, BLOCKER B3.)
        fw = np.zeros(M + 1, dtype=np.int64) if collapsed else np.arange(M + 1)
        n_f = 1 if collapsed else M + 1
        mass = np.bincount(fw, weights=p_w, minlength=n_f)
        wsum = np.bincount(fw, weights=p_w * eta_w, minlength=n_f)
        ebar_f = np.where(mass > 0, wsum / np.where(mass > 0, mass, 1.0), 0.0)
        ebar_w = ebar_f[fw]

        risk_z_log = float((mass * _binary_entropy(ebar_f)).sum())
        risk_z_bri = float((mass * ebar_f * (1 - ebar_f)).sum())
        ok = (p_w > 0) & (eta_w > 0) & (eta_w < 1) & (ebar_w > 0) & (ebar_w < 1)
        cmi = float((p_w[ok] * (eta_w[ok] * np.log(eta_w[ok] / ebar_w[ok])
                                + (1 - eta_w[ok])
                                * np.log((1 - eta_w[ok]) / (1 - ebar_w[ok])))).sum())
        evar = float((p_w * (eta_w - ebar_w) ** 2).sum())

        n_fibers = n_f
        spread = 0.0 if not collapsed else float(eta_w.max() - eta_w.min())

    elif target == "position_specific":
        eta_pat = position_specific_eta(q, tau, seed)
        pats = np.array(list(itertools.product([0, 1], repeat=S_ACTIVE)), dtype=np.int64)
        a_of_pat = pats.sum(axis=1)
        p_pat = q ** a_of_pat * (1 - q) ** (S_ACTIVE - a_of_pat)
        risk_x_log = float((p_pat * _binary_entropy(eta_pat)).sum())
        risk_x_bri = float((p_pat * eta_pat * (1 - eta_pat)).sum())

        m1, m2 = _pattern_moments_by_active_count(eta_pat)
        a_grid = np.arange(S_ACTIVE + 1)
        # P(a | w) = Hypergeom(M, w, S)
        p_a_given_w = hypergeom.pmf(a_grid[None, :], M, w[:, None], S_ACTIVE)
        p_a_given_w = np.nan_to_num(p_a_given_w, nan=0.0)

        if collapsed:
            ebar_w = np.full(M + 1, float((p_pat * eta_pat).sum()))
            var_w = np.full(M + 1, float((p_pat * eta_pat ** 2).sum()) - ebar_w[0] ** 2)
        else:
            ebar_w = p_a_given_w @ m1
            e2_w = p_a_given_w @ m2
            var_w = np.maximum(e2_w - ebar_w ** 2, 0.0)

        risk_z_log = float((p_w * _binary_entropy(ebar_w)).sum())
        risk_z_bri = float((p_w * ebar_w * (1 - ebar_w)).sum())
        evar = float((p_w * var_w).sum())

        # independent path for I(Y;X|Z): joint over (pattern, w)
        # w = a(pattern) + Binom(M - S, q)
        rest = np.arange(M - S_ACTIVE + 1)
        p_rest = binom.pmf(rest, M - S_ACTIVE, q)
        cmi = 0.0
        for i in range(len(pats)):
            wi = a_of_pat[i] + rest
            qz = ebar_w[wi]
            e = eta_pat[i]
            kl = e * np.log(e / qz) + (1 - e) * np.log((1 - e) / (1 - qz))
            cmi += float(p_pat[i] * (p_rest * kl).sum())
        n_fibers = 1 if collapsed else M + 1
        spread = float(eta_pat.max() - eta_pat.min())
    else:
        raise ValueError(f"unknown target mechanism {target!r}")

    return {
        "risk_x_logloss": risk_x_log, "risk_z_logloss": risk_z_log,
        "risk_x_brier": risk_x_bri, "risk_z_brier": risk_z_bri,
        "gap_logloss": risk_z_log - risk_x_log,
        "gap_brier": risk_z_bri - risk_x_bri,
        "theoretical_gap_logloss": cmi, "theoretical_gap_brier": evar,
        "identity_error_logloss": abs((risk_z_log - risk_x_log) - cmi),
        "identity_error_brier": abs((risk_z_bri - risk_x_bri) - evar),
        "fiber_count": int(n_fibers),
        "reachable_encodings": shared_value_reachable(M, B),
        "max_fiber_posterior_spread": spread,
        "M": M, "activation_rate": q, "tau": tau, "target_mechanism": target,
        "encoder": "hash_shared", "bucket_width": B, "seed": seed,
        "exact_or_mc": "exact", "mcse": 0.0,
        "theoretical_gap_status": "IDENTIFIED_EXACT",
    }
