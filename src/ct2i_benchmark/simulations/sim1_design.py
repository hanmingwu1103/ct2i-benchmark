"""Scenario enumeration and seed assignment for Simulation 1, per the freeze.

Single source of truth: the runners, the summariser, the figure scripts and the
seed manifest all import scenario ids and seeds from here, so a scenario cannot
mean one thing in the raw output and another in a summary.

Seed blocks exclude the contrasted factors (S0 design review B1), so both arms
of every within-DGP contrast share one parameter draw:

  1A   block = (M, K, marginal, tau, n_int)          Delta_eta excluded
  1B   block = (M, K, marginal, tau, n_int)          Delta_eta, n_train excluded
  1C   block = (activation_rate, target_mechanism)   M, n_train excluded
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

from .sim1_core import dgp_block_seed

# ---------------------------------------------------------------------------
# Frozen factor levels
# ---------------------------------------------------------------------------

F1A = dict(M=[3, 5], K=[3, 4], marginal=["uniform", "zipf"], tau=[0.5, 1.5],
           n_int=[0, 2], delta_eta=[0.0, 0.1, 0.3])
F1B = dict(M=[5, 20], K=[4, 12, 50], marginal=["uniform", "zipf"], tau=[0.5, 1.5],
           n_int=[0, 3], delta_eta=[0.0, 0.1, 0.3], n_train=[500, 5000])
F1C = dict(M=[10, 50, 200, 1000], activation_rate=[0.05, 0.20, 0.50],
           target_mechanism=["position_specific", "hamming_weight"],
           n_train=[500, 5000])

REPS_1A, REPS_1B, REPS_1C = 100, 50, 50
N_EVAL = 50_000
TAU_1C = 1.5
D_ACTIVE_1B = 3

ENC_1A = ["identity", "label", "onehot", "designed_merge", "count_pop",
          "hash_column", "hash_shared"]
ENC_1B = ["label", "onehot", "count", "hash_column", "hash_shared",
          "target", "woe", "ordered_catboost_sim", "homals"]
ENC_1C = ["label", "onehot", "count", "hash_column", "hash_shared"]
HASH_ENC = {"hash_column", "hash_shared"}

LEARNERS_1B = ["bayes_z_oracle", "logistic", "lightgbm", "mlp"]
HEAVY = {"lightgbm", "mlp"}
# Option B (fractional): heavy learners run on this encoder subset, one width
HEAVY_SUBSET = ["label", "onehot", "count", "hash_column", "hash_shared", "target"]


def bucket_widths(M: int, K: int) -> dict[str, int]:
    k_tot = M * K
    return {"B0": max(2, round(0.5 * k_tot)), "B1": max(2, k_tot), "B2": max(2, 2 * k_tot)}


@dataclass
class Scenario:
    scenario_id: str
    component: str
    factors: dict
    block: tuple
    replicates: int
    seeds: list = field(repr=False)


def _mk(component: str, idx: int, factors: dict, block: tuple, reps: int) -> Scenario:
    sid = f"S1{component}-{idx:04d}"
    seeds = [dgp_block_seed(f"1{component}", block, r) for r in range(1, reps + 1)]
    return Scenario(sid, component, factors, block, reps, seeds)


def scenarios_1a() -> list[Scenario]:
    out, i = [], 0
    for M, K, marg, tau, ni, de in product(F1A["M"], F1A["K"], F1A["marginal"],
                                           F1A["tau"], F1A["n_int"], F1A["delta_eta"]):
        i += 1
        out.append(_mk("A", i, dict(M=M, K=K, marginal=marg, tau=tau, n_int=ni,
                                    delta_eta=de),
                       (M, K, marg, tau, ni), REPS_1A))
    return out


def scenarios_1b() -> list[Scenario]:
    out, i = [], 0
    for M, K, marg, tau, ni, de, nt in product(
            F1B["M"], F1B["K"], F1B["marginal"], F1B["tau"], F1B["n_int"],
            F1B["delta_eta"], F1B["n_train"]):
        i += 1
        out.append(_mk("B", i, dict(M=M, K=K, marginal=marg, tau=tau, n_int=ni,
                                    delta_eta=de, n_train=nt),
                       (M, K, marg, tau, ni), REPS_1B))
    return out


def scenarios_1c() -> list[Scenario]:
    out, i = [], 0
    for M, q, tgt, nt in product(F1C["M"], F1C["activation_rate"],
                                 F1C["target_mechanism"], F1C["n_train"]):
        i += 1
        out.append(_mk("C", i, dict(M=M, activation_rate=q, target_mechanism=tgt,
                                    n_train=nt, tau=TAU_1C),
                       (q, tgt), REPS_1C))
    return out


def encoder_configs(component: str, M: int, K: int) -> list[tuple[str, int | None, str]]:
    """(encoder, bucket_width, width_label) for one scenario."""
    encs = {"A": ENC_1A, "B": ENC_1B, "C": ENC_1C}[component]
    w = bucket_widths(M, K if component != "C" else 2)
    out = []
    for e in encs:
        if e in HASH_ENC:
            for lab in ("B0", "B1", "B2"):
                out.append((e, w[lab], lab))
        else:
            out.append((e, None, ""))
    return out


def learners_for(encoder: str, width_label: str, variant: str = "fractional") -> list[str]:
    """Option B keeps every encoder for oracle+logistic; heavy learners on a subset."""
    base = ["bayes_z_oracle", "logistic"]
    if variant == "full":
        return base + sorted(HEAVY)
    if encoder in HEAVY_SUBSET and width_label in ("", "B1"):
        return base + sorted(HEAVY)
    return base
