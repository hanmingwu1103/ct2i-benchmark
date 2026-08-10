"""Simulation 2: model-selection optimism (reissued protocol, §19).

Data model per replicate: candidate true values mu (K,), validation errors
eps_val ~ sigma * L where L induces exchangeable correlation rho (Gaussian
factor model), independent-test errors eps_test drawn independently with the
same marginal sigma_test = sigma * sqrt(50/n_test_factor)=sigma (frozen: test
noise uses the same sigma unless heterogeneous condition). Selection rules:
fixed, validation, nested (selection on val, evaluation on independent test),
test-oracle (select and report on the SAME test draw), one-SE (largest-
complexity-penalty-free rule: pick the LEAST complex candidate whose val score
is within one validation SE of the best; complexity = candidate index).
Outputs per scenario: oracle optimism, validation regret, P(select true best),
winner instability, independent-test performance, bound ratios, MCSE.
"""
from __future__ import annotations

import numpy as np


def run_scenario(K, mu, sigma, rho, R, seed, sigma_het=None, n_groups=None):
    """Vectorized Monte Carlo for one scenario. Returns dict of outputs."""
    rng = np.random.default_rng(seed)
    mu = np.asarray(mu, float)
    mu_star = mu.max()
    k_star_set = np.flatnonzero(mu == mu_star)
    sig = np.full(K, sigma) if sigma_het is None else np.asarray(sigma_het)

    # exchangeable correlation via common factor
    common = rng.standard_normal((R, 1))
    idio = rng.standard_normal((R, K))
    eps_val = sig * (np.sqrt(rho) * common + np.sqrt(1 - rho) * idio)
    # independent test draw (same construction, fresh randomness)
    common_t = rng.standard_normal((R, 1))
    idio_t = rng.standard_normal((R, K))
    eps_test = sig * (np.sqrt(rho) * common_t + np.sqrt(1 - rho) * idio_t)

    val = mu + eps_val
    test = mu + eps_test

    k_hat = val.argmax(axis=1)                       # honest validation selection
    k_oracle = test.argmax(axis=1)                   # test-oracle
    rows = np.arange(R)

    oracle_optimism = test.max(axis=1) - mu_star     # observed-max vs best true
    regret = mu_star - mu[k_hat]                     # validation-selection regret
    picked_best = np.isin(k_hat, k_star_set)
    honest_test_perf = test[rows, k_hat]             # independent-test eval of selected
    reporting_bias = honest_test_perf - mu[k_hat]    # should be ~0 in mean
    winner_instab = 1.0 - (np.bincount(k_hat, minlength=K).max() / R)

    # one-SE rule: least complex candidate within 1 sigma of best val
    best_val = val.max(axis=1)
    within = val >= (best_val[:, None] - sig[None, :])
    k_ose = within.argmax(axis=1)                    # first (lowest index = least complex)
    regret_ose = mu_star - mu[k_ose]

    def mcse(x):
        return float(np.std(x, ddof=1) / np.sqrt(len(x)))

    out = {
        "oracle_optimism_mean": float(oracle_optimism.mean()),
        "oracle_optimism_mcse": mcse(oracle_optimism),
        "regret_mean": float(regret.mean()),
        "regret_mcse": mcse(regret),
        "p_select_best": float(picked_best.mean()),
        "p_select_best_mcse": mcse(picked_best.astype(float)),
        "reporting_bias_mean": float(reporting_bias.mean()),
        "reporting_bias_mcse": mcse(reporting_bias),
        "winner_instability": float(winner_instab),
        "test_perf_selected_mean": float(honest_test_perf.mean()),
        "one_se_regret_mean": float(regret_ose.mean()),
        "bound_oracle": float(sig.max() * np.sqrt(2 * np.log(max(K, 2)))),
        "bound_regret": float(sig.max() * np.sqrt(2 * np.log(max(K, 2)))),
        "oracle_bound_ratio": float(oracle_optimism.mean()
                                    / (sig.max() * np.sqrt(2 * np.log(max(K, 2))))),
    }
    return out


def asymmetric_scenario(sigma, rho, R, seed, K_A=72, K_B=8):
    """Two candidate sets with EQUAL true maxima (all-zero mu): compare oracle
    (test-informed) reported maxima. Larger set should show >= oracle
    opportunity on average."""
    a = run_scenario(K_A, np.zeros(K_A), sigma, rho, R, seed)
    b = run_scenario(K_B, np.zeros(K_B), sigma, rho, R, seed + 1)
    return {
        "oracle_advantage_large_minus_small":
            a["oracle_optimism_mean"] - b["oracle_optimism_mean"],
        "large": a, "small": b,
    }
