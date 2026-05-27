# Final Report: Physion-Only Cam-PhysGeo-DPO

## Server State

- Hostname: `instance-afs92r3e`
- Branch: `physion-only-cam-physgeo-dpo`
- GPU: GPUs 0-3 were occupied by another accelerate job; GPUs 4-7 were idle during audit. No long training was launched.
- Running process observed: unrelated `/home/nvme02/GR00T/... accelerate ... train_agent_trl.py`; no Cam-PhysGeo training process was active.
- Git status: dirty worktree from prior untracked framework files and historical deletions; only safe code/config/docs/scripts/tests are intended for push.

## Physion-Only Switch

- Active sources: `physion_official`, `physion_movingcam`.
- `scan_phyinone.py` and `data_phyinone.yaml` are deprecated and return/no-op.
- `movingcam_synthetic` naming is deprecated; the data is now `physion_movingcam`.
- No CSGO/game action data is used as mainline.
- `action.npy` is dummy zero compatibility only, with `use_action=false`.

## Official Physion

- Existing non-git copies: `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/repos/physics-benchmarking-neurips2021` and `generation_functional_files_20260525/repos/physics-benchmarking-neurips2021`.
- Standalone official data root `/home/nvme03/workspace/physion_official/data` was not confirmed.
- Core/Complete/train split not confirmed downloaded.
- A fresh official repo clone attempt stalled due network; dataset download was not launched.

## Existing Physion Moving-Camera Data

- Root: `/home/nvme03/workspace/physion_moving_camera_mainline_20260505`
- Size: about 198 GB
- HDF5/H5: 1955
- MP4: 369
- `commandline_args.txt`: 2119
- `tdw_commands.json`: 2186
- `summary.json`: 92
- `batch_config.json`: 72
- Smoke manifest: 20 samples, all `physion_movingcam`.
- Templates: drop 7, collision 6, roll 3, containment 3, unknown 1.
- Camera motions: relative_yaw_180_reobserve 18, lookaway_up_reobserve 1, unknown 1.
- Camera/depth/ID/object state availability: 19/20.

## Camera Metadata Answer

- Moving-camera HDF5 has explicit `camera_pose`, `camera_position`, `camera_aim`, `camera_matrix`, and `projection_matrix`.
- K-style `intrinsics` is not always named explicitly, but projection/camera matrices are present and exported as calibration.
- Official Physion HDF5 still needs a standalone audit once the official data is downloaded.
- Current moving-camera Physion/TDW HDF5 is directly usable for camera-conditioned training/eval smoke.

## Prompt Answer

- Physion does not provide LingBot natural language prompts as the main condition.
- Prompts are generated as P0/P1/P2 from template and camera motion.
- Prompt generation avoids trial outcome leakage, frame-specific reobserve answers, action/WASD wording, and evaluation labels.

## HDF5 Reader And Converter

- Implemented `physion_hdf5_audit.py` and `physion_hdf5_reader.py`.
- Reader supports RGB/depth/ID/camera/object/collision keys from TDW HDF5.
- Converter generated `image.jpg`, `target.mp4`, `poses.npy`, `intrinsics.npy`, `prompt.txt`, `metadata.json`, optional depth/ID, and dummy zero `action.npy`.
- Smoke conversion completed for 3 samples under `data/physion_cam_lingbot_inputs_smoke`.

## Reward And Corruption

- Implemented `R_bg`, `R_cam`, `R_fg`, `R_phys`, `R_reobs`, `R_quality`, and `P_freeze` with Physion metadata hooks and lightweight CV fallbacks.
- Corruptions implemented: background drift, nonrigid warp, object deformation, color/identity change, freeze foreground/camera/global, wrong camera, camera shuffle, reobserve mismatch, remove/create object.
- Reward calibration smoke: 5 clean samples, 25 corrupted comparisons, clean win rate 0.68.
- Warning: reward separates freeze corruptions well but needs stronger background/reobserve/object-specific backends.

## DPO

- Pair builder now generates real corrupted videos, scores clean and corrupt videos, filters by measured margin, and writes JSONL pairs.
- Smoke DPO pairs: 9 kept, 16 rejected, mean margin 0.5599.
- Stage2 dry-run passed with pair dataset. Real LingBot DPO energy adapter remains TODO and intentionally guarded.

## Stage1/2/3

- Stage1 Physion warm-up dry-run passed and reuses legacy LingBot/TRD import path.
- Stage2 anchored DPO dry-run passed.
- Stage3 self-rollout DPO dry-run passed and remains gated by pass@K/quality/bg-cam/freeze thresholds.

## LingBot And Downloads

- LingBot-Base: `/home/nvme04/workspace/world_model_phys/PHYS/weight/Lingbot-base-cam`, about 149.246 GB, usable as teacher/baseline.
- LingBot-Fast: `/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam/lingbot_world_fast`, about 69.088 GB, already present; no duplicate download.
- V-JEPA2.1 local checkpoint exists.
- RAFT source/checkpoint exists.
- DINO/depth model downloads are not blocking; reward falls back to Physion HDF5 depth/ID and CV proxies.

## Smoke Tests

- `compileall`: passed.
- HDF5 audit limit 5: passed.
- manifest build limit 20: passed.
- manifest validation: passed with 0 bad samples.
- split manifest: passed.
- converter limit 3: passed.
- corruption limit 3: passed.
- reward calibration limit 5: passed with warning.
- DPO pair builder limit 5: passed, 9 pairs kept.
- Stage1/Stage2/Stage3/camera audit dry-runs: passed.
- Remote pytest unavailable in LingBot env; python assert smoke passed.

## Next Steps

1. Expand Physion HDF5 audit to a larger official/moving-camera subset.
2. Strengthen R_bg/R_cam with RAFT/depth rigid flow and R_reobs with feature landmarks.
3. Run reward calibration on a small full split.
4. Run Stage1 500-2000 clip Physion support warm-up.
5. Generate LingBot Base/Fast rollouts.
6. Build anchored DPO pairs with clean/corrupt/teacher/Fast rollouts.
7. Run Stage2 anchored DPO.
8. Consider Stage3 self-rollout DPO only after pass@K and quality gates pass.
