# Experiment Registry: TDW v5 200 Stage A Balanced Warmup

Date: 2026-06-09

## Experiment

Name: `exp_tdw_v5_200_stageA_balanced_warmup`

Remote folder:

`/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work/local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/`

This folder is under `local_assets` and must not be committed.

## Dataset

Dataset: TDW v5 aggressive 2x 200 human-approved camera-visible set.

Train split:

`local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/train.jsonl`

Val split:

`local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/val.jsonl`

## Sampler

Sampler: `balanced`

Balance keys: `template,camera_variant`

Shuffle seed: `123`

Dry-run status: passed. First 60 has all four templates, five camera variants, and no duplicate samples.

## Pilot

Mode: `staged_warmup_pilot`

Stage: A, diagnostic high-noise/global-camera.

Max steps: 60.

Trainable scope: `camera_control_lora_tiny`.

Checkpoint policy: exactly one tiny adapter-only LoRA checkpoint is allowed. Full model checkpoint and optimizer state are forbidden.

## dpo_diag

Path:

`local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/dpo_diag/README.md`

Status: `not_applicable_pre_dpo`.

No winner/loser pairs, DPO loss, policy/reference comparison, reward calibration, or rollout.

## Current Status

Status: passed.

The balanced Stage A pilot completed `60 / 60` steps on GPU7. The train sampler covered all four templates evenly:

- first 20: `drop:5`, `collision:5`, `roll:5`, `containment:5`;
- full 60: `drop:15`, `collision:15`, `roll:15`, `containment:15`.

Losses were finite throughout:

- train loss first / last / min / max: `0.065782 / 0.053271 / 0.033201 / 0.067220`;
- val losses at steps 20 / 40 / 60: `0.037449 / 0.046542 / 0.057670`.

Checkpoint:

`local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/checkpoint/stageA_balanced_camera_lora_final/adapter_state.pt`

The checkpoint is adapter-only, contains four LoRA tensors, and is `166,809` bytes. No full model checkpoint or optimizer state was saved.
