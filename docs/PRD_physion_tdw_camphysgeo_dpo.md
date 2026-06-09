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

## 2026-06-04 TDW v2 10-Sample Warmup Smoke Update

- User explicitly approved GPU0-bound `DISPLAY=:8` for exactly 10 `warmup_mild` samples.
- 10-sample TDW / Physion-style generation v2 smoke passed.
- Generated HDF5 count: 10.
- Validation ok count: 10.
- Rejected count: 0.
- Suitable for warmup: 10.
- target_visible_ratio avg/min/max: 1.0 / 1.0 / 1.0.
- max invisible frames max: 0.
- camera_path_length avg/min/max: 0.3575 / 0.1005 / 0.5927.
- LingBot cam-only conversion passed for all 10 new samples.
- `target.mp4` probe passed for all 10 converted samples.
- `metadata.json` keeps `use_action=false`; `action.npy` is dummy zero.
- No 50/200/1k generation was run.

Important limitation: the actual upstream generation produced only `drop` template samples, even though the dry-run plan requested `drop`, `collision`, `roll`, and `containment`. Before larger validation, we should either fix template coverage or explicitly approve a drop-only 50-sample validation.

## 2026-06-03 Template-Diverse TDW Gate Update

The drop-only limitation has been addressed in code, but the new actual TDW run has not been executed yet.

- `plan_trials.py` now supports exact `--template_counts`.
- `run_tdw_trial.py` now supports manifest-driven per-trial execution via `--plan`.
- The template-diverse 10-sample dry-run plan passes:
  - `drop:3`
  - `collision:3`
  - `roll:2`
  - `containment:2`
- Stress/reobserve bad count remains `0`.
- Validation and LingBot conversion now accept `--manifest` so template-diverse runs can be audited separately from older drop-only samples.

Actual template-diverse generation is still pending because it would use the GPU0-bound `DISPLAY=:8`, and this specific run has not been approved yet. The request is documented in:

- `docs/gpu_usage_approval_request_tdw_template_diverse_10.md`

Until that approval is granted and the 10-sample template-diverse batch passes, 50/200/1k TDW generation remains disallowed. Real DPO training also remains disallowed.

## 2026-06-04 Template-Diverse Actual + DPO Signal Update

The user approved exactly one GPU0-bound `DISPLAY=:8` template-diverse 10-sample attempt.

Result:

- planned distribution: `drop:3`, `collision:3`, `roll:2`, `containment:2`;
- `drop`: 3 commands returned 0;
- `collision/roll/containment`: 7 commands failed with upstream argument parsing errors;
- validation accepted count: 0;
- LingBot conversion: skipped;
- video deliverables: no new template-diverse videos added.

Exact TDW blocker:

The plan-mode runner passed drop-specific args to non-drop templates. This has been fixed in code by applying those args only when `template == "drop"`. Because the approval was for exactly one 10-sample attempt, no second actual run was started.

DPO signal:

- `dpo_signal_sensitivity_fast` was launched in `tmux` on GPU6/7;
- it produced three finite `1e-5` steps;
- it did not complete at least two LR settings;
- signal gate remains no-go;
- 5-pair tiny overfit remains no-go.

Next decisions:

1. approve one more GPU0 template-diverse 10-sample smoke after the args fix, or configure a GPU6/7 TDW display;
2. fix DPO signal runner speed/scope before any 5-pair;
3. do not run 50/200/1k TDW or real DPO training yet.

## 2026-06-04 Non-Drop Template Retry Update

The non-drop command dry-run confirmed that `collision`, `roll`, and `containment` no longer receive drop-only arguments (`--drop`, `--ymin`, `--ymax`, `--dscale`). This fixes the previous parser-level blocker.

The approved non-drop actual smoke then returned success at the command level for:

| Template | Count |
|---|---:|
| collision | 1 |
| roll | 1 |
| containment | 1 |

However, HDF5 validation found `0/3` generated files. The exact blocker is that the wrapper did not pass the upstream execution flag `--run 1`; the upstream TDW runner exits cleanly without writing data unless that flag is set.

Current fix:

- `run_tdw_trial.py` now adds `--run 1` to every upstream generation command;
- drop-only args remain restricted to `template == "drop"`;
- no template-diverse 10 retry was run after this fix, because the approval for actual TDW generation had already been consumed.

