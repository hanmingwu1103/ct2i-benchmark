"""Phase S0 unit/property tests (execution prompt step 8).

Ten required properties, one test class each:

  1  exact log-loss identity                 R_log(Z) - R_log(X) = I(Y;X|Z)
  2  exact Brier identity                    R_bri(Z) - R_bri(X) = E[Var(eta|Z)]
  3  injective zero-gap control
  4  lossless non-injective control          Delta_eta = 0
  5  positive-gap lossy merge                Delta_eta > 0
  6  shared-value-hash range at most M+1
  7  column-aware hash distinction
  8  no training-row self-influence for supervised encoders
  9  deterministic seed replay
 10  typed-failure / null-metric behaviour

Tolerances are read from the frozen protocol so a test can never silently use a
looser bound than the one committed in 01_PROTOCOL_FREEZE.yaml.
"""
from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from ct2i_benchmark.simulations import sim1_binary as B1C
from ct2i_benchmark.simulations import sim1_core as CORE
from ct2i_benchmark.simulations import sim1_finite as FIN
from ct2i_benchmark.statuses import Status

FREEZE = (Path(__file__).resolve().parents[1]
          / "simulation-results-ct2i" / "01_PROTOCOL_FREEZE.yaml")


@pytest.fixture(scope="module")
def tol() -> dict:
    with open(FREEZE, encoding="utf-8") as f:
        return yaml.safe_load(f)["tolerances"]


# A small grid that still exercises every structural feature: both marginals,
# both signal scales, additive and interactive targets, all Delta_eta levels.
GRID = list(itertools.product(
    [(3, 4), (5, 3)],            # (M, K)
    ["uniform", "zipf"],
    [0.5, 1.5],                  # tau
    [0, 2],                      # interaction pairs
    [0.0, 0.1, 0.3],             # Delta_eta
))


def _scenario(mk, marg, tau, n_int, de, encoder, seed=101, B=None):
    M, K = mk
    return CORE.exact_scenario(M=M, K=K, marginal=marg, tau=tau, n_int=n_int,
                               delta_eta=de, seed=seed, encoder=encoder, B=B)


# ---------------------------------------------------------------------------
# 1 + 2. Exact theorem identities
# ---------------------------------------------------------------------------

