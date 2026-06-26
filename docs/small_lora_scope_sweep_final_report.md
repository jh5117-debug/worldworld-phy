# Small-LoRA Scope Sweep Final Report

Updated: 2026-06-27 01:28:06

## Status

Screen16 sweep and selection are complete. Full80 all-checkpoint evaluation is incomplete.

## Screen16 Artifact Coverage

- Rollout videos: `208`
- Checkpoints inventoried: `12`
- Selected candidate: `D_step050`
- Selection reason: screen16 proxy/diagnostic selection; final full80 and visual audit still required

## Checkpoints

| model | checkpoint |
|---|---|
| A_step050 | `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_A_camera_r4_train200_20260624_141215/checkpoints/small_lora_A_camera_r4_train200_20260624_141215/high_only_phase/branches/step_000050/fast_stageA_high_noise_adapter` |
| A_step100 | `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_A_camera_r4_train200_20260624_141215/checkpoints/small_lora_A_camera_r4_train200_20260624_141215/high_only_phase/branches/step_000100/fast_stageA_high_noise_adapter` |
| A_step200 | `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_A_camera_r4_train200_20260624_141215/checkpoints/small_lora_A_camera_r4_train200_20260624_141215/high_only_phase/branches/step_000200/fast_stageA_high_noise_adapter` |
| B_step050 | `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_B_camera_r8_train200_20260624_141215/checkpoints/small_lora_B_camera_r8_train200_20260624_141215/high_only_phase/branches/step_000050/fast_stageA_high_noise_adapter` |
| B_step100 | `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_B_camera_r8_train200_20260624_141215/checkpoints/small_lora_B_camera_r8_train200_20260624_141215/high_only_phase/branches/step_000100/fast_stageA_high_noise_adapter` |
| B_step200 | `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_B_camera_r8_train200_20260624_141215/checkpoints/small_lora_B_camera_r8_train200_20260624_141215/high_only_phase/branches/step_000200/fast_stageA_high_noise_adapter` |
| C_step050 | `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_C_camera_self_r4_train200_20260624_141215/checkpoints/small_lora_C_camera_self_r4_train200_20260624_141215/high_only_phase/branches/step_000050/fast_stageA_high_noise_adapter` |
| C_step100 | `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_C_camera_self_r4_train200_20260624_141215/checkpoints/small_lora_C_camera_self_r4_train200_20260624_141215/high_only_phase/branches/step_000100/fast_stageA_high_noise_adapter` |
| C_step200 | `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_C_camera_self_r4_train200_20260624_141215/checkpoints/small_lora_C_camera_self_r4_train200_20260624_141215/high_only_phase/branches/step_000200/fast_stageA_high_noise_adapter` |
| D_step050 | `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_D_camera_cross_r4_train200_20260624_141215/checkpoints/small_lora_D_camera_cross_r4_train200_20260624_141215/high_only_phase/branches/step_000050/fast_stageA_high_noise_adapter` |
| D_step100 | `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_D_camera_cross_r4_train200_20260624_141215/checkpoints/small_lora_D_camera_cross_r4_train200_20260624_141215/high_only_phase/branches/step_000100/fast_stageA_high_noise_adapter` |
| D_step200 | `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_D_camera_cross_r4_train200_20260624_141215/checkpoints/small_lora_D_camera_cross_r4_train200_20260624_141215/high_only_phase/branches/step_000200/fast_stageA_high_noise_adapter` |

## Full80 Status

- Existing full80 videos: `160`
- Models present in full80 summary: `GT, original_fast, D_step050`
- Remaining: run full80 for all other checkpoints after Fast inference initialization is stable.

## Decision

`D_step050` remains the provisional candidate generator, but it is not a proven overall winner. Broad-LoRA remains a failed/mixed route for generation quality and should not be the main DPO candidate generator.
