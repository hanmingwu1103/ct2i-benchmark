"""Simulation 1B: finite-sample sampling, out-of-fold encoding, frozen learners.

Three things are frozen here and must not drift between S0 and S1.

1. Sampling. Coordinates are independent, so records are drawn coordinate-wise;
   eta is looked up from the exact active-block table built by sim1_core, which
   keeps the population quantities and the sampled data exactly consistent.

2. Out-of-fold construction for the supervised encoders. Fold assignment uses
   KFold(shuffle=True, random_state=seed_oof) -- deliberately NOT StratifiedKFold.
   Stratified folds depend on y, which would make the "no training-row
   self-influence" invariant untestable: flipping one label would move fold
   boundaries and legitimately change other rows' codes. With label-independent
   folds the invariant is exact and is asserted by the property tests.
   Ordered CatBoost keeps its own cross-fitting scheme (a row's code uses only
   strictly preceding rows under seeded permutations), so it is used directly.

3. Learner settings. Fixed, modest, and prespecified. This is not a
   hyperparameter benchmark, so nothing here is tuned per scenario.

Risk estimation is Rao-Blackwellised: because eta(x_i) is known exactly for
every evaluation record, the conditional expected loss is used in place of the
realised loss. For a predictor p_hat,

    E[ log loss | x ] = -eta ln p_hat - (1 - eta) ln(1 - p_hat)
    E[ Brier    | x ] = eta (1 - eta) + (eta - p_hat)^2

Substituting p_hat = eta, p_hat = ebar(z), and p_hat = the fitted learner's
prediction makes the decomposition

    total excess risk = representation loss + learner shortfall

hold exactly on the evaluation sample, with far lower Monte Carlo error than
using realised labels.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from ..encoders import REGISTRY as ENC_REGISTRY
from ..encoders import SUPERVISED
from ..encoders.base import Encoder
from ..encoders.hashing_enc import HASH_SEED
from ..encoders.supervised import OCB_ALPHA, OCB_PERMS, OrderedCatBoostEncoder
from ..hashing import bucket_of
from ..statuses import Status
from .sim1_core import (
    DGPParams,
    cell_probabilities,
    enumerate_cells,
    eta_raw,
    impose_delta_eta,
)

N_OOF_FOLDS = 5
EPS_PROB = 1e-12
OCB_PRIOR_FALLBACK = 0.5      # data-independent prior for the first ordered row
EVAL_CHUNK = 10_000           # evaluation rows processed at a time (memory ceiling)


# ---------------------------------------------------------------------------
# Ordered CatBoost with a running prior (simulation variant)
# ---------------------------------------------------------------------------

class OrderedCatBoostRunningPrior(OrderedCatBoostEncoder):
    """Ordered CatBoost whose prior also respects the permutation order.

    Why this variant exists. The baseline encoder computes its code for row i
    under a permutation as

        (sum of y over PRECEDING rows sharing the level + alpha * prior)
        / (count of those rows + alpha)

    which keeps row i's own label out of the numerator sum -- but takes
    `prior` to be the mean of y over ALL fitted rows, row i included. Row i's
    own label therefore re-enters its own code through the prior, with
    magnitude about alpha / (n * (count + alpha)). The effect is small
    (order 1e-4 at n = 400) but systematic, and it is a genuine violation of
    the no-training-row-self-influence invariant that Phase S0 is required to
    test. The baseline repository's own PC2 test exercises only the target
    encoder, so the channel was never asserted there.

    This variant replaces the fixed prior with a RUNNING prior: the mean of y
    over strictly preceding rows in the same permutation, falling back to a
    data-independent constant for the first row. Row i's code then depends only
    on rows that precede it, so self-influence is exactly zero -- which is also
    what ordered target statistics prescribe.

    The baseline encoder is left untouched. It produced the frozen real-data
    results and is not modified by this simulation-only assignment; the
    difference is recorded as a deviation and reported to the advisor.
    """

    name = "ordered_catboost_sim"

    def fit(self, X, y=None):
        assert y is not None
        y = np.asarray(y, float)
        n = len(y)
        self.prior_ = float(y.mean())        # inference-side prior for NEW rows only
        self.fitted_codes_ = np.zeros((n, X.shape[1]))
        for j, c in enumerate(X.columns):
            v = X[c].astype(str).to_numpy()
            acc = np.zeros(n)
            for p in range(OCB_PERMS):
                rng = np.random.default_rng(self.perm_seed + p)
                order = rng.permutation(n)
                run_sum: dict[str, float] = {}
                run_cnt: dict[str, int] = {}
                g_sum, g_cnt = 0.0, 0
                codes = np.empty(n)
                for i in order:
                    prior_i = g_sum / g_cnt if g_cnt > 0 else OCB_PRIOR_FALLBACK
                    s = v[i]
                    cnt = run_cnt.get(s, 0)
                    ssum = run_sum.get(s, 0.0)
                    codes[i] = (ssum + OCB_ALPHA * prior_i) / (cnt + OCB_ALPHA)
                    run_cnt[s] = cnt + 1
                    run_sum[s] = ssum + y[i]
                    g_sum += y[i]
                    g_cnt += 1
                acc += codes
            self.fitted_codes_[:, j] = acc / OCB_PERMS
        self.map_ = {}
        for c in X.columns:
            df = pd.DataFrame({"v": X[c].astype(str), "y": y})
            g = df.groupby("v")["y"].agg(["sum", "size"])
            self.map_[c] = (
                (g["sum"] + OCB_ALPHA * self.prior_) / (g["size"] + OCB_ALPHA)
            ).to_dict()
        return self


# ---------------------------------------------------------------------------
# Hash encoders with an explicit bucket width (simulation variant)
# ---------------------------------------------------------------------------

class SimHashEncoder(Encoder):
    """Hash encoder with B supplied explicitly and a vectorised transform.

    Two differences from the baseline encoder, both required by the plan:

    * B is a frozen experimental FACTOR here (0.5x, 1x, 2x the total category
      count), whereas the baseline fixes it with a cardinality staircase
      because the real-data benchmark needs a single value.
    * transform() is vectorised. The baseline loops over rows x columns in
      Python, which costs about 1.05 s per 50,000-row evaluation sample and
      would dominate the whole Phase S1 budget. Output is byte-identical: the
      token construction, the keyed blake2b hash, the seed and the unsigned
      counting are all unchanged, and a property test asserts equality against
      the baseline encoder at matched B.
    """

    def __init__(self, n_buckets: int, column_aware: bool):
        self.n_buckets_ = int(n_buckets)
        self.column_aware = bool(column_aware)
        self.name = "hash_column" if column_aware else "hash_shared"

    def fit(self, X, y=None):
        self.columns_ = list(X.columns)
        return self

    def _token(self, col: str, val: str) -> str:
        return f"{len(col)}:{col}={val}" if self.column_aware else val

    def _bucket_index(self, X) -> np.ndarray:
        """Bucket index of every (row, column) cell. Shape (n, n_cols)."""
        cols = []
        for c in self.columns_:
            vals = X[c].astype(str).to_numpy()
            uniq, inv = np.unique(vals, return_inverse=True)
            bk = np.fromiter(
                (bucket_of(self._token(c, u), self.n_buckets_, HASH_SEED) for u in uniq),
                dtype=np.int64, count=len(uniq))
            cols.append(bk[inv])
        return np.stack(cols, axis=1)

    def transform(self, X, chunk: int = EVAL_CHUNK):
        """Counts per bucket, assembled chunkwise.

        np.bincount over a flattened (row, bucket) index is far faster than
        np.add.at, but a single call would allocate n * B entries at once --
        800 MB for n = 50,000 and B = 2,000. Chunking bounds that intermediate
        while leaving the result identical.
        """
        n, B = len(X), self.n_buckets_
        idx = self._bucket_index(X)
        out = np.zeros((n, B))
        for lo in range(0, n, chunk):
            hi = min(lo + chunk, n)
            m = hi - lo
            base = (np.arange(m, dtype=np.int64) * B)[:, None]
            flat = (base + idx[lo:hi]).ravel()
            out[lo:hi] = np.bincount(flat, minlength=m * B).reshape(m, B)
        return out

    def state_summary(self):
        return {"B": self.n_buckets_, "seed": HASH_SEED,
                "column_aware": self.column_aware}


def make_sim_hash(column_aware: bool, n_buckets: int) -> SimHashEncoder:
    return SimHashEncoder(n_buckets=n_buckets, column_aware=column_aware)


def bucket_widths(M: int, K: int) -> dict[str, int]:
    """Frozen bucket-width factor: 0.5x, 1x, 2x the total category count."""
    k_tot = M * K
    return {"B0": max(2, round(0.5 * k_tot)),
            "B1": max(2, k_tot),
            "B2": max(2, 2 * k_tot)}


SIM_ENCODERS = dict(ENC_REGISTRY)
SIM_ENCODERS["ordered_catboost_sim"] = OrderedCatBoostRunningPrior
SIM_SUPERVISED = set(SUPERVISED) | {"ordered_catboost_sim"}
SIM_OWN_CROSSFIT = {"ordered_catboost", "ordered_catboost_sim"}


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

@dataclass
class EtaTable:
    """Exact active-block posterior table shared by the population and the sample."""
    cells: np.ndarray
    p_cell: np.ndarray
    eta: np.ndarray
    K: int
    d: int

    def cell_ids(self, active: np.ndarray) -> np.ndarray:
        """Row-major id of each active-block record."""
        ids = np.zeros(len(active), dtype=np.int64)
        for j in range(self.d):
            ids = ids * self.K + active[:, j]
        return ids


def build_eta_table(prm: DGPParams) -> EtaTable:
    cells = enumerate_cells(prm.K, prm.d_active)
    p_cell = cell_probabilities(cells, prm.p_marg)
    eta = impose_delta_eta(cells, p_cell, eta_raw(cells, prm), prm.delta_eta)
    return EtaTable(cells=cells, p_cell=p_cell, eta=eta, K=prm.K, d=prm.d_active)


def sample_records(prm: DGPParams, tab: EtaTable, n: int, seed: int):
    """Draw n records. Returns (X as string DataFrame, y, eta_i)."""
    rng = np.random.default_rng(seed)
    cols = rng.choice(prm.K, size=(n, prm.M), p=prm.p_marg)
    eta_i = tab.eta[tab.cell_ids(cols[:, :prm.d_active])]
    y = (rng.random(n) < eta_i).astype(np.int8)
    X = pd.DataFrame(cols.astype(str), columns=[f"v{j}" for j in range(prm.M)])
    return X, y, eta_i


# ---------------------------------------------------------------------------
# Out-of-fold encoding
# ---------------------------------------------------------------------------

def oof_train_codes(X: pd.DataFrame, y: np.ndarray, encoder_name: str,
                    seed_oof: int, encoder_kwargs: dict | None = None) -> np.ndarray:
    """Out-of-fold codes for training rows; row i's own label never enters."""
    cls = SIM_ENCODERS[encoder_name]
    kw = encoder_kwargs or {}
    if encoder_name in SIM_OWN_CROSSFIT:
        return cls(**kw).fit(X, y).fitted_codes_
    if encoder_name not in SIM_SUPERVISED:
        enc = cls(**kw).fit(X)
        return enc.transform(X)

    n = len(X)
    parts: dict[int, np.ndarray] = {}
    for fit_idx, hold_idx in KFold(n_splits=N_OOF_FOLDS, shuffle=True,
                                   random_state=seed_oof).split(np.arange(n)):
        enc = cls(**kw).fit(X.iloc[fit_idx], y[fit_idx])
        codes = enc.transform(X.iloc[hold_idx])
        for pos, i in enumerate(hold_idx):
            parts[int(i)] = codes[pos]
    return np.vstack([parts[i] for i in range(n)])


