# Current State After Meeting

Updated: 2026-06-24 12:47:51 CST

## Git

- Repo: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work`
- Branch: `research/quant-small-lora-dpo-probe-20260624`
- Start commit: `63d1b93`
- Remote:
```text
origin	git@github-worldworld-phy-deploy:jh5117-debug/worldworld-phy.git (fetch)
origin	git@github-worldworld-phy-deploy:jh5117-debug/worldworld-phy.git (push)
```
- Worktree status before this update:
```text
?? cleanup/
?? local_assets/
?? reports/
```

## Data State

- generated_v5 raw HDF5 count observed now: `3999`
- converted/stage1-ready video count observed now: `6598`
- Existing full-data audit summary: `local_assets/meeting_eval_20260624_011137/full_data_audit/manifests/stageA_v5_fullprep_20260624_0152_summary.json`

```json
{
  "created_at": "2026-06-24 01:55:59",
  "status": "partial_generated_v5_snapshot",
  "source_root": "/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets/data/physion/generated_v5",
  "converted_root": "/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets/data/physion/generated_v5/converted_stage1_v1",
  "eligible_count": 3299,
  "split_counts": {
    "train": 2804,
    "val": 329,
    "test_holdout": 166
  },
  "special_counts": {
    "camera_ood": 800,
    "template_ood": 200,
    "reobserve": 0
  },
  "template_distribution": {
    "drop": 1200,
    "collision": 1200,
    "roll": 699,
    "containment": 200
  },
  "camera_distribution": {
    "orbit_left_72": 1200,
    "orbit_right_64": 600,
    "strafe_left_180": 600,
    "orbit_right_60": 699,
    "orbit_left_44": 200
  },
  "manifest_info": {
    "all": [
      "/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/meeting_eval_20260624_011137/full_data_audit/manifests/stageA_v5_fullprep_20260624_0152_all.jsonl",
      "b0b7f609116b0f78e6996d026548e5a1148d881e8265f2df8060382ffe1eb256",
      3299
    ],
    "train": [
      "/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/meeting_eval_20260624_011137/full_data_audit/manifests/stageA_v5_fullprep_20260624_0152_train.jsonl",
      "53751f407a43ec9096e238f115c9dbd7edf5b002d30a80d5a275e2f4b8f35660",
      2804
    ],
    "val": [
      "/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/meeting_eval_20260624_011137/full_data_audit/manifests/stageA_v5_fullprep_20260624_0152_val.jsonl",
      "b33b19ccc42b415a1e078fb46a3c6a5825757200e874c0a5c0dc2d9095701b67",
      329
    ],
    "test_holdout": [
      "/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/meeting_eval_20260624_011137/full_data_audit/manifests/stageA_v5_fullprep_20260624_0152_test_holdout.jsonl",
      "53347db4161b4ec314a9cf550f496976fc0059266bcabcecbe9851af48960bf6",
      166
    ],
    "camera_ood": [
      "/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/meeting_eval_20260624_011137/full_data_audit/manifests/stageA_v5_fullprep_20260624_0152_camera_ood.jsonl",
      "d09252581e4fc9e12b7827af4ec84aaccca4f4444b2c8471675905c53afa7d9d",
      800
    ],
    "template_ood": [
      "/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/meeting_eval_20260624_011137/full_data_audit/manifests/stageA_v5_fullprep_20260624_0152_template_ood.jsonl",
      "c570cc366b1604804a0dfa7fc2aecd4e02f1080c9fcb6b6104daf219eb56b796",
      200
    ],
    "reobserve": [
      "/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/meeting_eval_20260624_011137/full_data_audit/manifests/stageA_v5_fullprep_20260624_0152_reobserve.jsonl",
      "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      0
    ]
  },
  "steps_per_epoch_global_batch7": 401,
  "target_steps_2epochs_global_batch7": 802,
  "hard_max_3epochs_global_batch7": 1203,
  "notes": "Only completed + converted stage1-ready samples are included. Raw-only samples are excluded. Current distribution is partial/imbalanced, so full-data long StageA is not launched in this task."
}
```

The current converted generated_v5 snapshot is still partial and imbalanced relative to the intended 5000-sample target. It is usable for small probe/sweep work only with explicit partial-data labeling.

## Checkpoints / Models

- Original LingBot-Fast source: `/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam`
- Last-week camera-only tiny LoRA final: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work/local_assets/experiments/exp_stageA_1000_combined_prompt_v2_warmup/checkpoint/stageA_1000_promptv2_high_noise_camera_lora_final/adapter_state.pt`
- Last-week camera-only tiny LoRA step200: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work/local_assets/experiments/exp_stageA_1000_combined_prompt_v2_warmup/checkpoint/stageA_1000_promptv2_high_noise_camera_lora_step_000200/adapter_state.pt`
- Current broad-LoRA step800: `local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505/formal_fast_stageA_high_only_balanced_snapshot_20260622_1830_20260622_1925/checkpoints/fast_stageA_high_only_balanced_snapshot_20260622_1830/high_only_phase/branches/step_000800/fast_stageA_high_noise_adapter`
- Current broad-LoRA final883: `local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505/formal_fast_stageA_high_only_balanced_snapshot_20260622_1830_20260622_1925/checkpoints/fast_stageA_high_only_balanced_snapshot_20260622_1830/high_only_phase/branches/final/fast_stageA_high_noise_adapter`

Known comparison:

- Camera-only tiny LoRA: 4 tensors, about 40,960 trainable params, visually more stable.
- Broad-LoRA: 560 Linear layers, 1120 adapter tensors, about 102,891,520 trainable params, fixed-val loss improved but generation quality FAILED_OR_MIXED.

## Reward / Metrics Status

- Epipolar and Camera-Conditioned SGC are implemented and runnable.
- Current calibration is PRELIMINARY/BLOCKED for DPO: clean-over-corrupt R_geo ordering was 0.50, below the 0.85 gate.
- These geometry metrics may be used as diagnostics, not as sole DPO pair-selection criteria.

## DPO Plumbing Status

- Existing DPO modules: `cam_physgeo/dpo/anchored_dataset.py`, `dpo_loss.py`, `pair_builder.py`, `preference_schema.py`, `self_rollout_dataset.py`.
- Existing training entrypoints include `cam_physgeo/training/train_stage2_anchored_dpo.py` and `train_stage3_self_dpo.py`.
- DPO BF16 path has not yet been validated; it requires a separate preflight before any DPO probe.

## GPU State

```text
index, name, memory.total [MiB], memory.used [MiB], utilization.gpu [%]
0, NVIDIA H20, 97871 MiB, 28 MiB, 0 %
1, NVIDIA H20, 97871 MiB, 1 MiB, 0 %
2, NVIDIA H20, 97871 MiB, 1 MiB, 0 %
3, NVIDIA H20, 97871 MiB, 1 MiB, 0 %
4, NVIDIA H20, 97871 MiB, 1 MiB, 0 %
5, NVIDIA H20, 97871 MiB, 1 MiB, 0 %
6, NVIDIA H20, 97871 MiB, 1 MiB, 0 %
7, NVIDIA H20, 97871 MiB, 1 MiB, 0 %
```

```text
# gpu         pid   type     sm    mem    enc    dec    jpg    ofa    command 
# Idx           #    C/G      %      %      %      %      %      %    name 
    0     883875     G      -      -      -      -      -      -    Xorg           
    1          -     -      -      -      -      -      -      -    -              
    2          -     -      -      -      -      -      -      -    -              
    3          -     -      -      -      -      -      -      -    -              
    4          -     -      -      -      -      -      -      -    -              
    5          -     -      -      -      -      -      -      -    -              
    6          -     -      -      -      -      -      -      -    -              
    7          -     -      -      -      -      -      -      -    -
```

No GPU cleanup was performed before writing this document. GPU0-7 are allowed for this round, but long full-data StageA remains disallowed.

## This Round Experiment List

1. Quantitative Benchmark v1: fixed 80-condition benchmark and auditable video scoring.
2. Small-LoRA Scope Sweep: four small/rank-limited LoRA scopes, no FFN, no broad all-block LoRA.
3. Reward Calibration v2: simulator-grounded trajectory, mask, identity, event and camera metrics.
4. Anchored DPO Probe: GT-anchored pairs, quality-floor hard negatives, BF16 DPO preflight, small probe only.

## Current Decision

Do not use broad-LoRA as the main generator for DPO data. Treat it as a possible negative candidate only after quality floor filtering. Prefer Original Fast and last-week camera-only tiny LoRA as candidate generators until the small-LoRA sweep proves a better option.
