# Builder Review — BrainIAC (paper) + Brain_Cal implementation

**Primary reference:** BrainIAC / brain MRI multi-task work as packaged in the implementation repo (see `brain_model_paper.pdf` in [AI_MRI_Brain_Analysis_Model](https://github.com/phindagijimana/AI_MRI_Brain_Analysis_Model)).

**Scope:** Builder-oriented read: deployment realism—**modality** routing, **checkpoint** compatibility, **reliability**, and **output** structure—grounded in the **Brain_Cal** pipeline, not a second audit of the PDF alone.

---

## Context

The review uses the **implemented** surface in that repository:

- **Local:** `./brain models`, `./brain run-tasks`
- **SLURM:** `./brain submit-models`
- **Outputs:** per-task **JSON** plus `quantitative_summary.csv` / `quantitative_summary.json`

---

## Usability and reproducibility

**Strengths**

- **Single CLI** for multiple downstream tasks.
- **Explicit** runtime checks: missing / corrupted / **incompatible** checkpoints skipped with **clear** messages.
- **Auto** quantitative summaries—less manual aggregation.
- **Brain-age** export includes `predicted_age_months` and `predicted_age_years` for easier reading.

**Fixes that improve “what actually ran”**

- **Modality gating (brain-age):** prefer **T1-like** files (e.g. `*_T1w.nii.gz`), avoiding mistaken **FLAIR-only** runs.
- **IDH (dual input):** paired `*_t2f` and `*_t1ce` required for the local path.
- **Task-level skip:** one bad model need not **fail** the whole run.

---

## Example run (illustrative)

*Upstream note:* numbers from a validated run such as `outputs_sub01_real_updated/quantitative_summary.csv` (see [review on GitHub](https://github.com/phindagijimana/AI_MRI_Brain_Analysis_Model/blob/main/review/Brain_Cal_br.md))—**not** a guarantee for new data.

- **brainage** on T1w: on the order of **~20 y** in that snapshot (~239 months as reported upstream).
- **mci / stroke** classifiers: **probabilities** and discrete labels; treat as **model scores**—**calibration** and external validation still required.
- **segmentation:** nonzero mask metrics for **T1w** and **FLAIR** when inputs match expectations.

**Builder read:** the **pipeline** can run **end-to-end** for the tasks that have **valid** assets; tables are **consistent** for reporting. **Overconfident** probabilities (e.g. very near 1.0) warrant **QC**, not automatic acceptance.

---

## Generalization and deployment risk

- **Site / scanner / protocol** shift: treat published performance as a **prior**.
- **Modality mismatch** is a common failure mode; **gating** reduces accidental wrong-input runs.
- **Architecture mismatch** (e.g. ResNet-style weights vs ViT loader): should **fail early** with clear skips when implemented that way.
- **Calibration** on new sites is still a **research** obligation.

---

## Integration readiness

- **Fit:** research deployment on **workstation** + **SLURM**; structured artifacts help **cohort** bookkeeping and **audit**.

**Gaps (typical; check current repo):**

- **`sequence`:** may be blocked if a **checkpoint** file is unusable.
- **`survival`:** may need a **ViT**-compatible `os.ckpt` (or equivalent).
- **`submit-models` + IDH:** may **skip** until **paired** SLURM wiring is complete.

---

## Builder conclusion

The paper’s task framing is **implementable in practice** when checkpoints and modalities align. The main **blockers** in hardened builds are often **assets** and **orchestration** (missing or incompatible weights, **paired** multi-sequence **SLURM** paths), not the high-level **pipeline** layout.

*Last updated: 2026-04-25.*