def full_fit_mapping(X: pd.DataFrame, y: np.ndarray, encoder_name: str,
                     encoder_kwargs: dict | None = None):
    """Encoder fitted on the FULL training sample, used to transform test rows."""
    cls = SIM_ENCODERS[encoder_name]
    kw = encoder_kwargs or {}
    enc = cls(**kw)
    return enc.fit(X, y) if encoder_name in SIM_SUPERVISED else enc.fit(X)


# ---------------------------------------------------------------------------
# Frozen learners
# ---------------------------------------------------------------------------

def make_learner(name: str, seed: int):
    """Frozen, modest, prespecified settings. Nothing is tuned per scenario."""
    if name == "logistic":
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        # `penalty` is deprecated in scikit-learn 1.8 and removed in 1.10; the
        # default is already L2, so C alone pins the frozen configuration.
        return make_pipeline(
            StandardScaler(),
            LogisticRegression(C=1.0, solver="lbfgs",
                               max_iter=2000, random_state=seed))
    if name == "lightgbm":
        from lightgbm import LGBMClassifier
        return LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31,
                              min_child_samples=20, reg_lambda=1.0, n_jobs=1,
                              random_state=seed, verbose=-1, deterministic=True,
                              force_row_wise=True)
    if name == "mlp":
        from sklearn.neural_network import MLPClassifier
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        return make_pipeline(
            StandardScaler(),
            MLPClassifier(hidden_layer_sizes=(64, 32), activation="relu",
                          alpha=1e-4, learning_rate_init=1e-3, max_iter=300,
                          early_stopping=True, n_iter_no_change=15,
                          validation_fraction=0.15, random_state=seed))
    raise ValueError(f"unknown learner {name!r}")


