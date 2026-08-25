"""Phase A0.1 / D17: independent reference check for acceptance criteria AD1, AD2.

WHY THIS EXISTS
---------------
`sim1_core.exact_gap_report` computes `gap = R(Z) - R(X)` and `theoretical_gap`
(the CMI / expected conditional variance) from the SAME `fiber_posteriors`
aggregation.  An identity error recomputed from those stored columns is
~1e-16 BY CONSTRUCTION (measured 1.28e-16 on the frozen twin), so AD1 and AD2
pass whatever the fiber algebra does.  `01B_ADDENDUM_ADVISOR_RULINGS.yaml`
ruling D17 makes the dependency-free `sim1_core.reference_gap_report` the
MANDATORY evaluation route.

WHAT THIS SCRIPT DOES
---------------------
For every cell of a deterministic sample it rebuilds the population layer from
the seed, then evaluates the SAME (fid, p_cell, eta) triple through both
implementations:

  production  sim1_core.exact_gap_report      numpy / bincount fast path
  reference   sim1_core.reference_gap_report  pure-Python dict grouping, `math`

and persists the six columns D17 names (plus keying and diagnostic columns).

WHAT IT CAN AND CANNOT CATCH (stated so the report cannot overclaim)
--------------------------------------------------------------------
  CAUGHT  a defect in the risk-aggregation layer -- masses, conditional means,
          the entropy/Brier/KL/variance sums -- because the reference recomputes
          all of them from `fid`, `p_cell`, `eta` with no shared code.
  NOT CAUGHT BY THE REFERENCE COMPARISON ALONE
          a defect in the CONSTRUCTION of `fid` itself (group_ids, hash_codes,
          ebar_coordinatewise).  Both implementations are handed the same fid,
          so both would be consistently wrong.  This script therefore adds two
          further, independent detectors for arms whose production output is on
          disk (`--stored`): `fiber_count`, and the stored representation loss
          against the recomputed population gap.  Sensitivity of all three is
          demonstrated with `--inject-defect`.
  WHY A FOURTH GATE
          Gate 3's tolerance is the Monte-Carlo noise floor, so an assignment
          defect whose effect on the population gap is smaller than 6 mcse
          survives it.  Measured on the frozen d = 3 arm: a one-cell swap
          between two fibers moved the population gap in 151 cells and gate 3
          fired in only 6 of them, ALL of them non-hash -- a swap confined to
          the hash configurations would have passed the whole arm while
          corrupting gaps by up to 1.4e-3.  Gate 4 compares a CANONICAL
          PARTITION FINGERPRINT, `sim1_core.partition_fingerprint`, which is
          exact and tolerance-free: equal digests if and only if equal
          partitions.  It needs the runner to persist `fiber_fingerprint`, so
          it is evaluable on the addendum arm and NOT on the frozen d = 3 twin,
          whose parquet predates the column.
  WHY A THIRD GATE
          `fiber_count` is INVARIANT UNDER FIBER RELABELLING.  A permutation of
          the cell -> fiber assignment, or a swap of one cell between two
          fibers, preserves the number of fibers AND the multiset of fiber
          sizes exactly, so gate 2 is blind to it, and gate 1 is blind to it
          because both implementations consume the same corrupted `fid`.  The
          stored `representation_loss` is the runner's Monte-Carlo risk under
          the partition the runner ACTUALLY used, so it is the only persisted
          quantity that crosses the fiber-construction boundary: it moves when
          the assignment moves, measured 3.01x on hash_column/B0 at d = 5.

ARMS
----
  d3_frozen  the EXISTING FROZEN d = 3 twin, 1B at M = 5, K = 4:
             48 scenarios (S1B-0001..S1B-0048) x 13 encoder configurations.
             Production values already exist, so the harness is validated here
             WITHOUT executing a single addendum cell (prohibition PR1).
  addendum   the dense-signal addendum, d = 5, S1BD-0001..S1BD-0048 x 13.
             Switching arms is a parameter change, not a rewrite.  This arm is
             an A1 gate and must not be run before the advisor authorises A1.

FROZEN SAMPLING RULE (read, not re-derived, from
01B_ADDENDUM_ADVISOR_RULINGS.yaml key
`rulings.D17.sampling_rule.frozen_replicate_rule.rule`):

    reference_replicate(scenario) = int(scenario_id[-4:])

i.e. S1BD-0001 -> replicate 1, ..., S1BD-0048 -> replicate 48; 1-based, and
1 <= 48 <= 50 so every scenario's frozen replicate exists.  The same rule is
applied to the d = 3 twin, whose ids run S1B-0001..S1B-0048 with 50 replicates.
The sample may only be enlarged, never reduced (`expansion_rule`).

TOLERANCES: two classes, because two different quantities are compared.
  gates 1 and 2  `exact_identity_abs` = 1.0e-10 (exact-vs-exact; integer
                 equality for the count).  Unchanged by any amendment.
  gate 4         EXACT STRING EQUALITY of the canonical partition digest.
                 No tolerance: a digest is either the same or it is not.
  gate 3         MCSE-SCALED, `6 * stored_mcse + 1e-9`.  The stored
                 representation loss is a MONTE-CARLO plug-in over the
                 evaluation sample, not an exact population number, so an
                 exact tolerance would fail for a CORRECT implementation
                 (01B rulings.D17.representation_loss_is_monte_carlo).  k = 6
                 is the same constant the runner-level AD1/AD2 property test
                 uses; the floor covers the injective encoders, whose mcse is
                 0 or denormal because ebar == eta pointwise.

`exact_identity_abs` = 1.0e-10, read at run time from
01_PROTOCOL_FREEZE.yaml key `tolerances.exact_identity_abs` (line 525);
unchanged by D17 (`rulings.D17.evaluation_rule.tolerance_ref`).

Usage
  s0b_reference_gap_check.py --arm d3_frozen --stored
  s0b_reference_gap_check.py --arm addendum                    # A1 ONLY
  s0b_reference_gap_check.py --arm d3_frozen --inject-defect ebar_bias \
                             --out /tmp/scratch.csv            # sensitivity

Exit code 0 only if every identity error and every production-vs-reference
difference is at or below the frozen tolerance (gate 1) and, with --stored,
every fiber_count matches (gate 2), every stored representation loss is
within its MCSE-scaled tolerance of the recomputed population gap (gate 3),
and every stored partition fingerprint matches the recomputed one (gate 4,
addendum arm only -- the frozen d = 3 parquet predates the column).
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from ct2i_benchmark.simulations import sim1_core as CORE       # noqa: E402
from ct2i_benchmark.simulations import sim1_design as DES      # noqa: E402
from ct2i_benchmark.simulations import sim1_finite as FIN      # noqa: E402

from run_sim1b_finite import ebar_coordinatewise               # noqa: E402

PKG = REPO / "simulation-results-ct2i"
FREEZE_01 = PKG / "01_PROTOCOL_FREEZE.yaml"
RULINGS_01B = PKG / "01B_ADDENDUM_ADVISOR_RULINGS.yaml"

# Gate 3 tolerance.  MCSE-SCALED, not `exact_identity_abs`: see the module
# docstring and 01B rulings.D17.evaluation_rule.gate_G3_stored_representation_loss.
# k = 6 matches tests/test_a0_2_defect_closure.AD12_K; the floor keeps the
# injective encoders (mcse == 0 exactly, or denormal) out of a division.
MCSE_K = 6.0
MCSE_FLOOR = 1.0e-9

# The six columns D17 mandates, in the order it names them.
D17_COLUMNS = ("reference_log_gap", "reference_brier_gap",
               "production_log_gap", "production_brier_gap",
               "log_identity_error", "brier_identity_error")

# D17 `persisted_columns.keying_columns_also_required`
KEY_COLUMNS = ("scenario_id", "replicate", "encoder", "bucket_width",
               "width_label", "d_active")

FIELDS = [
    # keying (D17 keying_columns_also_required, plus provenance)
    "arm", "component", "scenario_id", "replicate", "seed", "d_active",
    "M", "K", "marginal", "tau", "interaction_count", "delta_eta", "n_train",
    "encoder", "bucket_width", "width_label",
    # ---- the SIX mandated D17 columns ----
    "reference_log_gap", "reference_brier_gap",
    "production_log_gap", "production_brier_gap",
    "log_identity_error", "brier_identity_error",
    # production-vs-reference agreement (D17 evaluation_rule.also_required)
    "prod_ref_log_abs_diff", "prod_ref_brier_abs_diff",
    # the production SELF-check, retained only to show it is uninformative
    "production_self_identity_error_log", "production_self_identity_error_brier",
    # fiber-construction detector (not covered by the reference comparison)
    "fiber_count", "stored_fiber_count", "fiber_count_match",
    "stored_representation_loss_log_mc", "stored_representation_loss_brier_mc",
    "stored_mcse_log", "stored_mcse_brier",
    "stored_abs_diff_log_mc", "stored_abs_diff_brier_mc",
    "stored_mc_tolerance_log", "stored_mc_tolerance_brier",
    "stored_mc_within_tolerance",
    # fiber-ASSIGNMENT detector, exact (gate 4)
    "recomputed_fiber_fingerprint", "stored_fiber_fingerprint",
    "fiber_fingerprint_match",
    # bookkeeping
    "tolerance", "within_tolerance", "injected_defect", "status", "notes",
]


# ---------------------------------------------------------------------------
# Frozen constants read from the freeze files (never hardcoded silently)
# ---------------------------------------------------------------------------

def read_exact_identity_abs() -> tuple[float, str]:
    """`tolerances.exact_identity_abs` from 01_PROTOCOL_FREEZE.yaml."""
    txt = FREEZE_01.read_text(encoding="utf-8")
    m = re.search(r"^\s*exact_identity_abs:\s*([0-9.eE+-]+)", txt, re.M)
    if not m:
        raise RuntimeError(f"tolerances.exact_identity_abs not found in {FREEZE_01}")
    line = txt[:m.start()].count("\n") + 1
    return float(m.group(1)), f"01_PROTOCOL_FREEZE.yaml:{line} tolerances.exact_identity_abs"


def read_frozen_replicate_rule() -> str:
    """The D17 replicate rule, read verbatim so the report can cite it."""
    txt = RULINGS_01B.read_text(encoding="utf-8")
    m = re.search(r'^\s*rule:\s*"(reference_replicate\(scenario\)[^"]*)"', txt, re.M)
    if not m:
        raise RuntimeError("rulings.D17.sampling_rule.frozen_replicate_rule.rule "
                           f"not found in {RULINGS_01B}")
    line = txt[:m.start()].count("\n") + 1
    return f'{m.group(1)}   [{RULINGS_01B.name}:{line}]'


def reference_replicate(scenario_id: str) -> int:
    """D17 frozen rule: the replicate index IS the scenario ordinal.

    A pure function of the scenario id -- the implementer chooses nothing
    (`frozen_replicate_rule.no_discretion`).
    """
    return int(scenario_id[-4:])


# ---------------------------------------------------------------------------
# Arms
# ---------------------------------------------------------------------------

class Arm:
    """Everything that differs between the frozen d=3 twin and the addendum."""

    def __init__(self, name, component, d_active, scenarios, configs,
                 train_seed, n_train_nest_max, stored_path, stored_kind):
        self.name = name
        self.component = component
        self.d_active = d_active
        self.scenarios = scenarios
        self.configs = configs
        self.train_seed = train_seed
        self.n_train_nest_max = n_train_nest_max
        self.stored_path = stored_path
        self.stored_kind = stored_kind


def arm_d3_frozen() -> Arm:
    """The frozen 1B twin at M=5, K=4 -- production values already on disk."""
    scen = [s for s in DES.scenarios_1b()
            if s.factors["M"] == 5 and s.factors["K"] == 4]
    if len(scen) != 48:
        raise RuntimeError(f"expected 48 twin scenarios, found {len(scen)}")
    return Arm(
        name="d3_frozen", component="1B", d_active=DES.D_ACTIVE_1B,
        scenarios=scen,
        configs=DES.encoder_configs("B", 5, 4),
        # run_sim1b_finite.py:110 -- the training draw is seed + 100_000
        train_seed=lambda seed: seed + 100_000,
        n_train_nest_max=5000,
        stored_path=PKG / "05b_SIM1B_REPLICATE_RESULTS.parquet",
        stored_kind="parquet",
    )


def arm_addendum() -> Arm:
    """The dense-signal addendum, d = M = 5.  A1 ONLY."""
    import run_sim1b_dense_addendum as ADD          # imported lazily on purpose

    scen = ADD.addendum_scenarios()
    if len(scen) != ADD.N_SCENARIOS_ADD:
        raise RuntimeError(f"expected {ADD.N_SCENARIOS_ADD} addendum scenarios, "
                           f"found {len(scen)}")
    return Arm(
        name="addendum", component=ADD.COMPONENT, d_active=ADD.D_ADD,
        scenarios=scen,
        configs=ADD.encoder_configs(),
        train_seed=ADD.addendum_train_seed,
        n_train_nest_max=ADD.N_TRAIN_NEST_MAX,
        stored_path=ADD.DEFAULT_OUT,
        stored_kind="csv",
    )


ARMS = {"d3_frozen": arm_d3_frozen, "addendum": arm_addendum}


# ---------------------------------------------------------------------------
# Injected defects -- sensitivity evidence that the check CAN fail.
# All are in-process monkeypatches: nothing is written to any source file and
# no perturbed artefact is left on disk.
# ---------------------------------------------------------------------------

def install_defect(kind: str):
    """Patch `sim1_core` in this process only.  Returns an undo callable."""
    if kind == "none":
        return lambda: None

    if kind in ("ebar_bias", "mass_dropout"):
        # A defect in the SHARED aggregation.  `reference_gap_report` never
        # calls `fiber_posteriors`, so the reference stays correct and the
        # production-vs-reference comparison must fire.
        orig = CORE.fiber_posteriors

        def patched(fid, p_cell, eta):
            mass, ebar = orig(fid, p_cell, eta)
            if kind == "ebar_bias":
                return mass, ebar * (1.0 + 1e-6)
            mass = mass.copy()                       # drop the lightest fiber
            live = np.flatnonzero(mass > 0)
            if live.size:
                mass[live[int(np.argmin(mass[live]))]] = 0.0
            return mass, ebar

        CORE.fiber_posteriors = patched
        return lambda: setattr(CORE, "fiber_posteriors", orig)

    if kind == "fiber_merge":
        # A defect in fiber CONSTRUCTION.  Both implementations receive the
        # same corrupted partition, so the reference comparison is BLIND to it
        # by design; only the stored-production cross-check catches it.
        orig = CORE.group_ids

        def patched(codes):
            return orig(codes) // 2

        CORE.group_ids = patched
        return lambda: setattr(CORE, "group_ids", orig)

    if kind in ("fiber_permute", "fiber_swap"):
        # Cell -> fiber ASSIGNMENT defects.  Injected on the rebuilt partition
        # itself (see `fid_perturbation`), so nothing is monkeypatched here.
        return lambda: None

    raise ValueError(f"unknown defect kind {kind!r}")


def _swap_one_cell_between_two_fibers(fid: np.ndarray) -> np.ndarray:
    """Codex C4: move ONE cell out of fiber A and one out of fiber B.

    Swapping two entries of `fid` permutes the value multiset onto itself, so
    every fiber keeps its cardinality and the partition keeps its cardinality.
    The MEMBERSHIP changes, so every fiber conditional mean that involves
    either cell changes, and with it both population gaps.
    """
    fid = np.array(fid, dtype=np.int64, copy=True)
    if fid.size < 2:
        return fid
    j = int(np.argmax(fid != fid[0]))
    if fid[j] == fid[0]:                      # degenerate: one fiber only
        return fid
    fid[0], fid[j] = fid[j], fid[0]
    return fid


def fid_perturbation(kind: str):
    """The cell -> fiber assignment defects, as a function of the partition.

    These CANNOT be injected through `group_ids`: on the coordinate-wise route
    `group_ids` is called once per active COORDINATE over that coordinate's K
    levels, and the per-coordinate ids are then combined into a product
    partition, so any relabelling there is numerically inert.  The defect is
    therefore injected where the partition is consumed, which is also where a
    real assignment defect (`fid = np.roll(fiber_cache[key], 1)`, a wrong memo
    key, a wrong `ebar_coordinatewise` probe) would surface.
    """
    if kind == "fiber_permute":
        return lambda fid: np.roll(np.asarray(fid), 1)
    if kind == "fiber_swap":
        return _swap_one_cell_between_two_fibers
    return lambda fid: fid


DEFECTS = ("none", "ebar_bias", "mass_dropout", "fiber_merge",
           "fiber_permute", "fiber_swap")


# ---------------------------------------------------------------------------
# Population layer for one cell
# ---------------------------------------------------------------------------

def _full_space(prm, tab):
    """(cells, p_cell, eta) over the FULL M-coordinate space.

    Hash encoders mix all M coordinates, so their fibers live on the full
    space.  When d_active == M (the addendum) the eta table already IS the full
    space and is returned unchanged.
    """
    if prm.d_active == prm.M:
        return tab.cells, tab.p_cell, tab.eta
    full = CORE.enumerate_cells(prm.K, prm.M)
    p_full = CORE.cell_probabilities(full, prm.p_marg)
    ids = np.zeros(len(full), dtype=np.int64)
    for j in range(prm.d_active):
        ids = ids * prm.K + full[:, j]
    return full, p_full, tab.eta[ids]


def cell_triples(arm: Arm, s, rep: int):
    """Yield (encoder, bucket_width, width_label, fid, p_cell, eta) per config.

    The fitted mapping is rebuilt exactly as the production runner builds it:
    the same DGP draw, the same nested training draw (n=500 is the first 500
    rows of the n=5000 draw), the same `full_fit_mapping`.  Out-of-fold codes
    are deliberately NOT recomputed: they feed the learners only and never
    enter the fiber partition.
    """
    f = s.factors
    M, K, de, n_tr = f["M"], f["K"], f["delta_eta"], f["n_train"]
    seed = s.seeds[rep - 1]

    prm = CORE.draw_params(M, K, f["marginal"], f["tau"], f["n_int"], de, seed,
                           d_active=arm.d_active)
    tab = FIN.build_eta_table(prm)
    Xbig, ybig, _ = FIN.sample_records(prm, tab, arm.n_train_nest_max,
                                       arm.train_seed(seed))
    Xtr = Xbig.iloc[:n_tr].reset_index(drop=True)
    ytr = ybig[:n_tr]

    hash_cells = hash_p = hash_eta = None
    hash_cache: dict = {}

    for enc, Bw, lab in arm.configs:
        if enc in DES.HASH_ENC:
            if not CORE.hash_gap_identified(M, K):
                raise RuntimeError(f"hash gap not identified at M={M}, K={K}")
            if hash_cells is None:
                hash_cells, hash_p, hash_eta = _full_space(prm, tab)
            key = (Bw, enc == "hash_column")
            if key not in hash_cache:
                hash_cache[key] = CORE.group_ids(
                    CORE.hash_codes(hash_cells, K, Bw, enc == "hash_column"))
            yield enc, Bw, lab, hash_cache[key], hash_p, hash_eta, seed
        else:
            mp = FIN.full_fit_mapping(Xtr, ytr, enc)
            _ebar, fid = ebar_coordinatewise(mp, tab, prm)
            yield enc, Bw, lab, fid, tab.p_cell, tab.eta, seed


# ---------------------------------------------------------------------------
# Stored production values (the fiber-construction detector)
# ---------------------------------------------------------------------------

def load_stored(arm: Arm):
    """{(scenario_id, replicate, encoder, width_label): {...}} or None."""
    if not arm.stored_path.exists():
        return None
    import pandas as pd
    df = (pd.read_parquet(arm.stored_path) if arm.stored_kind == "parquet"
          else pd.read_csv(arm.stored_path))
    df = df[(df["learner"] == "bayes_z_oracle") & (df["status"] == "SUCCESS")]
    if arm.name == "d3_frozen":
        df = df[(df["M"] == 5) & (df["K"] == 4)]
    out: dict = {}
    for r in df.itertuples(index=False):
        k = (r.scenario_id, int(r.replicate), r.encoder,
             "" if r.width_label is None or r.width_label != r.width_label
             else str(r.width_label))
        d = out.setdefault(k, {})
        d["fiber_count"] = None if r.fiber_count != r.fiber_count else int(r.fiber_count)
        # `fiber_fingerprint` is an addendum column: the frozen d = 3 parquet
        # predates it, so gate 4 is NOT_EVALUATED there rather than silently
        # passing on a missing value.
        fp = getattr(r, "fiber_fingerprint", None)
        d["fiber_fingerprint"] = None if fp is None or fp != fp else str(fp)
        d[f"rep_loss_{r.metric}"] = float(r.representation_loss) \
            if r.representation_loss == r.representation_loss else None
        # gate 3 needs the mcse of the SAME metric: the log-loss mcse is about
        # 2x the Brier one on this arm, so reusing it for Brier would slacken
        # the Brier gate by that factor.
        d[f"mcse_{r.metric}"] = float(r.mcse) if r.mcse == r.mcse else None
    return out


# ---------------------------------------------------------------------------
# The pass criterion, as a function so it can be unit-tested without a run
# ---------------------------------------------------------------------------

# Arms whose result is quoted as evidence for acceptance criteria AD1/AD2.
# For these, `--stored` is MANDATORY: without it the checker recomputes BOTH
# sides itself and never looks at a single row the A1 runner produced, so a
# PASS says nothing about the production output (reconciliation C1).
GATE_ARMS = ("addendum",)


def evaluate(rows, tol: float) -> dict:
    """Decide PASS / FAIL from the evaluated cells.

    Gate 1  |production - reference| and the reference identity errors are at
            or below the frozen tolerance.
    Gate 2  every recomputed `fiber_count` matches the stored production value
            (only available with `--stored`).
    Gate 3  every stored `representation_loss` agrees with the recomputed
            population gap for the same cell to within `MCSE_K * stored_mcse +
            MCSE_FLOOR`, per metric (only available with `--stored`).
            Gate 2 is invariant under fiber RELABELLING -- a permutation of
            the cell -> fiber assignment, or a swap of one cell between two
            fibers, preserves the fiber count and the whole multiset of fiber
            sizes -- and gate 1 is invariant under it too, because both
            implementations consume the same corrupted `fid`. The stored
            representation loss is the runner's Monte-Carlo risk under the
            partition the runner ACTUALLY used, so it is the one persisted
            quantity that crosses the fiber-construction boundary. Its
            tolerance is MCSE-SCALED and NOT `exact_identity_abs`: the stored
            column is an MC plug-in, so an exact tolerance would fail for a
            correct implementation.
    Gate 4  every stored `fiber_fingerprint` equals the fingerprint of the
            recomputed partition, as strings. Gate 3's tolerance is the MC
            noise floor, so an assignment defect smaller than 6 mcse survives
            it; a canonical partition digest is exact. Evaluated only where the
            production row carries the column.
    Guard   the production-vs-reference difference must not be EXACTLY zero in
            every cell. Two genuinely independent implementations -- numpy
            `bincount` against pure-Python `math` -- agree to ~1e-16, not to
            the last bit, in every cell of a real sample. An all-exact-zero
            column is the signature of a reference column DERIVED FROM the
            production one (`ref = dict(pop)`), which 01B
            `rulings.D17.persisted_columns.forbidden` prohibits and which makes
            gate 1 vacuous rather than perfect. It is therefore reported as
            REFERENCE_NOT_INDEPENDENT, never as a flawless pass.
    """
    n = len(rows)
    n_out = int(sum(1 for r in rows if not r["within_tolerance"]))
    fc = [r["fiber_count_match"] for r in rows if r["fiber_count_match"] is not None]
    fc_bad = sum(1 for v in fc if v == 0)
    mc = [r.get("stored_mc_within_tolerance") for r in rows]
    mc = [v for v in mc if v is not None]
    mc_bad = sum(1 for v in mc if v == 0)
    fp = [r.get("fiber_fingerprint_match") for r in rows]
    fp = [v for v in fp if v is not None]
    fp_bad = sum(1 for v in fp if v == 0)
    diffs = [(r["prod_ref_log_abs_diff"], r["prod_ref_brier_abs_diff"])
             for r in rows]
    all_exact_zero = bool(n) and all(a == 0.0 and b == 0.0 for a, b in diffs)
    reasons = []
    if n_out:
        reasons.append(f"{n_out} cell(s) over tolerance {tol:.1e}")
    if fc_bad:
        reasons.append(f"{fc_bad} fiber_count mismatch(es) against stored production")
    if mc_bad:
        reasons.append(
            f"{mc_bad} stored representation loss(es) beyond "
            f"{MCSE_K:g}*mcse + {MCSE_FLOOR:.0e} from the recomputed population "
            f"gap (fiber-ASSIGNMENT detector; gates 1 and 2 are blind to "
            f"relabelling)")
    if fp_bad:
        reasons.append(
            f"{fp_bad} partition fingerprint mismatch(es) against stored "
            f"production (exact detector; the recomputed partition is not the "
            f"partition the runner used)")
    if all_exact_zero:
        reasons.append(
            "REFERENCE_NOT_INDEPENDENT: |production - reference| is EXACTLY 0.0 "
            "in every one of the {n} cells for BOTH metrics; the reference "
            "column is not being produced by an independent implementation"
            .format(n=n))
    if not n:
        reasons.append("no cells evaluated")
    return dict(cells=n, n_out=n_out, fc_checked=len(fc), fc_bad=fc_bad,
                mc_checked=len(mc), mc_bad=mc_bad,
                fp_checked=len(fp), fp_bad=fp_bad,
                all_exact_zero=all_exact_zero, ok=not reasons, reasons=reasons)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(arm_name: str, out_path: Path, defect: str, use_stored: bool,
        limit: int | None) -> int:
    arm = ARMS[arm_name]()
    tol, tol_src = read_exact_identity_abs()
    rule = read_frozen_replicate_rule()
    stored = load_stored(arm) if use_stored else None

    print(f"D17 reference-gap check   arm={arm.name}  d_active={arm.d_active}")
    print(f"  frozen replicate rule : {rule}")
    print(f"  tolerance             : {tol:.1e}   [{tol_src}]")
    print(f"  scenarios x configs   : {len(arm.scenarios)} x {len(arm.configs)}"
          f" x 1 replicate = {len(arm.scenarios) * len(arm.configs)} cells")
    print(f"  injected defect       : {defect}")
    print(f"  stored production     : "
          f"{arm.stored_path.name if stored is not None else 'NOT USED'}")

    undo = install_defect(defect)
    perturb = fid_perturbation(defect)
    rows: list[dict] = []
    t0 = time.perf_counter()
    scen = arm.scenarios[:limit] if limit else arm.scenarios
    try:
        for si, s in enumerate(scen, 1):
            rep = reference_replicate(s.scenario_id)
            if not 1 <= rep <= len(s.seeds):
                raise RuntimeError(f"{s.scenario_id}: frozen replicate {rep} "
                                   f"outside 1..{len(s.seeds)}")
            f = s.factors
            for enc, Bw, lab, fid, p_cell, eta, seed in cell_triples(arm, s, rep):
                fid = perturb(fid)
                fp = CORE.partition_fingerprint(fid)
                pop = CORE.exact_gap_report(fid, p_cell, eta)
                ref = CORE.reference_gap_report(fid, p_cell, eta)
                dlog = abs(pop["gap_logloss"] - ref["gap_logloss"])
                dbri = abs(pop["gap_brier"] - ref["gap_brier"])
                row = {k: None for k in FIELDS}
                row.update(
                    arm=arm.name, component=arm.component,
                    scenario_id=s.scenario_id, replicate=rep, seed=seed,
                    d_active=arm.d_active, M=f["M"], K=f["K"],
                    marginal=f["marginal"], tau=f["tau"],
                    interaction_count=f["n_int"], delta_eta=f["delta_eta"],
                    n_train=f["n_train"], encoder=enc, bucket_width=Bw,
                    width_label=lab,
                    reference_log_gap=ref["gap_logloss"],
                    reference_brier_gap=ref["gap_brier"],
                    production_log_gap=pop["gap_logloss"],
                    production_brier_gap=pop["gap_brier"],
                    log_identity_error=ref["identity_error_logloss"],
                    brier_identity_error=ref["identity_error_brier"],
                    prod_ref_log_abs_diff=dlog, prod_ref_brier_abs_diff=dbri,
                    production_self_identity_error_log=pop["identity_error_logloss"],
                    production_self_identity_error_brier=pop["identity_error_brier"],
                    fiber_count=pop["fiber_count"],
                    recomputed_fiber_fingerprint=fp,
                    tolerance=tol, injected_defect=defect, status="SUCCESS",
                )
                if stored is not None:
                    st = stored.get((s.scenario_id, rep, enc, lab))
                    if st is None:
                        row["notes"] = "NO_STORED_PRODUCTION_ROW"
                    else:
                        sfc = st.get("fiber_count")
                        row["stored_fiber_count"] = sfc
                        row["fiber_count_match"] = (
                            None if sfc is None else int(sfc == pop["fiber_count"]))
                        mc_ok = []
                        for metric, tag in (("logloss", "log"), ("brier", "brier")):
                            v = st.get(f"rep_loss_{metric}")
                            se = st.get(f"mcse_{metric}")
                            row[f"stored_representation_loss_{tag}_mc"] = v
                            row[f"stored_mcse_{tag}"] = se
                            if v is None:
                                continue
                            dv = abs(v - pop[f"gap_{metric}"])
                            row[f"stored_abs_diff_{tag}_mc"] = dv
                            if se is None:
                                continue
                            tv = MCSE_K * se + MCSE_FLOOR
                            row[f"stored_mc_tolerance_{tag}"] = tv
                            mc_ok.append(dv <= tv)
                        # gate 3: NULL, never a silent pass, where the stored
                        # row carries no representation loss or no mcse.
                        row["stored_mc_within_tolerance"] = (
                            int(all(mc_ok)) if mc_ok else None)
                        if not mc_ok:
                            row["notes"] = "STORED_MC_GATE_NOT_EVALUABLE"
                        sfp = st.get("fiber_fingerprint")
                        row["stored_fiber_fingerprint"] = sfp
                        row["fiber_fingerprint_match"] = (
                            None if sfp is None else int(sfp == fp))
                worst = max(row["log_identity_error"], row["brier_identity_error"],
                            dlog, dbri)
                row["within_tolerance"] = int(worst <= tol)
                rows.append(row)
            if si % 12 == 0 or si == len(scen):
                print(f"  scenario {si}/{len(scen)}  cells={len(rows):,}  "
                      f"elapsed={time.perf_counter() - t0:.0f}s", flush=True)
    finally:
        undo()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    a = {k: np.array([r[k] for r in rows], float) for k in
         ("log_identity_error", "brier_identity_error",
          "prod_ref_log_abs_diff", "prod_ref_brier_abs_diff",
          "production_self_identity_error_log",
          "production_self_identity_error_brier")}
    verdict = evaluate(rows, tol)
    fc, fc_bad, n_out = verdict["fc_checked"], verdict["fc_bad"], verdict["n_out"]
    mc, mc_bad = verdict["mc_checked"], verdict["mc_bad"]
    fpc, fp_bad = verdict["fp_checked"], verdict["fp_bad"]
    ok = verdict["ok"]
    # C1: an arm that is quoted as AD1/AD2 evidence is only REPORTABLE when the
    # stored production output was actually cross-checked.
    is_gate = arm.name in GATE_ARMS
    reportable = (stored is not None) if is_gate else True
    if is_gate and not reportable:
        ok = False
        verdict["reasons"].append(
            "NOT REPORTABLE: --stored was not supplied, so no row produced by "
            "the A1 runner was examined; this run cannot satisfy AD1/AD2")
    # Gate 4 is OPTIONAL only on arms whose production predates the column. On
    # the A1 gate arm its absence means the runner did not write it, which is a
    # non-conforming run, not a gate that quietly does not apply.
    if is_gate and reportable and fpc == 0:
        ok = False
        verdict["reasons"].append(
            "no stored `fiber_fingerprint` on any production row: gate 4 "
            "cannot be evaluated, and on the A1 gate arm that is a "
            "non-conforming runner output, not an inapplicable gate")
    if is_gate and reportable and mc == 0:
        ok = False
        verdict["reasons"].append(
            "no stored representation loss / mcse on any production row: "
            "gate 3 cannot be evaluated on the A1 gate arm")

    print(f"\n  max reference log identity error   {a['log_identity_error'].max():.3e}")
    print(f"  max reference Brier identity error {a['brier_identity_error'].max():.3e}")
    print(f"  max |production - reference| log   {a['prod_ref_log_abs_diff'].max():.3e}")
    print(f"  max |production - reference| Brier {a['prod_ref_brier_abs_diff'].max():.3e}")
    print(f"  max PRODUCTION SELF identity error "
          f"{max(a['production_self_identity_error_log'].max(), a['production_self_identity_error_brier'].max()):.3e}"
          f"   (uninformative by construction)")
    if fc:
        print(f"  fiber_count matches stored         {fc - fc_bad}/{fc}")
    if mc:
        worst = max(
            (r[f"stored_abs_diff_{t}_mc"] / r[f"stored_mc_tolerance_{t}"]
             for r in rows for t in ("log", "brier")
             if r.get(f"stored_mc_tolerance_{t}") is not None
             and r.get(f"stored_abs_diff_{t}_mc") is not None),
            default=float("nan"))
        print(f"  stored representation loss within  {mc - mc_bad}/{mc}"
              f"   (gate 3, tolerance {MCSE_K:g}*mcse + {MCSE_FLOOR:.0e}; "
              f"worst cell uses {worst:.3f} of its budget)")
    if fpc:
        print(f"  partition fingerprint matches      {fpc - fp_bad}/{fpc}"
              f"   (gate 4, exact)")
    elif stored is not None:
        print("  partition fingerprint              NOT EVALUATED"
              "   (gate 4: no stored `fiber_fingerprint` column on this arm)")
    if verdict["all_exact_zero"]:
        print("  !! |production - reference| is EXACTLY 0.0 in every cell -- "
              "the reference implementation is not independent")
    for why in verdict["reasons"]:
        print(f"  !! {why}")
    print(f"  wrote {out_path}")
    print(f"D17 REFERENCE CHECK arm={arm.name} defect={defect} "
          f"cells={len(rows)} tol={tol:.1e} "
          f"max_log_identity_error={a['log_identity_error'].max():.3e} "
          f"max_brier_identity_error={a['brier_identity_error'].max():.3e} "
          f"max_prod_ref_abs_diff="
          f"{max(a['prod_ref_log_abs_diff'].max(), a['prod_ref_brier_abs_diff'].max()):.3e} "
          f"cells_over_tolerance={n_out} fiber_count_mismatches={fc_bad} "
          f"stored_mc_gate_checked={mc} stored_mc_gate_violations={mc_bad} "
          f"fingerprint_checked={fpc} fingerprint_mismatches={fp_bad} "
          f"gates=G1_exact:{'PASS' if n_out == 0 else 'FAIL'},"
          f"G2_fiber_count:{'PASS' if fc and fc_bad == 0 else ('FAIL' if fc_bad else 'NOT_EVALUATED')},"
          f"G3_stored_repr_loss:{'PASS' if mc and mc_bad == 0 else ('FAIL' if mc_bad else 'NOT_EVALUATED')},"
          f"G4_partition_fingerprint:{'PASS' if fpc and fp_bad == 0 else ('FAIL' if fp_bad else 'NOT_EVALUATED')} "
          f"gate={'A1_AD1_AD2' if is_gate else 'SENSITIVITY_ONLY'} "
          f"stored_cross_check={'YES' if stored is not None else 'NO'} "
          f"reportable_for_AD1_AD2="
          f"{('YES' if reportable else 'NO') if is_gate else 'N/A_NOT_THE_GATE_ARM'} "
          f"RESULT={'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--arm", choices=sorted(ARMS), default="d3_frozen",
                    help="which arm to evaluate; 'addendum' is an A1 gate")
    ap.add_argument("--out", type=Path, default=None,
                    help="output CSV (default: S0B_REFERENCE_GAP_CHECK_<arm>.csv "
                         "in the package directory)")
    ap.add_argument("--inject-defect", choices=DEFECTS, default="none",
                    help="in-process defect injection for sensitivity evidence")
    ap.add_argument("--stored", action="store_true",
                    help="also cross-check fiber_count (gate 2) and the "
                         "stored representation loss (gate 3) of the "
                         "production run on disk")
    ap.add_argument("--limit", type=int, default=None,
                    help="evaluate only the first N scenarios (probe; the "
                         "frozen sample may never be reduced for a real check)")
    args = ap.parse_args(argv)

    out = args.out
    if out is None:
        if args.inject_defect != "none":
            ap.error("--inject-defect requires an explicit --out outside the "
                     "package directory; a perturbed artefact is never frozen")
        out = PKG / f"S0B_REFERENCE_GAP_CHECK_{args.arm}.csv"
    if args.inject_defect != "none" and PKG in out.resolve().parents:
        ap.error("refusing to write a defect-injected CSV into the package")
    if args.arm in GATE_ARMS and not args.stored:
        ap.error(f"--arm {args.arm} is the A1 AD1/AD2 gate: --stored is "
                 f"MANDATORY. Without it the checker recomputes both sides "
                 f"itself and never reads a single row the A1 runner wrote, so "
                 f"a PASS would certify nothing about the production output "
                 f"(reconciliation C1).")
    return run(args.arm, out, args.inject_defect, args.stored, args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
