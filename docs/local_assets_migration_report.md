# Local Assets Migration Report

The project now uses `local_assets/` under the repository root as the only active runtime asset root. Source locations on other disks are kept only in migration scripts and migration documentation.

## Created Layout

- `local_assets/data/physion/movingcam_raw`: Physion/TDW moving-camera raw metadata and assets.
- `local_assets/data/physion/movingcam_outputs`: Physion/TDW moving-camera HDF5/MP4 outputs.
- `local_assets/data/physion/processed`: LingBot cam-only inputs, corruptions, DPO pairs, and rollouts.
- `local_assets/weights`: LingBot-Fast, LingBot-Base, feature, flow, and optional depth weights.
- `local_assets/third_party`: VideoGPA, LingBot code, and optional official Physion repo.
- `local_assets/reports`: audits, reward calibration, DPO pair-builder reports, smoke logs, and contact sheets.
- `local_assets/outputs`: smoke inference/eval output.
- `local_assets/cache` and `local_assets/logs`: local caches and logs.

## Migration Status

- Physion moving-camera raw: copied to `local_assets/data/physion/movingcam_raw`, about 448K, 30 files.
- Physion moving-camera outputs: copied to `local_assets/data/physion/movingcam_outputs`, about 43G.
- LingBot-Fast: copied to `local_assets/weights/lingbot_fast`, about 70G, 43 files, including 16 safetensors shards.
- LingBot-Base: copied to `local_assets/weights/lingbot_base`, about 150G.
- V-JEPA2/Video feature checkpoint: copied to `local_assets/weights/vjepa2`, about 1.6G.
- Optical flow code/weights: copied to `local_assets/weights/optical_flow`, about 102M.
- LingBot code mirror: copied to `local_assets/third_party/lingbot_world`. This copy is large because it preserves the source tree needed by legacy imports; it is ignored by Git.
- VideoGPA official clone: `local_assets/third_party/VideoGPA/official_repo`, commit `551e63a5c2c493962f1e1d090bfa8324bf18b694`.

No source data, weights, or checkpoints were deleted.

## Active Config

`configs/cam_physgeo/paths.yaml` points active data, weights, third-party, output, report, manifest, split, and cache paths to `local_assets/`. New training, reward, conversion, eval, and DPO scripts use those paths.

The old external paths remain only as source paths in `scripts/00_plan_local_assets.sh`, `scripts/01_migrate_assets_to_project.sh`, and the architecture plan.

