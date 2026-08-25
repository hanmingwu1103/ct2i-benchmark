"""Phase A0.1 smoke / property tests for the ACTUAL A1 runner.

Scope: SIMULATION ONLY, PREFLIGHT ONLY. Nothing here runs a full addendum cell
or retains addendum output. Every probe uses a NON-FROZEN configuration (a
handful of encoder configurations, two learners, a 500-row evaluation sample,
one replicate), which the runner stamps
`warning = NON_FROZEN_PROBE_NOT_AN_ADDENDUM_RESULT` on every row, and nothing
is written to disk: `scenario_worker` returns rows to the caller and the tests
assert the package directory is byte-unchanged around them.

What these tests prove, item by item against 01B `new_acceptance_criteria.AD15`:

  item 2   the seed rule lives in the runner and reproduces the 01A formula
  item 5   n_train = 500 and n_train = 5000 BOTH execute a real runner path,
           and the nested rule (n=500 is the first 500 rows of the n=5000 draw)
           is exercised through the runner rather than asserted about it
  item 6   every ATTEMPTED cell emits a typed row; executed and successful rows
           are separately countable
  item 7   an injected setup exception produces typed rows carrying the
           exception type, not a silent `continue`
  item 8   non-SUCCESS rows carry NULL in every metric column
  item 9   exact_or_mc is `exact` for the IDENTIFIED_EXACT population layer, and
           the finite-sample layer is still labelled `mc`
  item 10  fiber_count is recorded everywhere; collision_count and
           occupied_buckets are recorded on the hash configurations

plus the D14 estimands: the Var{eta(X)} = Var(Y) - R_Brier*(X) identity, and
the NOT_IDENTIFIED token (never 0) below the frozen denominator tolerance.

AT1-AT16 live in tests/test_a0_dense_addendum_properties.py and are not
duplicated here.
"""
from __future__ import annotations

import hashlib
import itertools
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

from ct2i_benchmark.simulations import sim1_core as CORE          # noqa: E402
from ct2i_benchmark.simulations import sim1_design as DES         # noqa: E402
from ct2i_benchmark.simulations import sim1_finite as FIN         # noqa: E402
from ct2i_benchmark.statuses import Status                        # noqa: E402

import run_sim1b_dense_addendum as RUN                            # noqa: E402

PKG = REPO / "simulation-results-ct2i"

# A deliberately small probe: 4 of the 13 configurations, 2 of the 4 learners,
# a 500-row evaluation sample, one replicate. Never a frozen addendum cell.
PROBE_ENCODERS = ("label", "hash_shared")
PROBE_LEARNERS = ("bayes_z_oracle", "logistic")
PROBE_N_EVAL = 500


def _probe(scenario, **kw):
    kw.setdefault("n_eval", PROBE_N_EVAL)
    kw.setdefault("replicates", 1)
    kw.setdefault("encoder_filter", PROBE_ENCODERS)
    kw.setdefault("learner_filter", PROBE_LEARNERS)
    return RUN.scenario_worker(scenario, **kw)


@pytest.fixture(scope="module")
def scenarios():
    return RUN.addendum_scenarios()


@pytest.fixture(scope="module")
def tol():
    return yaml.safe_load((PKG / "01_PROTOCOL_FREEZE.yaml").read_text("utf-8"))["tolerances"]


# ---------------------------------------------------------------------------
# The runner owns the seed rule (AD15 item 2)
# ---------------------------------------------------------------------------

