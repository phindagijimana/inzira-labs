# Builder Review — HippUnfold (DeKraker et al., *eLife* 2022)

Concise **Builder Review** of the primary methods paper—not an audit of wrapper scripts. **HippUnfold**: Snakemake **BIDS App** that (i) segments hippocampal tissue and subfields with **deep learning** (nnU-Net–class models), (ii) **unfolds** the structure into an **intrinsic coordinate system** for position along the long axis, and (iii) outputs **surfaces, unfolded maps, and subfield labels** for **morphometry** and group work—aimed at clearer **intersubject alignment** and **surface-based** stats than voxel-only ROIs.

**DeKraker J, Haast RA, Yousif MD, Karat B, Lau JC, Köhler S, Khan AR.** *Automated hippocampal unfolding for morphometry and subfield segmentation with HippUnfold.* *eLife* 2022;11:e77945. https://doi.org/10.7554/eLife.77945

**Software ≥1.3.0 (unfolded-space atlas registration):** DeKraker J, et al. *eLife* 2023;12:RP88404. https://doi.org/10.7554/eLife.88404.3

---

## Methods and reproducibility (as presented)

- **Inputs:** **BIDS** structural MRI (**T1w** / **T2w**); tuned for research cohorts—**higher resolution** helps when available.
- **Segmentation:** **CNN** segmentation vs. manual labels in validation; comparison to other pipelines (e.g. FreeSurfer/ASHS-style) under stated acquisition assumptions.
- **Distribution:** Open code and **containers** help **reproducibility**; **exact metrics on new** data stay **protocol-dependent**.

---

## Strengths

- **Problem framing:** subfields and laminar position are easier to reason about in **unfolded** space than in slice or single-volume summaries alone.
- **End-to-end** path from BIDS to **surfaces, metrics, subfields** with docs and community tooling.
- **Empirical validation** vs. manual references and alternatives, with **resolution** and **failure** discussion (motion, contrast, FOV limits).

---

## Limitations and generalization

- Reported performance is **cohort-specific**; new scanner/sequence/cohort needs **local QA**—not universal numbers.
- **Unusual modalities** or species may need **masks** or **templates** off the default human T1w/T2w path.
- **Research software**—not a regulated clinical product; outputs remain **algorithm-dependent** and need **expert review** for care decisions.

---

## Positioning vs. other tools

Among **hippocampal subfield** options: vs. **volumetric ROI**-first tools, HippUnfold stresses **unfolding** and **unfold/surface** metrics. Teams needing only **fast volume** may prefer lighter stacks; teams needing **intrinsic coordinates**, **laminar-style** measures, or **unfolded registration** get a better fit at the cost of **compute** and **workflow** complexity.

---

## Synthesis

Credible case that **automated unfolding** plus **segmentation** lowers the barrier to **surface-oriented** hippocampal analysis in **typical multicenter T1w/T2w** settings, with explicit **QC**, **protocol**, and **automation** limits. Cite **2022 *eLife*** for core method; **2023 *eLife*** if you depend on **unfolded-space atlas registration** in current defaults.

---

## Relation to [HippUnfold_implement](https://github.com/phindagijimana/HippUnfold_implement)

That repo holds **HPC wrappers** (image pull, SLURM, isolation)—**not** the paper’s experiments. Successful **jobs** are **not** a substitute for the paper and [upstream](https://github.com/khanlab/hippunfold) docs for **interpretation**.

---

## References

- DeKraker et al. 2022 — HippUnfold methods (*eLife* e77945).
- DeKraker et al. 2023 — unfolded registration / multihist atlas (*eLife* RP88404).
- [hippunfold.readthedocs.io](https://hippunfold.readthedocs.io/) — manual.
- [github.com/khanlab/hippunfold](https://github.com/khanlab/hippunfold) — source.

*Updated: 2026-04-24.*
