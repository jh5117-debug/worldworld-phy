# Physion/TDW Camera-Conditioned LingBot-Fast DPO Alignment PRD

## 1. Project Title

Physion/TDW Camera-Conditioned LingBot-Fast DPO Alignment PRD.

## 2. Background and Problem

Previous CSGO/action and mixed SFT experiments showed small improvements on traditional metrics, but did not solve the actual world-consistency problem. The qualitative failures were background drift, object deformation, foreground/background inconsistency, and reobserve failure. PMF, PSNR, SSIM, and LPIPS are useful surface metrics, but they do not directly tell us whether the background is one rigid 3D scene, whether the foreground identity is preserved, or whether a scene can be revisited consistently.

The project therefore shifts away from CSGO/action as the main line. The current objective is camera-conditioned physical world consistency: given an initial observation, prompt, camera poses, and intrinsics, LingBot-Fast should predict a future video whose background is explainable by rigid camera geometry and whose foreground objects remain physically plausible and identity-consistent.

## 3. Data Definition and Terminology

Physion is not real-world captured video. Physion is a TDW / ThreeDWorld / Unity3D based physical simulation benchmark. The current `physion_movingcam_*` data should be described as Physion/TDW simulated clean GT, or Physion-style TDW moving-camera clean GT.

The current moving-camera data is not an official large-scale moving-camera split. It is regenerated and extended from Physion-style TDW scenes using the local moving-camera generation code. `local_assets` organizes and symlinks/migrates project assets; it does not mean a new large TDW dataset was generated this week.

Current source paths include:

- `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/synthetic_data_assets`
- `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/outputs`
- `local_assets/data/physion/movingcam_raw`
- `local_assets/data/physion/movingcam_outputs`

Avoid wording such as real-world Physion, original real moving camera, or TWD. Use TDW, Physion/TDW simulated clean GT, and Physion-style TDW moving-camera simulation.

## 4. Current Task Input / Output

Inputs:

- initial image / prefix video;
- prompt;
- `poses.npy` camera extrinsics;
- `intrinsics.npy` converted to LingBot `[fx, fy, cx, cy]` format;
- `action.npy` only as dummy fallback.

Output:

- future video.

The core condition is camera geometry, not real action. `use_action=false` is preserved in metadata.

## 5. Weekly Gates and Smoke Results

Completed this week:

- LingBot-Fast T5/runtime gate passed.
- 1-sample actual inference passed.
- 3 LingBot-Fast rollouts generated in the prior smoke.
- Camera condition path audited: poses/intrinsics enter `WanI2VFast.generate` through `action_path`.
- Plucker/control tensor changes with camera variants.
- DiT camera scale/shift path confirmed.
- 8-frame stress camera ablation passed: strong perturbations affect video output.
- Reward v5 repaired with clean GT HDF5 metadata, RAFT real optical flow, and DINOv2-small features.
- VideoGPA pair/metadata dry-run passed.
- LingBot/Wan VAE latent encode passed.
- Condition encode passed, including image, prompt/deferred text, poses, intrinsics, Plucker/control tensor, dummy action norm 0, and `use_action=false`.
- Same-noise / same-timestep DPO batch passed.
- Policy energy passed using flow target `noise - x0`.
- Reference energy passed with the same frozen LingBot-Fast checkpoint, not Base and not reward.
- Scalar DPO loss passed.
- Backward-only passed on tiny plumbing scope.
- Tiny camera-control LoRA backward passed.
- 1-pair optimizer-step dry-run passed with LoRA-only updates.
- 1-pair 5-step mini-loop passed.
- Fixed-noise diagnostic was stable but the signal remained weak.
- Signal-sensitivity gate is weak.
- 5-pair tiny overfit was skipped.
- Real DPO training remains disallowed.

## 6. Key Result Tables

### Table A: Data Smoke

| Item | Value |
|---|---|
| Manifest samples | 50 |
| physion_movingcam samples | 50 |
| has camera/depth/id/object_state | 42 |
| reobserve | 47 |
| LingBot converted samples | 5 |
| action | dummy zero |
| use_action | false |

