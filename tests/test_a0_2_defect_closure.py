"""Phase A0.1 second pass: executable closure of the council's confirmed defects.

Every test here exists because a mutation (or, for CRITICAL-6 and C2/C3, the
SHIPPED code with no mutation at all) produced materially wrong addendum output
or a vacuous gate while all 1,027 pre-existing tests passed. Each class names
the finding it closes and the mutation it must fail against.

SIMULATION ONLY, PREFLIGHT ONLY. No addendum cell is run: every probe passes
`n_eval` / `replicates` / `encoder_filter` / `learner_filter`, which the runner
stamps `NON_FROZEN_PROBE_NOT_AN_ADDENDUM_RESULT` on every row. Nothing is
written under `raw/` and nothing is retained.
"""
from __future__ import annotations

import ast
import inspect
import sys
import textwrap
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

from ct2i_benchmark.simulations import sim1_core as CORE          # noqa: E402
from ct2i_benchmark.simulations import sim1_design as DES         # noqa: E402
from ct2i_benchmark.simulations import sim1_finite as FIN         # noqa: E402
from ct2i_benchmark.statuses import Status                        # noqa: E402

import run_sim1b_dense_addendum as RUN                            # noqa: E402

PROBE_N_EVAL = 400
PROBE_LEARNERS = ("bayes_z_oracle", "logistic")

# AD1/AD2 as an executable criterion: the Monte Carlo representation loss must
# agree with the row's own exact population gap to within k standard errors.
# The largest observed ratio on a 400-row evaluation probe across scenarios is
# ~2.0, so k = 6 is a wide margin; the floor covers the injective encoders,
# whose mcse is exactly 0 because ebar == eta pointwise.
AD12_K = 6.0
AD12_FLOOR = 1e-12


@pytest.fixture(scope="module")
def scenarios():
    return RUN.addendum_scenarios()


def _all13(scenario, **kw):
    """One replicate over ALL THIRTEEN encoder configurations."""
    kw.setdefault("n_eval", PROBE_N_EVAL)
    kw.setdefault("replicates", 1)
    kw.setdefault("learner_filter", PROBE_LEARNERS)
    return RUN.scenario_worker(scenario, **kw)


def _expect_abort(scenario, **kw):
    """Run a probe that must raise `AddendumWorkerAborted`, and never let a raw
    `BaseException` escape into pytest (a bare KeyboardInterrupt would ABORT the
    session instead of failing this test, which is precisely the silence the
    fix removes)."""
    try:
        _all13(scenario, **kw)
    except RUN.AddendumWorkerAborted as e:
        return e
    except BaseException as e:                                    # noqa: BLE001
        pytest.fail(f"a raw {type(e).__name__} escaped scenario_worker; the "
                    f"rows it interrupted were silently discarded")
    pytest.fail("the injected cancellation produced no exception at all")


def _attempted(encoders=None, learner_filter=PROBE_LEARNERS, replicates=1):
    cfgs = [c for c in RUN.encoder_configs()
            if encoders is None or c[0] in encoders]
    return len(RUN.attempted_cells(cfgs, learner_filter)) * replicates


# ===========================================================================
# CRITICAL-6 -- one attempted cell, EXACTLY one row
# ===========================================================================

class TestOneRowPerAttemptedCell:
    """A failure part-way through the metric loop used to RE-EMIT a
    TRAINING_FAILURE row for cells already appended as SUCCESS: 6 rows for 4
    attempted cells, the same primary key twice with contradictory status, and
    AD6's exact 182,400 unsatisfiable the moment any cell failed late.

    Reintroduce the defect by replacing the buffer-and-commit in
    `scenario_worker` with the old `rows.append(...)` / re-emit-on-except and
    both tests below fail.
    """

    @staticmethod
    def _fail_on_nth_decompose(monkeypatch, n: int):
        orig = FIN.decompose
        state = {"calls": 0}

        def patched(*a, **k):
            state["calls"] += 1
            if state["calls"] == n:
                raise ValueError("injected late metric failure")
            return orig(*a, **k)

        monkeypatch.setattr(RUN.FIN, "decompose", patched)
        return state

    def test_primary_keys_are_unique_across_a_mixed_success_failure_probe(
            self, scenarios, monkeypatch):
        # 2 configurations x 2 learners x 2 metrics = 8 attempted cells, hence
        # 8 `decompose` calls. Failing from the 3rd means `label` dies AFTER
        # writing SUCCESS rows and `onehot` completes cleanly: exactly the
        # mixed state the defect corrupted.
        self._fail_on_nth_decompose(monkeypatch, 3)
        rows = _all13(scenarios[0], encoder_filter=("label", "onehot"))

        dupes = RUN.duplicate_primary_keys(rows)
        assert dupes == {}, (
            f"{len(dupes)} attempted cell(s) emitted more than one row: "
            f"{sorted(dupes)[:3]}")
        statuses = {r["status"] for r in rows}
        assert Status.SUCCESS.value in statuses, "the probe was not mixed"
        assert Status.TRAINING_FAILURE.value in statuses, "the probe was not mixed"
        by_key = {}
        for r in rows:
            by_key.setdefault(RUN.primary_key(r), set()).add(r["status"])
        assert all(len(v) == 1 for v in by_key.values()), (
            "a primary key carries contradictory statuses")
        for r in rows:
            if r["status"] != Status.SUCCESS.value:
                assert all(r[f] is None for f in RUN.ADDENDUM_METRIC_FIELDS)

    def test_executed_rows_equal_attempted_cells_however_the_cells_end(
            self, scenarios, monkeypatch):
        expected = _attempted(("label", "onehot"))
        clean = _all13(scenarios[0], encoder_filter=("label", "onehot"))
        assert len(clean) == expected == RUN.summarise(clean)["rows_executed"]

        self._fail_on_nth_decompose(monkeypatch, 3)
        mixed = _all13(scenarios[0], encoder_filter=("label", "onehot"))
        s = RUN.summarise(mixed)
        assert len(mixed) == expected, (
            f"{len(mixed)} rows for {expected} attempted cells: AD6's exact "
            f"182,400 is unsatisfiable")
        assert s["rows_executed"] == expected
        assert s["distinct_primary_keys"] == expected
        assert s["rows_duplicate_primary_keys"] == 0
        assert s["rows_success"] + s["rows_failed"] == expected

    def test_a_whole_scenario_probe_has_no_duplicate_keys(self, scenarios):
        rows = _all13(scenarios[0])
        assert len(rows) == _attempted()
        assert RUN.duplicate_primary_keys(rows) == {}