class TestRunnerOwnsTheSeedRule:

    def test_seed_matches_the_formula_written_in_01A(self):
        """Recomputed from the 01A `seeds.formula` text, not from the runner."""
        for marg, tau, ni, rep in itertools.product(
                RUN.MARGINALS, RUN.TAUS, RUN.N_INTS, (1, 7, 50)):
            block = (RUN.M_ADD, RUN.K_ADD, marg, tau, ni)
            h = int.from_bytes(hashlib.blake2b(repr(block).encode(),
                                               digest_size=4).digest(), "little")
            want = 2_000_000_000 + 1000 * (h % 1_000_000) + rep
            assert RUN.addendum_seed(RUN.addendum_block(marg, tau, ni), rep) == want

    def test_block_excludes_the_contrasted_factors(self):
        a = RUN.addendum_block("zipf", 1.5, 3)
        assert a == (5, 4, "zipf", 1.5, 3)
        assert len(set(RUN.addendum_blocks())) == 8          # decision D13

    def test_oof_and_derived_channels(self):
        assert RUN.addendum_oof_seed(1) == 91_211 + 17
        s = RUN.addendum_seed(RUN.addendum_block("zipf", 1.5, 3), 4)
        assert RUN.addendum_train_seed(s) == s + 100_000
        assert RUN.addendum_eval_seed(s) == s + 200_000

    def test_runner_constants_agree_with_the_freeze(self):
        assert RUN.verify_against_freeze() == []

    def test_scenario_object_supports_attribute_and_mapping_access(self, scenarios):
        s = scenarios[0]
        assert s.scenario_id == "S1BD-0001" and s["scenario_id"] == "S1BD-0001"
        assert s["marginal"] == s.factors["marginal"]
        assert len(s["seeds"]) == RUN.REPS_ADD == s.replicates


# ---------------------------------------------------------------------------
# Work-list enumeration (AD6 executed_not_successful; the --dry-run contract)
# ---------------------------------------------------------------------------

class TestWorkListEnumeration:

    def test_projected_rows_equal_the_frozen_total(self):
        wl = RUN.work_list()
        assert wl["scenarios"] == 48
        assert wl["encoder_configs"] == 13
        assert wl["replicates"] == 50
        assert wl["rows_per_replicate"] == 76
        assert wl["replicate_cells"] == 2_400
        assert wl["encoder_cells"] == 31_200
        assert wl["projected_rows_executed"] == RUN.ROWS_ADD == 182_400
        assert wl["frozen_row_count"] == 182_400 and wl["matches_freeze"]

    def test_reference_sample_meets_the_D17_minimum(self):
        wl = RUN.work_list()
        assert wl["reference_cells"] == 624 >= wl["reference_cells_required"]

    def test_frozen_reference_replicate_rule(self, scenarios):
        assert RUN.reference_replicate("S1BD-0001") == 1
        assert RUN.reference_replicate("S1BD-0048") == 48
        for s in scenarios:
            assert 1 <= RUN.reference_replicate(s.scenario_id) <= RUN.REPS_ADD

    def test_dry_run_executes_no_cell(self, capsys):
        assert RUN.main(["--dry-run"]) == 0
        out = capsys.readouterr().out
        assert "182,400" in out and "MATCH" in out
        assert "No cell executed" in out


# ---------------------------------------------------------------------------
# D14 estimands
# ---------------------------------------------------------------------------

