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

This PRD adds the v2 spec and wrapper/validator skeleton. Stage 0 dry-run planning is supported. The `warmup_mild` camera set has now been made explicit in the v2 wrapper/config:

- allowed: `orbit_left_12`, `orbit_right_12`, `strafe_left_025`, `strafe_right_025`, `dolly_in_010`, `dolly_out_010`;
- banned: lookaway, offscreen, reobserve, relative-yaw-180, occluder, extreme camera motions;
- dry-run plan check: 10 planned trials, `bad_count=0`.

Actual TDW generation has now passed for exactly one user-approved GPU0-bound
`DISPLAY=:8` sample:

| Item | Value |
|---|---|
| generated count | 1 |
| HDF5 | `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_1samples/00000_drop_orbit_left_12_seed10000/0000.hdf5` |
| template | `drop` |
| camera variant | `orbit_left_12` |
| frame count | 83 |
| RGB/depth/id/camera/object state | present |
| target visible ratio | 1.0 |
| max invisible frames | 0 |
| camera path length | 0.5927 |
| suitable for warmup | yes |

LingBot cam-only camera arrays and `target.mp4` were converted for this sample,
with `use_action=false` and dummy zero `action.npy`. The `target.mp4` writer/probe
now passes and the converted sample is ready for LingBot warmup inspection.

No 10/50 samples were generated. Multi-sample use of GPU0-bound `DISPLAY=:8`
requires separate user approval.

The display-routing audit found Xvfb displays `:9` to `:13`, but these are Mesa llvmpipe software displays, not GPU6/7 TDW Xorg displays. They do not prove TDW/Unity generation is safe in CPU/headless mode.

Representative existing videos and new generation deliverables are indexed under:

- `local_assets/reports/tdw_video_deliverables/video_index.md`
- `local_assets/reports/tdw_video_deliverables/video_gallery.html`

## 11. Next Plan

- Finish probe-confirmed `target.mp4` writing for the accepted 1-sample.
- Run short fixed-noise LR/scope sweep for DPO signal sensitivity once SSH/GPU access is stable.
- If signal improves, run 5-pair tiny overfit only after the go/no-go gate is updated.
- Ask for explicit approval before GPU0-bound 10-sample TDW smoke, or configure a GPU6/7 TDW display.
- Continue TDW generation v2 as staged 1 -> 10 -> 50 -> 200 -> 1k+, never directly full scale.
- Use `warmup_mild` for later LingBot-Fast camera-conditioned warmup.
- After enough data exists, use reward to choose top/bottom winner-loser pairs for DPO.
- Full TDW generation and real DPO training remain disallowed until gates pass.
## 2026-06-04 TDW Conversion + DPO Signal Finalize Update

- TDW v2 `warmup_mild` 1-sample HDF5 validation passed.
- Accepted sample: `00000_drop_orbit_left_12_seed10000`, template `drop`, camera variant `orbit_left_12`.
- LingBot cam-only conversion now passed for the accepted sample.
- `target.mp4` probe passed: 81 frames, 16 fps, 832x480.
- `poses.npy` and `intrinsics.npy` are `(81, 4, 4)`.
- `action.npy` is dummy zero, norm `0.0`; `metadata.json` keeps `use_action=false`.
- Video deliverables were updated under `local_assets/reports/tdw_video_deliverables/`.
- 10-sample TDW smoke was not run. It requires a new user approval because the available TDW display is still GPU0-bound `DISPLAY=:8`.
- DPO `dpo_signal_sensitivity_fast` was launched on GPU6/7 but did not produce a complete LR sweep in the safe runtime window. It was interrupted and recorded as a runtime blocker.
- 5-pair tiny overfit remains no-go.
- Real DPO training remains no.
