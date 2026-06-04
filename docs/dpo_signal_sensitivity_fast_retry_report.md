# DPO Signal Sensitivity Fast Retry Report

Date: 2026-06-04

## Scope

Short retry of `dpo_signal_sensitivity_fast` on GPU6/7 only.

This was not real DPO training, did not run VideoGPA `03_train.py`, did not save LoRA, and did not save a checkpoint.

## Command Shape

The retry used:

- `CUDA_VISIBLE_DEVICES=6,7`;
- `learning_rates`: `1e-5`, `1e-4`;
- `steps_per_lr`: `3`;
- fixed noise seed `123`;
- fixed timestep `579`;
- LoRA target `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`;
- rank/alpha `2 / 4.0`;
- restore after each LR.

Output directory:

`local_assets/outputs/smoke/lingbot_dpo_signal_sensitivity_fast_retry`

Primary log:

`local_assets/outputs/smoke/lingbot_dpo_signal_sensitivity_fast_retry/tmux_stdout_stderr.log`

## Result

The job was launched in `tmux` on GPU6/7, but it did not write usable per-LR metrics in the safe runtime window. The session was stopped and no 5-pair run was started.

| LR | Status | Steps completed | Notes |
|---:|---|---:|---|
| 1e-5 | not summarized | 0 metrics rows in retry output | no usable LR result |
| 1e-4 | not reached | 0 | no usable LR result |

## Safety

| Check | Status |
|---|---|
| GPU0 used for DPO | no |
| GPU6/7 used | yes, via `CUDA_VISIBLE_DEVICES=6,7` |
| LoRA saved | no |
| checkpoint saved | no |
| NaN/Inf | no usable metrics; no reported NaN/Inf |
| OOM | not reported |
| 5-pair run | no |

Final process check found no remaining DPO adapter process.

## Gate Decision

DPO signal retry: **no-go / incomplete**.

The gate requires at least two LR settings completed with finite losses and a clear Delta_policy movement above the previous near-zero baseline. This retry did not meet that condition.

5-pair tiny overfit: **no-go**.

