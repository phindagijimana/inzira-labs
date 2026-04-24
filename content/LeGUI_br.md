# Builder Review — LeGUI (Davis et al. 2021) + local deployment

**Builder Review** of the *Frontiers in Neuroscience* methods paper and a [LeGUI_implement](https://github.com/phindagijimana/LeGUI_implement)-style **deployment shell**—not a rewrite of LeGUI’s algorithms.

**Primary reference:** Davis TS, Caston RM, Philip B, *et al.* *LeGUI: A Fast and Accurate Graphical User Interface for Automated Detection and Anatomical Localization of Intracranial Electrodes.* *Front Neurosci.* 2021;15:769872. https://doi.org/10.3389/fnins.2021.769872

**Typical layout:** `LeGUI` CLI, `run_LeGUI.sh`, `verify_legui_setup.sh`, docs; **local** MATLAB Runtime **R2021b** (e.g. v9.11), `LeGUI_Linux_v1.2/` from releases, optional [Rolston-Lab/LeGUI](https://github.com/Rolston-Lab/LeGUI) source in `legui-repo/`. **GPL v3** upstream; compiled Linux build tied to a **specific** runtime.

---

## Context

**LeGUI** is a **MATLAB/SPM12** workflow: CT–MRI coregistration, MNI normalization, **automated** ECoG + SEEG detection, brain-shift / spacing correction, labeling, **atlas** anatomy, export for analysis. A deployment repo adds MCR install paths, **verification**, **`./LeGUI`** (`install`, `start`, `logs`, `stop`, `checks`)—**infrastructure**, not new science.

---

## Platform fit and reproducibility

**Published:** integrated **GUI** vs. chaining many tools; SPM12 for coregistration/segmentation; **standalone** binaries + **MATLAB Runtime** for users without a MATLAB license. Inputs: pre-implant T1, post-implant CT (ideally ≤1 mm isotropic), AC–PC alignment; time on the order of **~1 h**/case in the paper (mixed user + compute).

**Deployment strengths:** one surface: `./LeGUI install` → `./LeGUI start` after MCR; `checks` may wrap filesystem + `ldd` against bundled MCR.

**Friction:** **MCR ~3.7 GB**; silent install is slow; **GUI needs a display** (desktop, VNC, RDP, X11)—**not** a headless batch cluster product. **Atlas**/SPM toolbox and **DICOM** quirks still drive manual cleanup (false positives, labeling), as the paper notes.

**Reproducibility — paper vs. your site**

- Fixed **algorithmic** story and validation on **51** datasets; **sensitivity** and **atlas agreement** reported.
- **Your** end-to-end numbers need **your** imaging. **MNI**-centric; comparisons to **FreeSurfer**-class pipelines need **harmonization**.
- **This shell** = **runnable** MCR + binary + CLI; it does **not** re-validate the paper on new data by itself.

**Observed:** detection sensitivity varies by **implant** vendor/geometry; **CT** thresholds are **cohort-specific** (HU distribution)—avoid one global default.

---

## Performance, generalization, comparison

- **Paper:** ~**93%** auto-detection sensitivity with manageable FPs; ~**30 min** for heavy image steps; atlas vs. expert **73%** at **1.3 mm** sphere, **94%** with **~1 cm** neighborhood—**resolution** matters.
- **New institution:** treat paper stats as a **prior**; local **QC** and hand correction stay in scope. **`verify_legui_setup.sh`** = **linker**/MCR sanity, **not** imaging benchmarks.
- **Cohort:** epilepsy **surgical** monitoring (Utah + small WA set); other iEEG research is **plausible** but not a separate validation study. **>250** contacts, extreme artifacts, odd implants = config/code attention. **Not FDA-evaluated** in the paper—research governance applies.
- **Table 1** (paper) vs. iElvis, ALICE, iElectrodes, *etc.*: LeGUI trades some **FreeSurfer** depth for **SPM**, **shorter** wall time, **single** GUI, at the cost of **MathWorks** runtime for compiled use.

---

## Clinical relevance, interpretability, integration

- **Research:** strong for **SEEG/ECoG** localization (MNI, atlas, gray/white) feeding standard analyses.
- **Clinical production** (e.g. surgical CAD) **out of scope** of the publication and a thin **deploy** repo—expert **QA** at gyral boundaries remains essential.
- **Interpretability:** 2D/3D views, atlas overlays, saved structures (`ChannelMap.mat`, *etc.*). Labels only as good as **normalization** + **warping** (paper notes border cases, e.g. STG vs MTG).
- **Integration:** **MAT** / NIfTI ecosystem; custom atlases in `atlases/`; pairs with **BIDS**-style DICOM→NIfTI **upstream**. **No** PACS/HL7 here. CLI improves **ops**, not hospital plumbing.

---

## Limitations and builder insight

- **GUI**-first; headless “full” use is not the design center. **MCR** version must **match** the compiled app. **SPM/MATLAB** on **HPC** may need **Apptainer**/modules. **NFS** home can slow I/O; **local SSD** for heavy batch. **iEEG**-specific, not a general seg platform.

**Bottom line:** Strong **unified** workflow and validation story. **Builder gap** = **MCR R2021b** pin, a **graphical** execution path, and **QC** budget for detection + labeling.

*Extensions:* container with MCR + binary + entrypoint (display still for interactive use); **CI** on `verify_legui_setup.sh`; BIDS/sourcedata **helpers** and channel conventions per site.

---

## References

- Davis *et al.* 2021 *Front. Neurosci.* — [DOI](https://doi.org/10.3389/fnins.2021.769872).
- [Rolston-Lab/LeGUI](https://github.com/Rolston-Lab/LeGUI) — source and releases.
- [LeGUI_implement](https://github.com/phindagijimana/LeGUI_implement) — `LeGUI_br.md` upstream of this bundle.

*Last updated: 2026-04-24.*
