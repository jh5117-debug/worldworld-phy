# Implementation Status

Completed:

- Physion-only source schema.
- HDF5 key audit and reader.
- Physion official and moving-camera scanners.
- Cam-only LingBot converter.
- Prompt generation.
- Reward/corruption framework.
- Anchored DPO pair builder.
- Stage1/2/3 dry-run entries.
- Physion benchmark docs.

Smoke passed:

- compileall
- HDF5 audit
- manifest build/validate/split
- converter
- corruption
- reward calibration
- DPO pair builder
- Stage1/2/3/camera audit dry-runs

Remaining TODO:

- Full official Physion dataset download/audit.
- Strong R_bg/R_cam with optical flow and depth rigid residual.
- DINO/V-JEPA feature scoring for FG-ID/RCS.
- Real LingBot Stage2 energy adapter.
