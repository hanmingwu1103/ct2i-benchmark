"""Phase A0.1 RECONCILIATION tests (items R1, R9, R10).

Four agents built the A0.1 gate in parallel and left three things that no
single agent's own test suite could catch, because each is a disagreement
BETWEEN artefacts rather than a defect inside one:

  R1  the runner's D17 reference SAMPLE disagreed with the frozen sampling rule
      in 01B_ADDENDUM_ADVISOR_RULINGS.yaml. Both samples have 624 cells, so
      every count-based assertion in the package passed while the two files
      pointed at different replicates. 01B is the frozen ruling file and wins;
      the runner now READS the rule out of 01B instead of restating it, and the
      tests below fail if the two ever diverge again.

  R9  scripts/s0a_addendum_microbenchmark.py holds a PRIVATE copy of the
      addendum seed rule. AD15 item 3 requires that rule to live only in the
      runner -- but that file is an `S0A_*` A0 record and the advisor's ruling
      forbids overwriting or erasing the A0 freeze and council record. The gap
      is therefore closed by DETECTION, not by removal: the A0 record stays
      byte-identical and the duplicate is pinned to the runner's rule across
      all 48 scenarios and all 2,400 seeds.

  R10 `_typed_failure_rows` ignored `learner_filter` while the success path
      applied it, so the number of ATTEMPTED cells depended on whether the cell
      succeeded. The frozen arm passes `learner_filter=None`, so the 182,400
      total was never wrong; probe row-count assertions were.

SIMULATION ONLY, PREFLIGHT ONLY. Every probe here is a NON-FROZEN probe (two
encoder configurations, one or two learners, a 500-row evaluation sample) that
the runner stamps `warning = NON_FROZEN_PROBE_NOT_AN_ADDENDUM_RESULT`; no row
is written to disk and no full addendum cell is executed.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

from ct2i_benchmark.simulations import sim1_design as DES         # noqa: E402
from ct2i_benchmark.statuses import Status                        # noqa: E402

import run_sim1b_dense_addendum as RUN                            # noqa: E402
import s0a_addendum_microbenchmark as S0A                         # noqa: E402

PKG = REPO / "simulation-results-ct2i"
RULINGS_01B = PKG / "01B_ADDENDUM_ADVISOR_RULINGS.yaml"
S0A_PATH = REPO / "scripts" / "s0a_addendum_microbenchmark.py"

PROBE_ENCODERS = ("label", "hash_shared")
PROBE_N_EVAL = 500


def _probe(scenario, **kw):
    kw.setdefault("n_eval", PROBE_N_EVAL)
    kw.setdefault("replicates", 1)
    kw.setdefault("encoder_filter", PROBE_ENCODERS)
    return RUN.scenario_worker(scenario, **kw)


@pytest.fixture(scope="module")
def scenarios():
    return RUN.addendum_scenarios()


@pytest.fixture(autouse=True)
def _clear_rule_cache():
    """The 01B rule is cached per (path, mtime, size); never leak a monkeypatched
    ruling file into the next test."""
    RUN._D17_RULE_CACHE.clear()
    yield
    RUN._D17_RULE_CACHE.clear()


# ===========================================================================
# R1 -- the D17 reference sample is 01B's, not the runner's
# ===========================================================================

class TestD17ReferenceSampleFollows01B:

    @staticmethod
    def _rule_text_from_01B() -> str:
        """The rule as 01B literally carries it, read here through a plain YAML
        load and an explicit key walk -- independently of the runner's own
        reader, so the two are able to disagree."""
        import yaml
        node = yaml.safe_load(RULINGS_01B.read_text(encoding="utf-8"))
        for part in ("rulings", "D17", "sampling_rule",
                     "frozen_replicate_rule", "rule"):
            assert isinstance(node, dict) and part in node, (
                f"01B carries no rulings.D17.sampling_rule."
                f"frozen_replicate_rule.rule (stopped at {part!r}) -- the D17 "
                f"reference sample is undefined")
            node = node[part]
        return str(node)

    def test_the_runner_uses_the_expression_01B_freezes(self):
        raw = self._rule_text_from_01B()
        expr, _code = RUN._d17_rule()
        assert expr in raw, (
            f"the runner evaluates {expr!r}, which is not the right-hand side "
            f"of the 01B rule {raw!r}")
        assert expr == raw.split("=", 1)[1].strip()

    def test_every_scenarios_reference_replicate_matches_01B(self, scenarios):
        """The whole 624-cell sample, scenario by scenario.

        The expected value is derived HERE from the 01B rule text by an
        independent parse (`int(scenario_id[-N:])`), so this test fails both if
        the runner drifts and if 01B is amended without the runner following.
        """
        raw = self._rule_text_from_01B()
        m = re.fullmatch(r"reference_replicate\(scenario\)\s*=\s*"
                         r"int\(scenario_id\[-(\d+):\]\)", raw.strip())
        assert m, (
            f"the 01B D17 rule is now {raw!r}, which this test does not know "
            f"how to reproduce independently. Update BOTH this test and the "
            f"runner's whitelist deliberately -- do not delete the check.")
        width = int(m.group(1))
        for s in scenarios:
            assert RUN.reference_replicate(s.scenario_id) == int(
                s.scenario_id[-width:])

    def test_the_sample_is_not_a_single_fixed_replicate(self, scenarios):
        """01B `why_not_replicate_1_for_all` explicitly declines the runner's
        original `REFERENCE_REPLICATES = (1,)`."""
        reps = {RUN.reference_replicate(s.scenario_id) for s in scenarios}
        assert len(reps) == len(scenarios) == 48, (
            "the D17 sample collapsed onto a single slice of the replicate "
            "axis, which 01B declines by name")
        assert reps == set(range(1, 49))
        assert "why_not_replicate_1_for_all" in RULINGS_01B.read_text("utf-8")

    def test_the_sample_size_is_01Bs_frozen_cell_count(self):
        wl = RUN.work_list()
        assert wl["reference_cells"] == wl["reference_cells_required"] == 624
        assert RUN.d17_reference_cells() == 624

    def test_no_fixed_reference_replicate_constant_survives_in_the_runner(self):
        """The defect was a module constant, so the ban is checked structurally.

        A functional test alone would pass again the moment someone re-added a
        private default and stopped consulting 01B.
        """
        src = (REPO / "scripts" / "run_sim1b_dense_addendum.py").read_text("utf-8")
        tree = ast.parse(src)
        assigned = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    assigned.update(n.id for n in ast.walk(tgt)
                                    if isinstance(n, ast.Name))
        assert "REFERENCE_REPLICATES" not in assigned, (
            "a module-level reference-replicate constant is back; the sample "
            "must come from 01B (reconciliation R1)")

    def test_the_runner_follows_01B_when_01B_changes(self, tmp_path, monkeypatch):
        """The bite: amend the rule, and the runner's sample must move with it.

        This is what a hardcoded second copy of the rule cannot do, and it is
        why R1 was resolved by reading 01B rather than by editing a literal.
        """
        raw = RULINGS_01B.read_text(encoding="utf-8")
        amended = raw.replace(
            'rule: "reference_replicate(scenario) = int(scenario_id[-4:])"',
            'rule: "reference_replicate(scenario) = int(scenario_id[-2:])"', 1)
        assert amended != raw
        alt = tmp_path / "01B_AMENDED.yaml"
        alt.write_text(amended, encoding="utf-8")
        monkeypatch.setattr(RUN, "RULINGS_01B", alt)
        RUN._D17_RULE_CACHE.clear()
        assert RUN._d17_rule()[0] == "int(scenario_id[-2:])"
        assert RUN.reference_replicate("S1BD-0048") == 48
        assert RUN.reference_replicate("S1BD-0007") == 7

    def test_a_rule_out_of_the_frozen_replicate_range_is_refused(
            self, tmp_path, monkeypatch):
        raw = RULINGS_01B.read_text(encoding="utf-8")
        alt = tmp_path / "01B_BAD_RANGE.yaml"
        alt.write_text(raw.replace(
            'rule: "reference_replicate(scenario) = int(scenario_id[-4:])"',
            'rule: "reference_replicate(scenario) = int(scenario_id[-1:])"', 1),
            encoding="utf-8")
        monkeypatch.setattr(RUN, "RULINGS_01B", alt)
        RUN._D17_RULE_CACHE.clear()
        with pytest.raises(ValueError):
            RUN.reference_replicate("S1BD-0010")     # -> 0, outside 1..50

    @pytest.mark.parametrize("bad", [
        "__import__('os').system('true')",
        "open('/etc/passwd').read()",
        "int(scenario_id[-4:]) + other_name",
    ])
    def test_a_rule_that_is_not_a_pure_function_of_the_id_is_refused(self, bad):
        with pytest.raises(ValueError):
            RUN._d17_compile(bad)

    def test_a_missing_01B_refuses_rather_than_inventing_a_sample(
            self, tmp_path, monkeypatch):
        monkeypatch.setattr(RUN, "RULINGS_01B", tmp_path / "absent.yaml")
        RUN._D17_RULE_CACHE.clear()
        with pytest.raises(FileNotFoundError):
            RUN.reference_replicate("S1BD-0001")

    def test_the_worker_marks_the_01B_replicate_and_not_replicate_one(
            self, scenarios):
        """End-to-end: S1BD-0002's frozen replicate is 2, so a two-replicate
        probe must stamp `reference_checked` on replicate 2 ONLY.

        Under the superseded `REFERENCE_REPLICATES = (1,)` this test fails.
        """
        s = scenarios[1]
        assert s.scenario_id == "S1BD-0002"
        assert RUN.reference_replicate(s.scenario_id) == 2
        rows = _probe(s, replicates=2, encoder_filter=("label",),
                      learner_filter=("bayes_z_oracle",))
        checked = {r["replicate"] for r in rows if r["reference_checked"]}
        assert checked == {2}, (
            f"the D17 reference cell landed on replicate(s) {checked}, not on "
            f"01B's frozen replicate 2")
        for r in rows:
            if r["reference_checked"]:
                assert r["reference_log_gap"] is not None
                assert r["production_log_gap"] is not None
            else:
                assert r["reference_log_gap"] is None


# ===========================================================================
# R9 -- the A0 microbenchmark's private seed rule is pinned, not deleted
# ===========================================================================

class TestS0AMicrobenchmarkSeedRuleHasNotDrifted:
    """AD15 item 3, closed by DETECTION rather than by removal.

    `scripts/s0a_addendum_microbenchmark.py` keeps a private `SEED_BASE_1BD`,
    `OOF_BASE_1BD` and `addendum_seed`. AD15 item 3 wants exactly one copy of
    the seed rule, in the runner. Removing the duplicate would mean editing an
    `S0A_*` file, and the advisor ruled "Do not overwrite or erase the A0 freeze
    or council record". So the duplicate stays, byte-identical, and is pinned
    here: the A0 record remains an untouched historical artefact AND a drift
    between it and the runner is now a test failure rather than a silent
    inconsistency. What is NOT closed is the duplication itself -- see
    S0B_ADVISOR_RULING_IMPLEMENTATION_REPORT.md.
    """

    def test_the_two_seed_bases_agree(self):
        assert S0A.SEED_BASE_1BD == RUN.SEED_BASE_1BD == 2_000_000_000
        assert S0A.OOF_BASE_1BD == RUN.OOF_BASE_1BD == 91_211

    def test_the_microbenchmark_is_the_repository_file_not_a_stub(self):
        assert Path(S0A.__file__).resolve() == S0A_PATH.resolve()

    def test_every_one_of_the_2400_seeds_agrees_with_the_runner(self, scenarios):
        """All 48 scenarios x all 50 replicates, through both implementations."""
        n = 0
        for s in scenarios:
            blk = RUN.addendum_block(s["marginal"], s["tau"], s["n_int"])
            for rep in range(1, RUN.REPS_ADD + 1):
                mine = RUN.addendum_seed(blk, rep)
                theirs = S0A.addendum_seed(blk, rep)
                assert theirs == mine, (
                    f"S0A microbenchmark seed rule has drifted from the runner "
                    f"at block={blk} replicate={rep}: {theirs} != {mine}. The "
                    f"S0A file is an immutable A0 record -- fix the RUNNER or "
                    f"record the divergence, do not edit S0A.")
                assert s["seeds"][rep - 1] == mine
                n += 1
        assert n == 48 * RUN.REPS_ADD == 2_400

    @pytest.mark.parametrize("const,delta", [("SEED_BASE_1BD", 1_000),
                                             ("OOF_BASE_1BD", 2)])
    def test_the_pin_bites_when_a_runner_SEED_CONSTANT_moves(self, scenarios,
                                                             monkeypatch,
                                                             const, delta):
        """Move a runner seed CONSTANT in memory and watch the pin fire.

        RECONCILIATION C-R9 (2026-08-24). The earlier version of this test
        monkeypatched `RUN.addendum_seed` -- the very function whose agreement
        with S0A it then asserted -- so it fired BY CONSTRUCTION and was no
        evidence at all about the runner. It is the self-referential-check bug
        class this package has hit repeatedly.

        What is patched now is the module-level CONSTANT that the real
        `addendum_seed` / `addendum_oof_seed` read at call time, i.e. exactly
        the edit the council used to demonstrate the closure (SEED_BASE_1BD
        2_000_000_000 -> 2_000_001_000, 5 tests fired). The runner's own
        arithmetic is untouched, so a disagreement with S0A is a real drift
        signal. Nothing on disk changes; `monkeypatch` restores the constant.
        """
        monkeypatch.setattr(RUN, const, getattr(RUN, const) + delta)
        if const == "OOF_BASE_1BD":
            assert RUN.addendum_oof_seed(1) != S0A.OOF_BASE_1BD + 17
            return
        mismatches = 0
        for s in scenarios:
            blk = RUN.addendum_block(s["marginal"], s["tau"], s["n_int"])
            for rep in range(1, RUN.REPS_ADD + 1):
                if S0A.addendum_seed(blk, rep) != RUN.addendum_seed(blk, rep):
                    mismatches += 1
        assert mismatches == 2_400, (
            "a shifted runner seed BASE went undetected; the R9 pin does not "
            "bite and AD15 item 3 would be closed on paper only")
        assert RUN.verify_against_freeze(), (
            "moving the runner seed base must also disagree with 01A")


# ===========================================================================
# R10 -- attempted cells do not depend on which path the cell took
# ===========================================================================

class TestTypedFailureRowsHonourTheLearnerFilter:

    @staticmethod
    def _expected(encoders, learner_filter):
        cfgs = [c for c in RUN.encoder_configs() if c[0] in encoders]
        return sum(len(RUN._learners_for(e, lab, learner_filter))
                   for e, _b, lab in cfgs) * len(RUN.METRICS)

    def test_failure_rows_are_filtered_exactly_as_success_rows_are(
            self, scenarios, monkeypatch):
        """The bug: a filtered probe emitted more failure rows than success rows.

        Same scenario, same filters, one clean pass and one with an injected
        setup exception. The two row counts must be identical, because the set
        of ATTEMPTED cells is a property of the configuration.
        """
        s = scenarios[0]
        ok = _probe(s, learner_filter=("logistic",))
        assert all(r["status"] == Status.SUCCESS.value for r in ok)

        def explode(*a, **k):
            raise RuntimeError("injected setup failure (R10 probe)")

        monkeypatch.setattr(RUN.FIN, "build_eta_table", explode)
        bad = _probe(s, learner_filter=("logistic",))

        assert len(bad) == len(ok) == self._expected(PROBE_ENCODERS, ("logistic",))
        assert {r["learner"] for r in bad} == {"logistic"}
        assert {(r["encoder"], r["width_label"], r["learner"], r["metric"])
                for r in bad} == {
            (r["encoder"], r["width_label"], r["learner"], r["metric"])
            for r in ok}
        for r in bad:
            assert r["status"] == Status.NUMERICAL_FAILURE.value
            assert r["failure_stage"] == "dgp_setup"
            assert r["row_executed"] == 1 and r["row_success"] == 0
            for f in RUN.ADDENDUM_METRIC_FIELDS:
                assert r[f] is None

    def test_an_unfiltered_failure_still_covers_every_learner(
            self, scenarios, monkeypatch):
        """`learner_filter=None` is what the FROZEN arm passes, so the 182,400
        total must be unchanged by the R10 fix."""
        def explode(*a, **k):
            raise RuntimeError("injected setup failure (R10 probe)")

        monkeypatch.setattr(RUN.FIN, "build_eta_table", explode)
        rows = _probe(scenarios[0], learner_filter=None)
        assert len(rows) == self._expected(PROBE_ENCODERS, None)
        cfgs = [c for c in RUN.encoder_configs() if c[0] in PROBE_ENCODERS]
        assert {r["learner"] for r in rows} == {
            l for e, _b, lab in cfgs for l in DES.learners_for(e, lab)}

    def test_the_frozen_row_total_is_untouched_by_the_fix(self):
        """The full-arm projection is computed with no filter at all."""
        wl = RUN.work_list()
        assert wl["projected_rows_executed"] == 182_400 == wl["frozen_row_count"]
        per_rep = sum(len(RUN._learners_for(e, lab, None))
                      for e, _b, lab in RUN.encoder_configs())
        assert per_rep * len(RUN.METRICS) == wl["rows_per_replicate"] == 76

    @pytest.mark.parametrize("lf", [None, ("logistic",),
                                    ("bayes_z_oracle", "logistic")])
    def test_the_shared_helper_is_the_only_learner_selection(self, lf):
        for enc, _b, lab in RUN.encoder_configs():
            want = [l for l in DES.learners_for(enc, lab)
                    if lf is None or l in lf]
            assert RUN._learners_for(enc, lab, lf) == want


# ===========================================================================
# R12 -- mcse == 0.0 on an injective encoder is CORRECT, not a defect
# ===========================================================================

class TestZeroMonteCarloErrorIsLegitimate:
    """Recorded so that nobody later "fixes" it.

    At d = M = 5 the label encoder is injective over all 1024 states, so
    ebar(Z) == eta(X) pointwise, the representation loss is identically zero in
    every evaluation draw, and its Monte Carlo standard error is EXACTLY 0.0 --
    a zero-variance estimator, not a missing number. Any assertion of the form
    "mcse must be nonzero" must therefore be made on a MERGING encoder.
    """

    def test_injective_encoder_has_exactly_zero_mcse_and_a_merging_one_does_not(
            self, scenarios):
        rows = _probe(scenarios[0], encoder_filter=("label", "hash_shared"),
                      learner_filter=("bayes_z_oracle",))
        by_enc = {}
        for r in rows:
            if r["status"] == Status.SUCCESS.value:
                by_enc.setdefault(r["encoder"], []).append(r)
        assert set(by_enc) == {"label", "hash_shared"}
        for r in by_enc["label"]:
            assert r["fiber_count"] == 1024          # injective over the space
            assert r["mcse"] == 0.0                  # exact zero, never NULL
            assert r["mcse"] is not None
        assert any(r["mcse"] > 0.0 for r in by_enc["hash_shared"]), (
            "the merging encoder must carry a positive Monte Carlo error; that "
            "is where a 'mcse > 0' assertion belongs")