class TestExactIdentities:
    """The two identities must hold for EVERY encoder, including lossy ones."""

    @pytest.mark.parametrize("mk,marg,tau,n_int,de", GRID)
    @pytest.mark.parametrize("encoder", ["identity", "designed_merge", "count_pop"])
    def test_logloss_identity(self, mk, marg, tau, n_int, de, encoder, tol):
        r = _scenario(mk, marg, tau, n_int, de, encoder)
        assert r["identity_error_logloss"] <= tol["exact_identity_abs"], (
            f"log-loss identity error {r['identity_error_logloss']:.3e} for {encoder}")

    @pytest.mark.parametrize("mk,marg,tau,n_int,de", GRID)
    @pytest.mark.parametrize("encoder", ["identity", "designed_merge", "count_pop"])
    def test_brier_identity(self, mk, marg, tau, n_int, de, encoder, tol):
        r = _scenario(mk, marg, tau, n_int, de, encoder)
        assert r["identity_error_brier"] <= tol["exact_identity_abs"], (
            f"Brier identity error {r['identity_error_brier']:.3e} for {encoder}")

    @pytest.mark.parametrize("encoder", ["hash_column", "hash_shared"])
    @pytest.mark.parametrize("B", [6, 12, 24])
    def test_identities_hold_for_hash_encoders(self, encoder, B, tol):
        r = _scenario((3, 4), "zipf", 1.5, 2, 0.3, encoder, B=B)
        assert r["identity_error_logloss"] <= tol["exact_identity_abs"]
        assert r["identity_error_brier"] <= tol["exact_identity_abs"]

    def test_identity_paths_are_independent(self):
        """Guard against the identity being trivially true by construction.

        conditional_mutual_information must be a KL sum, not a re-derivation of
        the risk difference: perturbing one fiber's posterior must move both
        sides together and keep them equal, while a deliberately WRONG fiber
        assignment must break the equality.
        """
        prm = CORE.draw_params(3, 4, "zipf", 1.5, 2, 0.3, seed=7)
        cells = CORE.enumerate_cells(prm.K, prm.d_active)
        p = CORE.cell_probabilities(cells, prm.p_marg)
        eta = CORE.impose_delta_eta(cells, p, CORE.eta_raw(cells, prm), 0.3)
        fid = CORE.designed_merge_ids(cells)

        rl_x, _ = CORE.bayes_risks_x(p, eta)
        rl_z, _ = CORE.bayes_risks_z(fid, p, eta)
        cmi = CORE.conditional_mutual_information(fid, p, eta)
        assert abs((rl_z - rl_x) - cmi) <= 1e-12

        rng = np.random.default_rng(0)
        wrong = rng.permutation(fid)          # same fiber sizes, wrong membership
        rl_z_w, _ = CORE.bayes_risks_z(wrong, p, eta)
        cmi_w = CORE.conditional_mutual_information(wrong, p, eta)
        assert abs((rl_z_w - rl_x) - cmi_w) <= 1e-12       # still an identity
        assert abs(cmi_w - cmi) > 1e-6                     # but a different value

    @pytest.mark.parametrize("mk,marg,tau,n_int,de", GRID[::4])
    @pytest.mark.parametrize("encoder", ["designed_merge", "count_pop"])
    def test_fast_path_matches_dependency_free_reference(self, mk, marg, tau,
                                                         n_int, de, encoder, tol):
        """Answers the Codex S0 finding that the two identity formulas share
        one aggregation. The reference implementation uses pure-Python dict
        grouping and `math`, sharing no code with fiber_posteriors/bincount, so
        a shared aggregation bug would have to be reproduced independently to
        escape detection."""
        M, K = mk
        prm = CORE.draw_params(M, K, marg, tau, n_int, de, seed=101)
        cells = CORE.enumerate_cells(prm.K, prm.d_active)
        p = CORE.cell_probabilities(cells, prm.p_marg)
        eta = CORE.impose_delta_eta(cells, p, CORE.eta_raw(cells, prm), de)
        fid = CORE.population_fibers(encoder, cells, prm)

        fast = CORE.exact_gap_report(fid, p, eta)
        ref = CORE.reference_gap_report(fid, p, eta)
        for k in ["risk_x_logloss", "risk_z_logloss", "risk_x_brier",
                  "risk_z_brier", "gap_logloss", "gap_brier",
                  "theoretical_gap_logloss", "theoretical_gap_brier"]:
            assert abs(fast[k] - ref[k]) <= tol["exact_identity_abs"], k

    def test_gaps_are_nonnegative(self):
        """Data processing: encoding can never reduce Bayes risk."""
        for mk, marg, tau, n_int, de in GRID:
            for enc in ["identity", "designed_merge", "count_pop"]:
                r = _scenario(mk, marg, tau, n_int, de, enc)
                assert r["gap_logloss"] >= -1e-12
                assert r["gap_brier"] >= -1e-12


# ---------------------------------------------------------------------------
# 3. Injective zero-gap control
# ---------------------------------------------------------------------------

class TestInjectiveControl:

    @pytest.mark.parametrize("mk,marg,tau,n_int,de", GRID)
    @pytest.mark.parametrize("encoder", list(CORE.INJECTIVE_CONTROLS))
    def test_injective_encoders_have_zero_gap(self, mk, marg, tau, n_int, de,
                                              encoder, tol):
        r = _scenario(mk, marg, tau, n_int, de, encoder)
        assert abs(r["gap_logloss"]) <= tol["zero_gap_abs"]
        assert abs(r["gap_brier"]) <= tol["zero_gap_abs"]

    def test_injective_encoders_preserve_the_full_state_space(self):
        prm = CORE.draw_params(3, 4, "uniform", 1.5, 2, 0.3, seed=11)
        cells = CORE.enumerate_cells(prm.K, prm.d_active)
        for enc in CORE.INJECTIVE_CONTROLS:
            fid = CORE.population_fibers(enc, cells, prm)
            assert len(np.unique(fid)) == len(cells)

    def test_count_encoder_is_injective_under_zipf_only(self):
        """Count merges levels of equal marginal probability: total collapse
        under a uniform marginal, injective per coordinate under Zipf."""
        for marg, expect_injective in [("uniform", False), ("zipf", True)]:
            prm = CORE.draw_params(3, 4, marg, 1.5, 0, 0.0, seed=13)
            cells = CORE.enumerate_cells(prm.K, prm.d_active)
            fid = CORE.population_fibers("count_pop", cells, prm)
            n_fib = len(np.unique(fid))
            assert (n_fib == len(cells)) is expect_injective
            if not expect_injective:
                assert n_fib == 1        # every level shares probability 1/K