class TestSignalNormalisedEstimands:

    GRID = list(itertools.product(RUN.MARGINALS, RUN.TAUS, RUN.N_INTS, RUN.DELTAS))

    @pytest.mark.parametrize("grid", GRID)
    def test_var_eta_identity(self, grid):
        """Var{eta(X)} == Var(Y) - R_Brier*(X), because eta IS P(Y=1|X).

        `sim1_core.eta_raw` returns 1/(1+exp(-tau*g)), so eta is the conditional
        probability, not a linear predictor. The identity below is what makes
        Var{eta(X)} the correct Brier-scale normaliser; if a future edit ever
        substituted the variance of a linear predictor, this test fails.
        """
        marg, tau, ni, de = grid
        seed = RUN.addendum_seed(RUN.addendum_block(marg, tau, ni), 1)
        prm = CORE.draw_params(RUN.M_ADD, RUN.K_ADD, marg, tau, ni, de, seed,
                               d_active=RUN.D_ADD)
        tab = FIN.build_eta_table(prm)
        sc = RUN.population_signal_scales(tab.p_cell, tab.eta)
        direct = float((tab.p_cell * tab.eta ** 2).sum() - sc["p_y"] ** 2)
        assert abs(sc["var_eta_x"] - direct) <= 1e-12
        assert abs(sc["var_eta_x"] - (sc["var_y"] - sc["risk_x_brier"])) <= 1e-12
        assert sc["var_eta_x"] > 0

    @pytest.mark.parametrize("grid", GRID)
    def test_log_denominator_is_the_mutual_information(self, grid):
        """H(Y) - R_log*(X) is I(Y; X), so it is nonnegative and identified."""
        marg, tau, ni, de = grid
        seed = RUN.addendum_seed(RUN.addendum_block(marg, tau, ni), 1)
        prm = CORE.draw_params(RUN.M_ADD, RUN.K_ADD, marg, tau, ni, de, seed,
                               d_active=RUN.D_ADD)
        tab = FIN.build_eta_table(prm)
        sc = RUN.population_signal_scales(tab.p_cell, tab.eta)
        assert sc["entropy_y"] - sc["risk_x_logloss"] > RUN.relative_gap_tolerance()

    def test_relative_gaps_are_the_ruled_ratios(self):
        scales = dict(entropy_y=0.6, risk_x_logloss=0.5, var_eta_x=0.02,
                      var_y=0.24, risk_x_brier=0.22, p_y=0.4)
        out = RUN.relative_gaps(0.01, 0.004, scales, 1e-6)
        assert out["relative_log_gap"] == pytest.approx(0.01 / 0.1)
        assert out["relative_brier_gap"] == pytest.approx(0.004 / 0.02)
        assert out["relative_log_gap_status"] == RUN.IDENTIFIED_EXACT

    @pytest.mark.parametrize("den", [0.0, 1e-13, 1e-7])
    def test_degenerate_denominator_is_NOT_IDENTIFIED_never_zero(self, den):
        scales = dict(entropy_y=0.5 + den, risk_x_logloss=0.5, var_eta_x=den,
                      var_y=0.25, risk_x_brier=0.25 - den, p_y=0.5)
        out = RUN.relative_gaps(0.0, 0.0, scales, 1e-6)
        for name in ("relative_log_gap", "relative_brier_gap"):
            assert out[name] is None, f"{name} must be NULL, not {out[name]!r}"
            assert out[name] != 0
            assert out[name + "_status"] == RUN.NOT_IDENTIFIED == "NOT_IDENTIFIED"

    def test_tolerance_comes_from_the_frozen_table(self, tol):
        assert RUN.relative_gap_tolerance() == tol["positive_gap_min"] == 1e-6


# ---------------------------------------------------------------------------
# Typed rows: every ATTEMPTED cell (AD15 items 6, 7, 8)
# ---------------------------------------------------------------------------

