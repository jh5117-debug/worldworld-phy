# Experiment Registry: TDW v5 200 Stage A Warmup Pilot

Date: 2026-06-09

## Experiment

Name: `exp_tdw_v5_200_stageA_warmup_pilot`

Remote experiment folder:

`/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work/local_assets/experiments/exp_tdw_v5_200_stageA_warmup_pilot/`

This folder is under `local_assets` and must not be committed.

## Dataset

Dataset: TDW v5 aggressive 2x 200, human-approved camera-visible set.

Manifest:

`local_assets/data/physion/generated_v3/manifests/tdw_v5_200_lingbot_manifest.jsonl`

Splits:

- train: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/train.jsonl`
- val: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/val.jsonl`
- test: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/test.jsonl`

Counts from the prior gate: train 160, val 20, test 20.

## Pilot

Mode: `staged_warmup_pilot`

Stage: A, diagnostic high-noise/global-camera.

Trainable scope: `camera_control_lora_tiny`, runtime LoRA only.

GPU: GPU7 through `CUDA_VISIBLE_DEVICES=7`.

Initial 100-step launch was stopped after 3 completed steps because observed step time was about 141-149 seconds and would likely exceed the 7200 second timeout without writing a final summary. The completed gate run was relaunched as a 20-step pilot, matching the minimum pass criterion while staying inside the approved max-100-step scope.

## dpo_diag

Path:

`local_assets/experiments/exp_tdw_v5_200_stageA_warmup_pilot/dpo_diag/README.md`

Status: `not_applicable_pre_dpo`.

No winner/loser pairs, DPO loss, policy/reference preference comparison, reward calibration, or rollout were run.

## Gate Status

Status: `passed_stageA_warmup_pilot`.

Summary:

- steps completed: 20;
- train loss finite: yes;
- val loss finite: yes;
- trainable scope: `camera_control_lora_tiny`;
- trainable params: 40,960;
- LoRA tensors changed: 4;
- sampled base tensors changed: 0;
- checkpoint-like files saved: none.

Reports:

- `docs/tdw_v5_200_stageA_warmup_pilot_report.md`
- `docs/final_report_tdw_v5_200_stageA_warmup_pilot.md`
- `docs/gpu_usage_approval_request_tdw_v5_200_stageB_or_rollout.md`
