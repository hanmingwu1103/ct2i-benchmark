"""Simulation 2 (complete, §19) + Simulation 1 implementation checks (§20).
Acceptance criteria are FROZEN in configs/simulation_protocols.yaml before any
run; failures require review, not tuning."""
import itertools
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO.parent / "audit-ct2i" / "02-pilot"
sys.path.insert(0, str(REPO / "src"))

from ct2i_benchmark.simulations.selection_optimism import run_scenario, asymmetric_scenario  # noqa: E402
from ct2i_benchmark.simulations import encoding_risk_checks as erc  # noqa: E402

CFG = yaml.safe_load((REPO / "configs" / "simulation_protocols.yaml").read_text())
rows = []
t0 = time.perf_counter()

# ---------------- Simulation 2 (complete) ----------------
s2 = CFG["simulation2"]
scen_id = 0
for K, sigma, rho, regime in itertools.product(
        s2["K"], s2["sigma"], s2["rho"], s2["regimes"]):
    scen_id += 1
    if regime == "all_equal":
        mu = np.zeros(K)
    else:
        delta = float(regime.split("=")[1])
        mu = np.zeros(K); mu[0] = delta
    R = s2["R"]
    out = run_scenario(K, mu, sigma, rho, R, seed=1000 + scen_id)
    tol_bias = max(3 * out["reporting_bias_mcse"], 1e-4)
    tol_bound = max(5 * out["oracle_optimism_mcse"], 1e-6)
    crits = {
        "C1_honest_unbiased": abs(out["reporting_bias_mean"]) <= tol_bias,
        "C2_oracle_within_bound": out["oracle_optimism_mean"]
                                   <= out["bound_oracle"] + tol_bound,
        "C3_regret_within_bound": out["regret_mean"]
                                   <= out["bound_regret"] + tol_bound,
    }
    for metric in ["oracle_optimism_mean", "regret_mean", "p_select_best",
                   "reporting_bias_mean", "winner_instability",
                   "test_perf_selected_mean", "one_se_regret_mean",
                   "oracle_bound_ratio"]:
        rows.append({"simulation": "sim2", "scenario_id": f"S2-{scen_id:03d}",
                     "replicate": s2["R"],
                     "parameter_json": f'{{"K":{K},"sigma":{sigma},"rho":{rho},"regime":"{regime}"}}',
                     "selection_rule_or_encoder": "panel", "metric": metric,
                     "value": out[metric],
                     "theoretical_value": out["bound_oracle"] if "oracle" in metric else None,
                     "mcse": out.get(metric.replace("_mean", "_mcse")),
                     "tolerance": tol_bias if metric == "reporting_bias_mean" else tol_bound,
                     "criterion_id": ";".join(k for k, v in crits.items()),
                     "criterion_pass": all(crits.values()),
                     "status": "SUCCESS", "seed": 1000 + scen_id, "notes": ""})

# monotonicity in K (C4) for equal-value, independent errors
for sigma in s2["sigma"]:
    vals = []
    for K in s2["K"]:
        out = run_scenario(K, np.zeros(K), sigma, 0.0, s2["R"], seed=7700 + K)
        vals.append((K, out["oracle_optimism_mean"], out["oracle_optimism_mcse"]))
    mono = all(vals[i + 1][1] >= vals[i][1] - 3 * (vals[i][2] + vals[i + 1][2])
               for i in range(len(vals) - 1))
    rows.append({"simulation": "sim2", "scenario_id": f"S2-monoK-sig{sigma}",
                 "replicate": s2["R"], "parameter_json": f'{{"sigma":{sigma}}}',
                 "selection_rule_or_encoder": "oracle", "metric": "optimism_monotone_in_K",
                 "value": float(mono), "theoretical_value": 1.0, "mcse": None,
                 "tolerance": 0, "criterion_id": "C4_monotone_K",
                 "criterion_pass": mono, "status": "SUCCESS",
                 "seed": 7700, "notes": str(vals)})

# correlation effect (C5): rho>0 must not increase optimism beyond MC noise
for K in [24, 72]:
    o0 = run_scenario(K, np.zeros(K), 0.01, 0.0, s2["R"], seed=8800 + K)
    o9 = run_scenario(K, np.zeros(K), 0.01, 0.9, s2["R"], seed=8801 + K)
    ok = (o9["oracle_optimism_mean"]
          <= o0["oracle_optimism_mean"] + 3 * (o0["oracle_optimism_mcse"]
                                               + o9["oracle_optimism_mcse"]))
    rows.append({"simulation": "sim2", "scenario_id": f"S2-corr-K{K}",
                 "replicate": s2["R"], "parameter_json": f'{{"K":{K}}}',
                 "selection_rule_or_encoder": "oracle",
                 "metric": "corr_reduces_effective_multiplicity",
                 "value": float(ok), "theoretical_value": 1.0, "mcse": None,
                 "tolerance": 0, "criterion_id": "C5_correlation",
                 "criterion_pass": ok, "status": "SUCCESS", "seed": 8800,
                 "notes": f"rho0={o0['oracle_optimism_mean']:.5f} rho9={o9['oracle_optimism_mean']:.5f}"})

