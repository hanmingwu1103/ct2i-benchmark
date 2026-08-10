# ct2i-benchmark

Fold-safe, selection-valid, encoding-aware benchmark of tabular-to-image (T2I)
learning on categorical data. Companion code repository for the manuscript
"Benchmarking tabular-to-image learning on categorical data: Encoding, model
selection, and tabular baselines" (Stage 2 pilot infrastructure; CPU-only).

Status: private development repository. Stage 2 validates pipeline
correctness, leakage safety, typed failure handling, and artifact lineage on a
four-dataset CPU pilot. No Stage 2 output is a final benchmark result.

## Layout
- `src/ct2i_benchmark/` — package (data, splitting, encoders, layouts, readers,
  models, evaluation, simulations, artifacts)
- `tests/` — typed-failure (P-B), leakage-invariant (P-C), and unit tests
- `configs/` — validated run configurations incl. the frozen CPU pilot matrix
- `scripts/` — CLI entry points
- `docs/` — reproducibility documentation

## License
Project code: BSD-3-Clause (see LICENSE). Third-party datasets and model
weights retain their own licenses — see DATA_LICENSES.md and MODEL_LICENSES.md;
nothing there is relicensed under BSD-3-Clause.