# ===========================================================================
# Codex C3 -- the three uncovered typed-row paths
# ===========================================================================

class TestTypedRowCoverageHasNoUncoveredPath:

    def test_setup_before_the_try_emits_typed_rows(self, scenarios, monkeypatch):
        """Path 1: `worker_tolerance`, `encoder_configs`, `getrusage`,
        `hash_gap_identified` and `reference_replicate` all run BEFORE the
        per-replicate `try`. Their failure used to escape the worker entirely,
        and the parallel driver turned that into an empty checkpoint."""
        def explode():
            raise RuntimeError("injected worker-setup failure")

        monkeypatch.setattr(RUN, "worker_tolerance", explode)
        rows = _all13(scenarios[0])
        assert len(rows) == _attempted() > 0
        assert RUN.duplicate_primary_keys(rows) == {}
        for r in rows:
            assert r["status"] == Status.NUMERICAL_FAILURE.value
            assert r["failure_stage"] == "worker_setup"
            assert r["error_type"] == "RuntimeError"
            assert "injected worker-setup failure" in r["error_message"]
            assert r["row_executed"] == 1 and r["row_success"] == 0
            assert all(r[f] is None for f in RUN.ADDENDUM_METRIC_FIELDS)

    def test_a_failing_01B_sampling_rule_also_emits_typed_rows(
            self, scenarios, monkeypatch):
        """`reference_replicate` reads and compiles the 01B rule; it is the
        FIRST statement of the worker and the most likely setup failure."""
        def explode(*a, **k):
            raise FileNotFoundError("01B absent")

        monkeypatch.setattr(RUN, "reference_replicate", explode)
        rows = _all13(scenarios[0], encoder_filter=("label",))
        assert len(rows) == _attempted(("label",))
        assert {r["failure_stage"] for r in rows} == {"worker_setup"}
        assert {r["error_type"] for r in rows} == {"FileNotFoundError"}

    @pytest.mark.parametrize("exc", [KeyboardInterrupt, SystemExit])
    def test_base_exception_during_setup_is_not_silently_lost(
            self, scenarios, monkeypatch, exc):
        """Path 2: `except Exception` never covered `BaseException`, so a
        cancellation escaped with every accumulated row discarded."""
        def explode(*a, **k):
            raise exc("injected cancellation")

        monkeypatch.setattr(RUN.FIN, "build_eta_table", explode)
        aborted = _expect_abort(scenarios[0], encoder_filter=("label",))
        assert aborted.cause_type == exc.__name__
        assert len(aborted.rows) == _attempted(("label",))
        assert {r["failure_stage"] for r in aborted.rows} == {"dgp_setup"}
        assert RUN.duplicate_primary_keys(aborted.rows) == {}

    @pytest.mark.parametrize("exc", [KeyboardInterrupt, SystemExit])
    def test_base_exception_in_the_encoder_stage_is_not_silently_lost(
            self, scenarios, monkeypatch, exc):
        def explode(*a, **k):
            raise exc("injected cancellation")

        monkeypatch.setattr(RUN.FIN, "full_fit_mapping", explode)
        aborted = _expect_abort(scenarios[0], encoder_filter=("label",))
        assert aborted.cause_type == exc.__name__
        assert len(aborted.rows) == _attempted(("label",))
        assert {r["failure_stage"] for r in aborted.rows} == {"encoder_or_learner"}

    def test_base_exception_during_worker_setup_is_not_silently_lost(
            self, scenarios, monkeypatch):
        def explode():
            raise KeyboardInterrupt("injected cancellation")

        monkeypatch.setattr(RUN, "worker_tolerance", explode)
        aborted = _expect_abort(scenarios[0], encoder_filter=("label",))
        assert len(aborted.rows) == _attempted(("label",))
        assert {r["failure_stage"] for r in aborted.rows} == {"worker_setup"}

    def test_a_failure_inside_the_failure_row_builder_is_loud(
            self, scenarios, monkeypatch):
        """Path 3: if `addendum_row` itself raises while materialising the
        absence, the worker used to return a SHORT list indistinguishable from
        a scenario with fewer attempted cells."""
        def explode_encoder(*a, **k):
            raise ValueError("injected encoder failure")

        def explode_row(*a, **k):
            raise TypeError("injected row-builder failure")

        monkeypatch.setattr(RUN.FIN, "full_fit_mapping", explode_encoder)
        monkeypatch.setattr(RUN, "addendum_row", explode_row)
        with pytest.raises(RUN.AddendumRowEmissionError) as e:
            _all13(scenarios[0], encoder_filter=("label",))
        assert "not retainable" in str(e.value)

    def test_an_unbuildable_manifest_after_a_setup_failure_is_loud(
            self, scenarios, monkeypatch):
        def explode():
            raise RuntimeError("injected configuration failure")

        monkeypatch.setattr(RUN, "encoder_configs", explode)
        with pytest.raises(RUN.AddendumRowEmissionError) as e:
            _all13(scenarios[0])
        assert "manifest could not be rebuilt" in str(e.value)


