"""Model wrappers with one interface: fit(X, y) / predict_proba(X)->p1.

Two branches (17.3):
- Representation-controlled (encoded features): logistic, lightgbm, xgboost,
  direct_mlp.
- Best-practice (native input): catboost_native (raw categorical DataFrame),
  tabm, tabicl_v2, tabpfn_3 (fixed documented inference configs; no HPO).

Foundation models are import-guarded; unavailability is typed, never faked.
"""
from __future__ import annotations

import numpy as np


class LogisticModel:
    name = "logistic"
    branch = "representation"

    def __init__(self, C: float = 1.0, seed: int = 5):
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        self._scaler = StandardScaler()
        self._m = LogisticRegression(C=C, max_iter=2000, solver="saga",
                                     random_state=seed)
        self.config = {"C": C, "seed": seed}

    def fit(self, X, y):
        Z = self._scaler.fit_transform(np.asarray(X, float))
        self._m.fit(Z, y)
        return self

    def predict_proba(self, X):
        return self._m.predict_proba(self._scaler.transform(np.asarray(X, float)))[:, 1]


class LightGBMModel:
    name = "lightgbm"
    branch = "representation"

    def __init__(self, n_estimators: int = 300, learning_rate: float = 0.05,
                 num_leaves: int = 31, seed: int = 5):
        import lightgbm as lgb
        self._m = lgb.LGBMClassifier(n_estimators=n_estimators,
                                     learning_rate=learning_rate,
                                     num_leaves=num_leaves, random_state=seed,
                                     n_jobs=4, verbose=-1)
        self.config = {"n_estimators": n_estimators, "learning_rate": learning_rate,
                       "num_leaves": num_leaves, "seed": seed}

    def fit(self, X, y):
        self._m.fit(np.asarray(X, float), y)
        return self

    def predict_proba(self, X):
        return self._m.predict_proba(np.asarray(X, float))[:, 1]


class XGBoostModel:
    name = "xgboost"
    branch = "representation"

    def __init__(self, n_estimators: int = 300, learning_rate: float = 0.05,
                 max_depth: int = 6, seed: int = 5):
        import xgboost as xgb
        self._m = xgb.XGBClassifier(n_estimators=n_estimators,
                                    learning_rate=learning_rate,
                                    max_depth=max_depth, random_state=seed,
                                    n_jobs=4, eval_metric="logloss")
        self.config = {"n_estimators": n_estimators, "learning_rate": learning_rate,
                       "max_depth": max_depth, "seed": seed}

    def fit(self, X, y):
        self._m.fit(np.asarray(X, float), y)
        return self

    def predict_proba(self, X):
        return self._m.predict_proba(np.asarray(X, float))[:, 1]


class DirectMLPModel:
    """Direct MLP on encoded features (scikit-learn; compact CPU diagnostic)."""
    name = "direct_mlp"
    branch = "representation"

    def __init__(self, hidden: int = 128, seed: int = 5, max_iter: int = 300):
        from sklearn.neural_network import MLPClassifier
        from sklearn.preprocessing import StandardScaler
        self._scaler = StandardScaler()
        self._m = MLPClassifier(hidden_layer_sizes=(hidden,), random_state=seed,
                                max_iter=max_iter)
        self.config = {"hidden": hidden, "seed": seed, "max_iter": max_iter}

    def fit(self, X, y):
        self._m.fit(self._scaler.fit_transform(np.asarray(X, float)), y)
        return self

    def predict_proba(self, X):
        return self._m.predict_proba(self._scaler.transform(np.asarray(X, float)))[:, 1]


class CatBoostNativeModel:
    """Native CatBoost on RAW categorical columns (best-practice branch)."""
    name = "catboost_native"
    branch = "best_practice"

    def __init__(self, iterations: int = 300, depth: int = 6,
                 learning_rate: float = 0.05, seed: int = 5):
        from catboost import CatBoostClassifier
        self._m = CatBoostClassifier(iterations=iterations, depth=depth,
                                     learning_rate=learning_rate,
                                     random_seed=seed, verbose=False,
                                     allow_writing_files=False, thread_count=4)
        self.config = {"iterations": iterations, "depth": depth,
                       "learning_rate": learning_rate, "seed": seed}

    def fit(self, X_df, y):
        self._cat_idx = list(range(X_df.shape[1]))
        self._m.fit(X_df.astype(str), y, cat_features=self._cat_idx)
        return self

    def predict_proba(self, X_df):
        return self._m.predict_proba(X_df.astype(str))[:, 1]


