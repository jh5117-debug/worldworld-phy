# Final Report: Fast Rollout / Camera Ablation / Reward Autoloop

## 1. Summary

- Status: `success` for the engineering smoke loop, with reward gate failed/provisional.
- Start: `2026-05-30T00:49:16+08:00`
- End: `2026-05-30T01:56:04+08:00`
- Total: `1.1131` hours
- Remote run dir: `local_assets/reports/smoke/fast_rollout_reward_autoloop_20260530_004916`
- No training, DPO, VideoGPA encode, or Stage1 warm-up was run.

## 2. Execution

- Worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_min_adapter_work`
- Branch used remotely: `physion-fast-rollout-reward-autoloop`
- Local assets: shared project `local_assets`; no data or weights were moved or deleted.
- GPU policy: commands were launched with `CUDA_VISIBLE_DEVICES=6,7`.
- Original Physion data and LingBot weights were not modified.

## 3. Previous Inference Confirmation

- Previous 1-sample video exists: `local_assets/reports/smoke/fast_inference_autoloop_20260529_144655/outputs/attempt_0005_actual_f8_s1_480x832_gpu6-7/physion_movingcam_07abddf5748b/generated.mp4`
- Previous contact sheet exists: `local_assets/reports/smoke/fast_inference_autoloop_20260529_144655/outputs/attempt_0005_actual_f8_s1_480x832_gpu6-7/physion_movingcam_07abddf5748b/contact_sheet.jpg`

## 4. Intrinsics Conversion

- Raw Physion intrinsics shape: `(81, 4, 4)` projection matrices.
- LingBot runtime intrinsics shape: `(81, 4)` vectors.
- Formula:
  - `fx = P[0,0] * width / 2`
  - `fy = P[1,1] * height / 2`
  - `cx = (1 - P[0,2]) * width / 2`
  - `cy = (1 - P[1,2]) * height / 2`
- Implemented in `cam_physgeo.utils.camera.convert_projection_to_lingbot_intrinsics`.
- Tests passed locally and remotely: `python tests/test_intrinsics_conversion.py`.
- Convention risk remains: the formula assumes TDW/Unity/OpenGL projection semantics.

## 5. Fast Rollout

3 Fast zero-shot rollouts succeeded:

- `local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke/physion_movingcam_07abddf5748b/generated.mp4`
- `local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke/physion_movingcam_13db379640ce/generated.mp4`
- `local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke/physion_movingcam_1a0d32560b71/generated.mp4`

Contact sheets are in each sample directory. Per-sample elapsed times were about `622.4s`, `675.1s`, and `658.6s`. All three runtime condition dirs used `projection4x4_to_pixel_vector` and wrote `(81,4)` intrinsics.

Visual note from the first contact sheet: output is coherent enough to inspect, but shows blurred/elongated object motion artifacts. This is a smoke result, not a quality claim.

Gate B: passed at the engineering level.

## 6. Camera Ablation

One sample completed correct/frozen/reversed camera variants:

- correct: `local_assets/data/physion/processed/rollouts/camera_ablation_smoke/physion_movingcam_07abddf5748b/correct/physion_movingcam_07abddf5748b/generated.mp4`
- frozen: `local_assets/data/physion/processed/rollouts/camera_ablation_smoke/physion_movingcam_07abddf5748b/frozen/physion_movingcam_07abddf5748b/generated.mp4`
- reversed: `local_assets/data/physion/processed/rollouts/camera_ablation_smoke/physion_movingcam_07abddf5748b/reversed/physion_movingcam_07abddf5748b/generated.mp4`

Comparison sheet:

```text
local_assets/data/physion/processed/rollouts/camera_ablation_smoke/physion_movingcam_07abddf5748b/comparison_contact_sheet.jpg
```

The variants are visually very similar in the short 8-frame, 1-step contact sheet. This proves the pipeline can receive altered poses, but it does not prove LingBot-Fast materially uses the camera condition.

Gate C: partial/not proven.

## 7. Reward On Rollout

Reward scoring completed for 3 clean/Fast pairs:

- Clean GT avg `R_total`: `0.5949391852320083`
- Fast rollout avg `R_total`: `0.8796054208438063`
- Clean > Fast win rate: `0.0`

Per-pair summary:

| sample | clean | fast | clean wins |
| --- | ---: | ---: | --- |
| `physion_movingcam_07abddf5748b` | 0.2130 | 0.7739 | false |
| `physion_movingcam_13db379640ce` | 0.9188 | 0.9436 | false |
| `physion_movingcam_1a0d32560b71` | 0.6531 | 0.9213 | false |

The reward currently prefers the Fast rollouts over clean GT in all three cases. This means reward-on-rollout is not ready for pair selection. The largest misleading term appears to be the proxy physical score: clean-minus-Fast `R_phys` deltas were negative for all three samples.

Gate D: failed/provisional.

## 8. Feature Backend

- DINOv2: no local checkpoint; fallback proxy only.
- V-JEPA2 / VideoMAE2: V-JEPA-like file exists, but the smoke did not load/run the teacher.
- Optical flow: real RAFT/GMFlow/WAFT forward is not wired; frame-diff proxy is active.
- `score_video --require_feature_backend true`: `feature_backend_requirement.met=false`.

This explains why reward-on-rollout is unreliable in this round.

## 9. Attempts

| id | phase | duration | status |
| --- | --- | ---: | --- |
| 1 | compile | 0.173s | ok |
| 2 | intrinsics_test | 0.469s | ok |
| 3 | rollout_f8_s1_480x832 | 1981.473s | ok |
| 4 | camera_ablation_correct_frozen_reversed | 1975.909s | ok |
| 5 | reward_on_rollout | 10.144s | ok |
| 6 | feature_backend_dinov2 | 11.442s | ok, fallback |
| 7 | feature_backend_vjepa2_or_videomae2 | 11.015s | ok, path-only |
| 8 | feature_backend_score_video | 8.274s | ok, requirement not met |

## 10. Gates

- Gate B, 3-10 Fast rollout: passed.
- Gate C, camera ablation: generated successfully, but camera usage is not proven.
- Gate D, reward-on-rollout: failed/provisional because Fast scored higher than clean GT.
- Gate E, VideoGPA encode: not allowed yet.
- Gate F, LingBotFastVideoGPAAdapter batch shape: not run.
- Gate G, DPO energy/logprob: not implemented; DPO remains disallowed.

## 11. Next Minimal Action

Do not move to VideoGPA or DPO yet. The next round should either:

1. fix camera-condition validation with stronger camera-only prompts/longer motion and seed controls, or
2. repair reward backends, especially real DINO/V-JEPA/flow and physical-event scoring, then rerun reward-on-rollout.

Only if camera use is demonstrated and reward ranks clean GT above visibly bad Fast rollouts should VideoGPA encode smoke be considered.
