# TDW v5 200 Stage A Warmup Pilot Report

Date: 2026-06-09

## Result

Status: `passed_stageA_warmup_pilot`

This was a small Stage A high-noise/global-camera LingBot-Fast warmup pilot on the TDW v5 200 human-approved dataset. It was not DPO, not VideoGPA `03_train`, not Stage1, and not a rollout/reward run.

The first launch used `max_steps=100`, but the observed step time was about 141-149 seconds. It was stopped after 3 completed steps to avoid a likely timeout without a final summary. The completed gate run used `max_steps=20`, which meets the minimum Stage A pass criterion and stays inside the approved max-100-step scope.

## Setup

| Item | Value |
|---|---|
| Worktree | `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work` |
| Experiment folder | `local_assets/experiments/exp_tdw_v5_200_stageA_warmup_pilot/` |
| Dataset | TDW v5 aggressive 2x 200 human-approved camera-visible set |
| Train split | `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/train.jsonl` |
| Val split | `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/val.jsonl` |
| GPU | GPU7 via `CUDA_VISIBLE_DEVICES=7` |
| Model | `WanI2VFast` / `WanModelFast` |
| VAE | `Wan2_1_VAE` |
| Scheduler | `FlowUniPCMultistepScheduler` |
| Timestep mode | diagnostic `high_noise` |
| Timestep / sigma | 799 / 0.799 |
| Batch size | 1 |
| Frames / resolution | 8 frames, 480x832 |
| Learning rate | `1e-5` |

## Trainable Scope

Only runtime LoRA parameters were trainable.

| Metric | Value |
|---|---:|
| Trainable scope | `camera_control_lora_tiny` |
| LoRA targets | `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer` |
| LoRA rank / alpha | 2 / 4 |
| Trainable parameter count | 40,960 |
| LoRA parameter count | 40,960 |
| LoRA tensors changed | 4 |
| Base sampled tensors changed | 0 |
| Frozen params unchanged | true |

## Metrics

| Metric | Value |
|---|---:|
| Steps completed | 20 |
| Train metrics rows | 20 |
| Val metrics rows | 2 |
| Train loss first | 0.052260 |
| Train loss last | 0.056665 |
| Train loss min | 0.030702 |
| Train loss max | 0.062314 |
| Val loss step 10 | 0.033537 |
| Val loss step 20 | 0.034270 |
| Grad norm first | 0.004051 |
| Grad norm last | 0.007884 |
| Grad norm max | 0.007884 |
| Loss finite | true |
| Nonzero LoRA gradients | true |
| OOM | false |
| NaN / Inf | false |
| Runtime | 3456.8 seconds |

Tensor path:

- latent shape: `[16, 2, 60, 104]`
- camera/control shape: `[1, 384, 2, 60, 104]`
- dummy action norm: `0.0`
- `use_action=false`

## Safety

- No DPO training.
- No VideoGPA `03_train`.
- No Stage1.
- No rollout.
- No reward calibration.
- No checkpoint saved.
- No LoRA saved.
- No optimizer state saved.
- No checkpoint-like files were found in the experiment folder.
- GPU0 was not used.

## Caveat

The first 20 train rows in the current split order were all `collision + orbit_right_64`. This pilot proves that the real high-noise warmup path is stable for a minimal LoRA scope, but it is not a balanced template-coverage training conclusion. Any next warmup pilot should use a shuffled or balanced sampler before judging template-general behavior.

## Gate Decision

Stage A stability gate: passed.

Next action: do not run Stage B automatically. Ask the user whether to approve a Stage B mixed/low-noise pilot, rerun Stage A with checkpoint saving for rollout, or rerun Stage A with a shuffled/balanced sampler.
