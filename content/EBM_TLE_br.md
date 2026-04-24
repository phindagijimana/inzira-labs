# Builder Review — EBM_TLE (Lopez et al. 2022) + local deployment

Evaluation of the *Epilepsia* EBM/MTLE-HS methods paper and this workspace’s implementation, using the **Inzira Labs Builder Review** style (usability, reproducibility, performance, generalization, clinical use, interpretability, integration, limitations, and builder-oriented conclusions). Full criteria **Word** templates, if you use them, can stay **local** only; this Markdown review is what ships in-repo alongside [USER_GUIDE.md](USER_GUIDE.md).

**Primary reference:** Lopez SM, Aksman LM, Oxtoby NP, et al. *Event-based modeling in temporal lobe epilepsy demonstrates progressive atrophy from cross-sectional data.* Epilepsia. 2022;63(8):2081–2095. https://doi.org/10.1111/epi.17316 (PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC9540015/)

**Typical local layout:** `EBM_TLE/` (`./ebm` CLI, `src/ebm_tle/`, `requirements.txt`, `pyproject.toml`); **`pySuStaIn` / `kde_ebm` from GitHub** via pip; optional `runs/`, `.ebm/logs/`; paper summary in `EBM_TLE.md`.

---

## Context

Lopez et al. use **cross-sectional** T1 morphometry from **ENIGMA-Epilepsy** to infer a **KDE event-based model (EBM)** sequence (hippocampus → neocortex → thalamus → ventricle) and per-subject **stages**, with clinical associations strongest for **Stage 0 vs non-0** on T1. The statistical stack is in the **UCL POND** lineage: **`kde_ebm`** (mixtures) + **`MixtureSustain`** in **pySuStaIn**—overlapping authorship with the tooling.

This workspace adds a **deployment shell**: venv + **`./ebm`** (`install`, `check`, `demo`, `fit`, `start`, `stop`, `logs`) and thin wrappers—not a reimplementation of ENIGMA extraction or the paper’s exact mega-analysis.

