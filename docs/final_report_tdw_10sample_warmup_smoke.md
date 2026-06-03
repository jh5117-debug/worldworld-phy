# Final Report: TDW v2 10-Sample Warmup Smoke

Generated: 2026-06-04

## Approval

User explicitly approved GPU0-bound `DISPLAY=:8` for exactly 10 TDW / Physion-style `warmup_mild` samples.

No 50/200/1k generation was run.

## Execution Context

- Remote worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_fixed_noise_diagnostic_work/world_model_phys_tdw_generation_v2_prd_work/world_model_phys_tdw_generation_v2_mild_smoke_work`
- Remote execution branch: `physion-tdw-generation-v2-mild-smoke`
- Remote execution commit: `847bea8` plus uncommitted TDW v2 wrapper fixes from previous gate work
- `local_assets`: symlink to `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets`
- Remote URL: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`

No assets, videos, HDF5, NPY, latents, weights, or logs are committed.

## Generation

| Metric | Value |
|---|---:|
| Requested samples | 10 |
| Generated HDF5 count | 10 |
| Success / ok count | 10 |
| Failed count | 0 |
| Rejected count | 0 |
| Suitable for warmup | 10 |
| Duration | 1266 sec |
| GPU used | GPU0 via `DISPLAY=:8` |
| Raw HDF5 storage | 842M |

Template distribution:

| Template | Count |
|---|---:|
| drop | 10 |

Camera variants:

| Variant | Count |
|---|---:|
| orbit_left_12 | 2 |
| orbit_right_12 | 2 |
| strafe_left_025 | 2 |
| strafe_right_025 | 2 |
| dolly_in_010 | 1 |
| dolly_out_010 | 1 |

## Validation

All 10 samples have RGB, depth, ID, camera pose, camera position, camera aim, projection/camera matrix, and object state.

| Metric | Avg | Min | Max |
|---|---:|---:|---:|
| target_visible_ratio | 1.0 | 1.0 | 1.0 |
| camera_path_length | 0.3575 | 0.1005 | 0.5927 |

| Metric | Value |
|---|---:|
| max invisible frames avg | 0.0 |
| max invisible frames max | 0 |

Camera motion stayed mild; foreground stayed visible for all validated samples.

## LingBot Conversion

| Metric | Value |
|---|---:|
| Converted unique 10-sample dirs | 10 |
| Conversion failures | 0 |
| target.mp4 probe passed | 10 |
| use_action=false | 10 |
| dummy action zero norm | 10 |

Each converted video probes at 81 frames, 16 fps, 832x480.

## Video Deliverables

- Gallery: `local_assets/reports/tdw_video_deliverables/video_gallery.html`
- Index: `local_assets/reports/tdw_video_deliverables/video_index.md`
- New category: `New TDW v2 warmup_mild 10-sample smoke`

Compared with the old stress/reobserve sample, these 10 samples keep the target visible and use mild camera variants. They are more suitable for warmup inspection.

## Important Limitation

The actual upstream runner produced only `drop` template samples, although the dry-run plan requested `drop`, `collision`, `roll`, and `containment`. Before 50-sample validation or larger generation, decide whether to:

1. accept a drop-only validation run; or
2. fix template coverage first.

## Next Decision

Choose one:

1. Approve GPU0-bound `DISPLAY=:8` for 50-sample validation.
2. Configure GPU6/7 TDW display first.
3. Fix template coverage and rerun a smaller template-diverse smoke.
4. Continue DPO signal runner work.
5. Pause.

## Safety

- No training.
- No DPO training.
- No VideoGPA `03_train.py`.
- No Stage1.
- No LingBot rollout.
- No reward calibration.
- No 50/200/1k generation.
- No local_assets committed.
