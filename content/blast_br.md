# Builder Review — BLAST-CT (Monteiro et al. 2020) + local deployment

*Bundled for the Inzira site; same text as* [github.com/…/Blast-CT-implementation/…/blast_br.md](https://github.com/phindagijimana/Blast-CT-implementation/blob/main/review/blast_br.md) *(`main`).*

---

Concise builder-oriented review of the BLAST-CT paper and this workspace implementation, focusing on deployability, reproducibility, operational behavior, and practical research use.

**Primary reference:** Monteiro M, Newcombe VFJ, Mathieu F, et al. *Multi-class semantic segmentation and quantification of traumatic brain injury lesions on head CT using deep learning.* The Lancet Digital Health. 2020. https://doi.org/10.1016/S2589-7500(20)30085-6

**Code reference:** [biomedia-mira/blast-ct](https://github.com/biomedia-mira/blast-ct)

---

## Context

BLAST-CT is a DeepMedic-based multiclass CT lesion segmentation pipeline for TBI, producing:

- voxel-wise lesion masks (IPH, EAH, oedema, IVH),
- class-level lesion volumes,
- optional atlas-based regional localisation.

This local implementation adds builder-focused hardening: unified CLI (`./blast`), SLURM submission, run metadata/events, safety defaults around pre-trained inference, and log/status tooling.

---

## Builder Fit

### What works well

- **Inference-first workflow:** pre-trained checkpoints are default; retraining is explicitly gated.
- **Unified operations surface:** `single`/`batch` + `--submit` for SLURM + `status`/`logs`.
- **Reproducibility artifacts:** `run_metadata.json`, `events.jsonl`, `log.txt`.
- **Real scheduler validation:** full-feature SLURM runs were submitted and completed in this environment.
- **Robustness fix applied:** SimpleITK transform composition incompatibility was resolved (`CompositeTransform` path with fallback).

### Practical friction points

- **Localisation output is heavy:** CSV becomes very wide; pandas fragmentation warnings appear (performance concern, not correctness failure in final run).
- **Input heterogeneity:** some NIfTI files required orientation sanitization (`--sanitize-input`) for ITK compatibility.
- **Cluster environment dependency:** GPU requested does not guarantee CUDA-ready PyTorch runtime unless environment is aligned.

---

## Performance and Generalization

### Paper claims (high-level)

- multiclass segmentation/volume quantification on a large multi-centre cohort,
- external detection validation,
- clinically relevant volume/progression outputs.

### What this implementation verifies

- **Operational fidelity:** full-feature pipeline executes end-to-end on real jobs.
- **Output fidelity:** expected artifacts are produced (mask, prob maps, class volumes, localisation outputs).
- **Not yet paper-level replication:** single/few-case runs do not reproduce cohort-level DSC/AUC/Bland-Altman statistics.

Builder takeaway: this stack is suitable for research inference workflows, but paper-equivalent performance claims require cohort evaluation with matched ground truth.

---

## Clinical and Research Applicability

- **Research workflow:** strong fit (single/batch processing, scheduler integration, audit logs, volumetric outputs).
- **Clinical workflow:** out of scope for this implementation and paper release notes; should not be used as a clinical decision system without additional governance/validation.

---

## Integration Quality (this repo)

- Added `blast_ct/submit.py` and wrapper `./blast`.
- Added `status` and `logs` subcommands for local + SLURM observability.
- Added Dockerfile and smoke tests for basic reliability checks.
- Kept output and job handling reproducible and inspectable.

---

## Limitations and Risks

- No built-in cohort evaluator in this repo yet (for automatic paper-style metrics).
- Localisation table generation is functionally correct in tested runs but computationally noisy (pandas warning profile).
- Runtime behavior still depends on site-specific scheduler and Python/CUDA stack consistency.

---

## Builder Conclusion

This BLAST-CT implementation is **research-usable and operationally credible** after hardening:

- single and batch inference are production-like for lab workflows,
- SLURM submission is proven on real jobs,
- full-feature pipeline (ensemble + localisation + exports) runs successfully.

It is **not** a substitute for cohort-level validation. For paper-level confidence, next steps are systematic benchmark evaluation and metric reporting against labeled datasets.

---

*Last updated: 2026-03-06.*