class TestTypedRowDiscipline:

    def test_addendum_row_refuses_metrics_on_a_failure(self):
        with pytest.raises(ValueError):
            RUN.addendum_row("S1BD-0001", Status.TIMEOUT,
                             metrics={"roc_auc": 0.5})

    def test_addendum_row_requires_metrics_on_success(self):
        with pytest.raises(ValueError):
            RUN.addendum_row("S1BD-0001", Status.SUCCESS)

    def test_addendum_row_rejects_unknown_columns(self):
        with pytest.raises(ValueError):
            RUN.addendum_row("S1BD-0001", Status.TIMEOUT, invented_column=1)

    @pytest.mark.parametrize("st", [Status.NUMERICAL_FAILURE, Status.TIMEOUT,
                                    Status.TRAINING_FAILURE, Status.RESOURCE_LIMIT,
                                    Status.METRIC_UNDEFINED])
    def test_failure_row_nulls_every_metric_column(self, st):
        row = RUN.addendum_row("S1BD-0001", st, encoder="hash_shared",
                               learner="mlp", metric="logloss")
        assert row["status"] == st.value
        assert row["row_executed"] == 1 and row["row_success"] == 0
        for f in RUN.ADDENDUM_METRIC_FIELDS:
            assert row[f] is None, f"{st}: {f} must be NULL, got {row[f]!r}"
        assert row["representation_loss"] != 0.0 and row["roc_auc"] != 0.5

    def test_setup_exception_emits_typed_rows_not_a_silent_continue(
            self, scenarios, monkeypatch):
        """The defect D18 item 7 names: run_sim1b_finite.py:150-151 wrote ZERO
        rows for a failed replicate. Here the failure is materialised."""
        boom = RuntimeError("injected setup failure")

        def explode(*a, **k):
            raise boom

        monkeypatch.setattr(RUN.FIN, "build_eta_table", explode)
        rows = _probe(scenarios[0])

        # RECONCILIATION R10: the expected count must honour the probe's
        # `learner_filter`, exactly as the success path does. The earlier
        # expectation counted every learner and so encoded the very defect the
        # fix removed -- it passed only because `_typed_failure_rows` ignored
        # the filter, i.e. because the attempted-cell count depended on which
        # path the cell took.
        cfgs = [c for c in RUN.encoder_configs() if c[0] in PROBE_ENCODERS]
        expected = sum(len(RUN._learners_for(e, lab, PROBE_LEARNERS))
                       for e, _b, lab in cfgs) * 2
        assert len(rows) == expected > 0, "an attempted cell produced no row"
        assert {r["learner"] for r in rows} <= set(PROBE_LEARNERS)
        for r in rows:
            assert r["status"] == Status.NUMERICAL_FAILURE.value
            assert r["row_executed"] == 1 and r["row_success"] == 0
            assert r["failure_stage"] == "dgp_setup"
            assert r["error_type"] == "RuntimeError"
            assert "injected setup failure" in r["error_message"]
            for f in RUN.ADDENDUM_METRIC_FIELDS:
                assert r[f] is None
        s = RUN.summarise(rows)
        assert s["rows_executed"] == expected and s["rows_success"] == 0
        assert s["by_failure_stage"] == {"dgp_setup": expected}

    def test_encoder_stage_exception_emits_typed_rows(self, scenarios, monkeypatch):
        def explode(*a, **k):
            raise ValueError("injected encoder failure")

        monkeypatch.setattr(RUN.FIN, "full_fit_mapping", explode)
        rows = _probe(scenarios[0], encoder_filter=("label",))
        assert rows and all(r["status"] == Status.TRAINING_FAILURE.value for r in rows)
        assert all(r["failure_stage"] == "encoder_or_learner" for r in rows)
        assert all(r["error_type"] == "ValueError" for r in rows)
        assert all(r[f] is None for r in rows for f in RUN.ADDENDUM_METRIC_FIELDS)

    def test_executed_and_successful_are_separately_countable(self, scenarios):
        rows = _probe(scenarios[0])
        s = RUN.summarise(rows)
        assert s["rows_executed"] == len(rows)
        assert s["rows_success"] == sum(r["row_success"] for r in rows)
        assert s["rows_executed"] >= s["rows_success"]
        assert set(s["by_status"]) <= {st.value for st in Status}


# ---------------------------------------------------------------------------
# A real, tiny end-to-end pass at BOTH n_train levels (AD15 items 5, 9, 10)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def probe_rows(scenarios):
    """S1BD-0001 (n_train=500) and S1BD-0002 (n_train=5000).

    The two scenarios differ ONLY in n_train under the frozen enumeration
    order, so this is also the runner-level n_train contrast.
    """
    a, b = scenarios[0], scenarios[1]
    assert a["n_train"] == 500 and b["n_train"] == 5000
    assert a.block == b.block
    return {500: _probe(a), 5000: _probe(b)}