| Piece | Location | Role |
|--------|-----------|------|
| CLI driver | `./ebm` | Bash: `install` creates `.venv`; other commands call `python -m ebm_tle`. |
| Python package | `src/ebm_tle/` | `demo`, `fit`, lifecycle commands; `synthetic.py` avoids broken `sim` package imports in upstream pySuStaIn. |
| Upstream | [ucl-pond/pySuStaIn](https://github.com/ucl-pond/pySuStaIn), [kde_ebm](https://github.com/ucl-pond/kde_ebm) | Pinned in `requirements.txt` (Git installs). |
| Dependencies | `requirements.txt` | `kde_ebm`, `awkde`, numpy/scipy/sklearn, etc. (git + network on first install). |
| Run state | `.ebm/run/pid`, `.ebm/logs/fit.log` | Background `start` / `stop` / `logs`. |

---

## Platform fit and reproducibility

### Usability

**Published offering**

- Large multi-site case–control cohort; feature screen (e.g. |Cohen’s *d*| ≥ 0.5); KDE mixtures + MCMC ordering + bootstrap narrative; staging 0…*k*.

**This implementation**

- **Strength:** One surface after `./ebm install`: `./ebm check`, `./ebm demo` (synthetic sanity), `./ebm fit cohort.csv` (your biomarker table), plus `./ebm start|stop|logs` for background demo runs.
- **Friction:** First install pulls **`kde_ebm`** and **`awkde`** from GitHub; **MCMC wall time** grows with `--mcmc` and pySuStaIn’s internal phases—plan for HPC for research-scale iterations.
- **Hidden steps:** Real Lopez-style work still needs **ENIGMA-compatible** regional features (FreeSurfer or equivalent) merged into CSV; this repo does **not** run recon-all.

### Reproducibility

**What the paper supports**

- Fixed methodological story (KDE EBM, ENIGMA features, bootstrap uncertainty in the publication).

**Gaps for an external builder**

- No bundled **pretrained pickle** from the paper; you **retrain** on your CSV/cohort or obtain artifacts from authors if ever shared.
- End-to-end replication of paper figures requires **ENIGMA-Epilepsy** data access and their pipelines—not shipped here.

**Observed**

- **Our deployment** reproduces *runnable infrastructure* (imports, demo fit, `fit` path); it does not re-validate paper metrics on ENIGMA data.
- **`ebm_tle/synthetic.py`** replaces vendored `sim` package imports (`from simfuncs import *` fails when `sim` is installed as a package).

---

## Performance, generalization, and comparison

### Performance (real vs reported)

**Paper**

- Heavy MCMC + bootstrap; multicenter *N*; staging and sequence inference are compute-intensive relative to a single GLM.

**Builder expectation**

- Default **`demo`** uses modest `--mcmc` for smoke tests; raise **`--mcmc`** for analyses meant to align with published practice (longer runs).
- **`./ebm check`** does **not** benchmark MCMC; it validates environment and paths.

### Generalization

- Model ordering and mixtures are **dataset-specific**; applying a model trained elsewhere requires **matched** biomarker definitions and preprocessing.
- **Site/scanner** effects in real morphometry still matter; the paper discusses center heterogeneity (e.g. Stage 0 rates).

### Comparison to existing methods

- **Granger / longitudinal** approaches differ; EBM here is **cross-sectional ordering** under mixture + monotonicity assumptions. **Builder takeaway:** same tooling family as other **pySuStaIn** / **kde_ebm** disease-progression work (e.g. AD), adapted to MTLE-HS morphometry in the publication.

---

## Clinical relevance, interpretability, and integration

### Clinical relevance

- **Research:** Staging and sequence support **hypothesis generation** and cohort description; the paper emphasizes limits of fine-stage vs clinical variables (much of the signal in **Stage 0 vs not**).
- **Clinical production** (diagnosis, prognosis, surgical candidacy) is **out of scope** for this repo and under-supported by fine-grained stage–outcome links in that paper.

### Interpretability and trust

- **Strength:** Outputs include **`ml_stage`**, subtype/stage probabilities, and pySuStaIn **`pickle_files/`** for inspection with upstream tooling.
- **Trust limits:** Stages depend on **KDE separation** and chosen biomarkers; bad segmentation or wrong columns in CSV dominate failures.

### Integration potential

- **Research integration:** Natural downstream of **BIDS + FreeSurfer/ENIGMA-style** summary tables → **`ebm fit`**.
- **Clinical integration:** Not provided; governance and intended-use labeling remain with the deploying institution.

---

## Limitations and failure modes

- **No imaging pipeline** in-repo; CSV quality is the builder’s responsibility.
- **`./ebm install`** needs network access to clone **`pySuStaIn`** / **`kde_ebm`** / **`awkde`** from GitHub.
- **Background `start`** runs the **synthetic demo** by default—not a generic job queue; change `cli.cmd_start` to background **`fit`** if needed.
- **Headless:** set `MPLBACKEND=Agg` (default in `./ebm`); plotting in SuStaIn may still touch matplotlib.
- **NFS/home latency** can slow venv I/O and large pickle writes; local SSD may help heavy runs.

---

## Builder insight

EBM_TLE is **strong on wiring the same open stack** the paper’s methods imply (**`kde_ebm` + `MixtureSustain`**) into a **small, operable CLI** for internal research. The **builder gap** is **feature engineering and validation**: building ENIGMA-like tables, choosing biomarkers and |*d*| thresholds, and interpreting stages in light of the paper’s **Stage 0** findings—not installing Python packages.

**Potential extensions (system-level)**

- Example **`examples/cohort_template.csv`** and a **Makefile** target for smoke `fit`.
- **Slurm wrapper** for long `fit` jobs with frozen `requirements.txt` hash in logs.
- **Optional** patch or upstream PR for vendored **`sim`** package imports (use relative `from .simfuncs import *`) so `synthetic.py` could be retired.

---

## Commands (quick reference)

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

**Outputs:** `demo_stages.csv` / `*_stages.csv`, `demo_meta.json` / `fit_meta.json`, **`pickle_files/`** under `--output`. Package version **0.1.0** (`pyproject.toml`).

---

## References (selected)

- Lopez et al. 2022 *Epilepsia* — MTLE-HS KDE EBM (DOI above).
- `EBM_TLE.md` — concise paper summary in this folder.
- pySuStaIn / kde_ebm — UCL POND tooling (installed via `requirements.txt`, GitHub).
- Builder Review criteria (local or internal docs) — full dimension list if needed for alignment with other reviews.

---

*Last updated: 2026-04-14.*
