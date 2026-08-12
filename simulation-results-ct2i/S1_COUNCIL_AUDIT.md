# S1 Council Audit — post-run independent review

**Phase:** S1 (after the full run, before packaging). **Scope:** simulation only.

Two seats audited the completed study. Provider notes are reproduced **verbatim**.

| Seat | Provider | Task |
|---|---|---|
| Numerical reproduction | Codex | independently recompute a sample of raw-to-summary calculations |
| Interpretation scope and completeness | Gemini (`gemini-2.5-pro`, Vertex AI) | judge whether the results can support the claims, and what must not be written |

---

## 1. Gemini — disposition

| Finding | Severity | Verdict | Action |
|---|---|---|---|
| `05b_SIM1B_REPLICATE_RESULTS.parquet` missing, so SIM1-RESULT-02/03 unsupported and results unverifiable | BLOCKER | **False alarm, but it caught a real defect.** The file exists. Gemini read `00_README.md`, which had been generated during a packaging dry run *before* Simulation 1B finished and still listed the file as MISSING. Its inference from that stale input was correct. | README regenerated from the completed set; the package gate now reports 30/30. Had this not been caught, the advisor would have received a README claiming the main data file was absent. |
| The fractional design (D7) is recorded as a deviation but NOT as a limitation, so comparisons involving LightGBM and the MLP are narrower than they appear | MAJOR | **Valid and accepted.** | Added to the stated limitations in `19_VALIDATION_REPORT.md`. |
| H6 rejection with reversed direction is handled honestly; states plainly what the advisor must not write | — | Accepted as written | Carried into the handoff memo's open items. |
| H5 mixed reporting is honest and complete | — | No action | — |
| CPU ceiling disclosure (D11) adequate | — | No action | — |
| NULL-versus-zero guard adequate | — | No action | — |
| Nothing in the package reads as a student-drawn interpretive conclusion | — | No action | — |

### Limitation of this audit seat

The audit workspace contained the protocol, specs, reports, summaries and
tables, but **not** the multi-hundred-megabyte parquet files. Gemini therefore
could not verify any number directly and reasoned from the documents it had —
which is exactly why its BLOCKER tracked a stale document rather than the data.
Direct numerical verification is the Codex seat's job, below.

---

## 2. Gemini audit — verbatim

