# DPO Signal Sensitivity Fast Report v2

Date: 2026-06-03

## Scope

This report covers the requested `dpo_signal_sensitivity_fast` gate for the current template-diverse TDW / DPO signal turn.

No real DPO training, VideoGPA `03_train.py`, Stage1, checkpoint save, or LoRA save was run.

## Intended Command

```bash
CUDA_VISIBLE_DEVICES=6,7 TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 \
/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python \
  -m cam_physgeo.dpo.lingbot_fast_videogpa_adapter \
  --mode dpo_signal_sensitivity_fast \
  --config configs/cam_physgeo/videogpa_adapter.yaml \
  --batch local_assets/outputs/smoke/lingbot_dpo_batch_dryrun \
  --out local_assets/outputs/smoke/lingbot_dpo_signal_sensitivity_fast \
  --limit_pairs 1 \
  --beta 0.1 \
  --device cuda \
  --dtype bf16 \
  --trainable_scope camera_control_lora_tiny \
  --lora_rank 2 \
  --lora_alpha 4 \
  --target_modules blocks.39.cam_shift_layer,blocks.39.cam_scale_layer \
  --learning_rates 1e-5 5e-5 1e-4 \
  --steps_per_lr 5 \
  --fixed_noise_seed 123 \
  --fixed_timestep 579 \
  --resample_noise_each_step false \
  --resample_timestep_each_step false \
  --max_grad_norm 1.0 \
  --no_save_lora true \
  --no_checkpoint true \
  --reuse_model_load true \
  --restore_after_each_lr true
```

## Current Outcome

The signal gate remains no-go.

Reasons:

- Previous fast-sweep attempts did not produce a usable multi-LR summary in the safe runtime window.
- The latest remote SSH check was unstable; the direct main worktree import also did not expose `cam_physgeo.dpo.lingbot_fast_videogpa_adapter` from that path.
- Earlier measured default rank-2 signal remained extremely weak:
  - default rank-2 energy movement: about `5.960e-08`;
  - preference logit movement: about `2.831e-08`;
  - LR `1e-4` only completed a one-step fallback previously.

## LR Results

| LR | Status | Loss Delta | Delta_policy Movement | Preference Logit Movement | Notes |
|---:|---|---:|---:|---:|---|
| 1e-5 | not completed this turn | n/a | n/a | n/a | previous runner runtime-blocked |
| 5e-5 | not completed this turn | n/a | n/a | n/a | previous runner runtime-blocked |
| 1e-4 | partial historical fallback | n/a | very weak | about `2.831e-08` | insufficient for 5-pair gate |

## Safety

| Check | Status |
|---|---|
| Real training | no |
| VideoGPA `03_train.py` | no |
| LoRA save | no |
| Checkpoint save | no |
| 5-pair overfit | not run |
| GPU0 use for DPO | no |

## Gate Decision

`dpo_signal_sensitivity_fast`: **no-go / incomplete**.

`5-pair tiny overfit`: **no-go**.

Next action is to fix the signal runner robustness and/or test a stronger camera-control LoRA scope before attempting 5-pair.

