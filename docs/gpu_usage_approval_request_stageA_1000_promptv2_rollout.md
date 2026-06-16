# GPU Usage Approval Request: Stage A 1000 prompt_v2 Rollout

## Proposed next task

Run a small rollout comparison using the completed Stage A 1000 combined_prompt_v2 adapter.

## Inputs

- Dataset: TDW v5 1000 combined_prompt_v2
- Final adapter checkpoint: `local_assets/experiments/exp_stageA_1000_combined_prompt_v2_warmup/checkpoint/stageA_1000_promptv2_high_noise_camera_lora_final/adapter_state.pt`
- Checkpoint size: 166809 bytes

## Proposed rollout

- Conditions: 12 total, balanced across drop / collision / roll / containment
- Outputs: GT / Base LingBot-Fast / StageA_1000_prompt_v2 adapter comparison videos
- Preferred visualization: side-by-side combined videos with labels
- GPU: GPU7 or GPU6/7
- No DPO
- No reward calibration
- Reward scoring only after rollout is approved and generated

## Purpose

Check whether the prompt_v2 Stage A adapter improves camera-conditioned behavior and foreground stability over Base before doing reward/pair construction.

User approval is required before running rollout.
