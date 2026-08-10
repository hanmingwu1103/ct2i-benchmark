"""Image layouts (contract 10.5).

- IGTDReimpl  : FITTED placement layout, host reimplementation of the IGTD
  rank-matching swap algorithm, ALWAYS labelled "igtd_reimpl" in artifacts
  (Amendment B.8: method identity never silently changed; TINTOlib's IGTD is
  file-based and is exercised in the REFINED/TINTOlib smoke path instead).
  Fit: on training-side scaled features only. Deterministic under seed.
- BIERenderer : stateless serialization layout (IEEE-754 float32 bit rows,
  Stage 1 formal definition). Source: this module; no fitted state (verified
  by inspection + tests).
- BarGraphRenderer : stateless per-record bar chart on a D x D canvas.
- Pixel cap: native_pixels > MAX_NATIVE_PIXELS -> SKIPPED_INELIGIBLE upstream.
- CPU diagnostic raster: all pilot images resized to 64x64 float32 via
  area-average pooling (deterministic, no interpolation randomness).
"""
from __future__ import annotations

import numpy as np

MAX_NATIVE_PIXELS = 262_144
DIAG_SIZE = 64


class IGTDReimpl:
    """Rank-matching placement: greedy pairwise swaps reducing the difference
    between feature-distance ranks and pixel-distance ranks (IGTD, Zhu et al.
    2021, squared-error variant), reimplemented in-memory.

    fit(Z_train) learns placement phi; transform(Z) renders any rows under the
    FITTED phi (out-of-sample contract: pure lookup, no refit)."""

    name = "igtd_reimpl"
    fitted_layout = True

    def __init__(self, max_step: int = 2000, seed: int = 7):
        self.max_step = max_step
        self.seed = seed

    def _grid(self, d):
        h = int(np.ceil(np.sqrt(d)))
        w = int(np.ceil(d / h))
        return h, w

    def fit(self, Z: np.ndarray) -> IGTDReimpl:
        d = Z.shape[1]
        self.h_, self.w_ = self._grid(d)
        # feature distance ranks (Pearson-correlation distance)
        with np.errstate(invalid="ignore"):
            C = np.corrcoef(Z.T)
        C = np.nan_to_num(C, nan=0.0)
        fdist = 1.0 - C
        # pixel coordinates for first d cells (row-major)
        coords = np.array([(i // self.w_, i % self.w_) for i in range(d)], float)
        pdist = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=2)
        fr = _rank_matrix(fdist)
        pr = _rank_matrix(pdist)
        perm = np.arange(d)
        rng = np.random.default_rng(self.seed)

        def err(p):
            return float(((fr[np.ix_(p, p)] - pr) ** 2).mean())

        cur = err(perm)
        for _ in range(self.max_step):
            i, j = rng.integers(0, d, 2)
            if i == j:
                continue
            perm[[i, j]] = perm[[j, i]]
            new = err(perm)
            if new < cur:
                cur = new
            else:
                perm[[i, j]] = perm[[j, i]]
        self.perm_ = perm.copy()
        return self

    def transform(self, Z: np.ndarray) -> np.ndarray:
        n, d = Z.shape
        img = np.zeros((n, self.h_, self.w_), dtype=np.float32)
        rows = self.perm_ // self.w_
        cols = self.perm_ % self.w_
        img[:, rows, cols] = Z.astype(np.float32)
        return img

    def native_pixels(self, d: int) -> int:
        h, w = self._grid(d)
        return h * w

    def state_summary(self):
        return {"perm": self.perm_.tolist(), "h": self.h_, "w": self.w_,
                "seed": self.seed, "max_step": self.max_step}


def _rank_matrix(D):
    iu = np.triu_indices_from(D, k=1)
    vals = D[iu]
    ranks = vals.argsort().argsort().astype(float)
    R = np.zeros_like(D)
    R[iu] = ranks
    return R + R.T


class BIERenderer:
    """Stateless: row l of the image is the 32-bit IEEE-754 big-endian bit
    pattern of float32(z_l). Native size = D x 32."""
    name = "bie"
    fitted_layout = False

    def fit(self, Z=None):
        return self

    def transform(self, Z: np.ndarray) -> np.ndarray:
        n, d = Z.shape
        as_f32 = Z.astype(np.float32)
        as_u32 = as_f32.view(np.uint32)
        bits = ((as_u32[..., None] >> np.arange(31, -1, -1, dtype=np.uint32)) & 1)
        return bits.astype(np.float32)  # (n, d, 32)

    def native_pixels(self, d: int) -> int:
        return d * 32

    def state_summary(self):
        return {"stateless": True}


class BarGraphRenderer:
    """Stateless: D x D canvas; column l is a bar of height round(z_l * (D-1))
    filled from the bottom with value 1.0."""
    name = "bargraph"
    fitted_layout = False

    def fit(self, Z=None):
        return self

    def transform(self, Z: np.ndarray) -> np.ndarray:
        n, d = Z.shape
        img = np.zeros((n, d, d), dtype=np.float32)
        heights = np.rint(np.clip(Z, 0, 1) * (d - 1)).astype(int)
        for r in range(n):
            for l in range(d):
                h = heights[r, l]
                if h > 0:
                    img[r, d - h:, l] = 1.0
        return img

    def native_pixels(self, d: int) -> int:
        return d * d

    def state_summary(self):
        return {"stateless": True}


def resize_to_diag(img: np.ndarray, size: int = DIAG_SIZE) -> np.ndarray:
    """Deterministic area-average resize of (n,H,W) to (n,size,size)."""
    n, H, W = img.shape
    ys = np.linspace(0, H, size + 1).astype(int)
    xs = np.linspace(0, W, size + 1).astype(int)
    out = np.zeros((n, size, size), dtype=np.float32)
    for i in range(size):
        y0, y1 = ys[i], max(ys[i + 1], ys[i] + 1)
        for j in range(size):
            x0, x1 = xs[j], max(xs[j + 1], xs[j] + 1)
            out[:, i, j] = img[:, y0:y1, x0:x1].mean(axis=(1, 2))
    return out


REGISTRY = {"igtd_reimpl": IGTDReimpl, "bie": BIERenderer, "bargraph": BarGraphRenderer}
