# Builder Review — MOFA (Argelaguet et al. 2018) + MOFA_Omics

**Builder Review** in the Inzira style (reproducibility, performance, fit, clinical research use, interpretability, integration, limits, builder takeaway). A [MOFA_implement](https://github.com/phindagijimana/MOFA_implement) workspace can **ground** practical notes; the **paper** and **MOFA2** are the review target, not a separate product audit.

**Paper:** Argelaguet R, *et al.* *Multi-omics factor analysis: a framework for unsupervised integration of multi-omics data sets.* *Mol Syst Biol.* 2018;14:e8124. https://doi.org/10.15252/msb.20178124

**Typical implement layout:** `mofa` / `mofa_realdata` / `mofa_ctl` → **MOFA2** (`mofapy2`); `mofa_full` → NumPy reference (approximate for some likelihoods). `README.md`, `MOFA.md`, tests, `.mofa/` for daemon config/logs. This adds **tables + CLI + tests**, not a rewrite of MOFA2’s variational engine.

---

## Context

**MOFA:** variational **multi-view** model (**Z** shared, **W** per view), **ARD** + spike-and-slab, **Gaussian / Poisson / Bernoulli** likelihoods, **missing** data. Validated (paper) on **CLL** and **scRNA + methylation** among other settings.

---

## Can it run? (usability, reproducibility)

- **Usability:** **MOFA2** ships **HDF5**, tutorials, **AnnData** / **muon**. In a wrapper repo: e.g. `mofa_realdata train`, `./mofa start` + `config.json`, `./mofa checks`. **Friction:** install stack, large **D**, correct **likelihoods** and **QC** (normalization, HVG, `union`/`inner` feature alignment)—MOFA does not replace that work.
- **Reproducibility:** Paper + public data via **EGA/GEO**; [MOFA_analysis](https://github.com/bioFAM/MOFA_analysis) for paper-style reruns. A minimal wrapper: **runnable** pipeline + tests; **no** bundled patient data; **`mofa_full` ≠ mofapy2** for production publication fits. Factors depend on **K**, **drop R²**, scaling—use multiple inits when feasible (**MOFA2**; `multirestart_fit` in `mofa_full` is light).

---

## Does it work? (performance, generalization, comparison)

- **Performance:** Paper-era speedups vs iCluster/GFA; large **N×D** still needs iteration count, feature count, optional **GPU** tuning. **`checks`** = sanity, not full-cohort benchmark.
- **Generalization:** Evidence in the paper’s **CLL** / **mESC**-style cases; new cohorts need **local** validation. **Linear** factors miss strong **non-linearity** (see MOFA2 extensions). **Research** framing; diagnostics need care.
- **vs alternatives:** Clear **loadings** and **mixed** likelihoods vs marginal single-omics tests or opaque graph fusion; vs **iCluster/GFA**, MOFA trades **linearity** and **VI** assumptions for interpretability and missing views.

---

## Can it be used? (clinical research, trust, integration)

- **Research / exploratory:** Useful for **stratification** and hypothesis generation (e.g. factors vs outcomes in the paper’s framing). **Not** a licensed diagnostic—**external** validation required.
- **Interpretability:** Loadings, **variance explained**, enrichment; factors can still absorb **batch** or **composition** (label–omics **discordance** in the paper’s discussion).
- **Integration:** HDF5 → **MOFAtools**; CSV paths in a thin CLI; upstream fits with Snakemake/Nextflow-style prep. **No** EHR/LIMS; CLI = **ops** glue.

---

## Limits and builder insight

- **Likelihood** misspec, zero-inflation, **non-linearity** break assumptions. Do **not** mix **mofapy2** and **`mofa_full`** outputs in one figure without cross-checks. **Headless** training is fine; **plotting** often in **R**. **Multi-group** + factor ARD: e.g. `train_mofa2_multigroup`, not NumPy alone.

**Bottom line:** MOFA remains strong for **interpretable multi-omics** when **MOFA2** is the engine. The **builder gap** is **harmonized** matrices (IDs, preprocessing, **likelihood** choice) and **compute** for **K** / iteration depth.

*Extensions:* Makefile/Snakemake → `config.json` → HDF5; CI on `./mofa checks` + tiny train; [Apptainer](https://github.com/bioFAM/MOFA) for reproducible `mofapy2`; point exports to **MOFAtools** vignettes.

---

## References

- Argelaguet *et al.* 2018 — [DOI](https://doi.org/10.15252/msb.20178124).
- [bioFAM / MOFA](https://github.com/bioFAM/MOFA) — core; [MOFA_analysis](https://github.com/bioFAM/MOFA_analysis) — paper-style analyses.
- [MOFA_implement](https://github.com/phindagijimana/MOFA_implement) — `mofa_br.md` upstream of this bundle.

*Last updated: 2026-04-24.*
