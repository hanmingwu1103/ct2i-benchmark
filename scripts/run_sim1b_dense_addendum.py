"""Phase A1 runner: dense-signal Simulation 1B addendum (d = M = 5, K = 4).

SIMULATION ONLY. No real dataset, no image, no GPU, no manuscript.

Design authority
---------------
  simulation-results-ct2i/01A_ADDENDUM_PROTOCOL_FREEZE.yaml   (IMMUTABLE design)
  simulation-results-ct2i/01B_ADDENDUM_ADVISOR_RULINGS.yaml   (binding rulings D13-D18)

Both files are READ, never written, by this module. 01A owns the factor grid,
the seed rule and the tolerances; 01B owns the advisor rulings that A0 left
open (D13 inference scheme, D14 signal-normalised estimands, D15 manifest
coverage, D16 E1 decision rules, D17 independent reference check, D18 this
runner gate).

Why this file exists (decision D18 / criterion AD13)
---------------------------------------------------
A0 could not test code A0 was forbidden to write. This module is the SINGLE
SOURCE OF TRUTH for the addendum seed rule: `addendum_block`, `addendum_seed`,
`addendum_oof_seed`, `addendum_train_seed`, `addendum_eval_seed` and
`addendum_scenarios` are defined HERE and imported by every consumer
(tests/test_a0_dense_addendum_properties.py, the microbenchmark). The seed
semantics are transcribed from 01A `seeds:` verbatim and must not be changed:

  block key      (M, K, marginal, tau, interaction_pairs)
                 delta_eta and n_train are EXCLUDED so both arms of every
                 within-DGP contrast share one parameter draw
  base offset    2_000_000_000
  formula        seed = 2_000_000_000
                        + 1000 * (blake2b(repr(block), digest_size=4) % 1e6)
                        + replicate
  train draw     seed + 100_000
  eval draw      seed + 200_000
  oof            91_211 + 17 * replicate
  learner        seed
  n_train pairing  n = 500 is the FIRST 500 ROWS of the n = 5000 draw
                   (explicit slicing; re-drawing at n=500 would unpair the
                   LABELS -- measured, see AT8)

Defects this runner corrects relative to `run_sim1b_finite.py`
--------------------------------------------------------------
D18-a  a setup exception no longer produces `except Exception: continue` and
       ZERO rows. Every ATTEMPTED cell emits a typed row, carrying the
       exception type and message, at whichever stage it failed.
D18-b  non-SUCCESS rows carry NULL (None) in every metric column. Never 0,
       never a chance-level 0.5, never NaN-as-sentinel-zero. Enforced by
       routing through `sim1_finite.cell_result`, which raises if a failure
       row tries to smuggle a metric.
D18-c  `exact_or_mc` no longer labels every row "mc". At (M, K) = (5, 4) the
       full state space is 1024 <= ENUM_CAP, so the POPULATION quantities are
       exact for all 13 configurations, both hash encoders included. The row
       therefore carries THREE explicit labels rather than one ambiguous one:
         population_quantity_kind  exact | mc | not_identified   (the pop_* columns)
         sample_quantity_kind      mc                            (the risk_*/*_loss columns)
         exact_or_mc               = population_quantity_kind, kept under the
                                     05b column name for schema continuity
       The finite-sample Rao-Blackwellised columns are and remain Monte Carlo;
       `mcse` is their error. They are never relabelled "exact".
D18-d  `fiber_count`, `collision_count` and `occupied_buckets` are WRITTEN
       (known gap G1: the 1B runner declares them and never assigns them, so
       both hash diagnostics are NULL across all 1,094,400 frozen rows).
D18-e  EXECUTED rows and SUCCESSFUL rows are distinguished in the schema
       (`row_executed`, `row_success`) and in the printed summary. This is the
       TabS1 defect (decision D12) at its source.
D18-f  n_train in {500, 5000} both run, from one nested draw.

Signal-normalised estimands (advisor ruling D14)
------------------------------------------------
  relative_log_gap   = (R_log*(Z)   - R_log*(X))   / (H(Y) - R_log*(X))
  relative_brier_gap = (R_Brier*(Z) - R_Brier*(X)) / Var{eta(X)}

`sim1_core.eta_raw` returns 1/(1+exp(-tau*g)), so eta IS P(Y=1|X) and NOT a
linear predictor. Hence Var{eta(X)} is the correct Brier-scale normaliser and

  Var{eta(X)} = Var(Y) - R_Brier*(X),  Var(Y) = p(1-p),  p = E[eta],
                                       R_Brier*(X) = E[eta(1-eta)]

which is implemented that way and asserted as an identity in the property
tests. Both denominators are nonnegative population quantities that vanish
exactly when eta is constant. When a denominator falls below the frozen
numerical tolerance the row records the status token NOT_IDENTIFIED and a NULL
value -- never 0.

Usage
-----
  run_sim1b_dense_addendum.py --dry-run                 enumerate, run nothing
  run_sim1b_dense_addendum.py --execute [--out PATH]    run the arm

`--dry-run` is the DEFAULT. Executing cells requires the explicit `--execute`
flag AND a present, valid 01B ruling file, because Phase A1 execution is gated
on advisor approval.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import os
import resource
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

from ct2i_benchmark.simulations import sim1_core as CORE       # noqa: E402
from ct2i_benchmark.simulations import sim1_design as DES      # noqa: E402
from ct2i_benchmark.simulations import sim1_finite as FIN      # noqa: E402
from ct2i_benchmark.statuses import Status                     # noqa: E402

# The frozen coordinate-wise ebar route and the frozen hash diagnostics are
# IMPORTED, not re-implemented: duplicating either would recreate exactly the
# defect D18 exists to remove.
from run_sim1a_exact import hash_diagnostics                   # noqa: E402
from run_sim1b_finite import ebar_coordinatewise               # noqa: E402

PKG = REPO / "simulation-results-ct2i"
RAW = PKG / "raw"
FREEZE_01 = PKG / "01_PROTOCOL_FREEZE.yaml"
FREEZE_01A = PKG / "01A_ADDENDUM_PROTOCOL_FREEZE.yaml"
RULINGS_01B = PKG / "01B_ADDENDUM_ADVISOR_RULINGS.yaml"
DEFAULT_OUT = RAW / "sim1b_dense_addendum_replicates.csv"

# ---------------------------------------------------------------------------
# The frozen addendum design (01A `design:` and `seeds:`), transcribed.
# Every constant below is asserted against the YAML by `verify_against_freeze`,
# so a drift between this module and the freeze is a test failure, not a
# silent divergence.
# ---------------------------------------------------------------------------
COMPONENT = "1BD"
M_ADD, K_ADD, D_ADD = 5, 4, 5
N_CELLS = K_ADD ** D_ADD                     # 1024, exactly enumerable
MARGINALS = ("uniform", "zipf")
TAUS = (0.5, 1.5)
N_INTS = (0, 3)                              # matched by COUNT to d=3 (decision D1)
DELTAS = (0.0, 0.1, 0.3)
N_TRAINS = (500, 5000)
N_EVAL = DES.N_EVAL                          # 50_000
REPS_ADD = 50
N_SCENARIOS_ADD = 48
ROWS_ADD = 182_400
N_TRAIN_NEST_MAX = 5000                      # the single draw n=500 is sliced from

SEED_BASE_1BD = 2_000_000_000
OOF_BASE_1BD = 91_211                        # original 1B uses 4211 + 17*replicate
TRAIN_DRAW_OFFSET = 100_000                  # inherited from the 1B runner
EVAL_DRAW_OFFSET = 200_000                   # inherited from the 1B runner

METRICS = ("logloss", "brier")
NOT_IDENTIFIED = "NOT_IDENTIFIED"
IDENTIFIED_EXACT = "IDENTIFIED_EXACT"

# D17 (01B rulings.D17.sampling_rule): ONE frozen replicate per scenario,
# all 48 scenarios x all 13 encoder configurations = 624 reference cells, which
# is the advisor's stated minimum. The replicate is a pure function of the
# scenario id -- the implementer chooses nothing.
#
# RECONCILIATION R1 (2026-08-24). An earlier draft of this runner fixed
# `REFERENCE_REPLICATES = (1,)`, i.e. replicate 1 for every scenario. 01B
# `rulings.D17.sampling_rule.frozen_replicate_rule` freezes a DIFFERENT sample
# of the same size and its `why_not_replicate_1_for_all` clause declines the
# runner's choice by name. 01B is the frozen ruling file, so the runner follows
# 01B. It does so by READING the rule expression out of 01B at run time -- there
# is no second copy of the rule in this file to drift from. D18 makes the runner
# the single source of truth for the SEED rule; D17 makes 01B the single source
# of truth for the SAMPLING rule, and each side reads the other rather than
# restating it.
D17_REFERENCE_CELLS = 624               # the advisor's stated minimum, 01B cell_count
D17_RULE_KEY = "rulings.D17.sampling_rule.frozen_replicate_rule.rule"
D17_CELL_COUNT_KEY = "rulings.D17.sampling_rule.cell_count"

# Only these names and calls may appear in the 01B rule expression. The rule is
# DATA read from a frozen protocol file, not code: it is parsed, whitelisted and
# then evaluated, so a rule that tried to do anything other than map a scenario
# id to an integer is refused instead of executed.
_D17_ALLOWED_CALLS = frozenset({"int"})
_D17_ALLOWED_NAMES = frozenset({"scenario_id", "scenario"})
_D17_RULE_CACHE: dict = {}


def _d17_rule_text(rulings: dict | None = None) -> str:
    """The verbatim rule expression from 01B, e.g. `int(scenario_id[-4:])`.

    Read at run time from `rulings.D17.sampling_rule.frozen_replicate_rule.rule`
    so that amending 01B amends the runner's behaviour, and so that a divergence
    between the two is impossible rather than merely tested for.
    """
    if rulings is None:
        rulings, _missing = load_rulings_01b(strict=False)
    if rulings is None:
        raise FileNotFoundError(
            f"the D17 sampling rule lives in {RULINGS_01B.name}, which is "
            f"absent; the runner will not substitute a reference sample of its "
            f"own choosing (reconciliation R1).")
    try:
        raw = str(_dig(rulings, D17_RULE_KEY))
    except KeyError:
        raise KeyError(
            f"{RULINGS_01B.name} does not provide {D17_RULE_KEY}; the D17 "
            f"reference sample is undefined and the runner will not guess it."
        ) from None
    # "reference_replicate(scenario) = int(scenario_id[-4:])" -> the RHS.
    expr = raw.split("=", 1)[1].strip() if "=" in raw else raw.strip()
    if not expr:
        raise ValueError(f"{RULINGS_01B.name} {D17_RULE_KEY} is empty: {raw!r}")
    return expr


def _d17_compile(expr: str):
    """Parse + whitelist the 01B rule expression. Anything unexpected raises."""
    import ast
    tree = ast.parse(expr, mode="eval")
    call_funcs = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for node in ast.walk(tree):
        if id(node) in call_funcs and isinstance(node, ast.Name):
            continue        # checked as part of its ast.Call below
        if isinstance(node, (ast.Expression, ast.Subscript, ast.Slice,
                             ast.Constant, ast.Index)):
            continue
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            continue
        if isinstance(node, ast.Name):
            if node.id not in _D17_ALLOWED_NAMES:
                raise ValueError(
                    f"D17 rule {expr!r} refers to {node.id!r}, which is not one "
                    f"of {sorted(_D17_ALLOWED_NAMES)}")
            continue
        if isinstance(node, ast.Call):
            if not (isinstance(node.func, ast.Name)
                    and node.func.id in _D17_ALLOWED_CALLS):
                raise ValueError(
                    f"D17 rule {expr!r} calls something other than "
                    f"{sorted(_D17_ALLOWED_CALLS)}")
            continue
        if isinstance(node, (ast.Load, ast.USub)):
            continue
        raise ValueError(
            f"D17 rule {expr!r} contains an unsupported construct "
            f"{type(node).__name__}; the rule must be a pure function of the "
            f"scenario id")
    return compile(tree, filename=f"<{RULINGS_01B.name}:{D17_RULE_KEY}>",
                   mode="eval")


def _d17_rule(rulings: dict | None = None):
    """(expr_text, code_object), cached per (path, mtime, size) of 01B."""
    try:
        st = RULINGS_01B.stat()
        key = (str(RULINGS_01B), st.st_mtime_ns, st.st_size)
    except OSError:
        key = (str(RULINGS_01B), None, None)
    if _D17_RULE_CACHE.get("key") != key or rulings is not None:
        expr = _d17_rule_text(rulings)
        _D17_RULE_CACHE.clear()
        _D17_RULE_CACHE.update(key=key, expr=expr, code=_d17_compile(expr))
    return _D17_RULE_CACHE["expr"], _D17_RULE_CACHE["code"]


def reference_replicate(scenario_id: str, rulings: dict | None = None) -> int:
    """The D17 frozen reference replicate for `scenario_id`, PER 01B.

    The rule is not written here. It is read from
    `01B rulings.D17.sampling_rule.frozen_replicate_rule.rule`, which currently
    reads `reference_replicate(scenario) = int(scenario_id[-4:])`: S1BD-0001 ->
    replicate 1, ..., S1BD-0048 -> replicate 48. Replicate indices are 1-based
    in this package and 1 <= 48 <= 50, so every scenario's frozen replicate
    exists. 01B's `why_not_replicate_1_for_all` explains why a single fixed
    replicate index was declined; see reconciliation R1.
    """
    expr, code = _d17_rule(rulings)
    sid = str(scenario_id)
    value = eval(code, {"__builtins__": {"int": int}},           # noqa: S307
                 {"scenario_id": sid, "scenario": sid})
    rep = int(value)
    if not 1 <= rep <= REPS_ADD:
        raise ValueError(
            f"the 01B D17 rule {expr!r} maps {scenario_id!r} to replicate "
            f"{rep}, outside the frozen range 1..{REPS_ADD}")
    return rep


def d17_reference_cells(rulings: dict | None = None) -> int:
    """01B `rulings.D17.sampling_rule.cell_count`, with the minimum as fallback."""
    if rulings is None:
        rulings, _missing = load_rulings_01b(strict=False)
    if rulings is None:
        return D17_REFERENCE_CELLS
    try:
        return int(_dig(rulings, D17_CELL_COUNT_KEY))
    except (KeyError, TypeError, ValueError):
        return D17_REFERENCE_CELLS


# ---------------------------------------------------------------------------
# SEED RULE -- the single source of truth (decision D18 / criterion AD13)
# ---------------------------------------------------------------------------

def addendum_block(marginal: str, tau: float, n_int: int) -> tuple:
    """Block key: same SHAPE and same exclusions as the frozen 1B block.

    (M, K, marginal, tau, interaction_pairs). `delta_eta` and `n_train` are
    EXCLUDED. MEASURED effect of those exclusions: at fixed (block, replicate)
    the three `delta_eta` levels and the two `n_train` levels share ONE
    parameter draw bit for bit (max|da| = max|db| = exactly 0.0), which is what
    keeps every within-DGP contrast paired. Asserted by
    tests/test_a0_dense_addendum_properties.py::
    test_parameter_draw_identical_across_delta_eta.

    WHAT THIS DOCSTRING NO LONGER CLAIMS (corrected 2026-08-25). It previously
    stated that the exclusions "make the 48 scenarios cluster into 8
    parameter-draw blocks (decision D13: those 8 blocks, with 7 degrees of
    freedom, are the inferential units)". That premise was REFUTED BY
    MEASUREMENT at Phase A0.1. `addendum_seed` adds the replicate index into
    the seed and `draw_params` is called inside the replicate loop, so `a` and
    `b` are drawn AFRESH FOR EVERY REPLICATE: 8 blocks x 50 replicates = 400
    distinct parameter draws per arm, not 8. The repository's own property test
    ::test_replicate_still_varies_the_draw already asserted this.

    The block structure, stated factually: the 8 blocks are a complete,
    exhaustively enumerated 2x2x2 factorial of FIXED design factors (marginal x
    tau x interaction_pairs). The random unit is the draw, and the only cluster
    is (block, replicate), whose 6 members are the 3 delta_eta x 2 n_train
    scenarios that share it.

    WHICH UNIT GOVERNS INFERENCE IS AN OPEN QUESTION, NOT A FACT THIS FILE MAY
    ASSERT: see 01B_ADDENDUM_ADVISOR_RULINGS.yaml
    `advisor_confirmation_requested.Q6` (severity BLOCKS_A1_INFERENCE) and
    `rulings.D13.premise_refuted_at_A0_1`. Provenance and the re-runnable probe:
    simulation-results-ct2i/S0B_D13_PREMISE_INVESTIGATION.md,
    scripts/s0b_d13_premise_probe.py. This function's RETURN VALUE is unchanged
    and supports either unit.
    """
    return (M_ADD, K_ADD, marginal, tau, n_int)


def addendum_seed(block: tuple, replicate: int) -> int:
    """Addendum DGP seed. Same blake2b construction as `dgp_block_seed`, new base.

    Deliberately NOT routed through `sim1_core.dgp_block_seed`: that module
    validates its component against SEED_BASE and would have to be edited to
    accept a "1BD" tag, and it produced the frozen 1B output, so it is left
    byte-identical (decision D3). The addendum owns its base offset here.
    """
    h = int.from_bytes(
        hashlib.blake2b(repr(tuple(block)).encode(), digest_size=4).digest(),
        "little")
    return SEED_BASE_1BD + 1000 * (h % 1_000_000) + int(replicate)


def addendum_oof_seed(replicate: int) -> int:
    """Out-of-fold seed channel, disjoint from the original 4211 + 17*r channel."""
    return OOF_BASE_1BD + 17 * int(replicate)


def addendum_train_seed(seed: int) -> int:
    """Training draw seed. One draw of `N_TRAIN_NEST_MAX` rows serves both n_train."""
    return int(seed) + TRAIN_DRAW_OFFSET


def addendum_eval_seed(seed: int) -> int:
    return int(seed) + EVAL_DRAW_OFFSET


@dataclass
class AddendumScenario:
    """One of the 48 frozen addendum scenarios.

    Attribute access (`.scenario_id`, `.factors`, `.seeds`) mirrors
    `sim1_design.Scenario` so `_s1_parallel.run_parallel` accepts it unchanged.
    Mapping access (`s["marginal"]`, `s["seeds"]`) is also supported so the
    A0 property tests can import this enumeration in place of their own
    dict-based copy without rewriting every assertion.
    """
    scenario_id: str
    component: str
    factors: dict
    block: tuple
    replicates: int
    seeds: list = field(repr=False)

    def __getitem__(self, key):
        if key in self.factors:
            return self.factors[key]
        try:
            return getattr(self, key)
        except AttributeError as exc:                            # noqa: BLE001
            raise KeyError(key) from exc

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


def addendum_scenarios() -> list[AddendumScenario]:
    """The 48 frozen addendum scenarios, in the frozen enumeration order.

    01A `design.scenario_enumeration_order`:
      itertools.product(marginal, tau, interaction_pairs, delta_eta, n_train),
      index from 1. Frozen so scenario ids cannot be reassigned later.
    """
    out: list[AddendumScenario] = []
    for i, (marg, tau, ni, de, nt) in enumerate(
            itertools.product(MARGINALS, TAUS, N_INTS, DELTAS, N_TRAINS), start=1):
        blk = addendum_block(marg, tau, ni)
        out.append(AddendumScenario(
            scenario_id=f"S1BD-{i:04d}",
            component=COMPONENT,
            factors=dict(M=M_ADD, K=K_ADD, d_active=D_ADD, marginal=marg, tau=tau,
                         n_int=ni, delta_eta=de, n_train=nt),
            block=blk,
            replicates=REPS_ADD,
            seeds=[addendum_seed(blk, r) for r in range(1, REPS_ADD + 1)]))
    return out


def addendum_blocks() -> list[tuple]:
    """The 8 blocks: the complete 2x2x2 factorial of the fixed design factors.

    marginal x tau x interaction_pairs. These are FIXED, exhaustively
    enumerated design factors, not a random sample of blocks; the parameter
    draw varies with the replicate (see `addendum_block`). Whether the 8 blocks
    or the 400 draws are the inferential unit is 01B `Q6`, open.
    """
    return [addendum_block(m, t, n)
            for m in MARGINALS for t in TAUS for n in N_INTS]


# ---------------------------------------------------------------------------
# Protocol files: 01A is required, 01B is required to EXECUTE
# ---------------------------------------------------------------------------

# Keys this runner reads from 01B. A sibling agent authors that file; the
# runner names exactly what it expects so the two can be reconciled rather
# than guessed at. Anything missing is reported by name, never defaulted
# silently for a binding quantity.
REQUIRED_01B_KEYS = (
    "provenance.file_id",
    "provenance.phase",
    "rulings.D13.status",
    "rulings.D13.n_blocks",                                       # expect 8
    "rulings.D13.degrees_of_freedom",                             # expect 7
    "rulings.D13.block_key",
    "rulings.D14.status",
    "rulings.D14.estimands.normalized.relative_log_gap.denominator",
    "rulings.D14.estimands.normalized.relative_brier_gap.denominator",
    "rulings.D14.denominator_tolerance.frozen_value",             # expect 1.0e-6
    "rulings.D15.status",
    "rulings.D16.status",
    "rulings.D17.status",
    "rulings.D17.sampling_rule.cell_count",                       # expect 624
    "rulings.D17.sampling_rule.frozen_replicate_rule.rule",
    "rulings.D17.persisted_columns.columns",
    "rulings.D18.status",
    "rulings.D18.encoded_as",
)


def _dig(tree, dotted: str):
    cur = tree
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(dotted)
        cur = cur[part]
    return cur


def load_yaml(path: Path) -> dict:
    import yaml
    if not path.exists():
        raise FileNotFoundError(
            f"required protocol file is missing: {path}\n"
            f"The A1 runner reads BOTH the frozen design and the advisor "
            f"rulings and refuses to guess either.")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_freeze_01a() -> dict:
    return load_yaml(FREEZE_01A)


def load_tolerances() -> dict:
    """Tolerances are inherited verbatim from the ORIGINAL frozen protocol."""
    return load_yaml(FREEZE_01)["tolerances"]


def load_rulings_01b(strict: bool = True) -> tuple[dict | None, list[str]]:
    """Load 01B defensively. Returns (tree_or_None, missing_key_list).

    strict=True  -- the file must exist and carry every REQUIRED_01B_KEY;
                    anything else raises with the exact path / key names.
    strict=False -- used by --dry-run, which must be able to enumerate the
                    work list while the ruling file is still being authored.
                    The caller is told exactly what is missing.
    """
    if not RULINGS_01B.exists():
        msg = (f"MISSING ADVISOR RULING FILE: {RULINGS_01B}\n"
               f"  Phase A1 execution is gated on the binding rulings D13-D18.\n"
               f"  This runner reads, and expects that file to provide, the keys:\n"
               + "".join(f"    - {k}\n" for k in REQUIRED_01B_KEYS))
        if strict:
            raise FileNotFoundError(msg)
        return None, list(REQUIRED_01B_KEYS)

    tree = load_yaml(RULINGS_01B)
    missing = []
    for key in REQUIRED_01B_KEYS:
        try:
            _dig(tree, key)
        except KeyError:
            missing.append(key)
    if missing and strict:
        raise KeyError(
            f"{RULINGS_01B} is present but does not provide: {missing}. "
            f"The A1 runner will not substitute a default for a binding ruling.")
    return tree, missing


def relative_gap_tolerance(rulings: dict | None = None) -> float:
    """The frozen numerical tolerance below which a D14 denominator is NOT_IDENTIFIED.

    01B freezes it at `rulings.D14.denominator_tolerance.frozen_value` = 1.0e-6,
    reusing the inherited `tolerances.positive_gap_min` from
    01_PROTOCOL_FREEZE.yaml. Both D14 denominators -- I(Y;X) and Var{eta(X)} --
    are nonnegative gap-shaped population quantities, which is exactly what
    `positive_gap_min` bounds. The value 01B names is cross-checked against the
    parent freeze's tolerance table, so it can never be invented in either file;
    when 01B is absent (dry runs only) the same inherited value is used.
    """
    tol = load_tolerances()
    fallback = float(tol["positive_gap_min"])
    if rulings is None:
        return fallback
    try:
        value = float(_dig(rulings, "rulings.D14.denominator_tolerance.frozen_value"))
    except KeyError:
        return fallback
    # The value 01B freezes must be one the parent freeze already contains, so
    # a tolerance can never be invented in the ruling file or in this runner.
    if not any(isinstance(v, (int, float)) and float(v) == value
               for v in tol.values()):
        raise ValueError(
            f"01B rulings.D14.denominator_tolerance.frozen_value = {value!r} "
            f"matches no entry of {FREEZE_01.name} tolerances "
            f"{ {k: v for k, v in tol.items() if isinstance(v, (int, float))} }")
    return value


def verify_against_freeze() -> list[str]:
    """Assert every constant above equals the frozen 01A value. Returns findings."""
    f = load_freeze_01a()
    d, s = f["design"], f["seeds"]
    checks = [
        ("design.M", d["M"], M_ADD), ("design.K", d["K"], K_ADD),
        ("design.d_active", d["d_active"], D_ADD),
        ("design.marginal", tuple(d["marginal"]), MARGINALS),
        ("design.tau", tuple(d["tau"]), TAUS),
        ("design.interaction_pairs", tuple(d["interaction_pairs"]), N_INTS),
        ("design.delta_eta", tuple(d["delta_eta"]), DELTAS),
        ("design.n_train", tuple(d["n_train"]), N_TRAINS),
        ("design.n_eval", d["n_eval"], N_EVAL),
        ("design.replicates", d["replicates"], REPS_ADD),
        ("design.scenario_count", d["scenario_count"], N_SCENARIOS_ADD),
        ("design.row_count.total", d["row_count"]["total"], ROWS_ADD),
        ("design.encoders.configuration_count",
         d["encoders"]["configuration_count"],
         len(DES.encoder_configs("B", M_ADD, K_ADD))),
        ("seeds.base_offset", s["base_offset"], SEED_BASE_1BD),
        ("seeds.derived_seeds.train_draw", s["derived_seeds"]["train_draw"],
         f"seed + {TRAIN_DRAW_OFFSET}"),
        ("seeds.derived_seeds.eval_draw", s["derived_seeds"]["eval_draw"],
         f"seed + {EVAL_DRAW_OFFSET}"),
    ]
    bad = [f"{name}: freeze={got!r} runner={want!r}"
           for name, got, want in checks
           if not _freeze_equal(name, got, want)]
    return bad


def _freeze_equal(name, got, want) -> bool:
    if name.startswith("seeds.derived_seeds"):
        return str(got).replace("_", "").split("#")[0].strip() == \
               str(want).replace("_", "").strip()
    return got == want


# ---------------------------------------------------------------------------
# Row schema
# ---------------------------------------------------------------------------

# Finite-sample (Monte Carlo) metric columns inherited from the 1B schema.
SAMPLE_METRIC_FIELDS = tuple(FIN.METRIC_FIELDS)

# Exact population metric columns added by the addendum.
POP_METRIC_FIELDS = (
    "pop_risk_x_logloss", "pop_risk_z_logloss",
    "pop_risk_x_brier", "pop_risk_z_brier",
    "pop_gap_logloss", "pop_gap_brier",
    "pop_theoretical_gap_logloss", "pop_theoretical_gap_brier",
    "pop_identity_error_logloss", "pop_identity_error_brier",
    "p_y", "entropy_y", "var_eta_x",
    "relative_log_gap", "relative_brier_gap",
    "fiber_count", "merged_fiber_count", "merged_fiber_mass",
    "max_fiber_posterior_spread", "collision_count", "occupied_buckets",
    "n_cells",
    # D17 persisted columns, named exactly as 01B rulings.D17.persisted_columns
    "reference_log_gap", "reference_brier_gap",
    "production_log_gap", "production_brier_gap",
    "log_identity_error", "brier_identity_error",
    "abs_production_minus_reference_log",
    "abs_production_minus_reference_brier",
)

ADDENDUM_METRIC_FIELDS = SAMPLE_METRIC_FIELDS + POP_METRIC_FIELDS

FIELDS = [
    # ---- identification ----
    "scenario_id", "replicate", "seed", "component", "block_key",
    "d_active", "M", "K", "marginal", "tau", "interaction_count", "delta_eta",
    "n_train", "n_test", "encoder", "bucket_width", "width_label",
    "learner", "metric",
    # ---- execution accounting: EXECUTED is not SUCCESSFUL (decision D12) ----
    "row_executed", "row_success", "status", "failure_stage",
    "error_type", "error_message",
    # ---- finite-sample Rao-Blackwellised quantities (Monte Carlo) ----
    *SAMPLE_METRIC_FIELDS,
    # ---- exact population quantities ----
    "pop_risk_x_logloss", "pop_risk_z_logloss",
    "pop_risk_x_brier", "pop_risk_z_brier",
    "pop_gap_logloss", "pop_gap_brier",
    "pop_theoretical_gap_logloss", "pop_theoretical_gap_brier",
    "pop_identity_error_logloss", "pop_identity_error_brier",
    "p_y", "entropy_y", "var_eta_x",
    # ---- D14 signal-normalised estimands ----
    "relative_log_gap", "relative_log_gap_status",
    "relative_brier_gap", "relative_brier_gap_status",
    # ---- encoder / hash diagnostics (known gap G1: 1B never wrote these) ----
    "fiber_count", "merged_fiber_count", "merged_fiber_mass",
    "max_fiber_posterior_spread", "collision_count", "occupied_buckets",
    "n_cells",
    # D17 gate G4: the canonical digest of the cell -> fiber PARTITION this row
    # was computed under. `fiber_count` is invariant under fiber relabelling and
    # under any cardinality-preserving assignment defect; this is not.
    "fiber_fingerprint",
    # ---- exactness labelling (D18-c) ----
    "exact_or_mc", "population_quantity_kind", "sample_quantity_kind",
    "theoretical_gap_status",
    # ---- D17 independent reference implementation (01B column names) ----
    "reference_checked",
    "reference_log_gap", "reference_brier_gap",
    "production_log_gap", "production_brier_gap",
    "log_identity_error", "brier_identity_error",
    "abs_production_minus_reference_log",
    "abs_production_minus_reference_brier",
    # ---- provenance and cost ----
    "protocol_freeze_01a", "advisor_rulings_01b", "cpu_seconds",
    "warning", "notes",
]

_FIELD_SET = set(FIELDS)


def addendum_row(scenario_id: str, status: Status | str,
                 metrics: dict | None = None, **fields) -> dict:
    """Build ONE typed addendum row, enforcing the null-metric rule (D18-b).

    Routed through `sim1_finite.cell_result` so the frozen discipline is
    reused rather than re-implemented: a SUCCESS row must carry metrics, and a
    non-SUCCESS row may not smuggle any. The addendum's extra population metric
    columns obey the same rule and are nulled here explicitly.
    """
    st = Status(status)
    metrics = dict(metrics or {})
    unknown = set(metrics) - set(ADDENDUM_METRIC_FIELDS)
    if unknown:
        raise ValueError(f"{scenario_id}: unknown metric fields {sorted(unknown)}")
    bad_fields = set(fields) - _FIELD_SET
    if bad_fields:
        raise ValueError(f"{scenario_id}: unknown row fields {sorted(bad_fields)}")
    if st is not Status.SUCCESS and metrics:
        raise ValueError(f"non-SUCCESS cell {scenario_id} must not carry metrics")
    if st is Status.SUCCESS and not metrics:
        raise ValueError(f"SUCCESS cell {scenario_id} must carry metrics")

    inherited = ({k: metrics.get(k) for k in SAMPLE_METRIC_FIELDS}
                 if st is Status.SUCCESS else None)
    base = FIN.cell_result(scenario_id, st, inherited)

    row = {k: None for k in FIELDS}
    row.update(fields)
    row.update(base)
    if st is Status.SUCCESS:
        for k in POP_METRIC_FIELDS:
            row[k] = metrics.get(k)
    else:
        for k in ADDENDUM_METRIC_FIELDS:
            row[k] = None
    row["row_executed"] = 1
    row["row_success"] = 1 if st is Status.SUCCESS else 0
    row["component"] = row.get("component") or COMPONENT
    row["sample_quantity_kind"] = row.get("sample_quantity_kind") or "mc"
    return row


# ---------------------------------------------------------------------------
# D14 estimands
# ---------------------------------------------------------------------------

def population_signal_scales(p_cell: np.ndarray, eta: np.ndarray) -> dict:
    """P(Y=1), H(Y), Var{eta(X)} and the two Bayes-on-X risks, exactly.

    `sim1_core.eta_raw` returns 1/(1+exp(-tau*g)): eta IS the conditional
    probability P(Y=1|X), never a linear predictor. So

        Var{eta(X)} = Var(Y) - R_Brier*(X)
                    = p(1-p) - E[eta(1-eta)]

    is the Brier-scale normaliser D14 rules, and it is computed here from that
    identity rather than from a second moment, so the identity is load-bearing
    and testable rather than decorative.
    """
    p_cell = np.asarray(p_cell, float)
    eta = np.asarray(eta, float)
    p_y = float((p_cell * eta).sum())
    risk_log_x, risk_bri_x = CORE.bayes_risks_x(p_cell, eta)
    var_y = p_y * (1.0 - p_y)
    var_eta = var_y - risk_bri_x
    h_y = float(CORE._binary_entropy(np.array([p_y]))[0])
    return dict(p_y=p_y, entropy_y=h_y, var_y=var_y, var_eta_x=var_eta,
                risk_x_logloss=risk_log_x, risk_x_brier=risk_bri_x)


def relative_gaps(gap_logloss: float, gap_brier: float, scales: dict,
                  tolerance: float) -> dict:
    """The two D14 signal-normalised estimands, with NOT_IDENTIFIED handling.

    A denominator at or below the frozen numerical tolerance means the signal
    scale itself is (numerically) zero, so the ratio is not identified. The row
    then records the token NOT_IDENTIFIED and a NULL value. It is NEVER
    recorded as 0, which would read as "no relative gap" -- the opposite of
    "the quantity does not exist here".
    """
    den_log = scales["entropy_y"] - scales["risk_x_logloss"]      # = I(Y; X)
    den_bri = scales["var_eta_x"]                                 # = Var{eta(X)}
    out = {}
    for name, num, den in (("relative_log_gap", gap_logloss, den_log),
                           ("relative_brier_gap", gap_brier, den_bri)):
        if den is None or not np.isfinite(den) or den <= tolerance:
            out[name] = None
            out[name + "_status"] = NOT_IDENTIFIED
        else:
            out[name] = float(num) / float(den)
            out[name + "_status"] = IDENTIFIED_EXACT
    out["relative_log_gap_denominator"] = den_log
    out["relative_brier_gap_denominator"] = den_bri
    return out


# ---------------------------------------------------------------------------
# Work-list enumeration
# ---------------------------------------------------------------------------

def encoder_configs() -> list[tuple[str, int | None, str]]:
    """The 13 frozen encoder configurations (7 non-hash + 2 hash x 3 widths)."""
    return DES.encoder_configs("B", M_ADD, K_ADD)


def work_list() -> dict:
    """Full enumeration of the addendum, with EXECUTED-row projections.

    Nothing is executed here. Every count is derived from the frozen grid, and
    the row total is compared with 01A `design.row_count.total`.
    """
    scen = addendum_scenarios()
    cfgs = encoder_configs()
    per_rep_learner_cells = sum(len(DES.learners_for(e, lab)) for e, _b, lab in cfgs)
    rows_per_replicate = per_rep_learner_cells * len(METRICS)
    n_replicate_cells = len(scen) * REPS_ADD
    n_encoder_cells = n_replicate_cells * len(cfgs)
    n_learner_cells = n_replicate_cells * per_rep_learner_cells
    projected_rows = n_replicate_cells * rows_per_replicate
    frozen_total = load_freeze_01a()["design"]["row_count"]["total"]
    return dict(
        scenarios=len(scen),
        encoder_configs=len(cfgs),
        replicates=REPS_ADD,
        n_train_levels=sorted(N_TRAINS),
        blocks=len(addendum_blocks()),
        learner_cells_per_replicate=per_rep_learner_cells,
        rows_per_replicate=rows_per_replicate,
        replicate_cells=n_replicate_cells,
        encoder_cells=n_encoder_cells,
        learner_cells=n_learner_cells,
        projected_rows_executed=projected_rows,
        frozen_row_count=frozen_total,
        matches_freeze=projected_rows == frozen_total,
        reference_cells=len(scen) * len(cfgs),      # one frozen replicate each
        reference_cells_required=d17_reference_cells(),
        scenario_ids=[s.scenario_id for s in scen],
    )


# ---------------------------------------------------------------------------
# The scenario worker
# ---------------------------------------------------------------------------

def _base_row_fields(s: AddendumScenario, rep: int, seed: int,
                     n_eval: int) -> dict:
    f = s.factors
    # NOTE: scenario_id is deliberately absent -- it is passed positionally to
    # `addendum_row`, so including it here would collide on the splat.
    return dict(replicate=rep, seed=seed,
                component=COMPONENT, block_key=repr(s.block),
                d_active=D_ADD, M=f["M"], K=f["K"], marginal=f["marginal"],
                tau=f["tau"], interaction_count=f["n_int"],
                delta_eta=f["delta_eta"], n_train=f["n_train"], n_test=n_eval,
                protocol_freeze_01a=FREEZE_01A.name,
                advisor_rulings_01b=RULINGS_01B.name)


ROW_PRIMARY_KEY = ("scenario_id", "replicate", "encoder", "width_label",
                   "learner", "metric")


class AddendumRowEmissionError(RuntimeError):
    """The typed-failure-row BUILDER itself failed (reconciliation C3).

    Typed-row accounting is the guarantee D18 rests on, so a failure inside the
    machinery that materialises the absence must be LOUD. It is never allowed
    to leave the worker returning a short row list that looks complete.
    """


class AddendumWorkerAborted(RuntimeError):
    """A `BaseException` (KeyboardInterrupt, SystemExit, ...) aborted a worker.

    Reconciliation C3: `except Exception` does not cover `BaseException`, so a
    cancellation used to escape `scenario_worker` with the rows accumulated so
    far silently discarded and the parallel driver writing an EMPTY checkpoint
    for the scenario. The worker now emits typed rows for the cells the abort
    interrupted, attaches every row it holds to this exception, and raises a
    plain `RuntimeError` subclass so the payload survives the process-pool
    boundary. An aborted run is NOT retainable; the parent materialises the
    scenario's full attempted-cell manifest as typed failure rows.
    """

    def __init__(self, cause: BaseException, rows: list[dict]):
        super().__init__(f"worker aborted by {type(cause).__name__}: "
                         f"{str(cause)[:200]}")
        self.cause_type = type(cause).__name__
        self.cause_message = str(cause)[:300]
        self.rows = list(rows)


def primary_key(row: dict) -> tuple:
    """The (scenario, replicate, encoder, width, learner, metric) identity.

    AD6 counts EXECUTED rows and requires exactly 182,400 of them, which is only
    meaningful if the map from attempted cells to rows is injective. It is this
    key that must be unique.
    """
    return tuple(row[k] for k in ROW_PRIMARY_KEY)


def duplicate_primary_keys(rows) -> dict:
    """{key: count} for every primary key emitted more than once."""
    from collections import Counter
    c = Counter(primary_key(r) for r in rows)
    return {k: n for k, n in c.items() if n > 1}


def _learners_for(enc: str, lab: str, learner_filter=None) -> list[str]:
    """The learners ATTEMPTED for one encoder configuration.

    ONE definition, used by both the success path and the typed-failure path,
    so an attempted cell is the same cell whichever way it ends (R10).
    """
    return [l for l in DES.learners_for(enc, lab)
            if learner_filter is None or l in learner_filter]


def attempted_cells(configs, learner_filter=None) -> list[tuple]:
    """(encoder, bucket_width, width_label, learner, metric) for ONE replicate.

    The single definition of what "an attempted cell" is. Every path -- success,
    typed failure, parent-side materialisation after a worker death -- derives
    its rows from this list, so the count of attempted cells cannot depend on
    which path the cell took (R10, extended by C2/C3 to the parent).
    """
    return [(enc, Bw, lab, lrn, metric)
            for enc, Bw, lab in configs
            for lrn in _learners_for(enc, lab, learner_filter)
            for metric in METRICS]


def _typed_failure_rows(s, rep, seed, n_eval, configs, status, stage, exc,
                        warning=None, learner_filter=None) -> list[dict]:
    """A typed row for EVERY cell the failure prevented from running (D18-a).

    The 1B runner's `except Exception: continue` around the DGP draw wrote ZERO
    rows for a failed replicate, which criterion AD9 cannot detect because
    there is nothing to inspect. Here the absence is materialised: the cells
    are still ATTEMPTED, so they still emit rows, carrying the exception type
    and message and NULL metrics.

    RECONCILIATION R10 (2026-08-24). `learner_filter` used to be ignored here
    while the success path applied it, so a filtered probe emitted MORE failure
    rows than success rows for the same configuration -- an attempted-cell count
    that depended on which path the cell took. The frozen arm passes
    `learner_filter=None`, so the 182,400 total was never affected; what was
    affected is every probe-level row-count assertion. The set of ATTEMPTED
    cells must be a property of the configuration, not of whether it failed, so
    both paths now honour the same filter.
    """
    base = _base_row_fields(s, rep, seed, n_eval)
    return [
        addendum_row(
            s.scenario_id, status,
            **base, encoder=enc, bucket_width=Bw, width_label=lab,
            learner=lrn, metric=metric,
            failure_stage=stage,
            error_type=type(exc).__name__,
            error_message=str(exc)[:300],
            exact_or_mc=None, population_quantity_kind=None,
            theoretical_gap_status=None,
            reference_checked=0, warning=warning)
        for enc, Bw, lab, lrn, metric in attempted_cells(configs, learner_filter)
    ]


def _guarded_failure_rows(*a, **kw) -> list[dict]:
    """`_typed_failure_rows`, but a failure INSIDE it is loud (C3, path 3).

    If the row builder itself raises there is nothing left to inspect: the
    worker would return a short list that is indistinguishable from a scenario
    with fewer attempted cells. That case is converted into
    `AddendumRowEmissionError`, which the parallel driver materialises rather
    than silently accepting.
    """
    try:
        return _typed_failure_rows(*a, **kw)
    except BaseException as exc:                                  # noqa: BLE001
        raise AddendumRowEmissionError(
            f"the typed-failure-row builder raised "
            f"{type(exc).__name__}: {str(exc)[:200]}; typed-row accounting for "
            f"this unit cannot be completed and the run is not retainable"
        ) from exc


def _setup_failure_rows(s, n_eval, exc, warning=None, *, replicates=None,
                        encoder_filter=None, learner_filter=None) -> list[dict]:
    """Typed rows for EVERY cell of a scenario whose worker setup failed (C3).

    The manifest is rebuilt defensively here: the setup that failed is exactly
    the code that would normally provide it. If the manifest itself cannot be
    built the failure is raised as `AddendumRowEmissionError` rather than
    returned as a short (or empty) list -- loud, never silent.
    """
    try:
        configs = [c for c in encoder_configs()
                   if encoder_filter is None or c[0] in encoder_filter]
        seeds = list(s.seeds if replicates is None else s.seeds[:replicates])
        rows: list[dict] = []
        for rep, seed in enumerate(seeds, 1):
            rows.extend(_typed_failure_rows(
                s, rep, seed, n_eval, configs, Status.NUMERICAL_FAILURE,
                "worker_setup", exc, warning, learner_filter=learner_filter))
        if not rows:
            raise RuntimeError("empty attempted-cell manifest")
        return rows
    except BaseException as inner:                                # noqa: BLE001
        raise AddendumRowEmissionError(
            f"worker setup for {getattr(s, 'scenario_id', '?')} failed with "
            f"{type(exc).__name__}: {str(exc)[:150]}, and the attempted-cell "
            f"manifest could not be rebuilt ({type(inner).__name__}: "
            f"{str(inner)[:150]}); the run is not retainable"
        ) from inner


def scenario_worker(s: AddendumScenario, *, n_eval: int = N_EVAL,
                    replicates: int | None = None,
                    reference_replicates: tuple | None = None,
                    encoder_filter=None, learner_filter=None) -> list[dict]:
    """All rows for ONE addendum scenario, in its own process.

    Every keyword other than the defaults produces a NON-FROZEN PROBE: every
    row is stamped `warning=NON_FROZEN_PROBE_NOT_AN_ADDENDUM_RESULT` so a smoke
    run can never be mistaken for, or merged into, addendum output.
    """
    probe = (n_eval != N_EVAL or replicates is not None
             or reference_replicates is not None
             or encoder_filter is not None or learner_filter is not None)
    warning = "NON_FROZEN_PROBE_NOT_AN_ADDENDUM_RESULT" if probe else None

    # ---- WORKER SETUP, before the per-replicate try (reconciliation C3) ----
    # `reference_replicate` reads and compiles the 01B rule; `encoder_configs`,
    # `hash_gap_identified`, `worker_tolerance` and `getrusage` can all fail.
    # Every one of those failures used to escape `scenario_worker` and reach
    # `_s1_parallel`, which turned it into an EMPTY checkpoint: zero rows for a
    # scenario whose cells were all attempted. The setup is now inside its own
    # `BaseException` guard, and its failure is materialised as typed rows for
    # the whole scenario.
    rows: list[dict] = []
    try:
        ref_reps = (tuple(reference_replicates)
                    if reference_replicates is not None
                    else (reference_replicate(s.scenario_id),))
        ru0 = resource.getrusage(resource.RUSAGE_SELF)
        f = s.factors
        M, K, de, n_tr = f["M"], f["K"], f["delta_eta"], f["n_train"]
        configs = [c for c in encoder_configs()
                   if encoder_filter is None or c[0] in encoder_filter]
        seeds = s.seeds if replicates is None else s.seeds[:replicates]
        hash_exact = CORE.hash_gap_identified(M, K)
        tolerance = worker_tolerance()
    except BaseException as exc:                                  # noqa: BLE001
        setup_rows = _setup_failure_rows(s, n_eval, exc, warning,
                                         replicates=replicates,
                                         encoder_filter=encoder_filter,
                                         learner_filter=learner_filter)
        if isinstance(exc, Exception):
            return setup_rows
        raise AddendumWorkerAborted(exc, setup_rows) from exc

    fiber_cache: dict = {}

    for rep, seed in enumerate(seeds, 1):
        base = _base_row_fields(s, rep, seed, n_eval)
        # ---- setup: DGP draw, eta table, nested training draw, eval draw ----
        try:
            prm = CORE.draw_params(M, K, f["marginal"], f["tau"], f["n_int"], de,
                                   seed, d_active=D_ADD)
            if prm.d_active != M:
                raise ValueError(
                    f"addendum requires d_active == M; got {prm.d_active} != {M}")
            tab = FIN.build_eta_table(prm)
            scales = population_signal_scales(tab.p_cell, tab.eta)
            # nested rule: n=500 is the FIRST 500 ROWS of the n=5000 draw
            Xbig, ybig, _ = FIN.sample_records(prm, tab, N_TRAIN_NEST_MAX,
                                               addendum_train_seed(seed))
            Xtr = Xbig.iloc[:n_tr].reset_index(drop=True)
            ytr = ybig[:n_tr]
            Xev, yev, eta_ev = FIN.sample_records(prm, tab, n_eval,
                                                  addendum_eval_seed(seed))
            ev_cell = tab.cell_ids(
                Xev.iloc[:, :prm.d_active].to_numpy().astype(np.int64))
        except BaseException as exc:                              # noqa: BLE001
            rep_rows = _guarded_failure_rows(
                s, rep, seed, n_eval, configs,
                Status.NUMERICAL_FAILURE, "dgp_setup", exc, warning,
                learner_filter=learner_filter)
            rows.extend(rep_rows)
            if not isinstance(exc, Exception):
                raise AddendumWorkerAborted(exc, rows) from exc
            continue

        two_class = len(np.unique(yev)) > 1

        for enc, Bw, lab in configs:
            lrns = _learners_for(enc, lab, learner_filter)
            cfg_fields = dict(base, encoder=enc, bucket_width=Bw, width_label=lab)
            do_ref = rep in ref_reps
            # CRITICAL-6. The configuration's rows are BUFFERED and committed
            # only when the configuration completes. Before this, a failure
            # part-way through the `for lrn: for metric:` loop appended a
            # TRAINING_FAILURE row for every cell of the configuration on top
            # of the SUCCESS rows already written, so the same primary key
            # appeared twice with contradictory status and AD6's exact 182,400
            # became unsatisfiable the moment any cell failed late.
            cfg_rows: list[dict] = []
            try:
                # ---- fit the encoder ----
                if enc in DES.HASH_ENC:
                    mp = FIN.make_sim_hash(enc == "hash_column", Bw).fit(Xtr)
                    Ztr = mp.transform(Xtr)
                else:
                    Ztr = FIN.oof_train_codes(Xtr, ytr, enc, addendum_oof_seed(rep))
                    mp = FIN.full_fit_mapping(Xtr, ytr, enc)

                # ---- exact population layer ----
                # At d = M = 5 the active-block enumeration IS the full state
                # space (1024 cells), so one table serves the coordinate-wise
                # encoders and the hash encoders alike.
                if enc in DES.HASH_ENC:
                    if not hash_exact:
                        raise RuntimeError(
                            f"hash gap not identified at M={M}, K={K}; the "
                            f"addendum design asserts K**M <= ENUM_CAP")
                    key = (Bw, enc == "hash_column")
                    if key not in fiber_cache:
                        fiber_cache[key] = CORE.group_ids(
                            CORE.hash_codes(tab.cells, K, Bw,
                                            enc == "hash_column"))
                    fid = fiber_cache[key]
                    _mass, eb_cells = CORE.fiber_posteriors(fid, tab.p_cell, tab.eta)
                    ebar_cells = eb_cells[fid]
                    coll, occ = hash_diagnostics(M, K, Bw, enc == "hash_column")
                else:
                    ebar_cells, fid = ebar_coordinatewise(mp, tab, prm)
                    coll, occ = None, None
                ebar_ev = ebar_cells[ev_cell]

                # D17 gate G4. Computed ONCE per configuration from the very
                # `fid` the population layer below consumes, so a defect that
                # hands this configuration the wrong partition (a wrong memo
                # key, a permuted assignment) is recorded in the row rather
                # than having to survive as a numerical residue.
                fiber_fp = CORE.partition_fingerprint(fid)

                pop = CORE.exact_gap_report(fid, tab.p_cell, tab.eta)
                rel = relative_gaps(pop["gap_logloss"], pop["gap_brier"],
                                    scales, tolerance)

                # ---- D17: independent reference implementation ----
                ref = (CORE.reference_gap_report(fid, tab.p_cell, tab.eta)
                       if do_ref else None)

                pop_metrics = dict(
                    pop_risk_x_logloss=pop["risk_x_logloss"],
                    pop_risk_z_logloss=pop["risk_z_logloss"],
                    pop_risk_x_brier=pop["risk_x_brier"],
                    pop_risk_z_brier=pop["risk_z_brier"],
                    pop_gap_logloss=pop["gap_logloss"],
                    pop_gap_brier=pop["gap_brier"],
                    pop_theoretical_gap_logloss=pop["theoretical_gap_logloss"],
                    pop_theoretical_gap_brier=pop["theoretical_gap_brier"],
                    pop_identity_error_logloss=pop["identity_error_logloss"],
                    pop_identity_error_brier=pop["identity_error_brier"],
                    p_y=scales["p_y"], entropy_y=scales["entropy_y"],
                    var_eta_x=scales["var_eta_x"],
                    relative_log_gap=rel["relative_log_gap"],
                    relative_brier_gap=rel["relative_brier_gap"],
                    fiber_count=pop["fiber_count"],
                    merged_fiber_count=pop["merged_fiber_count"],
                    merged_fiber_mass=pop["merged_fiber_mass"],
                    max_fiber_posterior_spread=pop["max_fiber_posterior_spread"],
                    collision_count=coll, occupied_buckets=occ,
                    n_cells=int(len(tab.cells)),
                    # D17: the reference columns come from the independent
                    # implementation executed on the cell, never derived from
                    # the production columns (01B rulings.D17.persisted_columns
                    # .forbidden).
                    reference_log_gap=(ref["gap_logloss"] if ref else None),
                    reference_brier_gap=(ref["gap_brier"] if ref else None),
                    production_log_gap=(pop["gap_logloss"] if ref else None),
                    production_brier_gap=(pop["gap_brier"] if ref else None),
                    log_identity_error=(
                        ref["identity_error_logloss"] if ref else None),
                    brier_identity_error=(
                        ref["identity_error_brier"] if ref else None),
                    abs_production_minus_reference_log=(
                        abs(pop["gap_logloss"] - ref["gap_logloss"]) if ref else None),
                    abs_production_minus_reference_brier=(
                        abs(pop["gap_brier"] - ref["gap_brier"]) if ref else None),
                )

                # ---- fit the learners, predict the evaluation sample once ----
                models = {}
                for lrn in lrns:
                    if lrn == "bayes_z_oracle":
                        continue
                    mo = FIN.make_learner(lrn, seed=seed)
                    mo.fit(Ztr, ytr)
                    models[lrn] = mo
                preds = (FIN.predict_proba_chunked_multi(mp, models, Xev)
                         if models else {})
                if "bayes_z_oracle" in lrns:
                    preds["bayes_z_oracle"] = ebar_ev

                for lrn in lrns:
                    p = preds[lrn]
                    for metric in METRICS:
                        fn = FIN.rb_logloss if metric == "logloss" else FIN.rb_brier
                        dd = FIN.decompose(eta_ev, ebar_ev, p, metric)
                        sample_metrics = dict(
                            risk_x=dd["risk_x"], risk_z=dd["risk_z"],
                            risk_learner=dd["risk_learner"],
                            theoretical_gap=pop[f"theoretical_gap_{metric}"],
                            estimated_gap=dd["representation_loss"],
                            representation_loss=dd["representation_loss"],
                            learner_shortfall=dd["learner_shortfall"],
                            total_excess_risk=dd["total_excess_risk"],
                            mcse=dd["mcse"], roc_auc=None, pr_auc=None)
                        status = Status.SUCCESS
                        if metric == "logloss":
                            if two_class:
                                from sklearn.metrics import (average_precision_score,
                                                             roc_auc_score)
                                sample_metrics["roc_auc"] = float(roc_auc_score(yev, p))
                                sample_metrics["pr_auc"] = float(
                                    average_precision_score(yev, p))
                            else:
                                status = Status.METRIC_UNDEFINED
                        if status is Status.SUCCESS:
                            cfg_rows.append(addendum_row(
                                s.scenario_id, status,
                                metrics={**sample_metrics, **pop_metrics},
                                **cfg_fields, learner=lrn, metric=metric,
                                relative_log_gap_status=rel["relative_log_gap_status"],
                                relative_brier_gap_status=rel["relative_brier_gap_status"],
                                exact_or_mc="exact",
                                population_quantity_kind="exact",
                                theoretical_gap_status=IDENTIFIED_EXACT,
                                reference_checked=1 if do_ref else 0,
                                fiber_fingerprint=fiber_fp,
                                warning=warning))
                        else:
                            cfg_rows.append(addendum_row(
                                s.scenario_id, status,
                                **cfg_fields, learner=lrn, metric=metric,
                                failure_stage="metric",
                                error_type="SingleClassEvaluationSample",
                                error_message="evaluation sample has one class; "
                                              "roc_auc/pr_auc undefined",
                                exact_or_mc="exact",
                                population_quantity_kind="exact",
                                theoretical_gap_status=IDENTIFIED_EXACT,
                                reference_checked=0, warning=warning))
            except BaseException as exc:                          # noqa: BLE001
                # DISCARD the buffer: the cells it describes are re-emitted
                # below, exactly once each, as typed failures.
                cfg_rows = []
                try:
                    for lrn in lrns:
                        for metric in METRICS:
                            cfg_rows.append(addendum_row(
                                s.scenario_id, Status.TRAINING_FAILURE,
                                **cfg_fields, learner=lrn, metric=metric,
                                failure_stage="encoder_or_learner",
                                error_type=type(exc).__name__,
                                error_message=str(exc)[:300],
                                exact_or_mc=None, population_quantity_kind=None,
                                theoretical_gap_status=None,
                                reference_checked=0, warning=warning))
                except BaseException as inner:                    # noqa: BLE001
                    raise AddendumRowEmissionError(
                        f"{s.scenario_id} replicate {rep} config {enc}/{lab}: "
                        f"the typed-failure-row builder raised "
                        f"{type(inner).__name__}: {str(inner)[:200]} while "
                        f"handling {type(exc).__name__}; typed-row accounting "
                        f"cannot be completed and the run is not retainable"
                    ) from inner
                rows.extend(cfg_rows)
                if not isinstance(exc, Exception):
                    raise AddendumWorkerAborted(exc, rows) from exc
            else:
                rows.extend(cfg_rows)

    ru1 = resource.getrusage(resource.RUSAGE_SELF)
    cpu = (ru1.ru_utime - ru0.ru_utime) + (ru1.ru_stime - ru0.ru_stime)
    for r in rows:
        r["cpu_seconds"] = round(cpu / max(len(rows), 1), 6)
    return rows


# Cached per process. `ProcessPoolExecutor` spawns on macOS, so a value set in
# the parent would NOT reach a worker; each worker resolves it once from the
# frozen tolerance table (and from 01B when 01B names a different frozen name),
# which is deterministic, so every worker gets the same number.
_TOLERANCE_CACHE: dict = {}


def worker_tolerance() -> float:
    """The D14 denominator tolerance, resolved once per process from the freeze."""
    if "value" not in _TOLERANCE_CACHE:
        rulings, _missing = load_rulings_01b(strict=False)
        _TOLERANCE_CACHE["value"] = relative_gap_tolerance(rulings)
    return _TOLERANCE_CACHE["value"]


def worker_death_rows(s, exc) -> list[dict]:
    """PARENT-SIDE materialisation of a dead worker's cells (C2).

    `_s1_parallel.run_parallel` used to answer a worker or pool failure --
    a spawn/import error, an OOM kill, `BrokenProcessPool` -- by recording an
    EMPTY result and writing a header-only checkpoint. Every one of that
    scenario's 3,800 attempted cells then vanished from the arm with no typed
    row anywhere, the run still exited 0, and a restart skipped the scenario
    because its part file existed. D18 requires a typed row for every ATTEMPTED
    cell, and a cell attempted inside a worker that died is still attempted.

    A worker aborted by a BaseException carries its own rows on
    `AddendumWorkerAborted`; those are cells that genuinely ran, so they are
    kept and only the cells they do not cover are materialised here.
    """
    partial = list(getattr(exc, "rows", None) or [])
    have = {primary_key(r) for r in partial}
    status = (Status.RESOURCE_LIMIT
              if isinstance(exc, (MemoryError,)) else Status.TRAINING_FAILURE)
    rows = list(partial)
    for rep, seed in enumerate(s.seeds, 1):
        base = _base_row_fields(s, rep, seed, N_EVAL)
        for enc, Bw, lab, lrn, metric in attempted_cells(encoder_configs()):
            key = (s.scenario_id, rep, enc, lab, lrn, metric)
            if key in have:
                continue
            rows.append(addendum_row(
                s.scenario_id, status, **base,
                encoder=enc, bucket_width=Bw, width_label=lab,
                learner=lrn, metric=metric,
                failure_stage="worker_death",
                error_type=type(exc).__name__, error_message=str(exc)[:300],
                exact_or_mc=None, population_quantity_kind=None,
                theoretical_gap_status=None, reference_checked=0))
    return rows


def summarise(rows) -> dict:
    """EXECUTED vs SUCCESSFUL, never conflated (decision D12 / defect D18-e)."""
    from collections import Counter
    executed = len(rows)
    success = sum(1 for r in rows if r["status"] == Status.SUCCESS.value)
    by_status = Counter(r["status"] for r in rows)
    by_stage = Counter(r["failure_stage"] for r in rows
                       if r["status"] != Status.SUCCESS.value)
    not_identified = sum(
        1 for r in rows
        if r.get("relative_log_gap_status") == NOT_IDENTIFIED
        or r.get("relative_brier_gap_status") == NOT_IDENTIFIED)
    dupes = duplicate_primary_keys(rows)
    return dict(rows_executed=executed, rows_success=success,
                rows_failed=executed - success,
                rows_duplicate_primary_keys=sum(n - 1 for n in dupes.values()),
                distinct_primary_keys=executed - sum(n - 1 for n in dupes.values()),
                rows_reference_checked=sum(1 for r in rows
                                           if r.get("reference_checked")),
                rows_exact_population=sum(
                    1 for r in rows if r.get("population_quantity_kind") == "exact"),
                rows_relative_gap_not_identified=not_identified,
                by_status=dict(by_status), by_failure_stage=dict(by_stage))


def print_summary(summary: dict) -> None:
    print("\n--- addendum row accounting (EXECUTED is not SUCCESSFUL) ---")
    print(f"  rows_executed                     {summary['rows_executed']:,}")
    print(f"  rows_success                      {summary['rows_success']:,}")
    print(f"  rows_failed (typed, NULL metrics)  {summary['rows_failed']:,}")
    print(f"  distinct primary keys (AD6)       "
          f"{summary['distinct_primary_keys']:,}"
          + ("" if not summary["rows_duplicate_primary_keys"] else
             f"   !! {summary['rows_duplicate_primary_keys']:,} DUPLICATE ROWS"))
    print(f"  rows_reference_checked (D17)      {summary['rows_reference_checked']:,}")
    print(f"  rows_exact_population (D18-c)     {summary['rows_exact_population']:,}")
    print(f"  rows_relative_gap NOT_IDENTIFIED  "
          f"{summary['rows_relative_gap_not_identified']:,}")
    for st, n in sorted(summary["by_status"].items()):
        print(f"    status {st:<24} {n:,}")
    for stage, n in sorted(summary["by_failure_stage"].items(), key=lambda kv: str(kv[0])):
        print(f"    failure_stage {stage!s:<17} {n:,}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def print_dry_run(rulings_missing: list[str], freeze_findings: list[str]) -> dict:
    wl = work_list()
    print("cT2I dense-signal Simulation 1B addendum -- DRY RUN (no cell executed)")
    print(f"  design authority   {FREEZE_01A.relative_to(REPO)}")
    print(f"  advisor rulings    {RULINGS_01B.relative_to(REPO)}"
          f"{'  [MISSING]' if not RULINGS_01B.exists() else ''}")
    print(f"  runner             {Path(__file__).relative_to(REPO)}")
    print()
    print(f"  scenarios                       {wl['scenarios']}")
    print(f"  design blocks (marginal x tau x interaction_pairs)"
          f"                 {wl['blocks']}")
    print(f"  parameter draws per arm (blocks x replicates)"
          f"                      {wl['blocks'] * wl['replicates']}")
    print( "  inferential unit                                "
           "                  OPEN -- 01B Q6")
    print( "    D13 as ruled: the 8 blocks, 7 df. MEASURED: parameters are drawn")
    print( "    afresh per replicate, so there are 400 draws per arm, clustered")
    print( "    as (block, replicate) with 6 scenarios each. This runner does NOT")
    print( "    choose; see 01B advisor_confirmation_requested.Q6 and")
    print( "    simulation-results-ct2i/S0B_D13_PREMISE_INVESTIGATION.md.")
    print(f"  encoder configurations          {wl['encoder_configs']}")
    print(f"  replicates per scenario         {wl['replicates']}")
    print(f"  n_train levels                  {wl['n_train_levels']}")
    print(f"  learner cells per replicate     {wl['learner_cells_per_replicate']}")
    print(f"  rows per replicate (x2 metrics) {wl['rows_per_replicate']}")
    print()
    print(f"  replicate cells (48 x 50)                    {wl['replicate_cells']:,}")
    print(f"  encoder cells   (48 x 13 x 50)               {wl['encoder_cells']:,}")
    print(f"  learner cells   (48 x 38 x 50)               {wl['learner_cells']:,}")
    print(f"  D17 reference cells (48 x 13 x 1)            {wl['reference_cells']:,}"
          f"  (01B minimum {wl['reference_cells_required']:,})")
    print(f"PROJECTED CELL COUNT: {wl['projected_rows_executed']:,} EXECUTED rows "
          f"(01A design.row_count.total = {wl['frozen_row_count']:,}) "
          f"-> {'MATCH' if wl['matches_freeze'] else 'MISMATCH -- STOP'}")
    if freeze_findings:
        print("\n  !! runner constants disagree with 01A:")
        for b in freeze_findings:
            print(f"     - {b}")
    if rulings_missing:
        print(f"\n  !! 01B keys not available ({len(rulings_missing)}):")
        for k in rulings_missing:
            print(f"     - {k}")
        print("     --execute is refused until these are provided.")
    return wl


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", default=False,
                    help="enumerate the work list and print the projected cell "
                         "count without executing any cell (the default)")
    ap.add_argument("--execute", action="store_true", default=False,
                    help="actually run the arm; requires a valid 01B ruling file")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--workers", type=int,
                    default=int(os.environ.get("S1_WORKERS", 8)))
    ap.add_argument("--limit", type=int, default=None,
                    help="run only the first N scenarios (partial run; the "
                         "output is then NOT the frozen arm)")
    args = ap.parse_args(argv)

    freeze_findings = verify_against_freeze()
    _rulings, missing = load_rulings_01b(strict=False)

    if not args.execute:
        print_dry_run(missing, freeze_findings)
        print("\nNo cell executed. Pass --execute to run Phase A1.")
        return 0

    if freeze_findings:
        print("REFUSING TO EXECUTE: runner constants disagree with 01A:")
        for b in freeze_findings:
            print(f"  - {b}")
        return 2
    rulings, missing = load_rulings_01b(strict=True)     # raises with names
    _TOLERANCE_CACHE["value"] = relative_gap_tolerance(rulings)
    print(f"D14 denominator tolerance (NOT_IDENTIFIED below this): "
          f"{_TOLERANCE_CACHE['value']:.3e}")

    from _s1_parallel import run_parallel
    scen = addendum_scenarios()
    todo = scen[:args.limit] if args.limit else scen
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    n = run_parallel(todo, scenario_worker, out, FIELDS,
                     max_workers=args.workers, label="1BD",
                     failure_rows=worker_death_rows)
    print(f"SIM 1BD wall={(time.perf_counter() - t0) / 60:.1f}m rows_executed={n:,}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