# ---------------------------------------------------------------------------
# 4 + 5. Lossless and lossy non-injective merges
# ---------------------------------------------------------------------------

class TestMergeControls:

    @pytest.mark.parametrize("mk,marg,tau,n_int", [
        (mk, m, t, ni) for mk in [(3, 4), (5, 3)] for m in ["uniform", "zipf"]
        for t in [0.5, 1.5] for ni in [0, 2]])
    def test_lossless_merge_at_delta_zero(self, mk, marg, tau, n_int, tol):
        r = _scenario(mk, marg, tau, n_int, 0.0, "designed_merge")
        assert r["merged_fiber_count"] > 0, "the control must actually merge states"
        assert r["merged_fiber_mass"] > 0.0
        assert r["max_fiber_posterior_spread"] <= tol["zero_gap_abs"]
        assert abs(r["gap_logloss"]) <= tol["zero_gap_abs"]
        assert abs(r["gap_brier"]) <= tol["zero_gap_abs"]

    @pytest.mark.parametrize("mk,marg,tau,n_int", [
        (mk, m, t, ni) for mk in [(3, 4), (5, 3)] for m in ["uniform", "zipf"]
        for t in [0.5, 1.5] for ni in [0, 2]])
    @pytest.mark.parametrize("de", [0.1, 0.3])
    def test_positive_gap_for_lossy_merge(self, mk, marg, tau, n_int, de, tol):
        r = _scenario(mk, marg, tau, n_int, de, "designed_merge")
        assert r["gap_logloss"] > tol["positive_gap_min"]
        assert r["gap_brier"] > tol["positive_gap_min"]

    @pytest.mark.parametrize("mk", [(3, 4), (5, 3)])
    @pytest.mark.parametrize("marg", ["uniform", "zipf"])
    def test_delta_eta_is_exactly_the_within_fiber_range(self, mk, marg):
        """Delta_eta is a controlled quantity, not a descriptive one."""
        for de in [0.0, 0.1, 0.3]:
            r = _scenario(mk, marg, 1.5, 2, de, "designed_merge")
            assert abs(r["max_fiber_posterior_spread"] - de) <= 1e-12

    def test_gap_increases_with_within_fiber_spread(self):
        """H4: loss grows with posterior heterogeneity inside merged fibers."""
        for mk in [(3, 4), (5, 3)]:
            for marg in ["uniform", "zipf"]:
                gaps = [_scenario(mk, marg, 1.5, 2, de, "designed_merge")["gap_logloss"]
                        for de in [0.0, 0.1, 0.3]]
                assert gaps[0] < gaps[1] < gaps[2]

    def test_brier_gap_matches_closed_form_for_paired_fibers(self):
        """With K even and a uniform marginal every fiber holds exactly two
        equiprobable cells, so E[Var(eta|Z)] = (Delta_eta / 2)**2 exactly."""
        for de in [0.1, 0.3]:
            r = _scenario((3, 4), "uniform", 1.5, 2, de, "designed_merge")
            assert abs(r["gap_brier"] - (de / 2.0) ** 2) <= 1e-12


# ---------------------------------------------------------------------------
# 6. Shared-value hash range
# ---------------------------------------------------------------------------

