# Current Unified Eval / DPO Status (2026-06-27 04:43:25)

Active DPO data path:
- `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`
- 50 prefix-aware V2V-5 anchored pairs
- Readiness check: `reports/dpo_prefix5_pair_visual_audit/prefix5_training_readiness_summary.md`

Active code path:
- `cam_physgeo/dpo/prefix5_dpo_dataset.py` loads prefix5 pairs and validates schema/assets.
- `cam_physgeo/dpo/lingbot_fast_energy.py` computes real LingBot-Fast flow-matching energies on future latent slots.
- `cam_physgeo/dpo/anchored_dpo_trainer.py` runs minimal DPO BF16 preflight.

Current DPO decision: do not scale. Real BF16 preflight still must pass before any tiny probe.


---

# Current Unified Eval / DPO Status

Updated: 2026-06-27 01:28:06

This report is generated from the current H20 artifacts. It does not invent missing videos or missing metrics.

## Git / Artifact State

- Branch: `research/quant-small-lora-dpo-probe-20260624`
- Overnight root: `local_assets/overnight_quant_lora_dpo_20260624_overnight_test`
- Supervisor next action: `DPO blocked until real trainer/preflight is implemented`
- Supervisor blockers: `{'dpo': 'DPO trainer readiness hook exists, but launch command intentionally not defined until real preflight CLI is audited', 'old_tiny_camera': 'legacy checkpoint lacks adapter_metadata.json required by strict Fast adapter loader'}`
- Selected candidate: `D_step050`
- Candidate decision: `NEW_SMALL_LORA_SELECTED`

## Completion State

- small-LoRA A/B/C/D training: completed in supervisor state.
- screen16 rollout: completed, `208` MP4 files.
- screen16 video audit: completed in supervisor state.
- quant screen: completed in supervisor state.
- full80 benchmark: partial for model coverage; existing full80 videos = `160`.
- full80 candidates present: `GT, original_fast, D_step050`.
- pair build: `50` anchored pairs.
- reward calibration: completed as diagnostic, not DPO-ready.
- DPO diagnostic backend: `PASS`.
- LingBot-Fast DPO energy backend: `BLOCKED_FAST_ENERGY_BACKEND`.

## Important Blockers

1. Full80 all-checkpoint rollout is not complete. Existing full80 currently covers Original Fast and `D_step050` only.
2. LPIPS / FVD / VBench packages are not installed in the current environment, so those metrics are blocked rather than fabricated.
3. LingBot-Fast anchored DPO still needs a callable winner/loser flow-matching energy backend with frozen reference.

## Checkpoint Inventory

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