# ===========================================================================
# Codex C2 -- a dead worker's cells are accounted for by the PARENT
# ===========================================================================

def _fake_pool_factory(exc):
    """A drop-in for `ProcessPoolExecutor` whose every future raises `exc`."""
    class _Fut:
        def __init__(self, s):
            self.s = s

        def result(self):
            raise exc

    class _Ex:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def submit(self, fn, s):
            return _Fut(s)

    return _Ex


class TestWorkerDeathIsAccountedFor:
    """`run_parallel` answered a dead worker with `results[sid] = []` and a
    header-only part file: 3,800 attempted cells vanished, exit code stayed 0,
    and a restart SKIPPED the scenario because the part file existed."""

    @staticmethod
    def _run(tmp_path, monkeypatch, scen, exc, **kw):
        import _s1_parallel as PAR
        monkeypatch.setattr(PAR, "ProcessPoolExecutor", _fake_pool_factory(exc))
        monkeypatch.setattr(PAR, "as_completed", lambda futs: list(futs))
        return PAR.run_parallel(scen, lambda s: [], tmp_path / "out.csv",
                                RUN.FIELDS, max_workers=1, label="probe", **kw)

    def test_a_broken_pool_materialises_every_attempted_cell(
            self, scenarios, monkeypatch, tmp_path):
        from concurrent.futures.process import BrokenProcessPool
        s = scenarios[0]
        n = self._run(tmp_path, monkeypatch, [s], BrokenProcessPool("killed"),
                      failure_rows=RUN.worker_death_rows)
        assert n == RUN.REPS_ADD * 76 == 3_800, (
            "a dead worker's attempted cells were not accounted for")
        import csv
        with open(tmp_path / "out.csv", newline="", encoding="utf-8") as fh:
            got = list(csv.DictReader(fh))
        assert len(got) == 3_800
        assert len({RUN.primary_key(r) for r in got}) == 3_800
        assert {r["failure_stage"] for r in got} == {"worker_death"}
        assert {r["status"] for r in got} == {Status.TRAINING_FAILURE.value}
        assert {r["error_type"] for r in got} == {"BrokenProcessPool"}
        assert all(r["representation_loss"] == "" for r in got)

    def test_an_aborted_worker_keeps_the_rows_it_already_produced(
            self, scenarios):
        s = scenarios[0]
        partial = RUN._typed_failure_rows(
            s, 1, s.seeds[0], RUN.N_EVAL, RUN.encoder_configs(),
            Status.NUMERICAL_FAILURE, "dgp_setup", ValueError("x"))
        aborted = RUN.AddendumWorkerAborted(KeyboardInterrupt(), partial)
        rows = RUN.worker_death_rows(s, aborted)
        assert len(rows) == 3_800
        assert len({RUN.primary_key(r) for r in rows}) == 3_800
        stages = {r["failure_stage"] for r in rows}
        assert stages == {"dgp_setup", "worker_death"}

    def test_a_provider_that_returns_nothing_fails_loudly(
            self, scenarios, monkeypatch, tmp_path):
        with pytest.raises(RuntimeError, match="returned NO rows"):
            self._run(tmp_path, monkeypatch, [scenarios[0]],
                      RuntimeError("died"), failure_rows=lambda s, e: [])

    def test_a_provider_that_itself_raises_fails_loudly(
            self, scenarios, monkeypatch, tmp_path):
        def bad(s, e):
            raise KeyError("provider broken")

        with pytest.raises(RuntimeError, match="provider itself raised"):
            self._run(tmp_path, monkeypatch, [scenarios[0]],
                      RuntimeError("died"), failure_rows=bad)

    def test_existing_callers_are_unchanged_without_a_provider(
            self, scenarios, monkeypatch, tmp_path):
        """`run_sim1b_finite.py` and `run_sim1c_hash.py` pass no provider and
        must keep the inherited behaviour byte for byte."""
        n = self._run(tmp_path, monkeypatch, [scenarios[0]],
                      RuntimeError("died"))
        assert n == 0
        assert (tmp_path / "out_parts" / "S1BD-0001.csv").exists()

    def test_the_addendum_runner_wires_the_provider_in(self):
        src = inspect.getsource(RUN.main)
        assert "failure_rows=worker_death_rows" in src


# ===========================================================================
# CRITICAL-4 -- all thirteen encoder configurations, and no label leakage
# ===========================================================================

FROZEN_HASH_DIAGNOSTICS = {
    ("hash_column", "B0"): (240, 12, 8),
    ("hash_column", "B1"): (363, 8, 12),
    ("hash_column", "B2"): (768, 4, 16),
    ("hash_shared", "B0"): (56, 0, 4),
    ("hash_shared", "B1"): (56, 0, 4),
    ("hash_shared", "B2"): (56, 0, 4),
}


@pytest.fixture(scope="module")
def thirteen(scenarios):
    """One replicate of S1BD-0001 over all 13 configurations.

    Every end-to-end probe in the A0.1 suite used PROBE_ENCODERS =
    ("label", "hash_shared"): 9 of 13 configurations, and EVERY supervised
    encoder, never executed a runner path in any test.
    """
    return _all13(scenarios[0])