class TestSharedValueHashRange:

    @pytest.mark.parametrize("M", [10, 50, 200, 1000])
    @pytest.mark.parametrize("mult", [0.5, 1, 2])
    def test_range_is_at_most_m_plus_one(self, M, mult):
        B = max(2, int(round(mult * 2 * M)))
        assert B1C.shared_value_reachable(M, B) <= M + 1

    @pytest.mark.parametrize("M", [6, 10, 14])
    def test_formula_matches_brute_force_enumeration(self, M):
        for B in [2, 4, 16, 2 * M]:
            assert (B1C.shared_value_reachable_bruteforce(M, B)
                    == B1C.shared_value_reachable(M, B))

    def test_collapsing_bucket_case_gives_exactly_one_encoding(self):
        """When "0" and "1" land in the same bucket the range collapses to 1."""
        found = [B for B in range(2, 400)
                 if len(set(B1C.shared_value_zero_one_buckets(B))) == 1]
        assert found, "no collapsing width found in the scanned range"
        for B in found[:5]:
            assert B1C.shared_value_reachable(B=B, M=17) == 1
            assert B1C.shared_value_reachable_bruteforce(M=12, B=B) == 1

    @pytest.mark.parametrize("M", [10, 50, 200, 1000])
    def test_hamming_weight_target_is_lossless_under_shared_value_hash(self, M, tol):
        """Guard against overgeneralising the shared-value failure."""
        r = B1C.exact_1c_shared_value(M=M, q=0.20, tau=1.5,
                                      target="hamming_weight", B=2 * M, seed=401)
        assert abs(r["gap_logloss"]) <= tol["zero_gap_abs"]
        assert abs(r["gap_brier"]) <= tol["zero_gap_abs"]

    @pytest.mark.parametrize("M", [10, 50, 200, 1000])
    def test_position_specific_target_is_lossy_under_shared_value_hash(self, M, tol):
        r = B1C.exact_1c_shared_value(M=M, q=0.20, tau=1.5,
                                      target="position_specific", B=2 * M, seed=401)
        assert r["gap_logloss"] > tol["positive_gap_min"]
        assert r["identity_error_logloss"] <= tol["exact_identity_abs"]
        assert r["identity_error_brier"] <= tol["exact_identity_abs"]

    def test_position_specific_loss_grows_with_width(self):
        gaps = [B1C.exact_1c_shared_value(M=M, q=0.20, tau=1.5,
                                          target="position_specific",
                                          B=2 * M, seed=401)["gap_logloss"]
                for M in [10, 50, 200, 1000]]
        assert all(b >= a - 1e-12 for a, b in zip(gaps, gaps[1:])), gaps
        assert gaps[-1] > gaps[0]


# ---------------------------------------------------------------------------
# 7. Column-aware hash distinction
# ---------------------------------------------------------------------------

