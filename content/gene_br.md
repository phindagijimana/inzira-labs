# Builder Review — ILAE × MAGMA pipeline (Mushunuri et al. 2026 style)

**Builder Review** of the *Epilepsia* methods work and a **gene_epi**-style implementation: usability, reproducibility, performance, generalization, clinical framing, interpretability, integration, limits, and builder takeaway.

**Primary reference:** Mushunuri et al. *Epilepsia* 2026. https://doi.org/10.1111/epi.70021

**Typical repo layout:** `mushunuri_ilae_pipeline/` (numbered scripts, `README.md`, `DATA_ACQUIRED.md`), **`./gene`** CLI (`install`, `start`, `stop`, `logs`, `checks`), state in `.gene/`; public assets (EPIGAD ILAE, CNCR/VU MAGMA mirrors, Zenodo H-MAGMA, GitHub eMAGMA, Schulz meQTL, GEO GPL13534). This review does **not** re-implement MAGMA’s statistics—only the **compute and ops** path.

---

## Context

**Gene-level** follow-up of epilepsy **GWAS** with **MAGMA**, **E-MAGMA** (hippocampal expression), **H-MAGMA** (adult/fetal Hi-C context), and **ME-MAGMA** (methylation QTL linkage), on **ILAE** summary statistics.

---

## Platform fit and reproducibility

**Published stack:** standard post-GWAS **gene** analysis; clear split between summary stats and functional priors (expression, chromatin, methylation).

**Typical implementation strengths:** `./gene install` chains downloads + ILAE unzip + **three-column** p-value files; `./gene start` batches phenotypes in the background; `./gene checks` validates inputs and counts `*.genes.out`.

**Friction:** **MAGMA v1.10** expects **SNP, P, N** (`ncol=3`); ILAE `.tbl` uses `Effective_N`. Large **ILAE** zip (~1.8 GB) and **g1000_eur** (~488 MB) need bandwidth and disk. **ME-MAGMA:** if paper annotations are not shared, a builder may use **Schulz 2017** imputed meQTL + 450k manifest—**logic-aligned**, not byte-identical.

**Reproducibility — aligned with the paper**

- Public **ILAE3** sumstats (EPIGAD); public MAGMA / E- / H-MAGMA assets; pinned tool versions when documented.

**Gaps**

- **LD reference:** paper may use **ILAE2** European genotypes where available; defaults to **1000 Genomes EUR** are common but can shift gene *p*-values vs. ILAE2-LD.
- **ME-MAGMA:** rebuilt annotation + *p*-cutoff (e.g. `1e-4`) affects inclusion; not a deterministic replay of undisclosed author files.
- **Role of a wrapper:** a **runnable, documented** pipeline—not a claim to re-validate every gene in the paper line by line.

---

## Performance, generalization, comparison

- **Performance:** MAGMA over **~4.8M SNPs** and **~52k genes** is **CPU-heavy** (tens of minutes × annotations × phenotypes). **NFS** home latency hurts; fast local disk helps. Wrapper **`checks`** confirm **artifacts**, not wall-clock parity with the paper.
- **Generalization:** ILAE **.tbl** format is specific (`MarkerName`, `P-value`, `Effective_N`); other cohorts need mapping or conventions. Outputs are **research** gene lists—not clinical directives.
- **Comparison:** E-/H-/ME-MAGMA differ by **which SNPs** count per gene—**complementary** rankings, not one “true” list.

---

## Clinical relevance, interpretability, integration

- **Research:** useful for **genetic architecture** of epilepsy subtypes (GGE vs focal vs all-epilepsy), pathways, and follow-up variant interpretation. **Not** bedside validation or treatment choice.
- **`*.genes.out`:** gene ID, interval, SNP count, **ZSTAT**, **P**. **FDR** scripts (e.g. per-file in R) are **not** automatically unified across annotations—interpret **calibration** with LD, annotation build, and GWAS **winner’s curse** in mind.
- **Integration:** R/tidyverse downstream; optional VarElect; Entrez links to external DBs. **`./gene`** adds **ops**, not LIMS or dbGaP plumbing.

---

## Limitations and builder insight

- **Mirrors** (VU, Zenodo, EPIGAD) can change; pin URLs in **Sources** tables.
- **MAGMA v1.10:** avoid `ncol=2` + global `N=` patterns that conflict; standardize **3-column** p-values.
- **Incomplete runs:** partial `*.genes.out` if batch stops; **`checks`** may expect a full grid (e.g. phenotypes × annotations when ME exists).

**Bottom line:** Strong for **transparent, public-data** gene follow-up on ILAE GWAS with multiple priors. **Builder gap:** **harmonize** LD choice, treat **ME-MAGMA** as a reproducible **approximation** when author files are absent, and **budget compute** for full annotation sweeps.

*Extensions:* Slurm over `./gene start`; config YAML for phenotype paths; CI **`./gene checks`** on a tiny p-value smoke file.

---

## References (selected)

- Mushunuri et al. 2026 *Epilepsia* — [DOI](https://doi.org/10.1111/epi.70021).
- [gene_epi](https://github.com/phindagijimana/gene_epi) — implementation; `gene_br.md` upstream of this bundle.
- MAGMA: https://cncr.nl/research/magma/
- ILAE / EPIGAD: https://www.epigad.org/

*Last updated: 2026-04-24.*