Current TDW data gate:

| Gate | Status |
|---|---|
| drop-only 10-sample | passed |
| template-diverse plan | passed |
| non-drop command dry-run | passed |
| non-drop actual validation | failed: no HDF5, `--run 1` blocker fixed |
| template-diverse 10 retry | skipped |
| 50/200/1k generation | no-go |

DPO signal retry on GPU6/7 did not produce a usable two-LR summary, so 5-pair tiny overfit remains no-go. Real training remains disallowed.

## 2026-06-04 Non-Drop `--run 1` Retry Result

The user approved GPU0-bound `DISPLAY=:8` for a fixed non-drop 3-sample retry and conditional template-diverse 10.

Command dry-run passed:

- `collision`, `roll`, and `containment` all include `--run 1`;
- non-drop templates do not receive `--drop`, `--ymin`, `--ymax`, or `--dscale`;
- output directories include the template name;
- camera variants are from `warmup_mild`.

Actual result:

| Template | Camera variant | Command return | HDF5 validation |
|---|---|---:|---|
| collision | `orbit_left_12` | 0 | failed; no HDF5 |
| roll | `orbit_right_12` | 0 | failed; no HDF5 |
| containment | `strafe_left_025` | 0 | failed; no HDF5 |

The upstream TDW logs show TDW started and closed successfully, but no HDF5 files were written. This means the previous `--run 1` blocker is fixed, but non-drop template generation is still not producing data under the current random single-sample wrapper invocation.

Dependency decision:

- template-diverse 10 `run1`: skipped;
- LingBot conversion: skipped;
- video deliverables: unchanged;
- 50/200/1k generation: no-go.

Next TDW action is to inspect and fix upstream non-drop template arguments/stimulus requirements before another generation attempt. DPO signal remains a separate no-go gate.

## 2026-06-04 Non-Drop Upstream Fix and Template-Diverse Pass

The remaining non-drop blocker was resolved.

Root cause:

- v2 wrapper launched upstream TDW from the upstream Physion workspace;
- `--dir local_assets/...` was relative;
- non-drop HDF5 files were written under the upstream workspace, not under the project `local_assets` tree;
- validator therefore saw return code 0 but no HDF5.

Fix:

- pass absolute per-trial `--dir` paths;
- create per-trial output directories before launch;
- keep non-drop upstream-style required args;
- keep `--run 1`;
- add `imageio` fallback video probing for environments without `cv2`/system `ffprobe`.

Result:

| Gate | Status |
|---|---|
| non-drop 3-sample | passed, 3/3 HDF5 validated |
| template-diverse 10 | passed, 10/10 HDF5 validated |
| template distribution | drop 3 / collision 3 / roll 2 / containment 2 |
| suitable for warmup | 10/10 |
| LingBot cam-only conversion | passed, 10/10 |
| target.mp4 probe | passed, 10/10 |
| action | dummy zero |
| use_action | false |
| 50-sample | approval request only, not run |

DPO signal remains a separate no-go gate. Real training remains disallowed.

## TDW Template-Diverse 50-Sample Validation Update

The non-drop output-path blocker has been resolved and the template-diverse staged gate has now reached 50-sample validation.

Root cause previously fixed:

- the v2 wrapper passed a relative `--dir local_assets/...` to the upstream TDW runner;
- the subprocess ran with the upstream Physion workspace as `cwd`;
- non-drop HDF5 files were therefore not discovered under the intended project output tree;
- the wrapper now passes absolute output directories and creates each trial directory before launch.

50-sample validation result:

| Item | Value |
|---|---|
| Approved scope | GPU0-bound `DISPLAY=:8`, 50 samples only |
| Planned distribution | `drop:15`, `collision:15`, `roll:10`, `containment:10` |
| Generated HDF5 | 50 |
| Validation OK | 50 |
| Rejected | 0 |
| Suitable for warmup | 50 |
| target_visible_ratio avg/min/max | 1.0 / 1.0 / 1.0 |
| max invisible frames avg/max | 0.0 / 0 |
| camera_path_length avg/min/max | 0.3682 / 0.1005 / 0.8888 |
| LingBot conversion | 50/50 |
| target.mp4 probe | 50/50 |
| use_action=false | 50/50 |
| dummy action zero norm | 50/50 |

Key local deliverables:

