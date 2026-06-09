# Final Report: TDW v5 200 True LingBot Forward-Loss / MoE Gate

Date: 2026-06-09

## Codebase / PRD Audit

Scanned 527 lightweight code/config/doc files under `cam_physgeo`, `scripts`, `configs`, and `docs`. The previous warmup forward smoke was identified as a placeholder-only tensor path. This round upgraded it to a real LingBot-Fast component load and true forward-loss dry-run.

## GPU Cleanup

GPU4-7 were inspected. No GPU4-7 process required killing. GPU7 was used for the real component load and forward-loss smoke. GPU0-3 were occupied by an unrelated GR00T job and were not touched.

## Dataset

- Dataset: TDW v5 aggressive 2x 200 human-approved cam-only set.
- Manifest: 200 samples.
- Split: train 160, val 20, test 20.
- Template distribution: drop 60, collision 60, roll 40, containment 40.
- Dataloader smoke: passed.

Batch shapes:

- image `[2, 480, 832, 3]`;
- video `[2, 81, 480, 832, 3]`;
- poses `[2, 81, 4, 4]`;
- intrinsics `[2, 81, 4, 4]`;
- action `[2, 81, 4]`;
- action norm `0.0`;
- metadata `use_action=false`.

## MoE / Timestep Audit

- LingBot Base checkpoint has high-noise / low-noise branch layout.
- LingBot-Fast runtime loaded as `WanI2VFast` / `WanModelFast`.
- Fast checkpoint does not expose explicit high/low branch directories.
- Runtime expert route: `unavailable_in_fast_or_not_exposed`.
- Scheduler: `FlowUniPCMultistepScheduler`.
- Train timesteps: `1000`.

Because Fast routing is not exposed, high/low results are labeled scheduler-quantile diagnostics, not exact expert-boundary measurements.

## Component Load

Passed.

- Tokenizer: `T5TokenizerFast`, vocab size 256300.
- Policy: `WanI2VFast`.
- Model: `WanModelFast`.
- VAE: `Wan2_1_VAE`.
- Scheduler: `FlowUniPCMultistepScheduler`.
- GPU7 load memory: about 46.9 GiB.
- No backward, optimizer, checkpoint, LoRA save, or model update.

## True Forward-Loss

Passed.

Sample: `tdw_v3_00094_collision_orbit_right_64_seed22094_0000`.

Shapes:

- latent `[16, 2, 60, 104]`;
- camera control `[1, 384, 2, 60, 104]`;
- prediction `[16, 2, 60, 104]`;
- target `[16, 2, 60, 104]`.

Losses:

| Band | Timestep | Sigma | Loss | Finite |
|---|---:|---:|---:|---|
| diagnostic high-noise | 799 | 0.7990 | 0.046257 | yes |
| diagnostic low-noise | 200 | 0.2000 | 0.895799 | yes |
| random | 412 | 0.4120 | 0.437084 | yes |

No backward, no optimizer, and no checkpoint were used.

## Experiment Folder

`local_assets/experiments/exp_tdw_v5_200_true_forward_loss_gate/`

`dpo_diag` status: `not_applicable_pre_dpo`.

## Recommendation

Request approval for a staged warmup pilot, not full training:

1. Stage A: high-noise/global-camera pilot, max 100 steps, batch size 1, camera adapter/LoRA only.
2. Stage B: mixed/low-noise detail refinement only if Stage A is stable.

DPO remains later. Reward top/bottom pair selection should happen only after warmup produces usable camera-conditioned behavior.

No training, DPO, VideoGPA `03_train`, Stage1, rollout, reward calibration, checkpoint, LoRA save, or TDW generation was run in this task.