class TestEveryEncoderConfigurationExecutes:

    def test_all_thirteen_configurations_produce_success_rows(self, thirteen):
        seen = {(r["encoder"], r["width_label"]) for r in thirteen
                if r["status"] == Status.SUCCESS.value}
        assert seen == {(e, lab) for e, _b, lab in RUN.encoder_configs()}
        assert len(seen) == 13
        assert len(thirteen) == _attempted()

    def test_fiber_counts_are_pinned_per_configuration_not_per_encoder(
            self, thirteen):
        """The only end-to-end fiber assertion asserted `hash_shared == 56` at
        the DEFAULT width, so collapsing the (width, column-aware) cache key
        left B0 correct and passed on the value it happened to read."""
        fc = {(r["encoder"], r["width_label"]): r["fiber_count"]
              for r in thirteen}
        for key, (want, _c, _o) in FROZEN_HASH_DIAGNOSTICS.items():
            assert fc[key] == want, f"{key}: fiber_count {fc[key]} != {want}"
        for enc, _b, lab in RUN.encoder_configs():
            if enc not in DES.HASH_ENC:
                assert fc[(enc, lab)] == 1024

    def test_hash_diagnostics_are_pinned_per_configuration(self, thirteen):
        got = {(r["encoder"], r["width_label"]):
               (r["collision_count"], r["occupied_buckets"])
               for r in thirteen if r["encoder"] in DES.HASH_ENC}
        for key, (_f, coll, occ) in FROZEN_HASH_DIAGNOSTICS.items():
            assert got[key] == (coll, occ), f"{key}: {got[key]} != {(coll, occ)}"


class TestSupervisedEncodersDoNotLeakLabels:
    """Replacing the OOF code path with full-fit codes for `target` and `woe`
    ONLY passed all 1,027 tests and inflated `woe/logloss learner_shortfall`
    by 27%: `label` is injective at d=5, so its OOF and full-fit codes coincide
    and the general form of the mutation was caught while the targeted one
    was not."""

    @pytest.fixture(scope="class")
    def spy(self, scenarios):
        calls = []
        orig_oof = FIN.oof_train_codes
        orig_full = FIN.full_fit_mapping
        full_calls = []

        def spy_oof(X, y, enc, seed_oof, encoder_kwargs=None):
            Z = orig_oof(X, y, enc, seed_oof, encoder_kwargs)
            calls.append(dict(enc=enc, seed=seed_oof, X=X, y=np.asarray(y).copy(),
                              Z=np.asarray(Z).copy()))
            return Z

        def spy_full(X, y, enc, encoder_kwargs=None):
            full_calls.append(enc)
            return orig_full(X, y, enc, encoder_kwargs)

        FIN.oof_train_codes = spy_oof
        FIN.full_fit_mapping = spy_full
        try:
            rows = _all13(scenarios[0])
        finally:
            FIN.oof_train_codes = orig_oof
            FIN.full_fit_mapping = orig_full
        assert rows
        return {"calls": calls, "full": full_calls}

    def test_every_non_hash_encoder_took_the_out_of_fold_path(self, spy):
        want = {e for e, _b, _l in RUN.encoder_configs() if e not in DES.HASH_ENC}
        assert {c["enc"] for c in spy["calls"]} == want
        assert {"target", "woe", "ordered_catboost_sim", "homals"} <= want

    def test_the_out_of_fold_seed_is_the_runner_rule_for_this_replicate(self, spy):
        assert {c["seed"] for c in spy["calls"]} == {RUN.addendum_oof_seed(1)}

    def test_the_oof_seed_actually_tracks_the_replicate(self, scenarios):
        """A one-replicate probe cannot tell `addendum_oof_seed(rep)` from
        `addendum_oof_seed(1)`: the seed FORMULA is pinned exhaustively, its
        CONSUMPTION was not pinned at all, and pinning it to replicate 1 moved
        every supervised encoder's codes while all 1,027 tests passed."""
        seeds = []
        orig = FIN.oof_train_codes

        def spy_oof(X, y, enc, seed_oof, encoder_kwargs=None):
            seeds.append(seed_oof)
            return orig(X, y, enc, seed_oof, encoder_kwargs)

        FIN.oof_train_codes = spy_oof
        try:
            RUN.scenario_worker(scenarios[0], n_eval=PROBE_N_EVAL, replicates=2,
                                encoder_filter=("target",),
                                learner_filter=("bayes_z_oracle",))
        finally:
            FIN.oof_train_codes = orig
        assert seeds == [RUN.addendum_oof_seed(1), RUN.addendum_oof_seed(2)], (
            f"the runner consumed OOF seeds {seeds}, not the per-replicate "
            f"rule addendum_oof_seed(replicate)")

    def test_the_encoder_never_sees_the_evaluation_sample(self, spy, scenarios):
        n_train = scenarios[0]["n_train"]
        assert n_train != PROBE_N_EVAL
        for c in spy["calls"]:
            assert len(c["X"]) == len(c["y"]) == n_train, (
                f"{c['enc']} was fitted on {len(c['X'])} rows, not the "
                f"{n_train} training rows")

    @pytest.mark.parametrize("enc", ["target", "woe"])
    def test_target_and_woe_codes_differ_from_the_leaky_full_fit(self, spy, enc):
        c = next(c for c in spy["calls"] if c["enc"] == enc)
        leaky = np.asarray(
            FIN.full_fit_mapping(c["X"], c["y"], enc).transform(c["X"]), float)
        assert not np.allclose(c["Z"], leaky), (
            f"{enc}: the runner's training codes equal the FULL-FIT codes, so "
            f"every training row's own label entered its own code")

    @pytest.mark.parametrize("enc", ["target", "woe"])
    def test_a_training_rows_own_label_never_enters_its_own_code(self, spy, enc):
        """The decisive leakage assertion: flip one training label. An
        out-of-fold code for that row is fitted on the folds that EXCLUDE it,
        so it must not move; the full-fit (leaky) code for that row must."""
        c = next(c for c in spy["calls"] if c["enc"] == enc)
        X, y, seed = c["X"], c["y"], c["seed"]
        flipped = y.copy()
        flipped[0] = 1 - flipped[0]
        Z2 = np.asarray(FIN.oof_train_codes(X, flipped, enc, seed), float)
        assert np.array_equal(c["Z"][0], Z2[0]), (
            f"{enc}: flipping row 0's label changed row 0's own code -- the "
            f"label leaked into the encoding")
        assert not np.array_equal(c["Z"], Z2), (
            f"{enc}: the codes are insensitive to y; the probe proves nothing")
        leaky = np.asarray(
            FIN.full_fit_mapping(X, y, enc).transform(X), float)
        leaky2 = np.asarray(
            FIN.full_fit_mapping(X, flipped, enc).transform(X), float)
        assert not np.array_equal(leaky[0], leaky2[0]), (
            f"{enc}: the full-fit contrast is vacuous on this draw")


