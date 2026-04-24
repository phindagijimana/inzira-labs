# Builder Review — TCGA Pan-Cancer (Weinstein et al. 2013) + GDC tooling

**Builder Review** of the *Nature Genetics* Pan-Cancer **overview** and a [cancer_atlas](https://github.com/phindagijimana/cancer_atlas)-style tool layer: usability, reproducibility, performance, generalization, research/clinical fit, interpretability, integration, limits, and builder takeaway.

**Primary reference:** Weinstein JN, Collisson EA, Mills GB, *et al.*; TCGA Research Network. *The Cancer Genome Atlas Pan-Cancer analysis project.* *Nat Genet.* 2013;45(10):1113–1120. https://doi.org/10.1038/ng.2764 — [PMC3919969](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3919969/)

**Typical code layout:** `pancancer/` (Python), **`./atlas`** (`install`, `start`, `stop`, `logs`, `checks`, `pancancer` passthrough), `README.md`, `cancer_atlas.md`, report drivers; state under **`.atlas/`**. **Live** data: **NCI GDC** (https://api.gdc.cancer.gov)—no TCGA primary data in-repo. This is **GDC access + reporting**, not a re-run of MutSigCV, GISTIC2, MC3, or iCluster+.

---

## Context

The paper is a **program overview** (not one algorithm): **pancan12** (twelve tumor types), **six** assay layers (Figure 1 / Table 1), **Boxes 1–3**, **Figure 2** data flow (BCR → GCC/GSC → DCC → Firehose / cBioPortal / … → **Synapse** → GDACs), and pointers to **companion** analysis papers. The 2012 **Synapse** `pancan12` bundle is **historical**; **GDC** is the maintained public path.

A thin implementation adds **GDC** clients, Table 1–**style** case×platform **inventory** (with modern file-type proxies), mutation-index summaries, heuristics, a **downstream** catalog, optional **local HTTP** (`pancancer serve`), and **`./atlas`** lifecycle—**not** re-implementing consortium analysis stacks.

---

## Platform fit and reproducibility

**Published:** conceptual map of **multi-omic TCGA** coordination, Table 1 **counts**, research themes for **cross-lineage** work; for builders today, access is **GDC Portal** + APIs, not only Synapse snapshots.

**Implementation strengths (typical):** stdlib-friendly **core**; **`./atlas install`** / **`checks`**; **`python -m pancancer full-report`** for a **single** Markdown report aligned to paper sections; **README** maps code to **paper + GDC** sources.

**Friction:** **network** for live inventory; **controlled-access** MAFs need **dbGaP** + **GDC token**—UUID manifests do not bypass policy. **GDC** release bookkeeping ≠ 2012 Table 1 **exact** counts without **historical** snapshots.

**Reproducibility — honest tier**

- The paper gives **tumor codes**, **freeze** narrative, and Table 1 as **manuscript** sample counts.
- A **current** GDC **inventory** is an **analog** of Table 1, not a byte-level replay. **Companion** driver papers are **listed** in code like `pancancer/downstream_catalog.py` in upstream repos; they are **not** executed in this review bundle.

**Observed:** **`./atlas checks`** and health endpoints validate **reachability** (imports, GDC `/status`, case smoke)—good for **“can we talk to infrastructure?”** CI, not for **consortium** statistic replication.

---

## Performance, generalization, comparison

- **Performance:** `full-report` with **live** inventory = **many** GDC POSTs (minutes on typical networks); **`--skip-inventory`** / fast targets reduce load. **Top-mutated** lists use GDC’s **index**, not **MutSig**-style significance in this layer.
- **Generalization:** **Pancan12** is **adult**-heavy, TCGA-centric; other programs (e.g. TARGET, PCAWG) are out of the **default** scope unless you extend constants/catalogs. **Not** a clinical product—use follows **GDC/dbGaP** policy.
- **vs Synapse-only:** GDC + **`gdc-client`** is the **maintained** path; this pattern **documents** the shift.
- **vs full Pan-Cancer stacks:** **MutSig / GISTIC / iCluster+** stay **external**; **`program-catalog`**-style DOI lists point outward.

---

## Clinical relevance, interpretability, integration

- **Research / translational:** high-level **cross-tumor** framing matches the paper; **not** a diagnostic engine.
- **Interpretability:** static **2013** Table 1 next to **live** inventory; **Figure 2** flow; Box text in **`paper-info`**/reports; **downstream** catalog shows what is **out of scope** here. **Top genes** = **frequency** hints, not automatic **driver** calls.
- **Integration:** manifests for **`gdc-client`**, JSON health for **orchestration**, Markdown for **notebooks**/**pub** pipelines. **`./atlas`** = **ops** for a **local** helper, not EMR.

---

## Limitations and builder insight

- **Not** a full replay of the **2012** Synapse **freeze**.
- **Not** a drop-in for **MC3, MutSigCV, GISTIC2, MEMo, iCluster+**, *etc.*
- **Local HTTP** = **dev**-grade (e.g. localhost, no auth) unless you harden.
- **NFS** can slow **manifests** / reports; use fast disk for heavy **`gdc-client`** work.

**Bottom line:** The paper is **strong on framing** a **multi-tumor** data commons; the **builder** choice is **tier** of work: **GDC inventory + API smoke** (this style) vs **full** consortium recomputation (external + controlled data).

*Extensions (system):* scheduled **`./atlas checks`**; pinned **mock** JSON for offline unit tests; **container** with Python + `gdc-client`; **Snakemake** stubs per **downstream** catalog rows.

---

## References (selected)

- Weinstein *et al.* 2013 *Nat. Genet.* — [DOI](https://doi.org/10.1038/ng.2764).
- GDC API: https://docs.gdc.cancer.gov/API/Getting_Started/Getting_Started/
- [cancer_atlas](https://github.com/phindagijimana/cancer_atlas) — `atlas_br.md` upstream of this bundle.

*Last updated: 2026-04-24.*
