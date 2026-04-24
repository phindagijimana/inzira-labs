# Builder Review — Jiang et al. 2024 (TLE biotypes + SuStaIn)

Evaluation of the *Nature Communications* study and what a builder can realistically reuse, using the same Inzira Labs Builder Review layers as in a full framework doc (usability, reproducibility, performance, generalization, clinical use, interpretability, integration, limitations, builder insight).

**Primary reference:** Jiang Y, Li W, Li J, et al. *Identification of four biotypes in temporal lobe epilepsy via machine learning on brain images.* Nat Commun. 2024;15:2221. https://doi.org/10.1038/s41467-024-46629-6

**Local kit:** this repository (`JIANG_2024_REPLICATION.md`, `implement/`, `vendor/pySuStaIn/`, `data/public_supplementary/` after download).

---

# Context

The paper identifies four MRI-derived biotypes in temporal lobe epilepsy using z-scored regional morphometry and Subtype and Stage Inference (SuStaIn), then links biotypes to clinical variables and prediction models. Raw imaging and subject-level feature matrices are not public; publisher Source Data spreadsheets support summary figures and tables.

---

# Layer 1 — Can it run?

## Usability

For the published work:

- Methods and hyperparameters are documented (FreeSurfer 6.0, ROI set, z thresholds 1–2–3, MCMC settings, CVIC).
- Supplementary PDFs and Source Data (MOESM) are available from the publisher.

For an independent builder:

- You must supply T1 MRI, run cortical/subcortical extraction, and build a comparable z-score matrix with your own controls.
- This repo adds a CLI (`./sustain`), Excel loaders, figure-style plots from Source Data, and a synthetic pySuStaIn demo—not a one-click replay of the full cohort.

However:

- End-to-end replication without raw data still leaves SuStaIn fitting and subtype assignment as a bring-your-own-features exercise.
- Tooling assumes Python skill, optional HPC, and FreeSurfer or equivalent outside this repo.

## Reproducibility

What aligns with the paper without private data:

- Aggregate plots and tables driven from Source Data (e.g. Fig. 2–3–style summaries in predict_epi) can match published values when using the same spreadsheets.

What does not fully reproduce from supplements alone:

- Subject-level z-scores, SuStaIn MCMC chains, trajectory ordering, and individual biotype labels require the authors’ feature matrix or refitting on a new cohort.
- Downstream classifiers (e.g. SVM + PCA) inherit the same data boundary: labels and features must be reconstructed locally.

Observed:

- Sensitivity to random starts (25), MCMC length, and control-sample regression is expected; the paper reports robustness checks in supplementary material.
- Any new site must re-derive z-scores; thresholds are not automatically transferable without harmonization.

---

## Layer 2 — Does it work?

### Performance

The paper reports group separations, associations with clinical variables, and prediction metrics on their cohort. Those numbers are tied to their preprocessing and population.

Observed for an external builder:

- You should expect to validate de novo on your data; performance should not be assumed to port.
- The bundled synthetic SuStaIn run only exercises the Z-score / piecewise model class—it does not benchmark against the paper’s metrics.

## Generalization

Cross-scanner, cross-site, and pediatric or mixed-epilepsy populations are not established by the single-cohort study.

- SuStaIn subtypes are defined relative to the normative model and ROI set; changing atlas, software version, or covariate regression changes the latent space.
- There is no public pretrained SuStaIn pickle that assigns new patients to the authors’ four biotypes out of the box.

---

# Layer 3 — Can it be used?

## Clinical relevance

- Biotypes plus stages could enrich stratification and trial design if validated locally.
- Workflow gap: routine clinical MRI pipelines rarely output the exact ROI z-score table SuStaIn expects; research-grade preprocessing is still a prerequisite.
- Regulatory and deployment paths (CADx-style use) are not addressed in the paper and would need separate evidence.

## Interpretability and trust

- SuStaIn outputs are interpretable at the level of ordered ROI events and subtype means, which is stronger than a black-box embedding alone.
- Trust still depends on QC of FreeSurfer outputs, motion, and segmentation failures—failure modes may concentrate in specific biotypes.

## Integration potential

- Research integration: pySuStaIn, ENIGMA-style visualization, and BIDS-oriented preprocessing stacks (e.g. containerized neuroimaging environments) are natural adjacent layers.
- Clinical integration: would require DICOM → structured morphometry → QC → SuStaIn → reporting; none of that is turnkey in supplementary files alone.

---

# Limitations and failure modes

- Private imaging and features block exact numerical replication of SuStaIn fits.
- Subtype count selection (CVIC) and trajectory structure can shift with cohort composition.
- Class imbalance, comorbidities, and surgical candidacy may distort apparent biotype–outcome relationships if not modeled.
- The local demo uses synthetic data; it must not be mistaken for empirical results.

---

# Builder insight

The paper is strong on scientific framing and public summaries; the builder gap is the missing feature matrix and harmonization story for new sites. A practical path is: standardize preprocessing, mirror the ROI/covariate regression protocol, refit SuStaIn, then run prospective validation before any deployment narrative.

Potential extensions:

- Share (where ethics allow) a minimal simulated dataset with the same schema as the real features, for pipeline testing only.
- Publish a reference Dockerfile/Apptainer recipe pinning FreeSurfer 6.0 and analysis library versions.
- Pre-register subtype stability analyses when applying the model to an external cohort.

---

# References (selected)

- Jiang et al. 2024 Nat Commun — primary TLE biotype paper (DOI above).
- Young et al. 2018 Nat Commun — SuStaIn methods foundation.
- `JIANG_2024_REPLICATION.md` — replication kit notes and commands.

---

To refresh **`sustain_br.docx`** locally after edits: `python3 scripts/render_sustain_br_docx.py` (from the [predict_epi](https://github.com/phindagijimana/predict_epi) repo root). Word copies are not tracked on GitHub.

*Last updated: 2026-04-14.*
