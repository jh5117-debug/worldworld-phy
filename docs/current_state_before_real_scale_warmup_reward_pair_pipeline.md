# Current State Before Real-Scale Warmup / Rollout / Reward-Pair Pipeline

Date: 2026-06-11

## Current Dataset

- Active dataset: TDW v5 aggressive 2x human-approved camera-visible set.
- Count: 200 LingBot cam-only samples.
- Manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_lingbot_manifest.jsonl`
- Splits:
  - train: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/train.jsonl`
  - val: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/val.jsonl`
  - test: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/test.jsonl`
- Prior audit: 200/200 valid; target.mp4 probe 200/200; use_action=false; dummy action.

## Current Adapter

- Latest balanced Stage A smoke checkpoint:
  `local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/checkpoint/stageA_balanced_camera_lora_final/adapter_state.pt`
- Checkpoint size: 166,809 bytes.
- Contents: 4 LoRA tensors only; no full model; no optimizer state.

## Prior Rollout Observation

- 4-condition Base vs Stage A adapter rollout completed.
- User manually confirmed the adapter can generate videos.
- User also observed no obvious improvement over Base.
- Conclusion: warmup/adapter/rollout gate passed, but the 60-step adapter is not a final model.

## Why 60-Step Pilot Is Not Enough

- It validates the training and adapter-save pipeline only.
- It is too short to judge camera-conditioned behavior.
- It does not support reward-pair or DPO readiness by itself.

## TDW 1k Need

- A larger TDW v5 set is desirable, but not required to start the next warmup gate.
- Current H20 TDW display audit shows only GPU0-bound `DISPLAY=:8`; no GPU4-7 TDW Xorg display was found.
- Since this run is not approved to use GPU0 for TDW 1k generation, data scale-up is blocked pending approval or GPU4-7 display setup.

## Current Plan

1. Use existing TDW v5 200 for a longer Stage A high-noise/global-camera warmup.
2. If Stage A passes, run a small Stage B mixed/low-noise refinement.
3. Run 12-condition Base / Stage A / Stage B rollout comparison.
4. Score rollouts with reward v5.
5. Build winner/loser pairs only if reward confidence and margins pass.
6. Complete dpo_diag.
7. Write DPO pilot approval request only; do not run DPO.

## Safety

- No DPO training.
- No VideoGPA 03_train.
- No Stage1.
- No full model finetune.
- No full model checkpoint.
- No local_assets committed.
