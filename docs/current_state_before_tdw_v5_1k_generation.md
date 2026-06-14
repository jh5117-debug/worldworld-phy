# Current State Before TDW v5 1k Generation

Date: 2026-06-14

## Starting Point

The TDW v5 aggressive 2x 200-sample dataset had already been human approved as the current main camera-visible warmup data candidate.

Existing 200 paths:

- Raw HDF5: `local_assets/data/physion/generated_v3/raw_hdf5/warmup_visible_motion_v5_aggressive_2x_demo_plan_200samples/`
- LingBot converted: `local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v5_aggressive_2x_200_human_approved_all/`
- Review videos: `local_assets/reports/human_review/tdw_visible_motion_v5_aggressive_2x_200/videos/`

Known 200 status:

- HDF5: 200/200
- target.mp4: 200/200
- LingBot cam-only conversion: 200/200
- use_action=false with dummy zero action
- delayed camera motion: 0/200
- unique scene hash: 200/200

## Scope Approved

The user approved GPU0 / DISPLAY=:8 for TDW / Unity generation to add 800 new TDW v5 aggressive 2x samples, bringing the dataset to 1000 total samples.

No training, DPO, VideoGPA 03_train, Stage1, rollout, reward scoring, LoRA, checkpoint, or optimizer state was allowed in this task.

## Why Reuse The Existing 200

The 200 samples were already validated, converted, and human approved. The scale-up therefore reused the existing 200 and generated only the additional 800 samples.