### Table B: Camera Stress Ablation

| Comparison | Pixel L1 |
|---|---:|
| repeat A vs B | 0.0 |
| correct vs frozen | 0.0 |
| correct vs reversed | 0.02218 |
| correct vs exaggerated yaw | 0.03502 |
| correct vs exaggerated translation | 0.03765 |

### Table C: Reward v5

| Metric | Clean GT | LingBot-Fast |
|---|---:|---:|
| R_total avg | 0.9996 | 0.7489 |
| Confidence-weighted | 0.9828 | 0.4563 |
| Real-backend-only | 1.0000 | 0.7113 |
| Flow + DINO only | 1.0000 | 0.7113 |
| Clean > Fast | 3/3 | - |

### Table D: DPO Plumbing

| Component | Status |
|---|---|
| VAE latent encode | passed |
| condition encode | passed |
| same noise / timestep | passed |
| policy energy | passed |
| reference energy | passed |
| scalar loss | passed |
| backward-only | passed |
| optimizer-step dry-run | passed |
| 1-pair mini-loop | passed |
| fixed-noise diagnostic | stable but weak signal |
| signal-sensitivity | weak |
| 5-pair tiny overfit | skipped |
| real DPO training | no |

## 7. Current Video Observations

Video 1: Physion/TDW moving-camera clean GT. This is TDW simulated video, not real-world video. The current presentation sample has camera motion that is too strong for warmup, and foreground objects can leave the view. It should be treated as stress/test material, not warmup main data.

Video 2: LingBot-Fast 1-sample actual inference. The camera appears nearly static. This is acceptable for the inference gate but shows that ordinary camera-following is still weak.

Videos 3-5: Camera stress ablation correct/reversed/exaggerated yaw. These use a stress sample and strong perturbations, so the camera motion is visible. They show that camera condition can affect generation, but ordinary camera following still needs stronger data and training signal.

## 8. Current Conclusion

The engineering pipeline is now connected up to DPO smoke tests, including LingBot-compatible latent encoding, camera-conditioned batch construction, energy computation, scalar loss, LoRA backward, optimizer-step dry-run, and a 1-pair mini-loop. However, the learning signal is still weak, and real training remains blocked. The next work should strengthen signal sensitivity and build a cleaner TDW generation v2 data source.

## 9. TDW Generation v2 Requirements

Warmup data should not use strong reobserve or extreme camera motions. The warmup split should use mild/smooth camera motion, small-to-medium yaw and translation, and should keep the main foreground object visible through most frames. Use ID masks and camera metadata to reject clips where foreground disappears for too long.

Stress/reobserve samples such as `relative_yaw_180_reobserve`, lookaway, and offscreen should be separate test/stress splits, not warmup main data.

Generation must be staged:

1. 1-sample dry-run / smoke;
2. 10-sample smoke;
3. 50-sample validation;
4. 200-sample pilot;
5. 1k+ only after user confirmation and staged validation.

## 10. TDW / Physion-style Generation v2 Partial Data

This PRD adds the v2 spec and wrapper/validator skeleton. Stage 0 dry-run planning is supported. Actual warmup generation is blocked until the runner can guarantee mild-only camera variants, because the upstream batch script does not expose an explicit mild-only `camera_set`. This is intentional: we should not silently mix stress/reobserve camera motions into the warmup split.

Representative existing videos and new generation deliverables are indexed under:

- `local_assets/reports/tdw_video_deliverables/video_index.md`
- `local_assets/reports/tdw_video_deliverables/video_gallery.html`

## 11. Next Plan

- Run short fixed-noise LR/scope sweep for DPO signal sensitivity.
- If signal improves, run 5-pair tiny overfit only after explicit approval.
- Complete TDW generation v2 mild-only support and run 1 -> 10 -> 50 staged generation.
- Use `warmup_mild` for later LingBot-Fast camera-conditioned warmup.
- After enough data exists, use reward to choose top/bottom winner-loser pairs for DPO.
- Full TDW generation and real DPO training remain disallowed until gates pass.