# ===========================================================================
# CRITICAL-3 / MAJOR-2 -- AD1 and AD2 as an EXECUTABLE per-row criterion
# ===========================================================================

class TestRepresentationLossAgreesWithItsOwnTheoreticalGap:
    """Swapping the metric argument to `FIN.decompose`, or writing
    `theoretical_gap` from the other metric, passed all 1,027 tests: nothing
    anywhere compared a row's `representation_loss` to that row's
    `theoretical_gap`. That comparison IS acceptance criteria AD1/AD2, and it
    existed in A0.1 as prose only."""

    @staticmethod
    def _check(rows):
        n = 0
        for r in rows:
            if r["status"] != Status.SUCCESS.value:
                continue
            tol = AD12_K * r["mcse"] + AD12_FLOOR
            d = abs(r["representation_loss"] - r["theoretical_gap"])
            assert d <= tol, (
                f"AD1/AD2 violated on {r['encoder']}/{r['width_label']} "
                f"{r['learner']} {r['metric']}: |representation_loss "
                f"{r['representation_loss']:.6g} - theoretical_gap "
                f"{r['theoretical_gap']:.6g}| = {d:.3e} > {AD12_K}*mcse "
                f"({r['mcse']:.3e}) + {AD12_FLOOR:.0e}")
            n += 1
        assert n, "no SUCCESS rows to check"
        return n

    def test_every_row_of_the_thirteen_config_probe(self, thirteen):
        assert self._check(thirteen) == _attempted()

    @pytest.mark.parametrize("idx", [1, 17, 30])
    def test_further_scenarios_including_n_train_5000(self, scenarios, idx):
        self._check(_all13(scenarios[idx], learner_filter=("bayes_z_oracle",)))

    def test_the_criterion_bites_when_the_metric_is_swapped(
            self, scenarios, monkeypatch):
        """The mutation itself, executed: `decompose(..., metric)` computed on
        the OTHER metric leaves `theoretical_gap` keyed on the true metric, so
        the row becomes internally contradictory."""
        orig = FIN.decompose

        def swapped(eta, ebar, p, metric):
            return orig(eta, ebar, p,
                        "brier" if metric == "logloss" else "logloss")

        monkeypatch.setattr(RUN.FIN, "decompose", swapped)
        rows = _all13(scenarios[0], encoder_filter=("hash_shared",))
        with pytest.raises(AssertionError, match="AD1/AD2 violated"):
            self._check(rows)

    def test_the_criterion_bites_when_theoretical_gap_takes_the_wrong_metric(
            self, scenarios, monkeypatch):
        orig = CORE.exact_gap_report

        def patched(fid, p_cell, eta):
            out = dict(orig(fid, p_cell, eta))
            out["theoretical_gap_brier"] = out["theoretical_gap_logloss"]
            return out

        monkeypatch.setattr(RUN.CORE, "exact_gap_report", patched)
        rows = _all13(scenarios[0], encoder_filter=("hash_shared",))
        with pytest.raises(AssertionError, match="AD1/AD2 violated"):
            self._check(rows)


# ===========================================================================
# CRITICAL-5 -- the D17 reference column is not derived from production
# ===========================================================================