- validation report: `local_assets/data/physion/generated_v2/reports/validation_template_diverse_50.md`
- converted LingBot samples: `local_assets/data/physion/generated_v2/lingbot_cam_inputs_template_diverse_50/`
- video gallery: `local_assets/reports/tdw_video_deliverables/video_gallery.html`

No 200/1k generation was run. The next TDW step is a user-approved 200-sample pilot only if this 50-sample validation is accepted. DPO signal remains a separate no-go gate, and real training remains disallowed.

## Visible-Motion Reassessment Update

Manual review of the 50-sample `warmup_mild` videos showed that the camera motion is too weak for final camera-conditioned warmup data.

Updated interpretation:

| Dataset | Status |
|---|---|
| template-diverse 50 | pipeline validation passed |
| template-diverse 50 | not final warmup main data |
| reason | camera motion too weak / visually close to static I2V |

New profile added:

`warmup_visible_motion`

It uses stronger but non-stress variants:

- `orbit_left_24`, `orbit_right_24`
- `orbit_left_28`, `orbit_right_28`
- `strafe_left_050`, `strafe_right_050`
- `dolly_in_025`, `dolly_out_025`

The validator now adds camera/background motion checks and marks samples as:

- `too_static`
- `too_extreme`
- `suitable_for_visible_motion`

Visible-motion 10-sample plan dry-run passed with `bad_count=0`, but actual generation was not run because no GPU6/7 TDW display is available. The only verified TDW display is GPU0-bound `DISPLAY=:8`, and this turn forbids GPU0-5.

Next required action: configure a GPU6/7 TDW display, then run the 10-sample `warmup_visible_motion` smoke.
## 2026-06-05 Update: warmup_visible_motion GPU0 smoke

The prior template-diverse 50-sample `warmup_mild` run remains a pipeline validation pass, but manual review found the camera motion too weak for final camera-conditioned warmup data. It should not be treated as final warmup main data.

The user explicitly approved GPU0-bound `DISPLAY=:8` for a limited `warmup_visible_motion` smoke:

- one sample first;
- ten samples only if the one-sample gate passed;
- no 50 / 200 / 1k;
- no training, DPO, VideoGPA `03_train`, Stage1, rollout, or reward calibration.

Results:

| Gate | Result |
|---|---|
| 1-sample actual | passed |
| 1-sample suitable_for_visible_motion | true |
| 10-sample HDF5 generation | 10 / 10 |
| 10-sample HDF5/key validation | 10 / 10 |
| Suitable for warmup | 10 / 10 |
| Suitable for visible motion | 5 / 10 |
| Converted to LingBot cam-only | 5 / 5 accepted samples |
| target.mp4 probe | 5 / 5 converted samples |

Accepted visible-motion samples are the drop orbit 24/28 clips and collision strafe 0.50 clips. Rejected samples exposed useful tuning signals: dolly 0.25 remains too static, while containment orbit 24 and one collision orbit 28 exceeded the current camera-path threshold.

Conclusion: `warmup_visible_motion` is directionally correct, but the profile needs one more tuning pass before a 50-sample validation request.

## 2026-06-05 Update: warmup_visible_motion_v2 profile

Based on the 5/10 v1 acceptance result, a template-aware profile was added:

```text
warmup_visible_motion_v2
```

The profile assigns camera variants by template:

- drop: orbit 24/28;
- collision: strafe 0.50 and orbit 24, avoiding orbit 28;
- roll: strafe/orbit, avoiding dolly 0.25;
- containment: orbit 18/20 and strafe, avoiding orbit 24/28.

The v2 local plan dry-run passed with `drop:3, collision:3, roll:2, containment:2` and no stress/reobserve variants. Actual v2 generation was not launched because remote SSH repeatedly timed out while syncing code to the TDW helper worktree. No v2 HDF5 or MP4 was generated in this step.

50-sample readiness remains no until v2 actual smoke passes with at least 8/10 accepted and at least one accepted sample per template.

## 2026-06-06 Update: warmup_visible_motion_v2 actual smoke passed

The template-aware `warmup_visible_motion_v2` 10-sample actual smoke has now run on explicitly approved GPU0-bound `DISPLAY=:8`.

Results:

