# Builder Review — Jiang et al. 2024 (TLE biotypes + SuStaIn)

Condensed look at the *Nature Communications* study: what a builder can realistically reuse. Layers: **Can it run?** **Does it work?** **Can it be used?**—plus limitations and takeaway.

**Primary reference:** Jiang Y, Li W, Li J, et al. *Identification of four biotypes in temporal lobe epilepsy via machine learning on brain images.* Nat Commun. 2024;15:2221. https://doi.org/10.1038/s41467-024-46629-6

**Related work:** a replication-oriented kit lives in the [predict_epi](https://github.com/phindagijimana/predict_epi) repo (`JIANG_2024_REPLICATION.md`, `implement/`, `vendor/pySuStaIn/`, public supplementary data where published).

---

## Context

Four MRI-derived **biotypes** in TLE via z-scored regional morphometry and **SuStaIn**, linked to clinical variables and predictors. **Raw imaging and subject-level feature matrices are not public;** Source Data support summary figures and tables.

---

## Can it run?

**What the paper documents:** FreeSurfer 6.0, ROI set, z thresholds, MCMC, CVIC; supplements and Source Data on the publisher site.

**What you still bring:** T1 MRI → cortical/subcortical extraction → comparable z-score table with **your** controls. The predict_epi kit adds a CLI, loaders, figure-style plots from Source Data, and a **synthetic** SuStaIn demo—not a one-click full-cohort replay. Expect Python, optional HPC, and FreeSurfer (or equivalent) **outside** a single repo.

**Reproducibility without private data:** aggregate plots/tables from Source Data can match published values. **Not** from supplements alone: subject z-scores, full MCMC chains, trajectory order, or individual biotype labels (need the authors’ matrix or refit on a new cohort). Classifiers (e.g. SVM + PCA) share that boundary. Sensitivity to random starts, MCMC length, and control regression is expected; new sites must re-derive z-scores and harmonize.

---

## Does it work? Will it generalize?

- Reported metrics are **tied to their preprocessing and cohort**—**validate on your data**; do not assume portability.
- The bundled synthetic run only exercises the Z-score / piecewise **model class**—not a benchmark against the paper’s full metrics.
- **Single-cohort** study: cross-scanner, cross-site, pediatric, or mixed populations not established. SuStaIn subtypes depend on the normative model and ROI set; atlas or software changes shift the space. There is **no** public pretrained pickle that assigns to the authors’ four biotypes out of the box.

---

## Can it be used? (clinical / integration / trust)

- Biotypes and stages could support **stratification and trial design** if validated locally—not a CADx or deployment story in the paper; regulation would need separate evidence.
- Routine clinical pipelines rarely output the exact **ROI z-score** table SuStaIn needs; **research-grade** preprocessing is still required.
- SuStaIn is relatively **interpretable** (ordered ROI events, subtype means) vs. a black box; **trust** still depends on FreeSurfer QC, motion, segmentation—failures can cluster by biotype.
- **Research fit:** pySuStaIn, ENIGMA-style viz, BIDS + containers. **Clinical fit:** DICOM → morphometry → QC → SuStaIn → reporting is **not** turnkey from supplements alone.

---

## Limitations

- Private features block **numerical** replication of the authors’ SuStaIn fits.
- **CVIC** and trajectory structure can shift with cohort composition.
- Imbalance, comorbidities, and surgical selection can distort biotype–outcome links if unmodeled.
- **Synthetic demo ≠ empirical** results.

---

## Builder insight

Strong framing and public summaries; the **practical gap** is the missing feature matrix and **harmonization** for new sites. Reasonable path: **standardize preprocessing**, mirror ROI/covariate regression, **refit** SuStaIn, then **prospective** validation before any deployment story.

*Possible next steps (where useful):* minimal simulated data matching the feature schema; pinned FreeSurfer + analysis **container** recipe; pre-registered **stability** on external data.

---

## References (selected)

- Jiang et al. 2024 Nat Commun — TLE biotypes (DOI above).
- Young et al. 2018 Nat Commun — SuStaIn methods.

*Last updated: 2026-04-23.*