class TabMModel:
    """TabM (official yandex package) compact CPU diagnostic configuration:
    k=8 BatchEnsemble MLP on one-hot-ized numeric input via the packaged
    make/fit API; fixed epochs, AdamW, seed-controlled."""
    name = "tabm"
    branch = "best_practice"

    def __init__(self, seed: int = 5, epochs: int = 30, d_block: int = 128, k: int = 8):
        self.seed = seed; self.epochs = epochs; self.d_block = d_block; self.k = k
        self.config = {"seed": seed, "epochs": epochs, "d_block": d_block, "k": k}

    def fit(self, X, y):
        import tabm
        import torch
        torch.manual_seed(self.seed)
        X = np.asarray(X, np.float32)
        self._mean = X.mean(0); self._std = X.std(0) + 1e-8
        Xn = (X - self._mean) / self._std
        self._model = tabm.TabM.make(n_num_features=X.shape[1], cat_cardinalities=[],
                                     d_out=2, k=self.k, d_block=self.d_block)
        opt = torch.optim.AdamW(self._model.parameters(), lr=2e-3)
        xt = torch.tensor(Xn); yt = torch.tensor(np.asarray(y, np.int64))
        self._model.train()
        for _ in range(self.epochs):
            opt.zero_grad()
            out = self._model(xt)          # (n, k, 2)
            loss = torch.nn.functional.cross_entropy(
                out.flatten(0, 1), yt.repeat_interleave(self.k))
            loss.backward(); opt.step()
        return self

    def predict_proba(self, X):
        import torch
        X = np.asarray(X, np.float32)
        Xn = (X - self._mean) / self._std
        self._model.eval()
        with torch.no_grad():
            out = self._model(torch.tensor(Xn))
            p = torch.softmax(out, dim=-1)[..., 1].mean(dim=1)
        return p.numpy()


class TabICLv2Model:
    """TabICL v2 (soda-inria) fixed inference config on CPU."""
    name = "tabicl_v2"
    branch = "best_practice"

    def __init__(self, seed: int = 5):
        self.seed = seed
        self.config = {"seed": seed, "device": "cpu"}

    def fit(self, X, y):
        from tabicl import TabICLClassifier
        self._m = TabICLClassifier(device="cpu", random_state=self.seed)
        self._m.fit(np.asarray(X, np.float32), np.asarray(y))
        return self

    def predict_proba(self, X):
        return self._m.predict_proba(np.asarray(X, np.float32))[:, 1]


class TabPFN3Model:
    """TabPFN (Prior Labs official package, pinned in lockfile) fixed inference
    config on CPU. The package's own CPU/sample guard is honored — never
    overridden (§15.1)."""
    name = "tabpfn_3"
    branch = "best_practice"

    def __init__(self, seed: int = 5):
        self.seed = seed
        self.config = {"seed": seed, "device": "cpu"}

    def fit(self, X, y):
        from tabpfn import TabPFNClassifier
        self._m = TabPFNClassifier(device="cpu", random_state=self.seed)
        self._m.fit(np.asarray(X, np.float32), np.asarray(y))
        return self

    def predict_proba(self, X):
        return self._m.predict_proba(np.asarray(X, np.float32))[:, 1]


REGISTRY = {
    "logistic": LogisticModel,
    "lightgbm": LightGBMModel,
    "xgboost": XGBoostModel,
    "direct_mlp": DirectMLPModel,
    "catboost_native": CatBoostNativeModel,
    "tabm": TabMModel,
    "tabicl_v2": TabICLv2Model,
    "tabpfn_3": TabPFN3Model,
}