LEARNERS = ("bayes_z_oracle", "logistic", "lightgbm", "mlp")


# ---------------------------------------------------------------------------
# Rao-Blackwellised risks and the exact decomposition
# ---------------------------------------------------------------------------

def rb_logloss(eta: np.ndarray, p_hat: np.ndarray) -> np.ndarray:
    p = np.clip(p_hat, EPS_PROB, 1 - EPS_PROB)
    return -(eta * np.log(p) + (1 - eta) * np.log1p(-p))


def rb_brier(eta: np.ndarray, p_hat: np.ndarray) -> np.ndarray:
    return eta * (1 - eta) + (eta - p_hat) ** 2


def predict_proba_chunked(mapping, model, X_eval: pd.DataFrame,
                          chunk: int = EVAL_CHUNK) -> np.ndarray:
    """Encode and predict the evaluation sample in chunks.

    The encoded evaluation matrix can reach 763 MB (n_eval = 50,000 by
    B = 2,000), which is both the memory ceiling and the dominant runtime cost
    if it is materialised. Streaming keeps peak memory at chunk x B and returns
    only the (n_eval,) probability vector.
    """
    out = np.empty(len(X_eval), dtype=float)
    for lo in range(0, len(X_eval), chunk):
        hi = min(lo + chunk, len(X_eval))
        Z = mapping.transform(X_eval.iloc[lo:hi])
        out[lo:hi] = model.predict_proba(Z)[:, 1]
    return out


