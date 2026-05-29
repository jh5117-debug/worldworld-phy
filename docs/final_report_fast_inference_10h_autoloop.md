# Final Report: LingBot-Fast 1-Sample Inference Autoloop

Status: `success`

## Summary

- Start: `2026-05-29T14:46:55+08:00`
- End: `2026-05-29T14:59:47+08:00`
- Total wall time: `0.2147` hours
- Remote run directory: `local_assets/reports/smoke/fast_inference_autoloop_20260529_144655`
- Successful attempt: `attempt_0005_actual_f8_s1_480x832_gpu6-7`
- Output video: `local_assets/reports/smoke/fast_inference_autoloop_20260529_144655/outputs/attempt_0005_actual_f8_s1_480x832_gpu6-7/physion_movingcam_07abddf5748b/generated.mp4`
- Contact sheet: `local_assets/reports/smoke/fast_inference_autoloop_20260529_144655/outputs/attempt_0005_actual_f8_s1_480x832_gpu6-7/physion_movingcam_07abddf5748b/contact_sheet.jpg`

## Execution

- Executed in remote auxiliary worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_min_adapter_work`
- The auxiliary worktree shares the same `local_assets` data and weights.
- No data or weights were moved, deleted, or modified.
- No training, reward scoring, VideoGPA encode, DPO, Stage1, or rollout batch was run.
- GPU policy was respected: commands used `CUDA_VISIBLE_DEVICES=6,7`; the LingBot runtime uses `device_id=0`, which maps to physical GPU 6 under that visibility.

## What Changed

The first actual inference attempt reached generation but failed on camera intrinsics shape:

```text
RuntimeError: The expanded size of the tensor (1) must match the existing size (4) at non-singleton dimension 1.
```

Root cause:

- Physion converted samples store `intrinsics.npy` as `(81, 4, 4)` OpenGL-style projection matrices.
- LingBot-Fast `wan.utils.cam_utils.get_Ks_transformed()` expects per-frame pixel intrinsics shaped `(F, 4)` as `[fx, fy, cx, cy]`.

Minimal fix:

- `cam_physgeo.eval.run_inference` now creates a per-attempt `lingbot_condition/` directory.
- It leaves the source sample unchanged.
- It converts projection matrices to LingBot pixel vectors:
  - source shape: `[81, 4, 4]`
  - runtime shape: `[81, 4]`
  - adapter: `projection4x4_to_pixel_vector`
- It passes this runtime condition directory to LingBot-Fast.
- `action.npy` remains dummy-only compatibility data; `use_action=false` is preserved.

## Successful Sample

- Sample ID: `physion_movingcam_07abddf5748b`
- Camera motion: `offscreen_z_reobserve`
- Prompt: `A synthetic indoor physical scene. The static background should remain geometrically stable. Foreground objects move under physical dynamics such as gravity, collision, rolling, containment, or support. The camera follows the provided camera trajectory.`
- Requested frames: `8`
- LingBot normalized frames: `9`
- Steps: `1`
- Timesteps: `[0]`
- Resolution: `480x832`
- Peak CUDA allocation reported by the runtime: `59852665344` bytes

## Timing Markers

- T5 GPU bf16 preflight: passed, embedding shape `[[6, 4096]]`
- T5 model load in preflight: about `43.168s`
- Prompt encode in preflight: about `1.484s`
- Pipeline init done: `467.008s`
- `ready_to_generate`: `467.008s`
- Generation done: `616.865s`
- Save done: `625.198s`
- End-to-end sample elapsed in metadata: `640.856s`
- Autoloop attempt duration: `664.301s`

## Official Demo

- Official candidate search succeeded.
- `local_assets/third_party/lingbot_world/generate_fast.py --help` succeeded.
- An official demo generation was not run because the task limit was one successful short video and the cam_physgeo path succeeded.

## Warnings

LingBot reported many `physics_*` weights as newly initialized when loading `WanModelFast`. This did not block the smoke inference, but it should be audited before trusting output quality or starting larger rollouts.

## Attempts

| id | phase | result | notes |
| --- | --- | --- | --- |
| 1 | `preflight_t5_gpu` | passed via JSON override | Probe produced `ok=true` but the interpreter returned `120` after a harmless unraisable-hook shutdown message. |
| 2 | `official_demo_find` | passed | Candidate files were found. |
| 3 | `official_demo_help` | passed | `generate_fast.py --help` works. |
| 4 | `cam_physgeo_dry_run` | passed | Sample and runtime bundle checks succeeded. |
| 5 | `actual_f8_s1_480x832_gpu6-7` | passed | Generated `generated.mp4` and `contact_sheet.jpg`. |

## Gate Update

- Gate A, LingBot-Fast 1-sample actual inference: passed.
- Fast rollout: yes, next round may generate a very small 3-10 sample set if requested.
- Reward-on-rollout: no in this round; only after the user starts the next phase.
- VideoGPA encode: no in this round.
- DPO: no.

## Next Minimal Action

Next round should generate only a tiny Fast rollout set, such as 3 samples first, then inspect contact sheets manually before any reward-on-rollout or VideoGPA work. Also audit the newly initialized `physics_*` weights to confirm the Fast checkpoint and local LingBot code variant match.
