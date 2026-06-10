# Experiment Registry: TDW v5 Scale-Up / Warmup / Reward Pairs

Date: 2026-06-10

Name: `exp_tdw_v5_scaleup_warmup_reward_pairs`

Experiment folder:

`local_assets/experiments/exp_tdw_v5_scaleup_warmup_reward_pairs/`

Planned structure:

- `data_scaleup/`
- `manifests/`
- `splits/`
- `warmup_stageA/`
- `rollout/`
- `reward_scoring/`
- `pair_construction/`
- `dpo_diag/`
- `logs/`
- `reports/`

Data source:

`local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v5_aggressive_2x_200_human_approved_all/`

Manifest:

`local_assets/data/physion/generated_v3/manifests/tdw_v5_200_lingbot_manifest.jsonl`

Splits:

`local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/`

Warmup adapter checkpoint:

`local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/checkpoint/stageA_balanced_camera_lora_final/adapter_state.pt`

Status:

- data scale-up: `not_run_needs_tdw_display_or_gpu0_approval`
- longer warmup: `not_run_needs_long_runtime_approval`
- rollout: `code_ready_not_run_needs_runtime_approval`
- rollout dry-run: `passed_4_conditions_one_per_template`
- reward scoring: `blocked_pending_rollout`
- pair construction: `blocked_pending_reward`
- dpo_diag: `planned_pending_pairs`

DPO status: not run.
