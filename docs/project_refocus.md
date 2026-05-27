# Physion-Cam-PhysGeo-DPO Refocus

This project is no longer a CSGO/action-data fine-tuning line, and PhyInOne is not an active data source. The active research target is **Physion-Cam-PhysGeo-DPO: Camera-Conditioned Physical-Geometric Preference Alignment for LingBot-Fast**.

The model receives an initial image or prefix video, an automatically generated Physion prompt, camera poses, and intrinsics. It should generate future video in which the static background follows the rigid geometry implied by the provided camera trajectory, dynamic foreground objects preserve identity and shape, physical events stay plausible, and look-away/reobserve sequences return to the same world. The model should not win by freezing, blurring, or suppressing motion.

## Active Scope

- Data: Physion/TDW moving-camera synthetic data under `local_assets/data/physion`, with optional official Physion assets later copied into the same tree.
- Model: LingBot-Fast is the main policy. LingBot-Base is retained only as a baseline, not as the default teacher, because Base can also fail in this domain.
- Conditions: image or prefix video, prompt, camera poses, and intrinsics.
- Compatibility: `action.npy` is dummy zero only if a legacy LingBot interface requires it; `metadata.json` must contain `use_action=false`.
- Outputs: all manifests, processed samples, corruptions, rollouts, reports, cache, and third-party code live under `local_assets`.

## Data Narrative

The moving-camera data is not an official Physion moving-camera split. It is a Physion/TDW rerendered synthetic dataset with camera trajectories and simulator metadata. Official Physion remains useful for static-camera physical dynamics and metadata audit, but active smoke tests use the project-local moving-camera copy.

If official Physion HDF5 lacks explicit intrinsics or extrinsics, the generation path should export `camera_position`, `camera_aim`, `camera_pose`, `projection_matrix`, depth, ID masks, object states, and event metadata for the subset we use.

## Method

We borrow GeoFlow's geometric consistency idea, but the reward is known-camera and simulator-grounded: Physion/TDW can provide camera pose, projection/intrinsics, depth, ID mask, and object metadata. We also keep VideoREPA-style TRD as an auxiliary physical-temporal representation signal, not as a replacement for camera-following, background rigid consistency, or reobserve consistency.

DPO is VideoGPA-based. The first pairs are anchored `clean Physion GT > corrupted Physion GT`; later stages may add LingBot-Fast best-of-N rollouts only after reward calibration is reliable. Direct self-rollout DPO is not used at the start.

## Innovations

- Shift from action/game modeling to Physion-based camera-conditioned physical world consistency.
- Keep all active assets under project-local `local_assets` for reproducibility.
- Use known-camera, simulator-grounded GeoFlow-style rewards.
- Use ID-mask/video-level corrupted negatives before any rollout-based DPO.
- Preserve DINOv2/V-JEPA2/VideoMAE2 hooks for foreground, reobserve, and temporal features.
- Export preference data through a VideoGPA adapter instead of treating a toy DPO trainer as the main path.