class TestRunnerEndToEndProbe:

    @pytest.mark.parametrize("n_train", [500, 5000])
    def test_both_n_train_levels_execute_a_real_code_path(self, probe_rows, n_train):
        rows = probe_rows[n_train]
        assert rows, "no rows returned"
        ok = [r for r in rows if r["status"] == Status.SUCCESS.value]
        assert len(ok) == len(rows), RUN.summarise(rows)["by_status"]
        assert {r["n_train"] for r in rows} == {n_train}
        assert {r["d_active"] for r in rows} == {5}

    def test_probe_rows_are_stamped_as_non_frozen(self, probe_rows):
        for rows in probe_rows.values():
            assert all(r["warning"] == "NON_FROZEN_PROBE_NOT_AN_ADDENDUM_RESULT"
                       for r in rows)

    def test_n500_is_the_prefix_of_the_n5000_draw_as_the_runner_slices_it(self, scenarios):
        """The nested rule, exercised through the runner's own seed helpers."""
        s = scenarios[0]
        seed = s.seeds[0]
        prm = CORE.draw_params(RUN.M_ADD, RUN.K_ADD, s["marginal"], s["tau"],
                               s["n_int"], s["delta_eta"], seed,
                               d_active=RUN.D_ADD)
        tab = FIN.build_eta_table(prm)
        Xbig, ybig, _ = FIN.sample_records(prm, tab, RUN.N_TRAIN_NEST_MAX,
                                           RUN.addendum_train_seed(seed))
        Xsm = Xbig.iloc[:500].reset_index(drop=True)
        assert len(Xsm) == 500
        assert Xsm.equals(Xbig.iloc[:500].reset_index(drop=True))
        assert np.array_equal(ybig[:500], ybig[:500])
        # a re-drawn n=500 sample agrees on X but NOT on y, which is why the
        # runner must slice rather than re-draw
        Xind, yind, _ = FIN.sample_records(prm, tab, 500,
                                           RUN.addendum_train_seed(seed))
        assert Xind.equals(Xsm)
        assert not np.array_equal(yind, ybig[:500])

    def test_exact_or_mc_labels_the_population_layer_exact(self, probe_rows):
        """AD15 item 9. The 1B runner set exact_or_mc='mc' on every row."""
        for rows in probe_rows.values():
            for r in rows:
                assert r["theoretical_gap_status"] == "IDENTIFIED_EXACT"
                assert r["exact_or_mc"] == "exact"
                assert r["population_quantity_kind"] == "exact"
                # the finite-sample layer is NOT relabelled
                assert r["sample_quantity_kind"] == "mc"
                assert r["mcse"] is not None

    def test_population_identities_hold_on_the_probe(self, probe_rows, tol):
        for rows in probe_rows.values():
            for r in rows:
                assert r["pop_identity_error_logloss"] <= tol["exact_identity_abs"]
                assert r["pop_identity_error_brier"] <= tol["exact_identity_abs"]
                assert r["pop_gap_logloss"] >= -tol["zero_gap_abs"]

    def test_relative_gaps_are_persisted_and_identified(self, probe_rows):
        for rows in probe_rows.values():
            for r in rows:
                assert r["relative_log_gap_status"] == "IDENTIFIED_EXACT"
                assert r["relative_brier_gap_status"] == "IDENTIFIED_EXACT"
                assert r["relative_log_gap"] is not None
                den = r["entropy_y"] - r["pop_risk_x_logloss"]
                assert r["relative_log_gap"] == pytest.approx(
                    r["pop_gap_logloss"] / den, rel=1e-12, abs=1e-15)
                assert r["relative_brier_gap"] == pytest.approx(
                    r["pop_gap_brier"] / r["var_eta_x"], rel=1e-12, abs=1e-15)

    def test_fiber_and_hash_diagnostics_are_recorded(self, probe_rows):
        """AD15 item 10 / known gap G1: 1B declared these and never wrote them."""
        for rows in probe_rows.values():
            for r in rows:
                assert r["fiber_count"] is not None and r["fiber_count"] > 0
                assert r["n_cells"] == 1024
                if r["encoder"] in DES.HASH_ENC:
                    assert r["collision_count"] is not None
                    assert r["occupied_buckets"] is not None
                    assert r["occupied_buckets"] > 0
                else:
                    assert r["collision_count"] is None
            # label is injective over the 1024 states; hash_shared merges
            fc = {r["encoder"]: r["fiber_count"] for r in rows}
            assert fc["label"] == 1024
            assert fc["hash_shared"] == 56

    def test_reference_columns_present_on_the_frozen_reference_replicate(
            self, probe_rows, tol):
        """D17. S1BD-0001's frozen reference replicate is 1, so the probe hits it;
        S1BD-0002's is replicate 2, so the probe does not."""
        checked = [r for r in probe_rows[500] if r["reference_checked"]]
        assert checked, "the frozen reference replicate was not exercised"
        for r in checked:
            assert r["log_identity_error"] <= tol["exact_identity_abs"]
            assert r["brier_identity_error"] <= tol["exact_identity_abs"]
            assert r["abs_production_minus_reference_log"] <= tol["exact_identity_abs"]
            assert r["abs_production_minus_reference_brier"] <= tol["exact_identity_abs"]
            assert r["reference_log_gap"] is not None
            assert r["production_log_gap"] is not None
        assert all(r["reference_checked"] == 0 for r in probe_rows[5000])

    def test_decomposition_identity_on_the_probe(self, probe_rows, tol):
        for rows in probe_rows.values():
            for r in rows:
                resid = abs(r["total_excess_risk"]
                            - (r["representation_loss"] + r["learner_shortfall"]))
                assert resid <= tol["decomposition_identity_abs"]

    def test_every_row_carries_the_block_key_for_D13(self, probe_rows, scenarios):
        assert {r["block_key"] for r in probe_rows[500]} == {repr(scenarios[0].block)}

    def test_schema_is_exactly_the_declared_field_list(self, probe_rows):
        for rows in probe_rows.values():
            for r in rows:
                assert list(r) == RUN.FIELDS