| Gate | Result |
|---|---|
| HDF5 generation | 10 / 10 |
| HDF5/key validation | 10 / 10 |
| Suitable for warmup | 10 / 10 |
| Suitable for visible motion | 10 / 10 |
| Rejected | 0 / 10 |
| LingBot cam-only conversion | 10 / 10 |

The v2 profile fixes the v1 template-specific failures: roll no longer receives dolly variants, containment no longer receives orbit 24 / 28, and all templates have accepted samples.

This makes `warmup_visible_motion_v2` ready for a user-approved 50-sample validation request. It does not approve 50 / 200 / 1k automatically, and it does not approve DPO or any training.

## 2026-06-06 Update: warmup_visible_motion_v2 50-sample validation passed

The user explicitly approved GPU0-bound `DISPLAY=:8` for exactly one `warmup_visible_motion_v2` 50-sample validation run. No 200 / 1k generation, DPO, VideoGPA `03_train`, Stage1, rollout, reward calibration, LoRA save, or checkpoint save was approved or run.

Results:

| Gate | Result |
|---|---|
| Planned distribution | drop 15, collision 15, roll 10, containment 10 |
| HDF5 generation | 50 / 50 |
| HDF5/key validation | 50 / 50 |
| Suitable for warmup | 50 / 50 |
| Suitable for visible motion | 50 / 50 |
| Rejected | 0 / 50 |
| Too static | 0 / 50 |
| Too extreme | 0 / 50 |
| LingBot cam-only conversion | 50 / 50 |

Motion-quality summary:

- camera path length min/avg/max: `0.5016 / 1.0778 / 1.4814`;
- background motion proxy min/avg/max: `0.0121 / 0.0211 / 0.0332`;
- target visible ratio: `1.0` for every sample;
- max invisible frames: `0` for every sample.

Conclusion: the data-side visible-motion gate is ready for a user-approved 200-sample pilot request. This does not authorize 200 / 1k generation automatically, and it does not unblock DPO training; the DPO signal gate remains separate.

## 2026-06-06 Update: warmup_visible_motion_v3 human-review review set

Human review of the v2 50-sample set found that passing the numeric validator was not sufficient: the clips still looked too similar, camera motion was not visually strong enough, and some motion was not clear from frame 0. v2 is therefore retained as a pipeline validation set, not final camera-conditioned warmup main data.

`warmup_visible_motion_v3_start0_scene_diverse` was added to address this:

- camera motion starts at frame 0 and spans the clip;
- camera values are stronger than v2;
- scene diversity is measured with scene hashes;
- validation includes early-motion and delayed-camera-motion flags.

The approved v3 50-sample review run completed:

| Gate | Result |
|---|---|
| HDF5 generation | 50 / 50 |
| HDF5/key validation | 50 / 50 |
| Unique scene hashes | 50 / 50 |
| Accepted for visible-motion v3 | 28 / 50 |
| Rejected | 22 / 50 |
| Delayed camera motion | 22 / 50 |
| Too static | 22 / 50 |
| LingBot conversion | 28 / 28 accepted samples |

The v3 run fixed scene diversity but did not meet the 200-readiness target because all strafe variants were rejected as too static / delayed. The next data task is to tune strafe strength or remove strafe from the review profile and rerun a smaller smoke. No 200 / 1k generation, training, DPO, VideoGPA `03_train`, Stage1, rollout, or reward calibration is approved.

### Human-review override

After reviewing the rendered v3 videos, the user confirmed that all 50 videos are usable. For this batch, the numeric `too_static` / `delayed_camera_motion` flags are diagnostic warnings rather than hard rejects.

Updated status:

- human review acceptance: `50 / 50`;
- LingBot cam-only conversion: `50 / 50`;
- final conversion root: `local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v3_start0_scene_diverse_50_human_accepted_all/`;
- old generated_v2 waste assets were removed to reduce storage pressure.

The next possible data step is a user-approved v3 200-sample pilot. This is not automatic approval to run 200 / 1k, and it does not affect the separate DPO no-go state.

## 2026-06-07 Update: warmup_visible_motion_v3 200-sample pilot

The user requested the v3 200-sample pilot. It ran on GPU0-bound `DISPLAY=:8`.

Results:

