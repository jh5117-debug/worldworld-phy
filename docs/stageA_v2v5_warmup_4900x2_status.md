# StageA V2V-5 Warmup 4900x2 Status

Date: 2026-07-05
Branch: research/quant-small-lora-dpo-probe-20260624

## User Request

Re-run V2V-5 prefix-aware StageA warmup with:

- 4900 training clips
- 100 test clips
- 2 epochs
- H20 physical GPU4-7 only

## Current Finding

Status: BLOCKED_INSUFFICIENT_STAGE1_READY_DATA

The previous V2V-5 warmup was intentionally a pilot, not a full 5000-clip run:

- Dataset: `local_assets/stageA_v2v5_pilot_20260627/dataset`
- Train/val/test rows: 800 / 100 / 100
- Config: `configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml`
- LoRA: LingBot-Fast camera-conditioning LoRA, rank 4, alpha 4, dropout 0.05
- Optimizer steps: hard-capped at 100 high-noise steps
- Prefix-aware policy: prefix_len=5, prediction_start_frame=5, future-only loss frames 5-80

The requested 4900/100 split cannot be built from current disk state:

- Raw generated_v5 HDF5 files present: 3999
- Converted Stage1-ready generated_v5 clips present: 3299 unique
- Worktree local converted clips: 368, all duplicates of the main converted root
- Required Stage1-ready clips: 5000
- Shortfall: 1701 Stage1-ready clips

Data gate output:

- `reports/stageA_v2v5_warmup_4900x2/data_gate.md`
- `reports/stageA_v2v5_warmup_4900x2/stage1_ready_inventory.json`
- `reports/stageA_v2v5_warmup_4900x2/stage1_ready_inventory.csv`

## Runtime Note

The LingBot conda Python currently hangs during normal site initialization after the earlier metric backend work. Minimal execution passes with:

```bash
PYTHONNOUSERSITE=1 /home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python3.10 -c "print(123)"
```

The new 4900x2 launcher therefore exports `PYTHONNOUSERSITE=1` to avoid user-site pollution.

## Prepared Files

- Split/data gate builder: `cam_physgeo/data/build_v2v5_warmup_4900_split.py`
- Config: `configs/cam_physgeo/fast_stageA_v2v5_camera_r4_4900x2.yaml`
- Launcher: `scripts/launch_fast_stageA_v2v5_camera_r4_4900x2.sh`

The launcher refuses to run unless `metadata_train.csv` has exactly 4900 rows and `metadata_test.csv` has exactly 100 rows. It also defaults to `CUDA_VISIBLE_DEVICES=4,5,6,7` and blocks GPU0-3.

## Decision

Do not start the requested warmup yet. Starting now would either use only 3299 unique clips or repeat samples while claiming 4900 unique training clips, which would violate the request.

Next safe actions:

1. Recover/convert additional generated_v5 raw samples if possible, but current raw HDF5 count is only 3999.
2. If the true 5000 simulated clips exist elsewhere, point the builder at that converted Stage1 root.
3. If the missing 1701 clips do not exist, run/finish simulation generation first.
4. Once at least 5000 unique Stage1-ready clips exist, run the builder and then launch GPU4-7 warmup.