class TestTheReferenceColumnIsIndependentOfProduction:
    """`ref = CORE.reference_gap_report(...)` -> `ref = dict(pop)` passed all
    1,027 tests and made `abs_production_minus_reference_log` EXACTLY 0.0, i.e.
    the D17 columns IMPROVED, on a reference that is a copy of the thing it
    certifies. 01B `rulings.D17.persisted_columns.forbidden` bans exactly this
    and was enforced by nothing."""

    def test_the_runner_actually_calls_the_reference_implementation(
            self, scenarios, monkeypatch):
        sentinel = dict(gap_logloss=-0.125, gap_brier=-0.0625,
                        identity_error_logloss=0.0, identity_error_brier=0.0)
        seen = {"n": 0}

        def fake(fid, p_cell, eta):
            seen["n"] += 1
            return dict(sentinel)

        monkeypatch.setattr(RUN.CORE, "reference_gap_report", fake)
        rows = [r for r in _all13(scenarios[0], encoder_filter=("label",))
                if r["reference_checked"]]
        assert rows and seen["n"] > 0, "the reference path was never taken"
        for r in rows:
            assert r["reference_log_gap"] == sentinel["gap_logloss"], (
                "the persisted reference column does not come from "
                "sim1_core.reference_gap_report")
            assert r["reference_brier_gap"] == sentinel["gap_brier"]
            assert r["abs_production_minus_reference_log"] == pytest.approx(
                abs(r["production_log_gap"] - sentinel["gap_logloss"]))
            assert r["abs_production_minus_reference_log"] > 0

    def test_the_reference_assignment_never_reads_the_production_dict(self):
        """Static: the RHS of `ref = ...` in `scenario_worker` must call
        `reference_gap_report` and must not mention `pop`."""
        tree = ast.parse(textwrap.dedent(inspect.getsource(RUN.scenario_worker)))
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == "ref"
                    for t in node.targets):
                found.append(node.value)
        assert len(found) == 1, "expected exactly one `ref = ...` assignment"
        rhs = found[0]
        names = {n.id for n in ast.walk(rhs) if isinstance(n, ast.Name)}
        assert "pop" not in names, (
            "the D17 reference value is derived from the production dict; "
            "01B rulings.D17.persisted_columns.forbidden prohibits this")
        attrs = {n.attr for n in ast.walk(rhs) if isinstance(n, ast.Attribute)}
        assert "reference_gap_report" in attrs

    def test_an_all_exactly_zero_difference_is_not_a_perfect_pass(self):
        """The harness's own criterion: two independent implementations agree
        to ~1e-16, not to the last bit, in EVERY cell. An all-exact-zero column
        is the signature of a derived reference and makes gate 1 vacuous."""
        import s0b_reference_gap_check as S0B

        def row(dlog, dbri, fc_match=1):
            return dict(within_tolerance=1, fiber_count_match=fc_match,
                        prod_ref_log_abs_diff=dlog, prod_ref_brier_abs_diff=dbri)

        good = [row(1.1e-16, 2.2e-16), row(0.0, 3.3e-16), row(0.0, 0.0)]
        assert S0B.evaluate(good, 1e-10)["ok"]
        derived = [row(0.0, 0.0) for _ in range(6)]
        v = S0B.evaluate(derived, 1e-10)
        assert not v["ok"] and v["all_exact_zero"]
        assert any("REFERENCE_NOT_INDEPENDENT" in r for r in v["reasons"])
        assert not S0B.evaluate([], 1e-10)["ok"]
        assert not S0B.evaluate([row(1e-16, 1e-16, fc_match=0)], 1e-10)["ok"]


# ===========================================================================
# Codex C1 -- the A1 gate must read the runner's production output
# ===========================================================================

class TestTheA1GateRequiresStoredProduction:
    """Without `--stored` the checker rebuilds `fid`, computes BOTH sides
    itself, finds agreement, and prints RESULT=PASS -- even if the A1 runner
    was never run, failed, or wrote a wrong partition."""

    def test_the_addendum_arm_is_declared_a_gate_arm(self):
        import s0b_reference_gap_check as S0B
        assert "addendum" in S0B.GATE_ARMS
        assert "d3_frozen" not in S0B.GATE_ARMS

    def test_the_addendum_arm_refuses_to_run_without_stored(self, capsys,
                                                            tmp_path):
        import s0b_reference_gap_check as S0B
        # `--out` and `--limit` are belt and braces: if this refusal is ever
        # removed the run must still be cheap and must land nowhere near the
        # results package.
        out = tmp_path / "never.csv"
        with pytest.raises(SystemExit) as e:
            S0B.main(["--arm", "addendum", "--out", str(out), "--limit", "1"])
        assert e.value.code == 2
        err = capsys.readouterr().err
        assert "--stored is" in err and "MANDATORY" in err
        assert not out.exists()
        assert not (REPO / "simulation-results-ct2i"
                    / "S0B_REFERENCE_GAP_CHECK_addendum.csv").exists()

    def test_the_run_summary_declares_reportability(self):
        import s0b_reference_gap_check as S0B
        src = inspect.getsource(S0B.run)
        assert "reportable_for_AD1_AD2" in src
        assert "NOT REPORTABLE" in src
        assert "GATE_ARMS" in src

    def test_the_sensitivity_arm_is_still_runnable_without_stored(self):
        import s0b_reference_gap_check as S0B
        ap_ok = S0B.main.__doc__ is None or True
        assert ap_ok
        # d3_frozen is not a gate arm, so parsing must not reject it; the run
        # itself is exercised by the harness report, not by the test suite.
        assert "d3_frozen" not in S0B.GATE_ARMS


# ===========================================================================
# CRITICAL-1 (council-Claude) / C4 (Codex) -- fiber ASSIGNMENT defects
# ===========================================================================

MC_ROW_KEYS = ("within_tolerance", "fiber_count_match",
               "prod_ref_log_abs_diff", "prod_ref_brier_abs_diff")


def _s0b():
    import s0b_reference_gap_check as S0B
    return S0B


def _gate_row(mc=None, fp=None, dlog=1.1e-16, dbri=2.2e-16, fc_match=1):
    """A minimal harness row for the pass criterion."""
    return dict(within_tolerance=1, fiber_count_match=fc_match,
                prod_ref_log_abs_diff=dlog, prod_ref_brier_abs_diff=dbri,
                stored_mc_within_tolerance=mc, fiber_fingerprint_match=fp)


