# Small-LoRA Scope Sweep Launch Report

Updated: 2026-06-24 14:45 CST

## Status

Status: RUNNING_IN_TMUX.

The four 200-step high-noise small-LoRA sweep jobs are running on H20-2 using all eight GPUs in four 2-GPU groups.

Run timestamp: `20260624_141215`

| Experiment | GPUs | Scope | Rank/alpha | Trainable params | Session |
| --- | --- | --- | --- | ---: | --- |
| A | 0,1 | camera-only all camera-conditioning layers | r4/a4 | 6,553,600 | `small_lora_A_camera_r4_train200_20260624_141215` |
| B | 2,3 | camera-only all camera-conditioning layers | r8/a8 | 13,107,200 | `small_lora_B_camera_r8_train200_20260624_141215` |
| C | 4,5 | camera + last-4 self-attention | r4/a4 | 1,310,720 | `small_lora_C_camera_self_r4_train200_20260624_141215` |
| D | 6,7 | camera + last-4 cross-attention | r4/a4 | 1,310,720 | `small_lora_D_camera_cross_r4_train200_20260624_141215` |

## Dataset

Prepared Stage1 dataset:

`local_assets/experiments/small_lora_scope_sweep_20260624/stage1_dataset_fullprep_20260624_0152_fixed/`

Counts: train 2804, val 329, test 166.

## Early Progress

At 2026-06-24 14:43 CST:

- A reached optimizer step 3/200.
- B reached optimizer step 2/200.
- C reached optimizer step 6/200.
- D reached optimizer step 7/200.
- No OOM, SIGFPE, NaN/Inf, or traceback observed.
- Scheduler warning from preflight no longer appears after the scheduler-step fix.

## Runtime Risk

A/B are much slower than C/D because they attach LoRA to all 160 camera-conditioning Linear layers. C/D are limited to blocks 36-39 and are expected to finish earlier.

## Next Gate

Wait for step50 checkpoints and fixed validation. Do not run benchmark rollout, reward calibration, pair construction, or DPO probe until at least one candidate checkpoint is available and documented.

## Step-50 Checkpoint Update - 2026-06-24 16:39 CST

Small-LoRA C and D have reached the first checkpoint:

- C = camera conditioning + limited self-attention, selected last 4 blocks, rank 4.
  - step: 50 / 200
  - fixed-val loss: 0.125559
  - unweighted fixed-val: 0.186228
  - gate: PASS at the minimum step gate
  - checkpoint: `local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_C_camera_self_r4_train200_20260624_141215/checkpoints/small_lora_C_camera_self_r4_train200_20260624_141215/high_only_phase/branches/step_000050/fast_stageA_high_noise_adapter/adapter_state.pt`

- D = camera conditioning + limited cross-attention, selected last 4 blocks, rank 4.
  - step: 50 / 200
  - fixed-val loss: 0.125559
  - unweighted fixed-val: 0.186227
  - gate: PASS at the minimum step gate
  - checkpoint: `local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_D_camera_cross_r4_train200_20260624_141215/checkpoints/small_lora_D_camera_cross_r4_train200_20260624_141215/high_only_phase/branches/step_000050/fast_stageA_high_noise_adapter/adapter_state.pt`

A/B are still running and are slower because camera-only all-block adapters match substantially more camera-conditioning linears. No OOM, SIGFPE, NaN, or traceback has been observed. No rollout has been launched yet because all GPUs remain occupied by the four sweep trainings.
