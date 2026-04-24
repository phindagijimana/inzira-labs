# Builder Review — voxTool (intracranial localization on CT)

Evaluation of the **[pennmem/voxTool](https://github.com/pennmem/voxTool)** stack and a **modernized** [vox_implement](https://github.com/phindagijimana/vox_implement) layout (Python 3, conda-forge, `vox` CLI, targeted fixes). Dimensions: usability, reproducibility, performance, generalization, clinical research fit, interpretability and trust, comparison, limitations, integration, builder insight.

**Primary reference (software):** [pennmem/voxTool](https://github.com/pennmem/voxTool) — GUI for interactive SEEG/ECoG-style **contact localization** on post-implant **CT**, with JSON coordinate export (MIT license).

**Typical kit:** `voxTool/` sources, `environment.yml`, `implementation.md`, **`./vox`** (`install`, `check`, `start`, `stop`, `logs`).

---

## Context

**voxTool** is an interactive **desktop** app: load CT, threshold for contacts, define **leads** (geometry, naming), place contacts in **3D/slice** views, optional seeding/interpolation, save coordinates (and optional bipolar midpoints). Upstream targeted **Python 2.7 / PyQt4 / older VTK**—impractical on current Linux. A maintainer fork may ship **Python 3.10+**, **VTK/Mayavi** with **PySide6** (via pyface), pinned `environment.yml`, and lifecycle helpers.

---

## Usability

**Upstream:** README covers workflow, shortcuts, Conda setup (`setup_env.sh`, env `vt`); small, readable codebase.

**Typical implementation:** `./vox install` (e.g. micromamba + `voxtool-env/` from conda-forge pins); `./vox check` imports `PylocControl` offscreen; `./vox start -f` on a **workstation with display**; background mode → `.vox/voxtool.log`.

**Friction:** **Mayavi/VTK** need a real **graphics** stack—headless or broken **OpenGL** → warnings or blank 3D. **Operator** skill: lead layouts, CT quality, when **seeding/interpolation** is unsafe (upstream notes duplicate locations and ordering pitfalls).

---

## Reproducibility

- **Aligned with upstream conceptually:** `launch_pyloc.py`, `config.yml`, lead/contact model, save semantics per upstream README.
- **Changed stack:** interpreter, Qt, VTK major, matplotlib backends—**re-validate** on representative CTs after upgrades.
- **Patch example:** dropping a Traits/Mayavi hook in `view/slice_viewer.py` that **segfaulted** on import with modern stacks; slice views stay **matplotlib**-based.
- **Repeatability** is dominated by **threshold**, **CT** protocol, and **manual** clicking—not automated detection.

---

## Performance, generalization

- **Performance:** depends on **volume size**, GPU/CPU, VTK scene complexity—no standard benchmark in upstream or a thin wrapper. Expect **interactive** use on typical clinical CT on a normal workstation.
- **Generalization:** scanners, kernels, implants, **recon** vary; settings are **study-specific**. **No** pretrained model for contacts; cross-site use = **QC** and operator judgment. Seeding/interpolation = **heuristics**—worse on odd grids or **artifact**-heavy CTs.

---

## Clinical relevance, interpretability, integration

- **Use:** **research** and **surgical-planning adjunct**: named contacts and coordinates (optional bipolars) for downstream registration/analysis—**not** a silent clinical device.
- **Trust:** placements are **explicit** (click + submit); state is visible in UI and **exported JSON**. Still depends on **artifact** review, lead definition consistency, and double-checking **seeding/interpolation**.

---

## Comparison, limitations

- **Niche:** open, **CT-centric**, **interactive** localization vs. commercial tools, atlas pipelines, or fully manual logs. This fork’s edge vs. stock upstream is **runnable modern pins** + small **CLI**, not new segmentation.
- **Limits:** legacy upstream `conda_env.yml` may be **unsupported**—only the modern **environment** path. **Background GUI** without `DISPLAY` is **unreliable**; **foreground** on a desktop session is robust. **Stub** / incomplete upstream files may remain unless extended locally. **Installers** and **enterprise** packaging out of scope unless added.

---

## Integration

- **Natural:** BIDS-oriented stacks, FreeSurfer/brain viz, **MNE**-family tools consuming contact JSON; containers for **pre-CT** steps.
- **Boundary:** exports follow voxTool **JSON** conventions—downstream must map **fields** and **frames** explicitly.

---

## Builder insight

Value is **workflow capture** (structured leads + coordinates), not full **automation**. Highest-leverage work is **keeping the GUI stack viable** (Python, Qt, VTK, Mayavi) and documenting **display/OpenGL** needs. Roadmap: pin versions; CI with **`vox check`**; **smoke** tests on tiny **synthetic** NIfTI where licensing allows; consider **upstreaming** Python 3 deltas.

---

## References

- [pennmem/voxTool](https://github.com/pennmem/voxTool) — upstream README and code.
- [vox_implement](https://github.com/phindagijimana/vox_implement) — `implementation.md`, `vox_br.md` upstream of this bundle.

*Last updated: 2026-04-24.*
