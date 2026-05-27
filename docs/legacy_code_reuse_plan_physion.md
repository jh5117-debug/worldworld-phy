# Legacy Code Reuse Plan: Physion

Reusable:

- LingBot path discovery and checkpoint audit from `cam_physgeo.training.model_loading`.
- Legacy Stage1 LingBot/TRD loading path under `src/physical_consistency/stages/stage1_physinone_cam` as a cam-control branch loader.
- TRD loss utilities under `src/physical_consistency/losses/trd.py` and trainer patterns under `src/physical_consistency/trainers/trd_v1.py`.

Needs adaptation:

- Dataset assumptions must be Physion cam-only samples, not PhyInOne.
- Any action-dependent path must be disabled or supplied dummy zero action only.
- Stage2 DPO still needs the real LingBot denoising/velocity energy adapter before non-dry-run training.

Deprecated:

- PhyInOne scanners/configs.
- CSGO/game action scripts and datasets.
