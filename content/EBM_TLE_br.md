# Builder Review — Lopez et al. 2022 (*Epilepsia* KDE EBM in MTLE-HS)

**Builder Review** of the paper below—design, evidence, and what to expect when using the same methods. A small local stack (`EBM_TLE/`, `./ebm`) **grounds** notes on reproducibility and runtime; it supports the write-up, not a separate product review. Style: usability, reproducibility, performance, generalization, clinical framing, interpretability, integration, limitations, builder takeaway.

> **Review object:** the **publication** (Lopez et al. 2022). **Supporting context:** how we wired the paper’s implied tooling in a minimal shell—only to clarify the paper.

**Primary reference:** Lopez SM, Aksman LM, Oxtoby NP, et al. *Event-based modeling in temporal lobe epilepsy demonstrates progressive atrophy from cross-sectional data.* Epilepsia. 2022;63(8):2081–2095. [DOI](https://doi.org/10.1111/epi.17316) · [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9540015/)

**Related:** [EBM_TLE.md](EBM_TLE.md) (short summary). **Code layout:** `EBM_TLE/` (CLI), `src/ebm_tle/`; upstream [pySuStaIn](https://github.com/ucl-pond/pySuStaIn), [kde_ebm](https://github.com/ucl-pond/kde_ebm).

---

## Context

Lopez et al. use **cross-sectional** T1 morphometry from **ENIGMA-Epilepsy** to infer a **KDE EBM** sequence (hippocampus → neocortex → thalamus → ventricle) and per-subject **stages**, with strongest clinical signal for **Stage 0 vs non-0**. Stack: **`kde_ebm`** + **`MixtureSustain`** in **pySuStaIn** (UCL POND lineage).

**Builder read:** a clear **disease–progression** story from cross-sectional structure—not a generic tool release.

**Where the grounding code lives (optional map):** `./ebm` (Bash → `python -m ebm_tle`); `src/ebm_tle/` (demo, fit, synthetic workaround for vendored `sim` imports); `requirements.txt` pins `kde_ebm` / `awkde`; `.ebm/` for run logs. This does **not** reproduce ENIGMA extraction or the full mega-analysis.

---

## Platform fit and reproducibility

**From the paper**

- Multi-site case–control; feature screen (e.g. |Cohen’s *d*| ≥ 0.5); KDE mixtures + MCMC ordering + bootstrap; stages 0…*k*.

**When mirroring the methods in code**

- After `./ebm install`: `./ebm check`, `./ebm demo`, `./ebm fit cohort.csv` probe the same stack the paper assumes—**compute-heavy** (MCMC, pySuStaIn phases), not a single GLM.
- Lopez-style work still needs **ENIGMA-compatible** regional features (e.g. FreeSurfer) → CSV; that **feature path** is where real studies spend effort.

**Replication limits in the public record**

- No turnkey **pretrained** drop-in for external teams; retraining on your table/cohort is expected.
- Figure-level match needs **ENIGMA-Epilepsy** data and their pipelines.

**Notes from wiring the stack**

- Demo uses modest `--mcmc` for smoke tests; longer runs match published practice more closely. `ebm_tle/synthetic.py` works around upstream pySuStaIn package import quirks—**ergonomics**, not a critique of the paper.

---

## Performance, generalization, comparison

- **Performance (paper):** heavy MCMC + bootstrap; staging is intensive vs. simple regression. Demo is a smoke test, not a benchmark of full published MCMC.
- **Generalization:** orderings are **cohort-specific**; transport needs aligned biomarkers and preprocessing. Site/scanner effects are discussed (e.g. Stage 0 rates).
- **vs. other work:** this EBM is **cross-sectional ordering** under mixture + monotonicity; the paper situates it in the **pySuStaIn** / **kde_ebm** line (e.g. vs. Granger / longitudinal paths).

---

## Clinical relevance, interpretability, integration

*How the **paper** positions use—not an endorsement of any local shell for care.*

- **Research:** staging for hypothesis generation; limits on fine stage vs. **clinical** endpoints (much of the signal in **Stage 0 vs not**). **Not** a regulated device claim.
- **Interpretable outputs:** e.g. `ml_stage`, subtype/stage structure, companion artifacts the methods describe.
- **Failure modes:** feature quality, segmentation, table semantics—measurement and cohort, not only code bugs.
- **Integration path:** BIDS + FreeSurfer/ENIGMA-style summaries → cohort `fit`. Regulated deployment is out of scope for the *Epilepsia* methods story.

---

## Limitations

**Paper / methods family:** sound **KDE** separation and defensible **biomarkers**; publication discusses heterogeneity and limits on fine clinical mapping.

**Operational (illustrative):** no in-repo imaging pipeline; networked install for `pySuStaIn` / `kde_ebm` / `awkde`; background `start` runs synthetic demo; headless may need `MPLBACKEND=Agg`; large **pickle** I/O on shared FS—**deployment hygiene**, not central to the article.

---

## Builder insight

Lopez et al. give a defensible **cross-sectional EBM** on T1 morphometry in TLE with a clear **Stage 0** message and honest **limits** on fine clinical staging. The **open stack** is the one the publication assumes; the **small shell** here was only to use that stack while writing the review, not to replace ENIGMA work or the original validation. The **builder gap** for the paper’s use cases is still **biomarker tables, screening, and biologically coherent staging interpretation**—not wiring alone.

*Optional research plumbing:* e.g. `examples/cohort_template.csv`, `Makefile` smokes, Slurm for long runs.

---

## Commands (appendix: local grounding)

```bash
chmod +x ./ebm
./ebm install
./ebm check
./ebm demo --output runs/demo --mcmc 8000
./ebm fit cohort.csv --output runs/fit_out --group-col group --subject-col subject_id
./ebm start; ./ebm logs -n 100; ./ebm stop
```

**Outputs:** e.g. `*_stages.csv`, `*_meta.json`, `pickle_files/` under `--output`.

---

## References (selected)

- Lopez et al. 2022 *Epilepsia* — [DOI above](https://doi.org/10.1111/epi.17316).
- [EBM_TLE.md](EBM_TLE.md) — short summary in-repo.
- pySuStaIn / kde_ebm — UCL POND (see `requirements.txt`).

*Last updated: 2026-04-24.*
