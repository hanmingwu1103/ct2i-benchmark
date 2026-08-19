"""Phase A0 unit / property tests for the dense-signal Simulation 1B addendum.

Scope: SIMULATION ONLY, PREFLIGHT ONLY. Nothing in this module runs an addendum
cell, writes a result file, or touches a real dataset. It verifies that the
frozen addendum design (M = 5, K = 4, d = M = 5) is implementable, exactly
verifiable, and seed-disjoint from the completed arm BEFORE any cell is run.

Design authority: simulation-results-ct2i/01A_ADDENDUM_PROTOCOL_FREEZE.yaml.
Tolerances are read from the ORIGINAL frozen protocol
(simulation-results-ct2i/01_PROTOCOL_FREEZE.yaml), which the addendum inherits
verbatim, so no test here can silently use a looser bound than the committed one.

Why this arm is unusually verifiable: 4**5 = 1024 <= ENUM_CAP = 1e6, so the
FULL state space enumerates. Every population quantity -- for all 13 encoder
configurations, both hash encoders included -- is an exact population quantity
rather than a Monte Carlo estimate. Fourteen of the sixteen criteria below are
therefore exact assertions and eight are exhaustive over all 1024 states.

Criteria AT1-AT16 map one-to-one onto the classes below.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

from ct2i_benchmark.hashing import bucket_of                      # noqa: E402
from ct2i_benchmark.simulations import sim1_core as CORE          # noqa: E402
from ct2i_benchmark.simulations import sim1_design as DES         # noqa: E402
from ct2i_benchmark.simulations import sim1_finite as FIN         # noqa: E402
from ct2i_benchmark.statuses import Status                        # noqa: E402

import run_sim1b_finite as RUNNER                                 # noqa: E402

PKG = REPO / "simulation-results-ct2i"
FREEZE = PKG / "01_PROTOCOL_FREEZE.yaml"
SEED_MANIFEST = PKG / "03_SEED_MANIFEST.csv"
RAW_MANIFEST = PKG / "RAW_FREEZE_MANIFEST.json"

# ---------------------------------------------------------------------------
# The frozen addendum design, restated here so a drift between the YAML freeze
# and the tests is a visible edit in both places rather than a silent one.
# ---------------------------------------------------------------------------
M_ADD, K_ADD, D_ADD = 5, 4, 5
N_CELLS = K_ADD ** D_ADD                     # 1024, exactly enumerable
MARGINALS = ("uniform", "zipf")
TAUS = (0.5, 1.5)
N_INTS = (0, 3)                              # matched by COUNT to d=3 (decision D1)
DELTAS = (0.0, 0.1, 0.3)
N_TRAINS = (500, 5000)
REPS_ADD = 50
N_SCENARIOS_ADD = 48
ROWS_ADD = 182_400

# Seed namespace. Structurally disjoint: the largest seed realised anywhere in
# the completed run is 995,419,050 (03_SEED_MANIFEST.csv) and the largest
# DERIVED seed is that + 200,000, so a base of 2e9 cannot collide with any
# original seed or any seed derived from one. Disjointness is nevertheless
# asserted by enumeration in AT6 rather than argued.
SEED_BASE_1BD = 2_000_000_000
OOF_BASE_1BD = 91_211                        # original 1B uses 4211 + 17*replicate
TRAIN_DRAW_OFFSET = 100_000                  # inherited from the 1B runner
EVAL_DRAW_OFFSET = 200_000                   # inherited from the 1B runner


def addendum_block(marginal: str, tau: float, n_int: int) -> tuple:
    """Block key: same SHAPE and same exclusions as the frozen 1B block.

    (M, K, marginal, tau, interaction_pairs). delta_eta and n_train are
    EXCLUDED, which is what keeps the within-DGP contrasts paired.
    """
    return (M_ADD, K_ADD, marginal, tau, n_int)


def addendum_seed(block: tuple, replicate: int) -> int:
    """Addendum DGP seed. Same blake2b construction as `dgp_block_seed`, new base.

    Deliberately NOT routed through `sim1_core.dgp_block_seed`: adding a key to
    that module's SEED_BASE would edit the module that produced the frozen 1B
    output. The addendum owns its base offset in its own namespace (decision D3).
    """
    h = int.from_bytes(
        hashlib.blake2b(repr(tuple(block)).encode(), digest_size=4).digest(),
        "little")
    return SEED_BASE_1BD + 1000 * (h % 1_000_000) + int(replicate)


def addendum_oof_seed(replicate: int) -> int:
    return OOF_BASE_1BD + 17 * int(replicate)


def addendum_scenarios() -> list[dict]:
    """The 48 frozen addendum scenarios, in frozen enumeration order."""
    out = []
    for i, (marg, tau, ni, de, nt) in enumerate(
            itertools.product(MARGINALS, TAUS, N_INTS, DELTAS, N_TRAINS), start=1):
        blk = addendum_block(marg, tau, ni)
        out.append(dict(
            scenario_id=f"S1BD-{i:04d}", M=M_ADD, K=K_ADD, marginal=marg, tau=tau,
            n_int=ni, delta_eta=de, n_train=nt, block=blk,
            seeds=[addendum_seed(blk, r) for r in range(1, REPS_ADD + 1)]))
    return out


COLS = [f"v{j}" for j in range(M_ADD)]


@pytest.fixture(scope="module")
def tol() -> dict:
    with open(FREEZE, encoding="utf-8") as f:
        return yaml.safe_load(f)["tolerances"]


def _dgp(marginal="zipf", tau=1.5, n_int=3, delta=0.3, replicate=1):
    """One addendum DGP draw at d = M = 5, from the addendum seed rule."""
    blk = addendum_block(marginal, tau, n_int)
    seed = addendum_seed(blk, replicate)
    prm = CORE.draw_params(M_ADD, K_ADD, marginal, tau, n_int, delta, seed,
                           d_active=D_ADD)
    return prm, FIN.build_eta_table(prm), seed


def _all_cells_frame(tab) -> pd.DataFrame:
    """All 1024 states as the string frame the encoders consume."""
    return pd.DataFrame(tab.cells.astype(str), columns=COLS)


def _fibers_for_config(enc, Bw, mapping, tab) -> np.ndarray:
    """Exhaustive fiber partition of the FULL 1024-state space for one config."""
    if enc in DES.HASH_ENC:
        # hash fibers are data-independent; this is the runner's own route
        return CORE.group_ids(
            CORE.hash_codes(tab.cells, K_ADD, Bw, enc == "hash_column"))
    return CORE.group_ids(CORE.quantize(mapping.transform(_all_cells_frame(tab))))


def _reports_for_draw(marginal, tau, n_int, delta, n_train=5000, replicate=1):
    """Exact gap report for all 13 encoder configurations on one DGP draw."""
    prm, tab, seed = _dgp(marginal, tau, n_int, delta, replicate)
    X, y, _ = FIN.sample_records(prm, tab, n_train, seed + TRAIN_DRAW_OFFSET)
    out = {}
    for enc, Bw, lab in DES.encoder_configs("B", M_ADD, K_ADD):
        mapping = (FIN.make_sim_hash(enc == "hash_column", Bw).fit(X)
                   if enc in DES.HASH_ENC else FIN.full_fit_mapping(X, y, enc))
        fid = _fibers_for_config(enc, Bw, mapping, tab)
        rep = CORE.exact_gap_report(fid, tab.p_cell, tab.eta)
        rep["n_fibers_exhaustive"] = int(len(np.unique(fid)))
        out[(enc, lab)] = rep
    return out


# A structurally complete grid: both marginals, both signal scales, additive and
# interactive targets, all three Delta_eta levels. 24 draws x 13 configurations.
IDENTITY_GRID = list(itertools.product(MARGINALS, TAUS, N_INTS, DELTAS))


@pytest.fixture(scope="module")
def exact_reports() -> dict:
    return {g: _reports_for_draw(*g) for g in IDENTITY_GRID}


# ---------------------------------------------------------------------------
# AT1 - the full space enumerates exactly
# ---------------------------------------------------------------------------

class TestFullSpaceEnumeratesExactly:
    """AT1. exhaustive."""

    def test_cell_grid_shape_is_exactly_1024_by_5(self):
        cells = CORE.enumerate_cells(K_ADD, D_ADD)
        assert cells.shape == (N_CELLS, D_ADD)
        assert len(np.unique(cells, axis=0)) == N_CELLS      # all states distinct
        assert N_CELLS == 1024

    @pytest.mark.parametrize("marginal", MARGINALS)
    def test_cell_probabilities_sum_to_one(self, marginal):
        cells = CORE.enumerate_cells(K_ADD, D_ADD)
        p = CORE.cell_probabilities(cells, CORE.marginal_pmf(K_ADD, marginal))
        assert len(p) == N_CELLS
        assert abs(p.sum() - 1.0) <= 1e-12
        assert (p > 0).all()

    @pytest.mark.parametrize("marginal", MARGINALS)
    @pytest.mark.parametrize("delta", DELTAS)
    def test_eta_defined_at_every_one_of_the_1024_states(self, marginal, delta):
        _, tab, _ = _dgp(marginal=marginal, delta=delta)
        assert tab.eta.shape == (N_CELLS,)
        assert np.isfinite(tab.eta).all()
        assert tab.p_cell.shape == (N_CELLS,)

    def test_active_block_is_the_whole_record_at_d_equals_M(self):
        prm, tab, _ = _dgp()
        assert prm.d_active == M_ADD == D_ADD
        assert tab.cells.shape[1] == M_ADD


# ---------------------------------------------------------------------------
# AT2 - the coordinate-wise probe route is correct at d = 5
# ---------------------------------------------------------------------------

class TestEbarCoordinatewiseMatchesDirectAtD5:
    """AT2. exact, and the load-bearing optimisation of the whole arm.

    `ebar_coordinatewise` encodes d*K = 20 probe rows instead of all 1024
    cells. It is what makes the arm cheap. Its correctness was established at
    d = 3; it must be re-established at d = 5 before the addendum relies on it.
    """

    NONHASH = ["label", "onehot", "count", "target", "woe",
               "ordered_catboost_sim", "homals"]

    @pytest.mark.parametrize("marginal", MARGINALS)
    @pytest.mark.parametrize("n_train", N_TRAINS)
    @pytest.mark.parametrize("encoder", NONHASH)
    def test_probe_route_equals_direct_enumeration(self, marginal, n_train, encoder):
        prm, tab, seed = _dgp(marginal=marginal)
        X, y, _ = FIN.sample_records(prm, tab, n_train, seed + TRAIN_DRAW_OFFSET)
        mapping = FIN.full_fit_mapping(X, y, encoder)

        eb_probe, fid_probe = RUNNER.ebar_coordinatewise(mapping, tab, prm)
        fid_direct = CORE.group_ids(
            CORE.quantize(mapping.transform(_all_cells_frame(tab))))
        _, ebar_direct = CORE.fiber_posteriors(fid_direct, tab.p_cell, tab.eta)

        assert np.array_equal(
            CORE.group_ids(fid_probe.reshape(-1, 1)),
            CORE.group_ids(fid_direct.reshape(-1, 1))), (
            f"{encoder}: probe partition differs from the direct 1024-cell partition")
        assert np.array_equal(eb_probe, ebar_direct[fid_direct]), (
            f"{encoder}: probe ebar is not bitwise equal to the direct ebar")

    def test_probe_encodes_far_fewer_rows_than_the_direct_route(self):
        """The optimisation is real: 20 probe rows against 1024 states."""
        assert D_ADD * K_ADD == 20
        assert N_CELLS == 1024


# ---------------------------------------------------------------------------
# AT3 / AT4 - both theorem identities, all 13 configurations, exhaustively
# ---------------------------------------------------------------------------

class TestExactIdentitiesAllThirteenConfigsAtD5:
    """AT3, AT4. exact and exhaustive over all 1024 states.

    This is the addendum's headline verification asset: because the full space
    enumerates, BOTH hash encoders are IDENTIFIED_EXACT here, so the identities
    are checked on every configuration rather than only the coordinate-wise ones.
    """

    @pytest.mark.parametrize("grid", IDENTITY_GRID)
    def test_logloss_identity_holds_for_every_configuration(self, grid, exact_reports, tol):
        reps = exact_reports[grid]
        assert len(reps) == 13, f"expected 13 encoder configurations, got {len(reps)}"
        for key, r in reps.items():
            assert r["identity_error_logloss"] <= tol["exact_identity_abs"], (
                f"{key} at {grid}: log-loss identity error "
                f"{r['identity_error_logloss']:.3e}")

    @pytest.mark.parametrize("grid", IDENTITY_GRID)
    def test_brier_identity_holds_for_every_configuration(self, grid, exact_reports, tol):
        for key, r in exact_reports[grid].items():
            assert r["identity_error_brier"] <= tol["exact_identity_abs"], (
                f"{key} at {grid}: Brier identity error {r['identity_error_brier']:.3e}")

    def test_both_hash_encoders_are_covered_at_all_three_widths(self, exact_reports):
        keys = set(exact_reports[IDENTITY_GRID[0]])
        for enc in ("hash_column", "hash_shared"):
            for lab in ("B0", "B1", "B2"):
                assert (enc, lab) in keys

    def test_gaps_are_nonnegative_everywhere(self, exact_reports):
        """A representation gap is a nonnegative quantity; a negative one would
        mean the fiber algebra is wrong, not that an encoder helps."""
        for grid, reps in exact_reports.items():
            for key, r in reps.items():
                assert r["gap_logloss"] >= -1e-12, (key, grid, r["gap_logloss"])
                assert r["gap_brier"] >= -1e-12, (key, grid, r["gap_brier"])

    def test_bucket_widths_are_the_matched_d3_widths(self):
        """Widths depend on (M, K) only, never on d, so the hash contrast pairs."""
        assert DES.bucket_widths(M_ADD, K_ADD) == {"B0": 10, "B1": 20, "B2": 40}


# ---------------------------------------------------------------------------
# AT5 - injective encoders keep an exactly zero gap at d = 5
# ---------------------------------------------------------------------------

class TestInjectiveZeroGapAtD5:
    """AT5. exact, exhaustive. This one is a theorem consequence, so it is gated."""

    @pytest.mark.parametrize("grid", IDENTITY_GRID)
    @pytest.mark.parametrize("encoder", ["label", "onehot"])
    def test_injective_encoders_separate_all_1024_states(self, grid, encoder,
                                                         exact_reports, tol):
        r = exact_reports[grid][(encoder, "")]
        assert r["n_fibers_exhaustive"] == N_CELLS, (
            f"{encoder} at {grid}: {r['n_fibers_exhaustive']} fibers, expected 1024")
        assert r["gap_logloss"] <= tol["zero_gap_abs"]
        assert r["gap_brier"] <= tol["zero_gap_abs"]

    def test_population_injective_controls_also_hold(self, tol):
        for enc in ("identity", "label", "onehot"):
            r = CORE.exact_scenario(M_ADD, K_ADD, "zipf", 1.5, 3, 0.3, seed=2_000_000_001,
                                    encoder=enc, d_active=D_ADD)
            assert r["n_cells"] == N_CELLS
            assert abs(r["gap_logloss"]) <= tol["zero_gap_abs"]
            assert abs(r["gap_brier"]) <= tol["zero_gap_abs"]

    def test_a_merging_encoder_does_have_a_positive_gap(self, tol):
        """Sanity guard: the zero above must not be zero for everyone."""
        r = CORE.exact_scenario(M_ADD, K_ADD, "zipf", 1.5, 3, 0.3, seed=2_000_000_001,
                                encoder="hash_shared", B=20, d_active=D_ADD)
        assert r["gap_logloss"] > tol["positive_gap_min"]


# ---------------------------------------------------------------------------
# AT6 - seed disjointness from the completed run
# ---------------------------------------------------------------------------

class TestAddendumSeedsDisjointFromOriginal:
    """AT6. exact. Execution-prompt step 3 / plan task 1."""

    @staticmethod
    def _original_seeds() -> set[int]:
        man = pd.read_csv(SEED_MANIFEST)
        seeds: set[int] = set()
        for lo, hi in zip(man.seed_start, man.seed_end):
            seeds.update(range(int(lo), int(hi) + 1))
        return seeds

    def test_addendum_seed_set_is_disjoint_from_every_realised_seed(self):
        orig = self._original_seeds()
        add = {s for sc in addendum_scenarios() for s in sc["seeds"]}
        assert len(add) > 0
        assert add.isdisjoint(orig), sorted(add & orig)[:10]

    def test_derived_data_seeds_are_also_disjoint(self):
        """The training and evaluation draws use seed + 100k / + 200k."""
        orig = self._original_seeds()
        orig_derived = ({s + TRAIN_DRAW_OFFSET for s in orig}
                        | {s + EVAL_DRAW_OFFSET for s in orig})
        add = {s for sc in addendum_scenarios() for s in sc["seeds"]}
        add_derived = ({s + TRAIN_DRAW_OFFSET for s in add}
                       | {s + EVAL_DRAW_OFFSET for s in add})
        assert (add | add_derived).isdisjoint(orig | orig_derived)

    def test_oof_seed_namespace_is_disjoint(self):
        original = {4211 + 17 * r for r in range(1, 101)}
        addendum = {addendum_oof_seed(r) for r in range(1, REPS_ADD + 1)}
        assert original.isdisjoint(addendum)

    def test_disjointness_is_structural_not_accidental(self):
        """Every addendum seed exceeds every original seed by a wide margin."""
        orig = self._original_seeds()
        add = {s for sc in addendum_scenarios() for s in sc["seeds"]}
        assert min(add) > max(orig) + EVAL_DRAW_OFFSET

    def test_scenario_ids_use_a_separate_namespace(self):
        ids = [s["scenario_id"] for s in addendum_scenarios()]
        assert len(ids) == N_SCENARIOS_ADD == len(set(ids))
        assert all(i.startswith("S1BD-") for i in ids)
        existing = {s.scenario_id for s in DES.scenarios_1b()}
        assert not (set(ids) & existing)

    def test_grid_and_row_count_match_the_freeze(self):
        scen = addendum_scenarios()
        assert len(scen) == N_SCENARIOS_ADD
        light = len(DES.encoder_configs("B", M_ADD, K_ADD)) * 2
        heavy = sum(1 for e, _, lab in DES.encoder_configs("B", M_ADD, K_ADD)
                    if e in DES.HEAVY_SUBSET and lab in ("", "B1")) * 2
        rows_per_rep = (light + heavy) * 2                    # x 2 metrics
        assert light == 26 and heavy == 12 and rows_per_rep == 76
        assert rows_per_rep * REPS_ADD * N_SCENARIOS_ADD == ROWS_ADD


# ---------------------------------------------------------------------------
# AT7 - block pairing preserved (the invariant that saved criterion A8)
# ---------------------------------------------------------------------------

class TestAddendumBlockPairingPreserved:
    """AT7. exact."""

    @pytest.mark.parametrize("marginal", MARGINALS)
    @pytest.mark.parametrize("n_int", N_INTS)
    def test_parameter_draw_identical_across_delta_eta(self, marginal, n_int):
        blk = addendum_block(marginal, 1.5, n_int)
        seed = addendum_seed(blk, 3)
        prms = [CORE.draw_params(M_ADD, K_ADD, marginal, 1.5, n_int, de, seed,
                                 d_active=D_ADD) for de in DELTAS]
        for p in prms[1:]:
            assert np.array_equal(prms[0].a, p.a)
            for b0, b1 in zip(prms[0].b, p.b):
                assert np.array_equal(b0, b1)

    def test_seed_is_invariant_to_delta_eta_and_n_train(self):
        """Both contrasted factors are excluded from the block key."""
        base = addendum_seed(addendum_block("zipf", 1.5, 3), 7)
        for sc in addendum_scenarios():
            if sc["marginal"] == "zipf" and sc["tau"] == 1.5 and sc["n_int"] == 3:
                assert sc["seeds"][6] == base

    def test_different_blocks_give_different_seeds(self):
        seen = {addendum_seed(addendum_block(m, t, n), 1)
                for m in MARGINALS for t in TAUS for n in N_INTS}
        assert len(seen) == 8

    def test_replicate_still_varies_the_draw(self):
        blk = addendum_block("zipf", 1.5, 3)
        p1 = CORE.draw_params(M_ADD, K_ADD, "zipf", 1.5, 3, 0.3,
                              addendum_seed(blk, 1), d_active=D_ADD)
        p2 = CORE.draw_params(M_ADD, K_ADD, "zipf", 1.5, 3, 0.3,
                              addendum_seed(blk, 2), d_active=D_ADD)
        assert not np.array_equal(p1.a, p2.a)

    def test_interaction_pair_count_is_matched_and_saturation_is_not(self):
        """Decision D1, asserted so the confound cannot be forgotten.

        3 pairs is 100% of the C(3,2) = 3 available pairs at d = 3, and 30% of
        the C(5,2) = 10 available at d = 5. The COUNT is held fixed; the
        SATURATION is not. This is the addendum's disclosed confound.
        """
        assert len(CORE.interaction_pairs(3, 3)) == 3
        assert len(CORE.interaction_pairs(5, 3)) == 3
        assert len([(j, l) for j in range(3) for l in range(j + 1, 3)]) == 3
        assert len([(j, l) for j in range(5) for l in range(j + 1, 5)]) == 10
        # matching saturation instead would require 10 pairs, which is legal:
        assert len(CORE.interaction_pairs(5, 10)) == 10


# ---------------------------------------------------------------------------
# AT8 - nested n_train draw at d = 5
# ---------------------------------------------------------------------------

class TestNestedNTrainDraw:
    """AT8. exact. n = 500 must be the first 500 rows of the n = 5000 draw."""

    def test_small_sample_is_the_prefix_of_the_large_one(self):
        prm, tab, seed = _dgp()
        Xbig, ybig, ebig = FIN.sample_records(prm, tab, 5000, seed + TRAIN_DRAW_OFFSET)
        Xsm = Xbig.iloc[:500].reset_index(drop=True)
        Xbig2, ybig2, ebig2 = FIN.sample_records(prm, tab, 5000, seed + TRAIN_DRAW_OFFSET)
        assert Xbig.equals(Xbig2) and np.array_equal(ybig, ybig2)
        assert np.array_equal(ebig, ebig2)
        assert Xsm.equals(Xbig2.iloc[:500].reset_index(drop=True))
        assert np.array_equal(ybig[:500], ybig2[:500])

    def test_explicit_slicing_is_load_bearing_for_the_labels(self):
        """Measured, not assumed: X nests for free, y does NOT.

        `sample_records` draws the covariates with one `rng.choice(K, (n, M), p)`
        call and the labels with a later `rng.random(n)`, so under PCG64 the
        covariate block of an independent n=500 draw IS the prefix of the
        n=5000 draw (the covariate stream is consumed row-major and the first
        500*M variates coincide), while the label block is NOT: the n=5000 draw
        has consumed 25,000 covariate variates before reaching `rng.random`,
        the n=500 draw only 2,500. An independent 500-draw therefore agrees on
        X and eta and disagrees on y.

        Consequence for the addendum: the nested rule ("n=500 is the first 500
        rows of the n=5000 draw", frozen in `seeds.n_train_pairing`) must be
        implemented by explicit slicing, exactly as `run_sim1b_finite.py` does.
        Re-drawing at n=500 would silently unpair the two training-size arms on
        the labels. This is asserted so the addendum runner cannot regress it.
        """
        prm, tab, seed = _dgp()
        Xbig, ybig, ebig = FIN.sample_records(prm, tab, 5000, seed + TRAIN_DRAW_OFFSET)
        Xind, yind, eind = FIN.sample_records(prm, tab, 500, seed + TRAIN_DRAW_OFFSET)
        assert Xind.equals(Xbig.iloc[:500].reset_index(drop=True))
        assert np.array_equal(eind, ebig[:500])
        assert not np.array_equal(yind, ybig[:500]), (
            "labels coincided; the nesting rule would then be untestable")

    def test_eta_lookup_is_consistent_between_table_and_sample(self):
        prm, tab, seed = _dgp()
        X, y, eta_i = FIN.sample_records(prm, tab, 2000, seed + EVAL_DRAW_OFFSET)
        ids = tab.cell_ids(X.to_numpy().astype(np.int64)[:, :prm.d_active])
        assert np.array_equal(eta_i, tab.eta[ids])


# ---------------------------------------------------------------------------
# AT9 - the Delta_eta construction is exact at d = 5
# ---------------------------------------------------------------------------

class TestDeltaEtaConstructionExactAtD5:
    """AT9. exhaustive over all 512 designed-merge fibers of the 1024-state space."""

    @pytest.mark.parametrize("grid", IDENTITY_GRID)
    def test_every_merged_fiber_realises_delta_eta_exactly(self, grid):
        marginal, tau, n_int, delta = grid
        prm, tab, _ = _dgp(marginal, tau, n_int, delta)
        fid = CORE.designed_merge_ids(tab.cells)
        sizes = np.bincount(fid)
        assert sizes.min() == 2 and sizes.max() == 2 and len(sizes) == N_CELLS // 2
        worst = 0.0
        for f in range(len(sizes)):
            sel = fid == f
            worst = max(worst, abs(float(tab.eta[sel].max() - tab.eta[sel].min()) - delta))
        assert worst <= 1e-15, f"worst |range - Delta_eta| = {worst:.3e} at {grid}"

    @pytest.mark.parametrize("grid", IDENTITY_GRID)
    def test_eta_never_leaves_the_no_clipping_band(self, grid):
        marginal, tau, n_int, delta = grid
        _, tab, _ = _dgp(marginal, tau, n_int, delta)
        assert tab.eta.min() >= CORE.ETA_LO - 1e-12
        assert tab.eta.max() <= CORE.ETA_HI + 1e-12

    def test_designed_merge_is_lossless_at_delta_zero_and_lossy_above(self, tol):
        lossless = CORE.exact_scenario(M_ADD, K_ADD, "zipf", 1.5, 3, 0.0,
                                       seed=2_000_000_001, encoder="designed_merge",
                                       d_active=D_ADD)
        lossy = CORE.exact_scenario(M_ADD, K_ADD, "zipf", 1.5, 3, 0.3,
                                    seed=2_000_000_001, encoder="designed_merge",
                                    d_active=D_ADD)
        assert abs(lossless["gap_logloss"]) <= tol["zero_gap_abs"]
        assert lossy["gap_logloss"] > tol["positive_gap_min"]


# ---------------------------------------------------------------------------
# AT10 - the hash gap is identified at (M, K) = (5, 4), independently of d
# ---------------------------------------------------------------------------

class TestHashGapIdentifiedAtM5K4:
    """AT10. exact. This is what makes AD4 a falsifiable prediction."""

    def test_state_space_is_inside_the_enumeration_cap(self):
        assert K_ADD ** M_ADD == 1024
        assert 1024 <= CORE.ENUM_CAP == 1_000_000
        assert CORE.hash_gap_identified(M_ADD, K_ADD) is True

    def test_identification_does_not_depend_on_d(self):
        """`hash_gap_identified` reads M and K only; d never enters."""
        import inspect
        src = inspect.getsource(CORE.hash_gap_identified)
        assert "d" not in [p for p in inspect.signature(CORE.hash_gap_identified).parameters]
        assert "K ** M" in src

    @pytest.mark.parametrize("B", [10, 20, 40])
    @pytest.mark.parametrize("encoder", ["hash_column", "hash_shared"])
    def test_exact_full_space_gap_is_available_at_d5(self, encoder, B, tol):
        prm, _, _ = _dgp()
        r = CORE.exact_full_space_gap(prm, encoder, B, delta_eta=0.3)
        assert r["theoretical_gap_status"] == "IDENTIFIED_EXACT"
        assert r["n_cells"] == N_CELLS
        assert r["identity_error_logloss"] <= tol["exact_identity_abs"]
        assert r["identity_error_brier"] <= tol["exact_identity_abs"]


# ---------------------------------------------------------------------------
# AT11 - collisions and occupied buckets are exact, not assumed
# ---------------------------------------------------------------------------

class TestCollisionsAndBucketsExact:
    """AT11. exact, exhaustive over the 20 tokens and all 1024 states.

    NOTE for the A1 acceptance report: the 1B runner does NOT persist
    `collision_count` / `occupied_buckets` (both columns are NULL in
    05b_SIM1B_REPLICATE_RESULTS.parquet). The invariant is therefore asserted
    here on the hash layer itself, and the addendum criteria must not gate on
    persisted columns that the runner never writes.
    """

    @pytest.mark.parametrize("B", [10, 20, 40])
    @pytest.mark.parametrize("column_aware", [True, False])
    def test_bucket_table_matches_an_independent_recomputation(self, B, column_aware):
        table = CORE._hash_buckets(M_ADD, K_ADD, B, column_aware)
        want = np.empty_like(table)
        for j in range(M_ADD):
            name = f"v{j}"
            for k in range(K_ADD):
                tok = f"{len(name)}:{name}={k}" if column_aware else f"{k}"
                want[j, k] = bucket_of(tok, B, CORE.HASH_SEED)
        assert np.array_equal(table, want)

    @pytest.mark.parametrize("B,column_aware,n_tokens,occupied", [
        (10, True, 20, 8), (20, True, 20, 12), (40, True, 20, 16),
        (10, False, 4, 4), (20, False, 4, 4), (40, False, 4, 4)])
    def test_collision_counts_are_exactly_predictable(self, B, column_aware,
                                                      n_tokens, occupied):
        toks = sorted({(f"{len('v%d' % j)}:v{j}={k}" if column_aware else f"{k}")
                       for j in range(M_ADD) for k in range(K_ADD)})
        assert len(toks) == n_tokens
        buckets = {bucket_of(t, B, CORE.HASH_SEED) for t in toks}
        assert len(buckets) == occupied
        assert n_tokens - len(buckets) == n_tokens - occupied

    @pytest.mark.parametrize("B,column_aware,fibers", [
        (10, True, 240), (20, True, 363), (40, True, 768),
        (10, False, 56), (20, False, 56), (40, False, 56)])
    def test_fiber_counts_over_the_full_space_are_exact(self, B, column_aware, fibers):
        cells = CORE.enumerate_cells(K_ADD, D_ADD)
        fid = CORE.group_ids(CORE.hash_codes(cells, K_ADD, B, column_aware))
        assert int(len(np.unique(fid))) == fibers

    def test_column_aware_never_loses_more_than_shared_value(self, exact_reports):
        for grid, reps in exact_reports.items():
            for lab in ("B0", "B1", "B2"):
                assert (reps[("hash_column", lab)]["gap_logloss"]
                        <= reps[("hash_shared", lab)]["gap_logloss"] + 1e-12), (grid, lab)


# ---------------------------------------------------------------------------
# AT12 - no training-row self-influence at d = 5
# ---------------------------------------------------------------------------

class TestNoSelfInfluenceAtD5:
    """AT12. exact. The A12 invariant, re-established in the dense regime."""

    @staticmethod
    def _sample(n=400):
        prm, tab, seed = _dgp()
        X, y, _ = FIN.sample_records(prm, tab, n, seed + TRAIN_DRAW_OFFSET)
        assert 20 <= y.sum() <= n - 20
        return X, y

    @pytest.mark.parametrize("encoder", ["target", "woe", "ordered_catboost_sim"])
    def test_flipping_a_row_label_leaves_its_own_code_unchanged(self, encoder):
        X, y = self._sample()
        oof = addendum_oof_seed(1)
        base = FIN.oof_train_codes(X, y, encoder, seed_oof=oof)
        rng = np.random.default_rng(5)
        for i in rng.choice(len(y), size=10, replace=False):
            y2 = y.copy()
            y2[i] = 1 - y2[i]
            alt = FIN.oof_train_codes(X, y2, encoder, seed_oof=oof)
            assert np.array_equal(base[i], alt[i]), (
                f"{encoder}: row {i} code moved when its OWN label was flipped")

    @pytest.mark.parametrize("encoder", ["target", "woe"])
    def test_other_rows_do_influence_the_code(self, encoder):
        X, y = self._sample()
        oof = addendum_oof_seed(1)
        base = FIN.oof_train_codes(X, y, encoder, seed_oof=oof)
        alt = FIN.oof_train_codes(X, 1 - y, encoder, seed_oof=oof)
        assert not np.allclose(base, alt)


# ---------------------------------------------------------------------------
# AT13 - bitwise seed replay at d = 5 across all 13 configurations
# ---------------------------------------------------------------------------

class TestSeedReplayBitwiseAtD5:
    """AT13. exact."""

    def test_one_scenario_replays_bitwise_across_all_13_configurations(self):
        a = _reports_for_draw("zipf", 1.5, 3, 0.3, n_train=500, replicate=4)
        b = _reports_for_draw("zipf", 1.5, 3, 0.3, n_train=500, replicate=4)
        assert set(a) == set(b) and len(a) == 13
        for key in a:
            for field, va in a[key].items():
                vb = b[key][field]
                assert va == vb, f"{key}.{field}: {va!r} != {vb!r}"

    def test_a_different_replicate_gives_a_different_draw(self):
        a = _reports_for_draw("zipf", 1.5, 3, 0.3, n_train=500, replicate=4)
        b = _reports_for_draw("zipf", 1.5, 3, 0.3, n_train=500, replicate=5)
        assert a[("hash_shared", "B1")]["gap_logloss"] != b[("hash_shared", "B1")]["gap_logloss"]

    def test_eta_table_replays_bitwise(self):
        _, t1, _ = _dgp()
        _, t2, _ = _dgp()
        assert np.array_equal(t1.eta, t2.eta) and np.array_equal(t1.p_cell, t2.p_cell)


# ---------------------------------------------------------------------------
# AT14 - typed failures carry NULL metrics
# ---------------------------------------------------------------------------

class TestTypedFailureNulls:
    """AT14. exact. A blank is not a zero."""

    @pytest.mark.parametrize("st", [Status.NUMERICAL_FAILURE, Status.TIMEOUT,
                                    Status.METRIC_UNDEFINED, Status.RESOURCE_LIMIT,
                                    Status.TRAINING_FAILURE])
    def test_failed_addendum_cell_carries_null_metrics(self, st):
        row = FIN.cell_result("S1BD-0001", st, encoder="hash_shared", learner="mlp")
        assert row["status"] == st.value
        for f in FIN.METRIC_FIELDS:
            assert row[f] is None, f"{st}: {f} must be null, got {row[f]!r}"
        assert row["roc_auc"] != 0.5 and row["representation_loss"] != 0.0

    def test_failure_may_not_smuggle_metrics(self):
        with pytest.raises(ValueError):
            FIN.cell_result("S1BD-0002", Status.TIMEOUT, metrics={"roc_auc": 0.5})

    def test_success_requires_metrics(self):
        with pytest.raises(ValueError):
            FIN.cell_result("S1BD-0003", Status.SUCCESS)

    def test_eta_band_violation_raises_rather_than_clipping(self):
        prm, tab, _ = _dgp()
        with pytest.raises(AssertionError):
            CORE.impose_delta_eta(tab.cells, tab.p_cell,
                                  CORE.eta_raw(tab.cells, prm), delta_eta=5.0)


# ---------------------------------------------------------------------------
# AT15 - the decomposition identity on fitted cells at d = 5
# ---------------------------------------------------------------------------

class TestDecompositionIdentityAtD5:
    """AT15. tolerance (decomposition_identity_abs = 1e-9)."""

    @pytest.mark.parametrize("encoder,Bw", [("label", None), ("onehot", None),
                                            ("count", None), ("target", None),
                                            ("hash_column", 20), ("hash_shared", 20)])
    @pytest.mark.parametrize("metric", ["logloss", "brier"])
    def test_total_equals_representation_plus_shortfall(self, encoder, Bw, metric, tol):
        prm, tab, seed = _dgp()
        Xtr, ytr, _ = FIN.sample_records(prm, tab, 500, seed + TRAIN_DRAW_OFFSET)
        Xev, _, eta_ev = FIN.sample_records(prm, tab, 5000, seed + EVAL_DRAW_OFFSET)

        if encoder in DES.HASH_ENC:
            mapping = FIN.make_sim_hash(encoder == "hash_column", Bw).fit(Xtr)
            Ztr = mapping.transform(Xtr)
            fid = CORE.group_ids(CORE.hash_codes(tab.cells, K_ADD, Bw,
                                                 encoder == "hash_column"))
            _, eb = CORE.fiber_posteriors(fid, tab.p_cell, tab.eta)
            ebar_cells = eb[fid]
        else:
            Ztr = FIN.oof_train_codes(Xtr, ytr, encoder, addendum_oof_seed(1))
            mapping = FIN.full_fit_mapping(Xtr, ytr, encoder)
            ebar_cells, _ = RUNNER.ebar_coordinatewise(mapping, tab, prm)

        ev_ids = tab.cell_ids(Xev.to_numpy().astype(np.int64)[:, :prm.d_active])
        ebar_ev = ebar_cells[ev_ids]
        model = FIN.make_learner("logistic", seed=seed)
        model.fit(Ztr, ytr)
        p = FIN.predict_proba_chunked_multi(mapping, {"logistic": model}, Xev)["logistic"]

        d = FIN.decompose(eta_ev, ebar_ev, p, metric)
        resid = abs(d["total_excess_risk"]
                    - (d["representation_loss"] + d["learner_shortfall"]))
        assert resid <= tol["decomposition_identity_abs"], resid
        assert d["representation_loss"] >= -1e-12


# ---------------------------------------------------------------------------
# AT16 - the frozen raw outputs are byte-identical
# ---------------------------------------------------------------------------

class TestOriginalRawUnchanged:
    """AT16. exact. Run at the start AND at the end of Phase A0."""

    def test_every_frozen_raw_output_matches_its_recorded_sha256(self):
        manifest = json.loads(RAW_MANIFEST.read_text(encoding="utf-8"))
        assert len(manifest) == 5
        for name, rec in manifest.items():
            got = hashlib.sha256((PKG / name).read_bytes()).hexdigest()
            assert got == rec["sha256"], f"{name}: {got} != {rec['sha256']}"

    def test_raw_csv_directory_is_present_and_unmodified_in_row_count(self):
        raw = PKG / "raw" / "sim1b_replicates.csv"
        assert raw.exists()
        with open(raw, "rb") as f:
            n = sum(1 for _ in f)
        assert n == 1_094_400 + 1          # data rows + header

    def test_original_protocol_freeze_is_untouched_by_the_addendum(self):
        """The addendum owns a separate file; A1-A15 are not renumbered."""
        freeze = yaml.safe_load(FREEZE.read_text(encoding="utf-8"))
        assert set(freeze["acceptance_criteria"]) == {f"A{i}" for i in range(1, 16)}
        assert freeze["simulation_1b"]["factors"]["M"] == [5, 20]
        assert "addendum" not in FREEZE.read_text(encoding="utf-8").lower()
