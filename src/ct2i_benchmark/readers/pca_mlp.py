"""PCA+MLP image reader at 64x64 diagnostic resolution.

PCA fitted on TRAINING images only (lineage-tracked); MLP = scikit-learn
MLPClassifier with fixed compact architecture; deterministic under seed.
"""
from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA
from sklearn.neural_network import MLPClassifier


class PcaMlpReader:
    name = "pca_mlp"

    def __init__(self, n_components: int = 64, hidden: int = 128, seed: int = 1042,
                 max_iter: int = 300):
        self.n_components = n_components
        self.hidden = hidden
        self.seed = seed
        self.max_iter = max_iter

    def fit(self, images_train: np.ndarray, y_train: np.ndarray) -> PcaMlpReader:
        Xf = images_train.reshape(len(images_train), -1)
        k = int(min(self.n_components, Xf.shape[1], max(2, len(Xf) - 1)))
        self.pca_ = PCA(n_components=k, random_state=self.seed).fit(Xf)
        Z = self.pca_.transform(Xf)
        self.mlp_ = MLPClassifier(hidden_layer_sizes=(self.hidden,),
                                  random_state=self.seed, max_iter=self.max_iter,
                                  early_stopping=False).fit(Z, y_train)
        return self

    def predict_proba(self, images: np.ndarray) -> np.ndarray:
        Z = self.pca_.transform(images.reshape(len(images), -1))
        return self.mlp_.predict_proba(Z)[:, 1]

    def state_summary(self):
        return {"pca_components": int(self.pca_.n_components_), "hidden": self.hidden,
                "seed": self.seed}