def predict_proba_chunked_multi(mapping, models: dict, X_eval: pd.DataFrame,
                                chunk: int = EVAL_CHUNK) -> dict:
    """Encode each evaluation chunk ONCE and predict it with every model.

    All learners sharing an encoder see the same encoded matrix, so encoding it
    per learner repeats the dominant cost. At M = 1000 the evaluation matrix is
    50,000 x 4,000 and the transform is a large fraction of the cell cost, so
    amortising it across the learners of one encoder is a substantial saving.
    Output is identical to calling predict_proba_chunked once per model.
    """
    out = {k: np.empty(len(X_eval), dtype=float) for k in models}
    for lo in range(0, len(X_eval), chunk):
        hi = min(lo + chunk, len(X_eval))
        Z = mapping.transform(X_eval.iloc[lo:hi])
        for name, model in models.items():
            out[name][lo:hi] = model.predict_proba(Z)[:, 1]
    return out


def decompose(eta: np.ndarray, ebar: np.ndarray, p_learner: np.ndarray,
              metric: str) -> dict:
    """representation loss + learner shortfall = total excess risk, exactly."""
    f = rb_logloss if metric == "logloss" else rb_brier
    r_x = float(f(eta, eta).mean())
    r_z = float(f(eta, ebar).mean())
    r_l = float(f(eta, p_learner).mean())
    rep, short = r_z - r_x, r_l - r_z
    resid = abs((r_l - r_x) - (rep + short))
    if resid > 1e-9:
        raise AssertionError(f"decomposition identity violated by {resid:.3e}")
    per_point = f(eta, ebar) - f(eta, eta)
    return {
        "risk_x": r_x, "risk_z": r_z, "risk_learner": r_l,
        "representation_loss": rep, "learner_shortfall": short,
        "total_excess_risk": r_l - r_x,
        "mcse": float(per_point.std(ddof=1) / np.sqrt(len(per_point))),
    }


# ---------------------------------------------------------------------------
# Typed failure discipline
# ---------------------------------------------------------------------------

METRIC_FIELDS = ("risk_x", "risk_z", "risk_learner", "theoretical_gap",
                 "estimated_gap", "representation_loss", "learner_shortfall",
                 "total_excess_risk", "mcse", "roc_auc", "pr_auc")


def cell_result(scenario_id: str, status: Status | str, metrics: dict | None = None,
                **fields) -> dict:
    """Build one replicate record, enforcing the null-metric rule.

    A cell that did not succeed carries None in EVERY metric field. No failure
    is ever recorded as a valid zero, a chance-level AUC, or an imputed value.
    """
    st = Status(status)
    row = {"scenario_id": scenario_id, "status": st.value}
    row.update(fields)
    if st is Status.SUCCESS:
        if metrics is None:
            raise ValueError("SUCCESS cell must carry metrics")
        for k in METRIC_FIELDS:
            row[k] = metrics.get(k)
    else:
        if metrics:
            raise ValueError(f"non-SUCCESS cell {scenario_id} must not carry metrics")
        for k in METRIC_FIELDS:
            row[k] = None
    return row
