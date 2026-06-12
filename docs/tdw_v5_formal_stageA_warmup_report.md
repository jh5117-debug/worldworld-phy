# TDW v5 Formal Stage A Warmup Report

Date: 2026-06-12

## Dataset

- Dataset: TDW v5 aggressive 2x human-approved 200-sample set.
- Train / val / test: 160 / 20 / 20.
- Active train manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/train.jsonl`
- Active val manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/val.jsonl`
- No TDW data was generated in this phase.

## Stage A Configuration

- Model: LingBot-Fast / WanI2VFast.
- Timestep mode: diagnostic high-noise band.
- Scope: `camera_control_lora_tiny`.
- Trainable params: 40,960 LoRA parameters.
- Base model: frozen.
- Batch size: 1.
- Frames / resolution fallback used for this formal run: 4 frames at 256x448.
- No DPO.
- No VideoGPA 03_train.
- No Stage1.
- No full model checkpoint.
- No optimizer state.

## Run Result

The first formal Stage A run requested 300 steps and reached step 206 before the wall-clock timeout. This was a timeout, not an instability failure.

- Stage A initial run:
  - steps completed: 206 / 300
  - train loss first / last / min / max: 0.016756 / 0.012007 / 0.008611 / 0.026613
  - val loss: 0.011178, 0.014068, 0.011391, 0.011301
  - NaN / Inf: none
  - OOM: none
  - checkpoints: adapter-only at step 100 and step 200

The run was then resumed from the step-200 adapter checkpoint for another 100 steps.

- Stage A resume:
  - status: passed
  - steps completed: 100
  - train loss first / last / min / max: 0.016869 / 0.011407 / 0.008492 / 0.018340
  - val loss: 0.017023, 0.009682
  - NaN / Inf: none
  - OOM: none
  - sampler coverage: 25 each for drop / collision / roll / containment
  - first 20 coverage: 5 each for drop / collision / roll / containment

## Checkpoint

- Final Stage A adapter:
  `local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/warmup_stageA_resume/checkpoint/stageA_high_noise_camera_lora_final/adapter_state.pt`
- Size: 166,809 bytes.
- Contents: 4 LoRA tensors only.
- Full model checkpoint: no.
- Optimizer state: no.

## Gate

Stage A formal warmup is considered passed for pipeline purposes. It produced a usable adapter-only checkpoint and did not show loss instability, NaN, Inf, or OOM.

