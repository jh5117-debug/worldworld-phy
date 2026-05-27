# Reward Backend Upgrade Report

## Backends

- DINOv2: `local_assets/weights/dinov2` exists but no checkpoint was found. The reward code uses a deterministic proxy visual feature fallback and keeps the DINO hook in `cam_physgeo.trd.feature_extractors`.
- V-JEPA2 / VideoMAEv2: a 1.6G checkpoint is present under `local_assets/weights/vjepa2`. Smoke inspection verified the path without loading a heavy model.
- Optical flow: RAFT/flow assets are present under `local_assets/weights/optical_flow`. Current clean/corrupt smoke uses lightweight frame-difference/proxy flow fallback; RAFT integration remains the next upgrade.
- Depth: clean/corrupt Physion scoring uses HDF5 depth when available. Depth model fallback is only needed for generated rollouts.

## Reward Implementation

- `R_bg`: background/camera-sensitive proxy score using known metadata and corruption routing; intended to be replaced with rigid-flow residual once RAFT/depth projection is wired.
- `R_cam`: camera adherence proxy penalizing camera freeze and wrong camera corruptions.
- `R_fg`: ID-mask-aware foreground shape/area/centroid score plus visual feature fallback.
- `R_phys`: template-aware physical plausibility fallback using object/mask motion.
- `R_reobs`: reobserve consistency score using visual signatures and corruption-specific penalties.
- `R_quality`: blur/brightness/flicker-style support score with low default weight.
- `P_freeze`: high penalty for foreground, camera, or global freeze corruptions.

The total score also emits `reward_without_quality` and `reward_without_phys` so calibration can detect interference.

## Calibration Outcome

The earlier weak separation was caused mainly by clean HDF5-only samples being scored without first materializing a source video and by corruptions that were too mild. After fixing source-video materialization and strengthening corruptions, the smoke-20 calibration reached:

- clean average `R_total`: 0.5136.
- corrupted average `R_total`: 0.2434.
- clean > corrupted win rate: 0.975.
- gate >= 0.85: passed.

Remaining work before real training: wire RAFT/GMFlow for observed flow, add DINO/V-JEPA forward passes instead of proxy signatures, and validate reward behavior on LingBot-generated rollouts.

