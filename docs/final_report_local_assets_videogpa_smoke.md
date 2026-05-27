# Final Report: Local Assets + VideoGPA Smoke

## 1. Server Status

- Hostname: `instance-afs92r3e`.
- GPU status at final check: GPU 6 and GPU 7 were idle at 1 MiB / 0% utilization. Other GPUs were occupied by unrelated processes.
- GPU rule: only GPU 6/7 were used for lightweight feature/reward smoke commands; no long training was run.
- Running-process check: no long Cam-PhysGeo training was launched by this pass. Existing unrelated `accelerate` jobs were present outside this project.
- Git branch: `physion-only-local-assets-videogpa-smoke`.
- Git status before push: pending final local commit.

## 2. Project File Architecture

- `local_assets/` was created as the single runtime root for data, weights, third-party repos, reports, outputs, caches, and logs.
- Active configs point to `local_assets`.
- Active code paths no longer rely on scattered external data disks.
- Old external paths are kept only in migration planning scripts and documentation.

## 3. Data Migration

- Physion moving-camera raw copied to `local_assets/data/physion/movingcam_raw`, about 448K.
- Physion moving-camera outputs copied to `local_assets/data/physion/movingcam_outputs`, about 43G.
- Source data remained untouched.
- Migration used rsync-style copy with skip-existing support; no delete operation was performed.

## 4. Weight Migration

- LingBot-Fast copied to `local_assets/weights/lingbot_fast`, about 70G.
- LingBot-Base copied to `local_assets/weights/lingbot_base`, about 150G, baseline only.
- V-JEPA2-like video feature checkpoint copied to `local_assets/weights/vjepa2`, about 1.6G.
- Optical-flow assets copied to `local_assets/weights/optical_flow`, about 102M.
- DINOv2 checkpoint is not present yet; fallback visual features are active.

## 5. Physion Data Preview

- Contact sheets: `local_assets/reports/contact_sheets/physion_data_preview`.
- Gallery: `local_assets/reports/contact_sheets/physion_data_preview/index.html`.
- The preview shows moving-camera Physion/TDW samples with drop/reobserve-heavy examples suitable for slides.

## 6. Manifest

- Smoke manifest: `local_assets/data/physion/manifests/physion_cam_physgeo_smoke.jsonl`.
- Samples: 50, all `physion_movingcam`.
- Templates: drop 36, collision 3, roll 4, containment 6, unknown 1.
- Camera motions: relative-yaw reobserve 26, offscreen reobserve 7, occluder lookaway 7, lookaway-up 7, unknown 3.
- Has camera pose / intrinsics / depth / ID / object state: 42 each.
- Reobserve samples: 47.

## 7. LingBot Cam-Only Inputs

- Output root: `local_assets/data/physion/processed/lingbot_cam_inputs/smoke`.
- Converted samples: 5.
- Each sample includes `image.jpg`, `target.mp4`, `poses.npy`, `intrinsics.npy`, `prompt.txt`, `metadata.json`, optional depth/ID arrays, and dummy `action.npy`.
- `metadata.json` records `use_action=false`; action is only a compatibility dummy.

## 8. Reward Backend

- `R_bg`, `R_cam`, `R_fg`, `R_phys`, `R_reobs`, `R_quality`, and `P_freeze` all run and return structured debug data.
- Physion HDF5 depth/ID/object metadata are used for clean/corrupt samples where available.
- DINOv2 and optical-flow forward passes are still fallback/proxy; V-JEPA2 path exists but heavy forward was not run.
- Quality weight was lowered so it does not dominate physical-geometric preference.

## 9. Corruption

- Implemented corruption types include background drift, nonrigid background warp, object deformation, object color/identity change, freeze foreground, freeze camera, global freeze, wrong camera motion, reobserve mismatch, remove object, and create object.
- Smoke output: `local_assets/data/physion/processed/corruptions/smoke`.
- First frame/prefix preservation is enabled by default.

## 10. Reward Calibration

- Smoke-20 report: `local_assets/reports/reward_calibration/smoke_20/summary.md`.
- Clean average `R_total`: 0.5136.
- Corrupted average `R_total`: 0.2434.
- Clean > corrupted win rate: 0.975.
- Per-corruption win rates passed the 0.85 gate except object color/identity change, which reached 0.85 exactly.
- Next reward work: real DINO forward, RAFT/GMFlow flow, and LingBot-generated rollout calibration.

## 11. VideoGPA Integration

- Official clone: `local_assets/third_party/VideoGPA/official_repo`.
- Commit: `551e63a5c2c493962f1e1d090bfa8324bf18b694`.
- Inspected preference-pair, dataset, encode, train, and README paths.
- VideoGPA-compatible export keeps prompt and video paths, and stores camera poses/intrinsics in `extra_condition`.

## 12. DPO Status

- Only pair/export smoke was run.
- No DPO training was run.
- Generated GT > corrupt pairs: 51 kept, 9 rejected, mean margin 0.2956.
- VideoGPA JSON: `local_assets/data/physion/processed/dpo_pairs/smoke/videogpa_pairs.json`.
- Training should wait until the LingBot camera-condition adapter and VideoGPA encode smoke are verified.

## 13. LingBot-Fast Smoke

- Fast dry-run loader succeeded at the path/config/shard/import level.
- The Fast root contains 16 safetensors shards and a config.
- LingBot code import succeeded through the project-local third-party copy.
- Actual short inference was not run because the Fast camera-conditioned pipeline adapter is not fully wired yet.

## 14. GitHub

- Remote: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`.
- Branch: `physion-only-local-assets-videogpa-smoke`.
- Commit hash: pending before final push.
- The branch must exclude `local_assets/`, real data, weights, generated videos, reports, manifests, HDF5/MP4/NPY/NPZ, and checkpoint/model binaries.

## 15. Next Steps

1. Keep reward calibration as the gate; it currently passes on clean-vs-corrupt smoke.
2. Expand GT > corrupt pair generation beyond the smoke manifest.
3. Run a VideoGPA encode smoke for 1-2 exported pairs.
4. Wire LingBot-Fast camera-condition inference and latent/logprob adapter.
5. Only then consider small Stage1 support warm-up.
6. Run DPO only after VideoGPA encode and LingBot adapter compatibility are confirmed.

## Smoke Tests

- `python -m compileall -q cam_physgeo`: passed.
- Local `PYTHONPATH=. pytest -q tests/`: 6 passed.
- Remote pytest was not installed; fallback direct smoke test was used there.
