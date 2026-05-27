# Project File Architecture Plan

`/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys` is the only engineering root. All active assets are under `local_assets/`, which is excluded from Git.

## Directory Tree

- `local_assets/data/physion/movingcam_raw`: copied Physion/TDW moving-camera source metadata and raw asset files.
- `local_assets/data/physion/movingcam_outputs`: copied HDF5/MP4/render outputs used for smoke and reward.
- `local_assets/data/physion/official`: optional official Physion repo/data if later downloaded.
- `local_assets/data/physion/processed/lingbot_cam_inputs`: camera-only LingBot samples.
- `local_assets/data/physion/processed/corruptions`: render/video-level corrupted negatives.
- `local_assets/data/physion/processed/dpo_pairs`: clean/corrupt DPO pair videos and JSON.
- `local_assets/data/physion/processed/rollouts`: future LingBot-Fast rollouts.
- `local_assets/data/physion/manifests` and `local_assets/data/physion/splits`: JSONL manifests and split files.
- `local_assets/weights`: LingBot-Fast/Base, DINOv2, V-JEPA2, VideoMAE2, optical-flow, and depth checkpoints.
- `local_assets/third_party/VideoGPA`: external VideoGPA checkout, untracked.
- `local_assets/third_party/lingbot_world`: lightweight LingBot code checkout, untracked.
- `local_assets/reports`: audits, reward calibration, DPO pair reports, contact sheets, and smoke reports.
- `local_assets/outputs`: smoke inference/eval outputs.
- `local_assets/cache` and `local_assets/logs`: local caches and run logs.

## Git Policy

Tracked: `cam_physgeo/`, `configs/cam_physgeo/`, `scripts/`, `docs/`, `tests/`, `README_cam_physgeo_dpo.md`, `.gitignore`.

Untracked: `local_assets/`, data, weights, third-party checkouts, generated videos/images, manifests, reports, logs, caches, checkpoints, HDF5/MP4/NPY/NPZ archives.

## Migration Table

- `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/synthetic_data_assets` -> `local_assets/data/physion/movingcam_raw`
- `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/outputs` -> `local_assets/data/physion/movingcam_outputs`
- `/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam/lingbot_world_fast` -> `local_assets/weights/lingbot_fast`
- `/home/nvme04/workspace/world_model_phys/PHYS/weight/Lingbot-base-cam` -> `local_assets/weights/lingbot_base`
- `/home/nvme04/workspace/world_model_phys/PHYS/weight/vjepa2_1` -> `local_assets/weights/vjepa2`
- `/home/nvme03/workspace/world_model_phys/external/RAFT` -> `local_assets/weights/optical_flow/RAFT`
- `/home/nvme03/workspace/lingbot-world` -> `local_assets/third_party/lingbot_world` with large model/env/output folders excluded.

## Active Config Rule

`configs/cam_physgeo/paths.yaml` points to project-local paths only. Old absolute paths appear only in migration scripts and migration reports.

If space is insufficient, stop migration, keep source data untouched, and record which active local targets remain incomplete. Do not silently fall back to scattered `/home/nvme03` paths for training, reward, or eval.