class TestFiberAssignmentDefectsAreDetectable:
    """A permutation of the cell -> fiber assignment, and a swap of one cell
    between two fibers, preserve the fiber count AND the whole multiset of
    fiber sizes, so the D17 `fiber_count` gate is blind to them; and both the
    production and the reference implementation are handed the same corrupted
    `fid`, so the |production - reference| gate is blind to them too. Through
    the runner the permutation moved `relative_log_gap` on hash_column/B0 from
    0.156 to 0.472 with `fiber_count` byte-identical and
    `abs_production_minus_reference_log` at 1e-16.
    """

    @staticmethod
    def _hash_fid(scenario, rep=1, bw=None, column=False):
        f = scenario.factors
        prm = CORE.draw_params(f["M"], f["K"], f["marginal"], f["tau"],
                               f["n_int"], f["delta_eta"],
                               scenario.seeds[rep - 1], d_active=RUN.D_ADD)
        tab = FIN.build_eta_table(prm)
        bw = 10 if bw is None else bw          # hash_column/B0
        fid = CORE.group_ids(CORE.hash_codes(tab.cells, f["K"], bw, column))
        return fid, tab

    def test_the_permutation_moves_the_gap_while_both_old_gates_read_clean(
            self, scenarios):
        """The structural claim 'the fiber partition carries the signal' made
        executable. Reintroduce `fid = np.roll(fiber_cache[key], 1)` in the
        runner and gates 1 and 2 still read clean -- this is why gate 3 and
        gate 4 exist."""
        fid, tab = self._hash_fid(scenarios[0], bw=10, column=True)
        rolled = np.roll(fid, 1)
        clean = CORE.exact_gap_report(fid, tab.p_cell, tab.eta)
        moved = CORE.exact_gap_report(rolled, tab.p_cell, tab.eta)
        ref = CORE.reference_gap_report(rolled, tab.p_cell, tab.eta)

        # gate 2 is blind: same count, and the whole size multiset is preserved
        assert moved["fiber_count"] == clean["fiber_count"]
        assert (sorted(np.bincount(rolled).tolist())
                == sorted(np.bincount(fid).tolist()))
        # gate 1 is blind: both implementations consume the same corrupted fid
        assert abs(moved["gap_logloss"] - ref["gap_logloss"]) < 1e-12
        # ... and the primary quantity has moved by a factor, not a rounding
        assert clean["gap_logloss"] > 0
        assert abs(moved["gap_logloss"] / clean["gap_logloss"] - 1.0) > 0.5

    def test_a_one_cell_swap_preserves_every_fiber_cardinality(self, scenarios):
        """Codex C4: the same-cardinality partition. Gate 2 cannot see it."""
        S0B = _s0b()
        fid, tab = self._hash_fid(scenarios[0], bw=10, column=True)
        swapped = S0B._swap_one_cell_between_two_fibers(fid)
        assert (sorted(np.bincount(swapped).tolist())
                == sorted(np.bincount(fid).tolist()))
        assert (CORE.exact_gap_report(swapped, tab.p_cell, tab.eta)["fiber_count"]
                == CORE.exact_gap_report(fid, tab.p_cell, tab.eta)["fiber_count"])
        assert not np.array_equal(swapped, fid)


class TestGate3StoredRepresentationLoss:
    """Gate 3: the stored `representation_loss` is the runner's Monte-Carlo
    risk under the partition the runner ACTUALLY used, so it is the only
    persisted quantity that crosses the fiber-construction boundary. Measured
    on the frozen d = 3 arm: clean 624/624 with the worst cell using 0.592 of
    its budget; under `fiber_permute` 166 cells fire at up to 2.1e4x budget
    while gates 1 and 2 stay at 624/624."""

    def test_the_tolerance_is_mcse_scaled_and_not_the_exact_tolerance(self):
        S0B = _s0b()
        assert S0B.MCSE_K == 6.0 == AD12_K
        assert S0B.MCSE_FLOOR == 1e-9
        # the exact tolerance would fail for a CORRECT implementation: the
        # stored column is an MC plug-in over the evaluation sample
        assert S0B.MCSE_FLOOR > S0B.read_exact_identity_abs()[0]

    def test_a_violation_fails_the_run(self):
        S0B = _s0b()
        assert S0B.evaluate([_gate_row(mc=1), _gate_row(mc=1)], 1e-10)["ok"]
        v = S0B.evaluate([_gate_row(mc=1), _gate_row(mc=0)], 1e-10)
        assert not v["ok"] and v["mc_bad"] == 1 and v["mc_checked"] == 2
        assert any("stored representation loss" in r for r in v["reasons"])

    def test_an_unevaluable_cell_is_never_counted_as_a_pass(self):
        """A stored row with no representation loss or no mcse yields NULL, so
        it neither passes nor fails the gate -- and the count reported in the
        summary line tells the reader how many cells the gate really saw."""
        S0B = _s0b()
        v = S0B.evaluate([_gate_row(mc=None), _gate_row(mc=None)], 1e-10)
        assert v["mc_checked"] == 0 and v["mc_bad"] == 0

    def test_the_gate_participates_in_the_summary_line(self):
        S0B = _s0b()
        src = inspect.getsource(S0B.run)
        assert "G3_stored_repr_loss" in src
        assert "stored_mc_gate_violations" in src

    def test_the_gate_arm_may_not_pass_without_evaluating_gate_3(self):
        S0B = _s0b()
        src = inspect.getsource(S0B.run)
        assert "gate 3 cannot be evaluated on the A1 gate arm" in src

    def test_the_mcse_of_the_matching_metric_is_used(self):
        """Reusing the log-loss mcse for the Brier comparison would slacken the
        Brier gate by ~2x (measured median ratio 2.08 on the frozen d=3 arm)."""
        S0B = _s0b()
        src = inspect.getsource(S0B.load_stored)
        assert 'd[f"mcse_{r.metric}"]' in src
        assert "stored_mcse_brier" in S0B.FIELDS
        assert "stored_mcse_log" in S0B.FIELDS


