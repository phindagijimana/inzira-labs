# Builder Review — MELD Graph (Ripart et al. 2025)

**Paper:** Ripart M, et al. *Detection of Epileptogenic Focal Cortical Dysplasia Using Graph Neural Networks: A MELD Study.* **JAMA Neurol.** 2025;82(4):397–406. https://doi.org/10.1001/jamaneurol.2024.5406

**Scope:** JAMA *Multicenter Epileptogenic Focal Cortical Dysplasia* study vs. a **deployment-oriented** workspace ([Meld_implement](https://github.com/phindagijimana/Meld_implement): `./meld`, `meld_config.sh`, `meld_graph/` with `new_patient_pipeline/`, `docker_version/meld-docker`, Apptainer images, `MELD_DEPLOY_ROOT` / `production.env`, SLURM/cohort flows). Deeper notes in that repo: `meld.md`, `meld_tech.md`, `saliency.md`.

---

## Context

- **MELD Graph:** surface **GNN** on **FreeSurfer-style** features (~34 channels × hemisphere), **clustered** predictions, **NIfTI** + **PDF** (location, size, **confidence**, **integrated-gradients** saliency). Framed as **adjunct** radiology. Main story: **higher PPV** and **fewer spurious clusters** than **MELD MLP**; multicenter + **independent** test sites.
- **Deployment note:** this write-up assumes **no GNN retraining**—**Apptainer**, paths, **SLURM**, and **interpretability** (saliency) aligned with upstream.

---

## Can it run? (usability, reproducibility)

**Published path:** open [MELDProject/meld_graph](https://github.com/MELDProject/meld_graph) + weights; T1 + optional FLAIR → **FreeSurfer or FastSurfer** → features → model → report. **Docs / Apptainer:** [install (Singularity/Apptainer)](https://meld-graph.readthedocs.io/en/latest/install_singularity.html).

**Strengths in a Meld-style stack:** `meld-docker` with `check`, `run`/`batch`, `validate`, `logs`, `slurm`, cohort flows; flags to **`new_pt_pipeline.py`** (e.g. `-harmo_code`, `--fastsurfer`, step skips, `no-report`); portable **`MELD_DEPLOY_ROOT`** / **`MELD_DATA_DIR`** for NFS-style layouts.

**Friction:** **FreeSurfer + MELD** licenses, **large** images/models, **long** per-subject runs. **BIDS** / cohort **`input/`** and **harmonization** (paper: ~**20** scans/site for ComBat; else **non-harmonized** with documented tradeoffs) are **data** work, not fixed by shell alone.

**Reproducibility:** JAMA metrics assume **MELD-style** cohorts; **full** table replay needs data **not** all public. This tree offers **runnable entrypoints**, not a replication of JAMA numbers. Local **PPV/sensitivity** can differ with **site + harmonization** even with the same weights. **Unit** tests in `meld_graph` are **structural**; **smoke** tests are **image + license + sanity**, not imaging benchmarks.

---

## Does it work off-paper? (performance, generalization)

- Treat JAMA results as a **prior** for **MELD-compatible** preprocessing; new sites need **QC, harmonization, and surface** quality, not only the checkpoint.
- **Harmonization off** especially hurts **specificity**; **multifocal** FCD and broad “all comers” epilepsy are **out of scope** in the paper. **Research adjunct**, not a cleared **device**—governance is local.
- **vs. MELD MLP:** emphasis on **actionable** output (**PPV** / off-mask **clusters**), not a single headline AUC.
- **`check` / logs** = **ops** health, **not** a local detection benchmark.

---

## Can it be used? (clinical fit, trust, integration)

- **Useful** for **FCD-oriented** **research** triage: location, clusters, **confidence**; **clinicians** still decide care.
- **Saliency** (Captum/IG in `meld_graph`) explains **model** drivers, not **causal** histology; **MRI-negative** / low-confidence cases in the paper are a warning **not** to treat weak scores as automatic positives.
- **Fits** **BIDS → NIfTI** research stacks; **PACS, identity, reporting** need **institutional** layers. Value in a builder stack: **container + SLURM + conventions**, not a hospital product.

---

## Limitations and builder insight

**Failure modes:** preprocessing **QC**; **NFS** I/O (prefer **scratch**/SSD); wrong **`-harmo_code`** or **FLAIR** assumptions; **version drift** (pinned **`meld_graph_*.sif`** vs. untested images); **license** compliance.

**Bottom line:** Strong **PPV** and **interpretability** story in a **multicenter** frame, with open **weights**. The **builder** work is **stack + data**: Apptainer, licenses, **harmonization** plan, BIDS/cohort layout, **SLURM** capacity, **QC**.

*Extensions:* CI on `meld-docker check` (+ optional smoke) on a **pinned** node; a **small public** BIDS fixture; a **version matrix** across `meld_config.sh` and `meld-docker` pins.

---

## References

- Ripart et al. 2025 — [DOI](https://doi.org/10.1001/jamaneurol.2024.5406). **Code:** https://github.com/MELDProject/meld_graph  
- [Meld_implement](https://github.com/phindagijimana/Meld_implement) — `reference_papers/meld_br.md` (upstream of this bundle)

*Last updated: 2026-04-24.*
