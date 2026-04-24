# Builder Review — *Epilepsia* KDE EBM in MTLE-HS (Lopez et al. 2022)

This document is a **Builder Review of the research paper** below—its design, evidence, and what a builder should expect when engaging with the same methods. A **local deployment** in this repository (`EBM_TLE/`, `./ebm` CLI, `src/ebm_tle/`) is used to **ground** notes on reproducibility, runtime, and integration. That stack **helps us write the review**; it is **not** what is being “reviewed” in the product sense. The write-up uses the **Inzira Labs Builder Review** style (e.g. usability, reproducibility, performance, generalization, clinical use, interpretability, integration, limitations, builder-oriented conclusions). Optional full-criteria **Word** templates, if you use them, can stay local; this file ships in-repo with [USER_GUIDE.md](USER_GUIDE.md).

> **Object of the review:** the **publication** (Lopez et al. 2022). **Supporting material:** how we **instantiated the paper’s implied stack** in a small, internal shell—narrated only to clarify the paper, not to score a product.

**Primary reference:** Lopez SM, Aksman LM, Oxtoby NP, et al. *Event-based modeling in temporal lobe epilepsy demonstrates progressive atrophy from cross-sectional data.* Epilepsia. 2022;63(8):2081–2095. [https://doi.org/10.1111/epi.17316](https://doi.org/10.1111/epi.17316) (PMC: [https://pmc.ncbi.nlm.nih.gov/articles/PMC9540015/](https://pmc.ncbi.nlm.nih.gov/articles/PMC9540015/))

**Related in-repo file:** [EBM_TLE.md](EBM_TLE.md) — short paper summary. **Typical layout of the grounding code:** `EBM_TLE/` (CLI, `pyproject.toml`, `requirements.txt`); `pySuStaIn` / `kde_ebm` from GitHub; optional `runs/`, `.ebm/logs/`.

---

## Context: what the paper does

Lopez et al. use **cross-sectional** T1 morphometry from **ENIGMA-Epilepsy** to infer a **KDE event-based model (EBM)** sequence (hippocampus → neocortex → thalamus → ventricle) and per-subject **stages**, with clinical associations strongest for **Stage 0 vs non-0** on T1. The statistical stack is in the **UCL POND** lineage: **`kde_ebm`** (mixtures) + **`MixtureSustain`** in **pySuStaIn**—overlapping authorship with the tooling.

**Builder read:** the contribution is a clear **disease–progression** story and staging narrative from **cross-sectional** structure, with uncertainty handled as in the publication—not a generic “tool release.”

**Grounding (not a second review object):** we use a small **deployment shell** here—venv + **`./ebm`** (`install`, `check`, `demo`, `fit`, `start`, `stop`, `logs`) and thin wrappers—to touch the *same* open stack the paper’s methods point to, not to reproduce ENIGMA extraction or the paper’s full mega-analysis. The next table is **only** “where the bits live” when a reader wants to line up the paper with a concrete tree.

| Piece | Location | Role (grounding) |
|--------|-----------|------|
| CLI driver | `./ebm` | Bash: `install` creates `.venv`; other commands call `python -m ebm_tle`. |
| Python package | `src/ebm_tle/` | `demo`, `fit`, lifecycle; `synthetic.py` works around vendored `sim` import issues in upstream pySuStaIn. |
| Upstream | [pySuStaIn](https://github.com/ucl-pond/pySuStaIn), [kde_ebm](https://github.com/ucl-pond/kde_ebm) | Pinned in `requirements.txt` (git installs), matching the paper’s tooling lineage. |
| Dependencies | `requirements.txt` | `kde_ebm`, `awkde`, numpy/scipy/sklearn, etc. |
| Run state | `.ebm/run/pid`, `.ebm/logs/fit.log` | Background `start` / `stop` / `logs`. |

---

## Platform fit and reproducibility (paper first)

### What the *paper* offers

**Published study design and claims**

- Large multi-site case–control cohort; feature screen (e.g. |Cohen’s *d*| ≥ 0.5); KDE mixtures + MCMC ordering + bootstrap narrative; staging 0…*k*.

**What a builder can expect when mirroring the *methods* in code** *(illustrative, from our grounding shell; not a product review)*

- **Accessible surface:** after `./ebm install`, the paper-relevant path can be probed with `./ebm check`, `./ebm demo` (synthetic sanity), `./ebm fit cohort.csv` (your table), and lifecycle helpers. That informs **reproducibility and operability of the *methods story***, not a rating of the wrapper as software.
- **Cost / friction the paper implies in practice:** first install reaches **`kde_ebm`** and **`awkde`**; **MCMC** cost scales with `--mcmc` and pySuStaIn’s phases—i.e. the *paper*’s analysis family is **compute-heavy** relative to a single GLM.
- **Data path the paper still assumes (not replaced here):** Lopez-style work needs **ENIGMA-compatible** regional features (e.g. FreeSurfer) merged to CSV; that **feature engineering** is where real studies spend effort—the publication’s limits apply, not a limitation “of the review.”

### Reproducibility

**What the paper *supports* for replication**

- Fixed methodological account (KDE EBM, ENIGMA features, bootstrap treatment as published).

**What the paper does *not* ship to an external team**

- No bundled **pretrained** artifact in the public record as a turnkey drop-in; retraining on your table/cohort or author-shared assets is expected.
- **Figure-level** match to the original paper needs **ENIGMA-Epilepsy** data access and their pipelines.

**Builder observation when wiring the *same stack* the paper presupposes**

- A minimal path can be made **runnable** (imports, **demo** + **`fit`**) to **stress-test** the paper’s *implicit* build burden; that does not re-validate the publication’s *numerical* results on ENIGMA data.
- A small `ebm_tle/synthetic.py` workaround addresses vendored `sim` import fragility in upstream pySuStaIn when installed as a package—**upstream ergonomics**, not a critique of the *paper*.

---

## Performance, generalization, and comparison

### Performance (as described vs. as experienced when reproducing the *method*)

**Paper**

- Heavy MCMC + bootstrap; multi-site *N*; staging/sequence are compute-intensive vs. a simple regression.

**When exercising a demo aligned with the paper’s stack**

- **Demo** uses modest `--mcmc` for **smoke** tests; **longer** runs are needed to approach published practice. `./ebm check` validates environment, not a bench of the *paper*’s full MCMC.

### Generalization (from the paper)

- Orderings and mixtures are **cohort-specific**; transport requires **aligned** biomarkers and preprocessing. **Site / scanner** effects in morphometry are discussed in the publication (e.g. Stage 0 rates).

### Comparison to other approaches

- **Granger / longitudinal** paths differ; this EBM is **cross-sectional ordering** under the paper’s mixture + monotonicity framing. The **publication** situates the work in the same broad **pySuStaIn** / **kde_ebm** line as other progression modeling (e.g. AD) applied here to MTLE-HS.

---

## Clinical relevance, interpretability, and integration

*All points below are about how the **paper** positions staging and use—not an endorsement of any local shell for care.*

### Clinical relevance (from the paper)

- **Research:** Staging/sequence for **hypothesis generation** and description; the paper highlights limits relating fine stages to **clinical** endpoints (much of the signal in **Stage 0 vs not**).
- **Clinical production** (diagnosis, surgery selection, etc.) is **not** the claim of Lopez et al. in the sense of a regulated device; fine stage–outcome links remain limited in that report.

### Interpretability and trust (methods-level)

- **What’s interpretable in the *paper’s* outputs:** e.g. **`ml_stage`**, subtype/stage structure, and companion artifacts the methods describe (e.g. **`pickle_files/`** in the SuStaIn pattern).
- **What dominates failure modes:** feature quality, segmentation, and table semantics—i.e. **measurement and cohort** issues, not just “code bugs.”

### Integration (where the *paper* points research workflows)

- **Natural research path:** BIDS + FreeSurfer/ENIGMA-style summaries **→** a cohort `fit` step on a table—consistent with the *paper*’s data choice.
- **Regulated / clinical** deployment is a separate design and governance problem from **reporting** the *Epilepsia* methods.

---

## Limitations: paper vs. operational asides

**From the *paper* and the methods family**

- Interpreting stages requires sound **KDE** separation and defensible **biomarkers**; the publication discusses heterogeneity and limitations on fine clinical mapping.

**Operational notes (from our *grounding* exercise; illustrative)**

- **No in-repo imaging pipeline;** table construction is the researcher’s job—again aligning with the **paper**’s reliance on pre-derived ENIGMA-style features.
- **Networked install** to pull `pySuStaIn` / `kde_ebm` / `awkde` as in `requirements.txt`.
- **Background** `start` in this tree runs the **synthetic** demo by default; not a production job scheduler. **Headless** runs may need `MPLBACKEND=Agg` (as in our wrapper). **I/O** on shared filesystems can hurt large **pickle** writes—these are **deployment hygiene** observations, not central to scoring the *article*.

---

## Builder insight (synthesis: **paper** in focus)

Lopez et al. give a defensible **cross-sectional EBM** account on **T1** morphometry in **TLE** with a clear **Stage 0** message and an honest discussion of **limits vs. fine clinical staging**. The **open stack** (`kde_ebm` + **MixtureSustain** / pySuStaIn) is the one the **publication**’s method story assumes; our **small shell** was only to **get hands on that same stack** to write this review, not to replace **ENIGMA** feature work or the **original study’s** validation. The real **builder gap**—for the *paper’s* use cases—is still **biomarker tables, |*d*| / screening, and biologically coherent staging interpretation**, not pip wiring alone.

**If extending *research plumbing* (optional; not a review of our repo as a product)**:

- e.g. `examples/cohort_template.csv`, `Makefile` smoke `fit`, **Slurm** wrappers for long jobs, or upstream `sim` import cleanups in pySuStaIn.

---

## Commands (appendix: local grounding)

```bash
chmod +x ./ebm          # once
./ebm install           # venv + pip install (-e pySuStaIn + kde_ebm)
./ebm check
./ebm demo --output runs/demo --mcmc 8000
./ebm fit cohort.csv --output runs/fit_out --group-col group --subject-col subject_id
./ebm start             # background demo → .ebm/logs/fit.log
./ebm logs -n 100
./ebm stop
```

**Outputs of that path:** e.g. `demo_stages.csv` / `*_stages.csv`, `demo_meta.json` / `fit_meta.json`, `pickle_files/` under `--output` (see `pyproject.toml` for version).

---

## References (selected)

- Lopez et al. 2022 *Epilepsia* — MTLE-HS KDE EBM (DOI above).
- [EBM_TLE.md](EBM_TLE.md) — short paper summary in this folder.
- pySuStaIn / kde_ebm — UCL POND tooling (via `requirements.txt`, GitHub).
- Builder Review criteria (local or internal) — for alignment with other *paper* reviews in this style.

---

*Last updated: 2026-04-24.*