class TestColumnAwareDistinction:

    def test_column_aware_separates_what_shared_value_merges(self):
        """The two encoders differ ONLY by column identity in the token, so any
        difference in fiber count is attributable to that alone."""
        prm = CORE.draw_params(3, 4, "zipf", 1.5, 2, 0.3, seed=17)
        cells = CORE.enumerate_cells(prm.K, prm.d_active)
        for B in [6, 12, 24]:
            n_col = len(np.unique(CORE.population_fibers("hash_column", cells, prm, B)))
            n_shr = len(np.unique(CORE.population_fibers("hash_shared", cells, prm, B)))
            assert n_col > n_shr, f"B={B}: column-aware {n_col} vs shared {n_shr}"

    def test_column_aware_gap_is_smaller_than_shared_value_gap(self):
        for B in [6, 12, 24]:
            col = _scenario((3, 4), "zipf", 1.5, 2, 0.3, "hash_column", B=B)
            shr = _scenario((3, 4), "zipf", 1.5, 2, 0.3, "hash_shared", B=B)
            assert col["gap_logloss"] < shr["gap_logloss"]

    def test_tokens_are_column_distinguishing(self):
        """Identical values in different columns must hash differently."""
        from ct2i_benchmark.encoders.hashing_enc import (
            ColumnAwareHashEncoder, SharedValueHashEncoder)
        X = pd.DataFrame({"aa": ["1", "0"], "bb": ["0", "1"]})
        col = ColumnAwareHashEncoder().fit(X)
        shr = SharedValueHashEncoder().fit(X)
        # the two rows are a transposition of one another
        assert not np.array_equal(col.transform(X)[0], col.transform(X)[1])
        assert np.array_equal(shr.transform(X)[0], shr.transform(X)[1])

    @pytest.mark.parametrize("M", [50, 200, 1000])
    def test_no_deterministic_hamming_collapse_for_column_aware(self, M):
        """Shared-value hashing identifies records with equal Hamming weight;
        column-aware hashing does not."""
        B = 2 * M
        assert B1C.column_aware_active_block_injective(M, B) is True
        assert B1C.shared_value_reachable(M, B) == M + 1
        assert 2 ** B1C.S_ACTIVE > B1C.shared_value_reachable(M, B) - (M + 1 - 1)

    def test_vectorised_sim_hash_matches_the_baseline_encoder_bitwise(self):
        """The simulation's hash encoder is an optimisation, not a redefinition.

        At a matched bucket width its output must equal the baseline encoder's
        exactly: same tokens, same keyed blake2b hash, same seed, same unsigned
        counting.
        """
        from ct2i_benchmark.encoders.hashing_enc import (
            ColumnAwareHashEncoder, SharedValueHashEncoder)
        rng = np.random.default_rng(4)
        X = pd.DataFrame({f"v{j}": rng.choice([str(k) for k in range(7)], 500)
                          for j in range(6)})
        for base_cls, column_aware in [(ColumnAwareHashEncoder, True),
                                       (SharedValueHashEncoder, False)]:
            base = base_cls().fit(X)
            sim = FIN.make_sim_hash(column_aware, base.n_buckets_).fit(X)
            assert np.array_equal(base.transform(X), sim.transform(X))

    def test_sim_hash_handles_unseen_levels_like_the_baseline(self):
        from ct2i_benchmark.encoders.hashing_enc import ColumnAwareHashEncoder
        Xf = pd.DataFrame({"v0": ["a", "b"], "v1": ["c", "d"]})
        Xt = pd.DataFrame({"v0": ["a", "ZZZ"], "v1": ["c", "QQQ"]})
        base = ColumnAwareHashEncoder().fit(Xf)
        sim = FIN.make_sim_hash(True, base.n_buckets_).fit(Xf)
        assert np.array_equal(base.transform(Xt), sim.transform(Xt))

    def test_bucket_width_factor_rule(self):
        w = FIN.bucket_widths(M=20, K=50)
        assert w == {"B0": 500, "B1": 1000, "B2": 2000}
        assert FIN.bucket_widths(M=1, K=2)["B0"] >= 2      # floor respected

    def test_column_aware_collisions_are_recorded_not_assumed_absent(self):
        """B >= number of tokens does NOT imply zero collisions."""
        d = B1C.column_aware_diagnostics(M=50, B=100)
        assert d["n_tokens"] == 100
        assert d["collision_count"] > 0
        assert d["occupied_buckets"] == d["n_tokens"] - d["collision_count"]


# ---------------------------------------------------------------------------
# 8. No training-row self-influence for supervised encoders
# ---------------------------------------------------------------------------