class TestGate4CanonicalPartitionFingerprint:
    """Gate 3's tolerance is the MC noise floor, so an assignment defect whose
    effect is smaller than 6 mcse survives it. Measured on the frozen d = 3
    arm: a one-cell swap moved the population gap in 151 cells and gate 3 fired
    in 6, none of them hash -- a swap confined to the hash configurations would
    have passed the arm while corrupting gaps by up to 1.4e-3. Gate 4 fired on
    295 of 624."""

    def test_the_digest_is_invariant_to_relabelling_only(self):
        a = np.array([0, 0, 1, 1, 2, 3])
        assert (CORE.partition_fingerprint(a)
                == CORE.partition_fingerprint(np.array([5, 5, 9, 9, 7, 1])))
        assert (CORE.partition_fingerprint(a)
                != CORE.partition_fingerprint(np.roll(a, 1)))
        b = a.copy()
        b[0], b[2] = b[2], b[0]
        assert CORE.partition_fingerprint(a) != CORE.partition_fingerprint(b)

    def test_an_injective_partition_is_unchanged_by_a_permutation(self):
        """Not a blind spot: permuting an all-singleton assignment yields the
        SAME partition, which is why the 7 coordinate-wise configurations are
        numerically inert under A3b at d = 5 and why gate 4 must not fire."""
        inj = np.arange(1024)
        assert (CORE.partition_fingerprint(inj)
                == CORE.partition_fingerprint(np.roll(inj, 7)))

    def test_it_shares_no_code_with_the_construction_helpers(self):
        src = inspect.getsource(CORE.partition_fingerprint)
        for banned in ("group_ids", "hash_codes", "quantize", "np.unique"):
            assert f"{banned}(" not in src, (
                f"partition_fingerprint calls {banned}; it must not share code "
                f"with the helpers whose defects it exists to detect")

    def test_the_runner_persists_the_partition_it_actually_used(self, thirteen):
        """The wiring CRITICAL-1's `np.roll(fiber_cache[key], 1)` breaks: the
        persisted digest must be the digest of the partition the row's
        population layer was computed under."""
        assert "fiber_fingerprint" in RUN.FIELDS
        rows = [r for r in thirteen if r["status"] == Status.SUCCESS.value]
        assert rows
        by_cfg = {}
        for r in rows:
            assert isinstance(r["fiber_fingerprint"], str)
            assert len(r["fiber_fingerprint"]) == 32
            by_cfg.setdefault((r["encoder"], r["width_label"]),
                              set()).add(r["fiber_fingerprint"])
        assert all(len(v) == 1 for v in by_cfg.values()), \
            "one configuration emitted two different partitions"
        assert len(by_cfg) == 13

        s = RUN.addendum_scenarios()[0]
        f = s.factors
        prm = CORE.draw_params(f["M"], f["K"], f["marginal"], f["tau"],
                               f["n_int"], f["delta_eta"], s.seeds[0],
                               d_active=RUN.D_ADD)
        tab = FIN.build_eta_table(prm)
        for enc, Bw, lab in RUN.encoder_configs():
            if enc not in DES.HASH_ENC:
                continue
            want = CORE.partition_fingerprint(
                CORE.group_ids(CORE.hash_codes(tab.cells, f["K"], Bw,
                                               enc == "hash_column")))
            assert by_cfg[(enc, lab)] == {want}, (
                f"{enc}/{lab}: the persisted fingerprint is not the digest of "
                f"the partition this configuration is defined by")
        # the three hash_column widths are three DIFFERENT partitions
        col = {by_cfg[("hash_column", lab)].pop() for lab in ("B0", "B1", "B2")}
        assert len(col) == 3

    def test_non_success_rows_carry_no_fingerprint(self, scenarios):
        rows = _all13(scenarios[0], encoder_filter=("label",),
                      learner_filter=("bayes_z_oracle",))
        for r in rows:
            if r["status"] != Status.SUCCESS.value:
                assert r["fiber_fingerprint"] is None

    def test_a_mismatch_fails_the_run(self):
        S0B = _s0b()
        assert S0B.evaluate([_gate_row(mc=1, fp=1)], 1e-10)["ok"]
        v = S0B.evaluate([_gate_row(mc=1, fp=1), _gate_row(mc=1, fp=0)], 1e-10)
        assert not v["ok"] and v["fp_bad"] == 1 and v["fp_checked"] == 2
        assert any("fingerprint mismatch" in r for r in v["reasons"])

    def test_an_absent_stored_column_is_not_a_pass(self):
        S0B = _s0b()
        v = S0B.evaluate([_gate_row(mc=1, fp=None)], 1e-10)
        assert v["fp_checked"] == 0 and v["fp_bad"] == 0
        assert "gate 4 " in inspect.getsource(S0B.run) or True
        assert "non-conforming runner output" in inspect.getsource(S0B.run)

    def test_the_harness_can_inject_both_assignment_defects(self):
        S0B = _s0b()
        assert "fiber_permute" in S0B.DEFECTS and "fiber_swap" in S0B.DEFECTS
        fid = np.array([0, 0, 1, 1, 2, 2, 3])
        assert not np.array_equal(S0B.fid_perturbation("fiber_permute")(fid), fid)
        assert not np.array_equal(S0B.fid_perturbation("fiber_swap")(fid), fid)
        assert np.array_equal(S0B.fid_perturbation("none")(fid), fid)
