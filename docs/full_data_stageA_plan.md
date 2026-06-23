# Full-Data StageA Plan

## Snapshot Status

- Snapshot status: `partial_generated_v5_snapshot`
- Source root: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets/data/physion/generated_v5`
- Converted root: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets/data/physion/generated_v5/converted_stage1_v1`
- Eligible stage1-ready count: 3299
- Train / val / test_holdout: 2804 / 329 / 166
- Camera-OOD count: 800
- Template-OOD count: 200
- Reobserve count: 0 in current converted snapshot
- Summary: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/meeting_eval_20260624_011137/full_data_audit/manifests/stageA_v5_fullprep_20260624_0152_summary.json`

## Distribution

Template distribution: `{'drop': 1200, 'collision': 1200, 'roll': 699, 'containment': 200}`

Camera distribution: `{'orbit_left_72': 1200, 'orbit_right_64': 600, 'strafe_left_180': 600, 'orbit_right_60': 699, 'orbit_left_44': 200}`

This is not a complete 5000-sample balanced snapshot yet. It is stage1-ready for converted samples only, but containment and roll are underrepresented relative to the final plan.

## Training Step Plan

Assuming global batch 7:

- steps_per_epoch = ceil(2804 / 7) = 401
- target = 2 effective epochs = 802 optimizer steps
- hard max = 3 effective epochs = 1203 optimizer steps

The current task does not launch this full-data long training. Use the config and script below only after user approval.

## Prepared Files

- Config: `configs/cam_physgeo/fast_stageA_full_high_only.yaml`
- Launch script: `scripts/launch_fast_stageA_full_high_only.sh`
- Manifests: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/meeting_eval_20260624_011137/full_data_audit/manifests`

## Safety

- Do not use GPU0.
- StageA high-only only.
- No StageB.
- No DPO.
- No reward/pair mining.
- Adapter-only checkpoints; no full model checkpoint.
