# Experiment Registry: TDW v5 Aggressive 2x 1k Generation

Date: 2026-06-14

## Experiment

- Name: `exp_tdw_v5_aggressive_2x_1k_generation`
- Folder: `local_assets/experiments/exp_tdw_v5_aggressive_2x_1k_generation/`
- Profile: `warmup_visible_motion_v5_aggressive_2x_demo`
- Approved GPU/display: GPU0-bound `DISPLAY=:8`
- DPO diag status: `not_applicable_data_generation`

## Data

- Existing 200 converted root: `local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v5_aggressive_2x_200_human_approved_all/`
- New 800 raw HDF5 root: `local_assets/data/physion/generated_v3/raw_hdf5/warmup_visible_motion_v5_aggressive_2x_1k_scaleup_800samples/`
- New 800 converted root: `local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v5_aggressive_2x_scaleup_800/`
- Combined 1000 manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_lingbot_manifest.jsonl`
- Split root: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_splits/`
- Review pack: `local_assets/reports/human_review/tdw_visible_motion_v5_aggressive_2x_1000/`

## Status

- New HDF5 generated: 800/800
- New validation OK: 800/800
- New conversion target.mp4: 800/800
- Combined manifest: 1000/1000
- Audit valid: 1000/1000
- Video probe: 1000/1000
- Train/val/test split: 800/100/100
- Review subset: 100 videos

## Next Action

Use the TDW v5 aggressive 2x 1000 dataset for the next LingBot-Fast camera-conditioned warmup stage on GPU4-7. DPO remains a later gate.