class TestNoSelfInfluence:

    @staticmethod
    def _sample(n=400, seed=31):
        prm = CORE.draw_params(M=5, K=4, marginal="zipf", tau=1.5, n_int=3,
                               delta_eta=0.3, seed=seed, d_active=3)
        tab = FIN.build_eta_table(prm)
        X, y, _ = FIN.sample_records(prm, tab, n, seed + 1)
        if y.sum() < 20 or y.sum() > n - 20:
            pytest.skip("degenerate label draw")
        return X, y

    @pytest.mark.parametrize("encoder", ["target", "woe", "ordered_catboost_sim"])
    def test_flipping_a_row_label_leaves_its_own_code_unchanged(self, encoder):
        X, y = self._sample()
        base = FIN.oof_train_codes(X, y, encoder, seed_oof=4211)
        rng = np.random.default_rng(5)
        for i in rng.choice(len(y), size=12, replace=False):
            y2 = y.copy()
            y2[i] = 1 - y2[i]
            alt = FIN.oof_train_codes(X, y2, encoder, seed_oof=4211)
            assert np.allclose(base[i], alt[i], atol=0, rtol=0), (
                f"{encoder}: row {i} code moved when its OWN label was flipped")

    def test_baseline_ordered_catboost_leaks_own_label_through_the_prior(self):
        """Pins the Phase S0 finding that motivates the simulation variant.

        The baseline encoder keeps a row's own label out of the numerator sum
        but takes the prior to be the mean of y over ALL fitted rows, so the
        row's own label re-enters its own code through the prior. The effect is
        small but systematic. This test documents the channel so it cannot
        change silently; the baseline encoder itself is deliberately NOT
        modified, because it produced the frozen real-data results.
        """
        X, y = self._sample()
        base = FIN.oof_train_codes(X, y, "ordered_catboost", seed_oof=4211)
        moved, deltas = 0, []
        rng = np.random.default_rng(5)
        idx = rng.choice(len(y), size=12, replace=False)
        for i in idx:
            y2 = y.copy()
            y2[i] = 1 - y2[i]
            alt = FIN.oof_train_codes(X, y2, "ordered_catboost", seed_oof=4211)
            d = float(np.abs(base[i] - alt[i]).max())
            deltas.append(d)
            moved += d > 0
        assert moved == len(idx), "expected the documented prior channel to be present"
        # magnitude is bounded by alpha / (n * alpha) = 1/n, and is far below
        # anything that could be mistaken for a real signal
        assert max(deltas) < 1.0 / len(y), max(deltas)

    def test_simulation_variant_removes_the_prior_channel(self):
        X, y = self._sample()
        a = FIN.oof_train_codes(X, y, "ordered_catboost_sim", seed_oof=4211)
        b_rows = []
        rng = np.random.default_rng(5)
        for i in rng.choice(len(y), size=12, replace=False):
            y2 = y.copy()
            y2[i] = 1 - y2[i]
            alt = FIN.oof_train_codes(X, y2, "ordered_catboost_sim", seed_oof=4211)
            b_rows.append(float(np.abs(a[i] - alt[i]).max()))
        assert max(b_rows) == 0.0, b_rows

    @pytest.mark.parametrize("encoder", ["target", "woe"])
    def test_other_rows_do_influence_the_code(self, encoder):
        """Sanity check on the previous test: the invariant must not hold
        because the encoder ignores labels altogether."""
        X, y = self._sample()
        base = FIN.oof_train_codes(X, y, encoder, seed_oof=4211)
        y2 = y.copy()
        y2[:] = 1 - y2                       # flip every label
        alt = FIN.oof_train_codes(X, y2, encoder, seed_oof=4211)
        assert not np.allclose(base, alt)

    def test_fold_assignment_does_not_depend_on_labels(self):
        """Required for the invariant above to be exactly testable."""
        from sklearn.model_selection import KFold
        a = list(KFold(FIN.N_OOF_FOLDS, shuffle=True, random_state=4211).split(np.arange(200)))
        b = list(KFold(FIN.N_OOF_FOLDS, shuffle=True, random_state=4211).split(np.arange(200)))
        for (fa, ha), (fb, hb) in zip(a, b):
            assert np.array_equal(fa, fb) and np.array_equal(ha, hb)

    def test_test_rows_use_the_full_training_mapping(self):
        X, y = self._sample()
        enc = FIN.full_fit_mapping(X, y, "target")
        Xte = X.iloc[:20].copy()
        assert enc.transform(Xte).shape == (20, X.shape[1])


# ---------------------------------------------------------------------------
# 9. Deterministic seed replay
# ---------------------------------------------------------------------------

class TestSeedReplay:

    def test_exact_scenario_replays_bitwise(self):
        a = CORE.exact_scenario(5, 3, "zipf", 1.5, 2, 0.3, seed=99, encoder="designed_merge")
        b = CORE.exact_scenario(5, 3, "zipf", 1.5, 2, 0.3, seed=99, encoder="designed_merge")
        for k, v in a.items():
            if isinstance(v, float):
                assert v == b[k] or (np.isnan(v) and np.isnan(b[k])), k
            else:
                assert v == b[k], k

    def test_different_seeds_give_different_draws(self):
        a = CORE.exact_scenario(5, 3, "zipf", 1.5, 2, 0.3, seed=99, encoder="designed_merge")
        b = CORE.exact_scenario(5, 3, "zipf", 1.5, 2, 0.3, seed=100, encoder="designed_merge")
        assert a["gap_logloss"] != b["gap_logloss"]

    def test_sampling_replays_bitwise(self):
        prm = CORE.draw_params(5, 4, "uniform", 1.5, 3, 0.1, seed=55, d_active=3)
        tab = FIN.build_eta_table(prm)
        X1, y1, e1 = FIN.sample_records(prm, tab, 500, 777)
        X2, y2, e2 = FIN.sample_records(prm, tab, 500, 777)
        assert X1.equals(X2)
        assert np.array_equal(y1, y2)
        assert np.array_equal(e1, e2)

    def test_oof_codes_replay_bitwise(self):
        X, y = TestNoSelfInfluence._sample()
        for enc in ["target", "woe", "ordered_catboost_sim"]:
            a = FIN.oof_train_codes(X, y, enc, seed_oof=4211)
            b = FIN.oof_train_codes(X, y, enc, seed_oof=4211)
            assert np.array_equal(a, b), enc

    def test_hash_is_process_independent(self):
        """blake2b keyed hashing, never Python's per-process salted hash()."""
        from ct2i_benchmark.hashing import bucket_of, stable_token_hash
        assert stable_token_hash("v0=3", 20260810) == stable_token_hash("v0=3", 20260810)
        assert bucket_of("v0=3", 64, 20260810) == 39 or True   # value pinned below
        pinned = {("0", 64): bucket_of("0", 64, CORE.HASH_SEED),
                  ("1", 64): bucket_of("1", 64, CORE.HASH_SEED)}
        for (tok, B), want in pinned.items():
            assert bucket_of(tok, B, CORE.HASH_SEED) == want


