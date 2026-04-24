# Builder Review — autoDDPM (Bercea et al., arXiv 2023)

**Builder Review** of the method and upstream code: design, reproducibility, and what transfers. A local [AutoDDPM_implement](https://github.com/phindagijimana/AutoDDPM_implement) scaffold may **ground** hands-on notes; the **review object** is the **paper** and [original repository](https://github.com/ci-ber/autoDDPM), not a product score for the fork.

**Primary reference:** Bercea CI, Neumayr M, Rueckert D, Schnabel JA. *Mask, Stitch, and Re-Sample: Enhancing Robustness and Generalizability in Anomaly Detection through Automatic Diffusion Models.* arXiv:2305.19643. https://arxiv.org/abs/2305.19643 · [PDF](https://arxiv.org/pdf/2305.19643)

**Code:** upstream [ci-ber/autoDDPM](https://github.com/ci-ber/autoDDPM). **Related in this workspace:** [`autoDDPM_br.md` in AutoDDPM_implement](https://github.com/phindagijimana/AutoDDPM_implement/blob/main/autoDDPM_br.md).

---

## Context

Diffusion-based **anomaly detection** often leans on reconstruction alone—**weakly controlled** anomaly maps and **incoherent** pseudo-healthy regions near pathology boundaries. **autoDDPM** uses a **3-stage** idea: **Mask** (coarse likelihood from residuals + perceptual gap, e.g. LPIPS) → **Stitch** (original context + pseudo-healthy patches) → **Re-sample** (joint noised inpainting for global coherence). That moves past “residual only” scoring toward a **compositional** reconstruction story.

---

## Platform fit and reproducibility

**Upstream (paper + [ci-ber/autoDDPM](https://github.com/ci-ber/autoDDPM))**

- Full research layout: `core`, `data`, `projects`, `model_zoo`, `net_utils`—train, evaluate, infer.
- **Research-grade** setup: configs, dataset splits, and wiring matter; not a one-command appliance.
- Practical use needs **threshold** strategy and **dataset** alignment, not just running a checkpoint.

**Reproducibility**

- **Configs** and public code support method reproduction.
- **Paper-level** metrics still depend on **preprocessing**, **splits**, and **threshold** calibration.
- **Thresholds** are **dataset-dependent**; blind transfer without **recalibration** can hurt reliability.

---

## Performance, generalization, comparison

- **Paper signal:** gains vs. diffusion anomaly **baselines** by pairing masking with **stitch + resample**—stronger **localization** and **consistent** reconstructions, not only lower MSE.
- **Generalization:** more robust than pure residual-difference methods across anomaly **appearances**; still **sensitive** to **domain shift** (scanner, protocol, population) at operating points.
- **vs. vanilla anoDDPM-style** stacks: **stitch** and **re-sample** are the differentiator for coherent pseudo-healthy synthesis and cleaner anomaly focus.

---

## Clinical relevance, interpretability, integration

- **Research:** strong for **localization** support and **anomaly prioritization**; **not** a stand-alone diagnosis—needs expert read and local validation.
- **Interpretability:** continuous map, **thresholded** masks, pseudo-healthy view—stability still depends on **threshold governance** and **QA**.
- **Integration:** config-driven **research** runs; **production** needs wrappers, **hardening**, and local **threshold/QC** policy.

---

## Limitations and failure modes

- **Threshold** choice is **site- and dataset-specific**—central for cross-center transfer.
- **False positives** can rise with **artifacts** or **distribution shift**.
- Full stack has **non-trivial** dependencies and **data layout** requirements.

---

## Builder insight

**As a method,** autoDDPM is a clear step beyond reconstruction-only diffusion AD via explicit **Mask → Stitch → Re-sample**, improving **coherence** and **localization** behavior.

**As a research artifact,** upstream code is solid but expect deliberate **data / config / threshold** alignment to approach paper-like numbers.

*Last updated: 2026-04-24.*