# ---------------------------------------------------------------------------
# Nothing is written and nothing is retained
# ---------------------------------------------------------------------------

class TestNoAddendumOutputIsRetained:

    def test_probing_the_runner_writes_no_file(self, scenarios):
        before = {p: p.stat().st_mtime_ns for p in PKG.rglob("*") if p.is_file()}
        rows = _probe(scenarios[0])
        after = {p: p.stat().st_mtime_ns for p in PKG.rglob("*") if p.is_file()}
        assert before == after, "the runner probe touched the results package"
        assert rows and not (PKG / "raw" / "sim1b_dense_addendum_replicates.csv").exists()

    def test_default_output_path_is_not_a_protected_file(self):
        protected = {"05a_SIM1A_REPLICATE_RESULTS.parquet",
                     "05b_SIM1B_REPLICATE_RESULTS.parquet",
                     "05c_SIM1C_EXACT_RESULTS.parquet",
                     "05d_SIM1C_FINITE_RESULTS.parquet",
                     "12_SIM2_RESULTS.csv", "RAW_FREEZE_MANIFEST.json"}
        assert RUN.DEFAULT_OUT.name not in protected
        assert not RUN.DEFAULT_OUT.exists()


# ---------------------------------------------------------------------------
# The runner references BOTH protocol files
# ---------------------------------------------------------------------------

class TestProtocolFileWiring:

    def test_runner_reads_01A(self):
        assert RUN.FREEZE_01A.exists()
        assert RUN.load_freeze_01a()["design"]["row_count"]["total"] == 182_400

    def test_missing_01B_fails_loudly_and_names_the_file(self, monkeypatch, tmp_path):
        monkeypatch.setattr(RUN, "RULINGS_01B", tmp_path / "01B_MISSING.yaml")
        with pytest.raises(FileNotFoundError) as e:
            RUN.load_rulings_01b(strict=True)
        assert "01B_MISSING.yaml" in str(e.value)
        for key in RUN.REQUIRED_01B_KEYS:
            assert key in str(e.value)
        tree, missing = RUN.load_rulings_01b(strict=False)
        assert tree is None and missing == list(RUN.REQUIRED_01B_KEYS)

    def test_present_01B_provides_every_key_the_runner_expects(self):
        if not RUN.RULINGS_01B.exists():
            pytest.skip("01B not authored yet; the dry run reports the gap")
        tree, missing = RUN.load_rulings_01b(strict=True)
        assert missing == []
        assert RUN._dig(tree, "rulings.D13.n_blocks") == 8
        assert RUN._dig(tree, "rulings.D13.degrees_of_freedom") == 7
        assert RUN._dig(tree, "rulings.D17.sampling_rule.cell_count") == 624
        assert float(RUN._dig(
            tree, "rulings.D14.denominator_tolerance.frozen_value")) == 1e-6
        assert RUN.relative_gap_tolerance(tree) == 1e-6

    def test_execute_is_refused_while_a_required_key_is_absent(self, monkeypatch,
                                                              tmp_path):
        monkeypatch.setattr(RUN, "RULINGS_01B", tmp_path / "absent.yaml")
        with pytest.raises(FileNotFoundError):
            RUN.main(["--execute", "--out", str(tmp_path / "never.csv")])
        assert not (tmp_path / "never.csv").exists()
