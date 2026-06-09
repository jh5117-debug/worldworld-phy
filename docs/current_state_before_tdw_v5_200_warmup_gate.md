# Current State Before TDW v5 200 Warmup Gate

Date: 2026-06-09

## Data Status

- TDW v5 aggressive 2x 200 has been manually approved by the user as the current main camera-conditioned warmup candidate.
- Raw HDF5 path: `local_assets/data/physion/generated_v3/raw_hdf5/warmup_visible_motion_v5_aggressive_2x_demo_plan_200samples/`
- LingBot converted path: `local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v5_aggressive_2x_200_human_approved_all/`
- Human review videos: `local_assets/reports/human_review/tdw_visible_motion_v5_aggressive_2x_200/videos/`

## Why v5 Replaces Earlier Sets

- `warmup_mild`: pipeline-valid but too static.
- `warmup_visible_motion_v2`: pipeline-valid but human review found weak motion and insufficient scene diversity.
- v5 aggressive 2x: user reviewed and accepted the motion level for next-stage warmup gate.

## This Round Is Not Training

The current gate only registers the dataset, audits files, creates splits, and runs dataloader / forward-smoke checks. No optimizer, backward pass, checkpoint, LoRA save, DPO, rollout, reward calibration, or new TDW generation is allowed.

## GPU Note

The user clarified that H20 GPU4-7 may be used and existing processes may be killed. The detected GPU4-7 process group was root-owned, and current SSH user lacks passwordless sudo, so direct kill was not possible. GPU7 later became free and was used only for a no-training placeholder forward smoke.
