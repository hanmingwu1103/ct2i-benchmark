# Figure captions — cT2I simulation-only package

Final caption text for every publication figure in this package. Written in
Phase R because the captions previously existed only as `fig.text()` footnotes
inside `scripts/run_sim1_figures.py` and `scripts/run_sim2_figures.py`, with no
durable artefact the advisor could paste into the manuscript.

The three clarifications mandated by the completion plan are marked **[MANDATED
CLARIFICATION]**. They also appear on the rendered figures themselves, so the
statement cannot be lost by a caption edit.

Nothing here changes a number. `01_PROTOCOL_FREEZE.yaml` is immutable and was
not touched.

---

## FigS1 — estimated versus theoretical representation gap

Estimated versus theoretical representation gap. The exact arms (Simulation 1A
and Simulation 1C exact) are shown in the first panel, where the theoretical gap
is available in closed form and the estimate reproduces it to the frozen
tolerance. The finite-sample arm (Simulation 1B) is shown only where the
population gap is identified. Every series is labelled EXACT or EMPIRICAL so
that an estimated finite-sample curve cannot be read as an identified population
quantity.

## FigS2 — representation loss versus within-fiber posterior spread (Simulation 1A, exact)

Representation loss against the within-fiber posterior range Delta_eta, by
encoder, for the uniform marginal (a) and the Zipf marginal (b). All cells are
exact.

**[MANDATED CLARIFICATION]** The shaded band is the **minimum-to-maximum range
across the 96 DGP conditions**. It is **not** a confidence interval and **not** a
standard-error band: these are exact cells, so the Monte Carlo standard error is
exactly zero.

## FigS3 — shared-value versus column-aware hashing as the binary width M grows

Population representation loss of the shared-value hash against binary width M,
on a log-M axis, for a position-specific target (top row) and a Hamming-weight
target (bottom row), at activation rates q = 0.05, 0.2, 0.5.

**[MANDATED CLARIFICATION]** Under the Hamming-weight target the shared-value
hash is loss-free: the largest absolute measured gap over the whole bottom row is
1.1e-16, far inside the frozen `zero_gap_abs = 1e-12` tolerance. That residual is
floating-point error, not signal, so those panels are drawn as exact zero and the
residual is stated in words on the panel rather than plotted as a curve. The two
rows of each column share one y-scale, so the position-specific loss and the
Hamming-weight zero are directly comparable and no 1e-16 axis appears.

The column-aware hash is omitted from this loss axis because its population
representation loss is **not identified**; its comparison is carried on the
ROC-AUC panel (FigS3_auc). A blank is not a zero.

## FigS3_auc — finite-sample ROC-AUC, shared-value versus column-aware hashing

Finite-sample ROC-AUC by encoder against binary width M, for the
position-specific and Hamming-weight targets. All series are EMPIRICAL. This
panel carries the shared-value versus column-aware comparison that the
population-loss axis of FigS3 cannot, because the column-aware population gap is
not identified. The dotted line marks chance (0.5).

## FigS4 — representation loss and learner shortfall (Simulation 1B)

(a) Representation loss by encoder and training size; (b) learner shortfall by
learner and training size. Markers are means over cells. Error bars are standard
errors across cells; in every cell the standard error is smaller than the
plotting marker, so no bar is separable from its marker in the rendered figure.
The two quantities are reported on separate axes and are never combined into a
single number.

**[MANDATED CLARIFICATION]** The completed Simulation 1B arm uses **d = 3 signal
coordinates in every existing cell**; M varies the number of pure-noise columns
only, so this design does **not** test dense high-cardinality signal. Simulation
1B is therefore a sparse-signal finite-sample experiment and must not be
described as establishing the pure effect of increasing signal dimension: exact
dense-signal behaviour is carried by Simulation 1A, and the binary-width
mechanism by Simulation 1C.

**[MANDATED CLARIFICATION]** Cells whose population gap is `NOT_IDENTIFIED` are
**omitted from panel (a), not assigned zero** — the count of omitted rows is
annotated on the panel. A blank is not a zero, and no failed or unidentified
cell is represented as zero or as chance performance anywhere in this figure.

*Rendering note.* This caption is the full methodological qualification for
FigS4. It previously lived as a single unwrapped `fig.text()` line inside the
figure, which stretched the `bbox_inches="tight"` canvas to 20.26 in wide and
made the panels unusable at manuscript width. The figure is now drawn on a fixed
6.9 x 3.15 in canvas and carries only a three-line condensed statement of the
two mandated clarifications above, so the disclosure cannot be lost by a caption
edit while the long qualification sits here, outside the graphics canvas. No
plotted value changed.

## Simulation 2 figure (16_SIM2_FIGURE)

(A) Oracle optimism against candidate count K at rho = 0, with the
sigma*sqrt(2 ln K) sub-Gaussian bound shown dashed in the matching colour.
(B) Validation regret (left axis, solid) and winner instability (right axis,
dashed) against K. The two quantities differ by orders of magnitude and
therefore carry one labelled axis each; the shared legend sits outside the data
region.
(C) The K = 72 minus K = 8 oracle advantage across sigma in {0.005, 0.010,
0.030}, reproduced values against the frozen Stage 2 validation targets. The
three evaluated sigma values are the only labelled ticks on the log axis.

Panels A and B are rendered from `12_SIM2_RESULTS.csv`; panel C compares the
reproduction against `01_PROTOCOL_FREEZE.yaml`
`simulation_2.validation_targets`. No numerical value was changed in Phase R;
`14_SIM2_ACCEPTANCE_REPORT.json`, `15_SIM2_FIGURE_DATA.csv` and
`17_SIM2_SUMMARY_TABLE.csv` are byte-identical to their pre-repair copies.