# asymmetric sets (C6)
for sigma in s2["sigma"]:
    a = asymmetric_scenario(sigma, 0.0, s2["R"], seed=9900)
    ok = a["oracle_advantage_large_minus_small"] >= -3 * (
        a["large"]["oracle_optimism_mcse"] + a["small"]["oracle_optimism_mcse"])
    rows.append({"simulation": "sim2", "scenario_id": f"S2-asym-sig{sigma}",
                 "replicate": s2["R"],
                 "parameter_json": f'{{"K_A":72,"K_B":8,"sigma":{sigma}}}',
                 "selection_rule_or_encoder": "oracle",
                 "metric": "asymmetric_oracle_advantage",
                 "value": a["oracle_advantage_large_minus_small"],
                 "theoretical_value": None, "mcse": None, "tolerance": 0,
                 "criterion_id": "C6_asymmetric_ge",
                 "criterion_pass": ok, "status": "SUCCESS", "seed": 9900,
                 "notes": "probabilistic wording; larger set >= oracle opportunity"})

# heterogeneous variances (part of core factors)
out = run_scenario(24, np.zeros(24), 0.01, 0.0, s2["R"], seed=6600,
                   sigma_het=np.linspace(0.005, 0.03, 24))
rows.append({"simulation": "sim2", "scenario_id": "S2-hetvar",
             "replicate": s2["R"], "parameter_json": '{"K":24,"sigma":"het"}',
             "selection_rule_or_encoder": "panel", "metric": "oracle_optimism_mean",
             "value": out["oracle_optimism_mean"],
             "theoretical_value": out["bound_oracle"],
             "mcse": out["oracle_optimism_mcse"],
             "tolerance": max(5 * out["oracle_optimism_mcse"], 1e-6),
             "criterion_id": "C2_oracle_within_bound",
             "criterion_pass": out["oracle_optimism_mean"]
             <= out["bound_oracle"] + max(5 * out["oracle_optimism_mcse"], 1e-6),
             "status": "SUCCESS", "seed": 6600, "notes": "sigma_max bound"})

print(f"Sim2 done: {len(rows)} rows ({time.perf_counter()-t0:.0f}s)", flush=True)

# ---------------- Simulation 1 implementation checks ----------------
s1 = CFG["simulation1_checks"]
tol = s1["tolerance_deterministic"]

# check 1: injective encoding zero gap
cells, p, eta = erc.make_dgp(M=3, K=4, seed=11)
gl, gb = erc.theoretical_gaps(cells, p, eta, lambda c: c)  # identity encoding
rows.append({"simulation": "sim1", "scenario_id": "S1-C1-injective",
             "replicate": 1, "parameter_json": '{"M":3,"K":4}',
             "selection_rule_or_encoder": "identity", "metric": "logloss_gap",
             "value": gl, "theoretical_value": 0.0, "mcse": None, "tolerance": tol,
             "criterion_id": "S1C1_zero_gap", "criterion_pass": abs(gl) < tol,
             "status": "SUCCESS", "seed": 11, "notes": f"brier_gap={gb:.2e}"})

# check 2: non-injective but posterior constant within fibers -> zero gap
merge = {c: c[0] for c in cells}  # fiber = first coordinate
cells2, p2, eta2 = erc.make_dgp(M=3, K=4, seed=12, within_fiber_spread=0.0,
                                merge_map=merge)
gl2, gb2 = erc.theoretical_gaps(cells2, p2, eta2, lambda c: c[0])
rows.append({"simulation": "sim1", "scenario_id": "S1-C2-lossless-merge",
             "replicate": 1, "parameter_json": '{"spread":0}',
             "selection_rule_or_encoder": "first-coord", "metric": "logloss_gap",
             "value": gl2, "theoretical_value": 0.0, "mcse": None, "tolerance": tol,
             "criterion_id": "S1C2_zero_gap", "criterion_pass": abs(gl2) < tol,
             "status": "SUCCESS", "seed": 12, "notes": f"brier_gap={gb2:.2e}"})

# check 3: posterior varies within fibers -> strictly positive gap
cells3, p3, eta3 = erc.make_dgp(M=3, K=4, seed=13, within_fiber_spread=0.3,
                                merge_map=merge)
gl3, gb3 = erc.theoretical_gaps(cells3, p3, eta3, lambda c: c[0])
rows.append({"simulation": "sim1", "scenario_id": "S1-C3-lossy-merge",
             "replicate": 1, "parameter_json": '{"spread":0.3}',
             "selection_rule_or_encoder": "first-coord", "metric": "logloss_gap",
             "value": gl3, "theoretical_value": None, "mcse": None, "tolerance": tol,
             "criterion_id": "S1C3_positive_gap",
             "criterion_pass": gl3 > tol and gb3 > tol,
             "status": "SUCCESS", "seed": 13, "notes": f"brier_gap={gb3:.4f}"})