> Here is the audit of the simulation study.
>
> ### **1. Manuscript Placeholders**
>
> -   **BLOCKER:** Two blocking placeholders, `SIM1-RESULT-02` and `SIM1-RESULT-03`, do not have the data they need. The required raw data file, `05b_SIM1B_REPLICATE_RESULTS.parquet`, is listed as "MISSING" in `00_README.md`. Without this file, the primary finite-sample results (summarized in `06_SIM1_SUMMARY.csv` and `tables/TabS3.csv`) are not verifiable. This prevents any responsible author from writing to these placeholders. All other blocking placeholders appear to have their required files.
>
> ### **2. Handling of Hypothesis H6**
>
> -   **Fine:** The reversed rejection of H6 is handled honestly.
>     -   The `01_PROTOCOL_FREEZE.yaml` file explicitly discloses that an S0 pilot suggested the hypothesis's direction might be wrong ("DISCLOSED_BEFORE_THE_RUN").
>     -   It documents the deliberate decision *not* to change the pre-specified hypothesis direction, which is the correct and ethical procedure.
>     -   The results in `tables/TabS3.csv` for contrasts C9, C10, and C11 accurately report large negative estimates with confidence intervals excluding zero, and consequently high p-values for the one-sided "greater" test, confirming the rejection.
> -   **What the advisor must NOT write:**
>     -   The advisor must not claim H6 was supported.
>     -   The advisor must not re-frame the result as a successful test of a new hypothesis (e.g., "we found that rare categories *decrease* instability"). The tested hypothesis was that they *increase* it; this was rejected.
>     -   The correct way to report this is to state that H6 was rejected, and to note that a significant effect was found in the opposite direction, a possibility that was anticipated and disclosed in the study protocol before the final run.
>
> ### **3. Reporting of Hypothesis H5**
>
> -   **Fine:** The reporting of the mixed result for H5 is honest and complete within the delivered package. The `tables/TabS3.csv` file clearly presents the estimates, confidence intervals, and both raw and Benjamini-Hochberg adjusted p-values for the relevant contrasts (C6, C7, C8). This transparently shows strong effects for LightGBM and logistic regression, and a non-significant effect for the MLP after FDR adjustment (`p_bh` = 0.052). The student has correctly provided the necessary data for the advisor to interpret this mixed result without drawing any premature conclusions themselves.
>
> ### **4. Stated Limitations**
>
> -   **BLOCKER:** The most severe limitation of the *delivered package* is undisclosed: the raw data file for Simulation 1B (`05b_SIM1B_REPLICATE_RESULTS.parquet`) is missing. This is a critical failure of reproducibility that prevents independent verification of the study's main finite-sample results.
> -   **MAJOR:** A material limitation of the study *design* is not included in the "Stated Limitations" section of the validation report: the use of the fractional factorial design (reported as deviation D7). This means the expensive learners (LightGBM, MLP) were run only on a subset of encoders, limiting the scope and generalizability of conclusions drawn about their performance relative to other models and encoders.
>
> ### **5. Disclosure of CPU Ceiling Overrun**
>
> -   **Fine:** The disclosure of the CPU ceiling overrun (Deviation D11) is adequate. It is stated clearly in `19_VALIDATION_REPORT.md` and in the summary table of `20_RESULT_HANDOFF_MEMO.md`. The reports specify the exact amount of the overrun (8.1 core-hours, 10%), attribute it to estimation error rather than scope creep, and provide a breakdown of resource usage. The disclosure is transparent and sufficient.
>
> ### **6. Guarding Against Misreading NULLs**
>
> -   **Fine:** The risk of a reader misinterpreting a blank (`NULL`) `representation_loss` or `learner_shortfall` as a zero is adequately guarded against. Following the protocol, the student has placed prominent, explicit warnings in the key entry-point documents.
>     -   Both `00_README.md` and `20_RESULT_HANDOFF_MEMO.md` contain a warning in bold: **"A blank is not a zero."**
>     -   The memo (`20_RESULT_HANDOFF_MEMO.md`) further explains that where the population gap is unidentified, both decomposition columns are `NULL` and that this affects the very encoders the manuscript indicts. This is sufficient to prevent reasonable misinterpretation.
>
> ### **7. Hostile Peer Review Attack Vectors**
>
> A hostile peer reviewer would have several powerful points of attack on the results as delivered:
> 1.  **BLOCKER / Unverifiable Results:** The primary attack would be the missing raw data for Simulation 1B (`05b_SIM1B_REPLICATE_RESULTS.parquet`). A reviewer would state that the central claims of the finite-sample simulation are entirely unverifiable and that the paper cannot be assessed until the raw data are provided and the summary results are reproduced from it.
> 2.  **MAJOR / Flawed Simulation Design:** The second line of attack would be the `d=min(M,3)` design of Simulation 1B. The reviewer would argue that by keeping the number of signal-carrying variables fixed at 3, the study fails to simulate the condition it claims to care about (high-dimensional categorical data) and instead only simulates a high-dimensional *noise* problem.
> 3.  **MAJOR / Incomplete Comparisons:** The use of the fractional factorial design for the heavy learners (LightGBM, MLP) would be attacked on the grounds that it makes comparisons involving them incomplete and potentially biased. The learners were not exposed to the same set of encoding challenges.
> 4.  **MINOR / Hypothesis Issues:** A less substantive, but still plausible, attack could target the handling of H5 (mixed results glossed over as "general" decrease) and H6 (rejection in the opposite direction). While the H6 handling was honest, a hostile reviewer could try to portray it as problematic.
>
> ### **8. Potential for Mistaken Interpretation**
>
> -   **Fine:** There is nothing in the package that an advisor could reasonably mistake for an interpretive conclusion drawn by the student. The student adhered strictly to the "simulation only" role. The `20_RESULT_HANDOFF_MEMO.md` and `19_VALIDATION_REPORT.md` are factual and neutral, reporting on the execution, validation, and limitations of the simulation as specified in the plan. The recommendation to add a simulation arm is a procedural suggestion for the advisor to consider, not a scientific interpretation of the existing results.

---

## 3. Codex — numerical reproduction

See section appended on completion.