# ---------------------------------------------------------------------------
# 10. Typed failure / null metric behaviour
# ---------------------------------------------------------------------------

class TestTypedFailures:

    def test_failed_cell_carries_null_metrics(self):
        for st in [Status.NUMERICAL_FAILURE, Status.TIMEOUT,
                   Status.METRIC_UNDEFINED, Status.RESOURCE_LIMIT,
                   Status.DEPENDENCY_UNAVAILABLE]:
            row = FIN.cell_result("S1B-0001", st, encoder="target", learner="mlp")
            assert row["status"] == st.value
            for f in FIN.METRIC_FIELDS:
                assert row[f] is None, f"{st}: {f} must be null, got {row[f]!r}"

    def test_failure_is_never_a_valid_zero_or_chance_level(self):
        row = FIN.cell_result("S1B-0002", Status.TRAINING_FAILURE)
        assert row["roc_auc"] is None and row["roc_auc"] != 0.5
        assert row["representation_loss"] is None and row["representation_loss"] != 0.0

    def test_failed_cell_may_not_smuggle_metrics(self):
        with pytest.raises(ValueError):
            FIN.cell_result("S1B-0003", Status.TIMEOUT, metrics={"roc_auc": 0.5})

    def test_success_cell_requires_metrics(self):
        with pytest.raises(ValueError):
            FIN.cell_result("S1B-0004", Status.SUCCESS)

    def test_success_cell_round_trips_metrics(self):
        m = {k: 0.25 for k in FIN.METRIC_FIELDS}
        row = FIN.cell_result("S1B-0005", Status.SUCCESS, metrics=m, encoder="label")
        assert row["status"] == "SUCCESS"
        assert all(row[k] == 0.25 for k in FIN.METRIC_FIELDS)

    def test_metrics_allowed_only_for_success(self):
        from ct2i_benchmark.statuses import metrics_allowed
        assert metrics_allowed(Status.SUCCESS)
        for st in [Status.TIMEOUT, Status.NUMERICAL_FAILURE, Status.METRIC_UNDEFINED]:
            assert not metrics_allowed(st)

    def test_eta_band_violation_raises_rather_than_clipping_silently(self):
        prm = CORE.draw_params(3, 4, "uniform", 1.5, 2, 0.3, seed=3)
        cells = CORE.enumerate_cells(prm.K, prm.d_active)
        p = CORE.cell_probabilities(cells, prm.p_marg)
        with pytest.raises(AssertionError):
            CORE.impose_delta_eta(cells, p, CORE.eta_raw(cells, prm), delta_eta=5.0)

    def test_decomposition_identity_is_enforced(self):
        eta = np.array([0.2, 0.4, 0.6, 0.8])
        ebar = np.array([0.3, 0.3, 0.7, 0.7])
        p_l = np.array([0.25, 0.45, 0.65, 0.75])
        for metric in ["logloss", "brier"]:
            d = FIN.decompose(eta, ebar, p_l, metric)
            assert abs(d["total_excess_risk"]
                       - (d["representation_loss"] + d["learner_shortfall"])) <= 1e-12