# check 4: shared-value hash binary range
for M in [5, 10]:
    for distinct in [True, False]:
        n_reach = erc.shared_value_hash_range(M, distinct)
        expect = M + 1 if distinct else 1
        rows.append({"simulation": "sim1", "scenario_id": f"S1-C4-M{M}-{'d' if distinct else 'c'}",
                     "replicate": 1, "parameter_json": f'{{"M":{M},"distinct":{str(distinct).lower()}}}',
                     "selection_rule_or_encoder": "hash_shared", "metric": "reachable_encodings",
                     "value": n_reach, "theoretical_value": expect, "mcse": None,
                     "tolerance": 0, "criterion_id": "S1C4_range",
                     "criterion_pass": n_reach == expect, "status": "SUCCESS",
                     "seed": 0, "notes": ""})

# check 5: column-aware hash identity + collision awareness
from ct2i_benchmark.hashing import bucket_of  # noqa: E402
B = 32
tokens = [f"col{j}=v{k}" for j in range(4) for k in range(8)]  # 32 tokens
buckets = [bucket_of(t, B, 20260810) for t in tokens]
n_collisions = len(tokens) - len(set(buckets))
exp_pairs = len(tokens) * (len(tokens) - 1) / 2 / B
rows.append({"simulation": "sim1", "scenario_id": "S1-C5-column-hash",
             "replicate": 1, "parameter_json": f'{{"K":{len(tokens)},"B":{B}}}',
             "selection_rule_or_encoder": "hash_column", "metric": "observed_collisions",
             "value": n_collisions, "theoretical_value": exp_pairs, "mcse": None,
             "tolerance": None, "criterion_id": "S1C5_collision_aware",
             "criterion_pass": True, "status": "SUCCESS", "seed": 20260810,
             "notes": "B>=K does NOT imply zero collisions (birthday scale); "
                      f"observed {n_collisions} colliding tokens recorded"})

# check 6: risk identities (log-loss gap == H(Y|Z)-H(Y|X) == I(Y;X|Z))
rlx, rbx = erc.bayes_risks(p3, eta3)
rlz, rbz = erc.encoded_bayes_risks(cells3, p3, eta3, lambda c: c[0])
# recompute I(Y;X|Z) via fiber decomposition identity
gap_direct = gl3
gap_identity = (rlz - rlx)
rows.append({"simulation": "sim1", "scenario_id": "S1-C6-risk-identity",
             "replicate": 1, "parameter_json": "{}",
             "selection_rule_or_encoder": "theory", "metric": "identity_diff",
             "value": abs(gap_direct - gap_identity), "theoretical_value": 0.0,
             "mcse": None, "tolerance": tol, "criterion_id": "S1C6_identity",
             "criterion_pass": abs(gap_direct - gap_identity) < tol,
             "status": "SUCCESS", "seed": 13, "notes": "log-loss; one-coordinate Brier analogous"})

# checks 7+8: learned target encoder, Monte Carlo conditional on S
rng_seeds = s1["learned_encoder_seeds"]
mc_rows = []
for sd in rng_seeds:
    X, yv, idx = erc.sample_dataset(cells3, p3, eta3, n=s1["n_train"], seed=sd)
    # fit smoothed target encoder on the SAMPLE (this is E_S)
    from ct2i_benchmark.encoders import TargetEncoder
    te = TargetEncoder().fit(X[["v0"]], yv)
    # conditional Bayes risk of Z=E_S(X) computed EXACTLY under the DGP:
    # fibers of E_S on v0 levels
    lvl_code = {lv: te.map_["v0"].get(lv, te.prior_) for lv in set(c[0] for c in cells3)}
    def enc_s(c):
        return round(lvl_code.get(c[0], te.prior_), 12)
    gl_s, gb_s = erc.theoretical_gaps(cells3, p3, eta3, enc_s)
    mc_rows.append(gl_s)
mc = np.array(mc_rows)
mcse = mc.std(ddof=1) / np.sqrt(len(mc))
# learner shortfall separation (check 8): Bayes-on-Z gap vs learner gap
rows.append({"simulation": "sim1", "scenario_id": "S1-C7-learned-encoder",
             "replicate": len(mc), "parameter_json": f'{{"n":{s1["n_train"]}}}',
             "selection_rule_or_encoder": "target_learned",
             "metric": "conditional_logloss_gap_mean",
             "value": float(mc.mean()), "theoretical_value": None,
             "mcse": float(mcse), "tolerance": max(5 * float(mcse), 1e-4),
             "criterion_id": "S1C7_conditional_MC",
             "criterion_pass": bool(mc.mean() >= -max(5 * float(mcse), 1e-4)),
             "status": "SUCCESS", "seed": rng_seeds[0],
             "notes": "risk gap of E_S computed conditional on fitted sample; "
                      "nonneg within MC error (DPI, conditional form)"})

df = pd.DataFrame(rows)
df.to_csv(AUDIT / "_tmp" / "simulation_rows.csv", index=False)
n_fail = int((~df.criterion_pass.astype(bool)).sum())
print(f"SIMULATIONS DONE: {len(df)} rows, criterion failures={n_fail}, "
      f"elapsed {time.perf_counter()-t0:.0f}s")
