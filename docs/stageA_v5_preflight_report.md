# StageA v5 Preflight Report

Date: 2026-06-20

## Result

Status: blocked before formal GPU preflight on generated_v5.

Reason: generated_v5 currently has raw HDF5 files, but validated-only snapshot count is 0 because validation reports show `Validation ok count: 0` and row status `blocked`.

## Checks Completed

- Local `compileall`: passed.
- Local `pytest -q`: passed, 6/6.
- Remote `compileall`: passed with `python3`.
- Remote pytest: not available in the installed Python environments (`pytest` module missing).
- Remote direct broad-LoRA smoke without pytest: passed.
- Stage1 dataset preparation from existing 1000 combined_prompt_v2 converted manifests: passed.
- Launcher dry-run with `CUDA_VISIBLE_DEVICES=7`: passed and excludes GPU0.

## Remote Direct Broad-LoRA Smoke

The direct smoke created a Wan-like fake model and applied required groups:

- camera_conditioning: 4
- self_attention: 4
- cross_attention: 4
- ffn: 2

It verified:

- LoRA wrappers replace target Linear modules.
- Base Linear weights are frozen.
- LoRA A/B weights are trainable.
- Camera-conditioning group is present.

## Dataset Preparation Check

Prepared Stage1-compatible dataset:

`local_assets/experiments/exp_stageA_v5_broad_lora/stage1_dataset_1000_promptv2`

Counts:

- train: 800 / 800
- val: 100 / 100
- test: 100 / 100
- missing rows: 0

This dataset is the existing 1000 combined_prompt_v2 fallback, not generated_v5 raw HDF5.

## generated_v5 Snapshot Check

Validated-only snapshot:

`local_assets/experiments/exp_stageA_v5_broad_lora/manifests/stageA_v5_snapshot_20260620_validated_only_all.jsonl`

Counts:

- eligible_count: 0
- train_count: 0
- val_count: 0
- test_holdout_count: 0

This blocks formal generated_v5 StageA training.

## TDW Safety

At the latest check:

- `tdw_v5_4000_gpu0_scaleup` alive.
- `tdw_v5_4000_monitor` alive.
- HDF5 count: 1987.
- GPU0 in use by TDW/Xorg only.
- GPUs 1-7 idle.

No TDW tmux sessions were attached, killed, restarted, or modified.