| Gate | Result |
|---|---|
| HDF5 generation | 200 / 200 |
| HDF5/key validation | 200 / 200 |
| Suitable for warmup | 200 / 200 |
| Unique scene hashes | 200 / 200 |
| Duplicate scene hashes | 0 |
| target_visible_ratio | 1.0 for all samples |
| max invisible frames | 0 |
| LingBot cam-only conversion | 200 / 200 |
| `use_action=false` | 200 / 200 |

Numeric diagnostics remain visible:

- numeric `suitable_for_visible_motion_v3`: 116 / 200;
- `delayed_camera_motion`: 84 / 200;
- `too_static`: 84 / 200;
- `too_extreme`: 0 / 200.

The 200 pilot is ready for human review. It does not approve 1k+ generation, training, DPO, VideoGPA `03_train`, Stage1, rollout, reward calibration, LoRA save, or checkpoint save.

## 2026-06-07 Visible-Motion v4 Stronger Start0 Smoke

After human review noted that v3 was usable but still visually slow, a small stronger-motion smoke profile was added: `warmup_visible_motion_v4_stronger_start0_review`.

Result:

- generated HDF5: `16 / 16`;
- validation OK: `16 / 16`;
- suitable for visible motion: `16 / 16`;
- too_static / too_extreme / delayed camera motion: `0 / 0 / 0`;
- camera path min/avg/max: `0.9017 / 1.4567 / 1.9758`;
- first-8-frame path min/avg/max: `0.0902 / 0.1457 / 0.1976`;
- LingBot cam-only conversion: `16 / 16`.

The next decision is human review of the v4 gallery, then explicit approval for a v4 50-sample review set if the motion is visually preferable. This does not approve 50/200/1k, training, DPO, VideoGPA `03_train`, Stage1, rollout, reward calibration, LoRA save, or checkpoint save.
## 2026-06-09 TDW v5 200 Warmup Gate Update

The human-approved TDW v5 aggressive 2x 200 dataset is now the current main candidate for camera-conditioned LingBot-Fast warmup.

- Manifest gate: passed, 200 / 200 samples.
- Data integrity audit: passed, 200 / 200 valid.
- Video probe: passed, 200 / 200.
- Split: train 160, val 20, test 20, with no scene-hash overlap.
- Dataloader smoke: passed with image/video/camera/action tensors and `use_action=false`.
- Forward-loss dry-run: partial only. A placeholder no-model-load no-backward/no-optimizer GPU7 tensor path passed, but a real LingBot-Fast/VAE/T5 model-load forward-loss smoke has not run yet.

No training, DPO, VideoGPA `03_train`, Stage1, rollout, reward calibration, checkpoint, or LoRA save was run. DPO remains a later gate after warmup and reward/pair selection.

Next required user decision: approve a real LingBot-Fast model-load forward-loss smoke on a free GPU7 or GPU6/7 window. Only after that passes should a 100 to 200 step warmup pilot be requested.

## 2026-06-09 Update: True LingBot-Fast Forward-Loss Gate Passed

The placeholder no-model-load warmup smoke has been replaced by a true LingBot-Fast component-load and forward-loss dry-run.

Current gate status:

- Dataset: TDW v5 aggressive 2x 200, human-approved.
- Manifest/audit/split: passed.
- Dataloader smoke: passed.
- Component load: passed with `WanI2VFast`, `WanModelFast`, `Wan2_1_VAE`, `T5TokenizerFast`, and `FlowUniPCMultistepScheduler`.
- Train timesteps: `1000`.
- LingBot Base checkpoint exposes high-noise / low-noise branches.
- LingBot-Fast runtime does not expose explicit expert routing in this smoke, so timestep-band losses are logged as scheduler-quantile diagnostics.
- True forward-loss: passed with finite losses at diagnostic high-noise, diagnostic low-noise, and random timesteps.

Forward-loss summary:

| Band | Timestep | Sigma | Loss |
|---|---:|---:|---:|
| diagnostic high-noise | 799 | 0.7990 | 0.046257 |
| diagnostic low-noise | 200 | 0.2000 | 0.895799 |
| random | 412 | 0.4120 | 0.437084 |

No training, DPO, VideoGPA `03_train`, Stage1, rollout, reward calibration, checkpoint, optimizer state, or LoRA save was run.

Next user decision: approve or reject a staged Stage A high-noise/global-camera warmup pilot on GPU7 or GPU6/7. DPO remains a later gate after warmup and reward-based pair selection.
