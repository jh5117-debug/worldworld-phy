# GPU Usage Approval Request: Stage A on TDW v5 1000 Combined Prompt v2

## Proposed task

Run LingBot-Fast Stage A camera-conditioned warmup on the TDW v5 1000 dataset using `combined_prompt_v2`.

## Dataset

- Manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_lingbot_manifest_combined_prompt_v2.jsonl`
- Splits: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_splits_combined_prompt_v2/`
- Train / val / test: 800 / 100 / 100
- use_action=false

## Prompt

`combined_prompt_v2`: template event + provided camera trajectory + first-frame object consistency + short negative constraints.

## Proposed training

- Model: LingBot-Fast
- Stage: Stage A high-noise diagnostic / global camera
- Trainable scope: camera adapter / LoRA only
- Max steps: 1000
- Batch size: 1
- Frames: 8
- Resolution: 480x832
- GPUs: GPU4-7 only
- Sampler: balanced by template and camera_variant
- Validation: val forward loss every fixed interval

## Saving

- Adapter-only checkpoints allowed if approved.
- No full model checkpoint.
- No optimizer state unless explicitly approved.

## Safety

- No DPO.
- No VideoGPA 03_train.
- No Stage1.
- No rollout during warmup.
- No reward calibration.

Explicit user approval is required before running this Stage A training.
