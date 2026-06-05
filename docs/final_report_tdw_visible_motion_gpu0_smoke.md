# Final Report: TDW Visible-Motion GPU0 Smoke

Date: 2026-06-05

## Worktree / Git

Execution worktree:

```text
/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_gpu67_visible_motion_work
```

Git branch for this report:

```text
physion-tdw-visible-motion-gpu0-smoke
```

`local_assets` on the remote helper worktree is a symlink to the shared project assets directory. No assets were moved or deleted.

Only docs and the small conversion-filter code fix are committed. Generated HDF5 / MP4 / NPY / logs are not committed.

## Approval

The user explicitly approved GPU0-bound `DISPLAY=:8` for this run only:

- one `warmup_visible_motion` sample;
- then ten `warmup_visible_motion` smoke samples if the one-sample gate passed.

No 50 / 200 / 1k generation was run.

## Existing 50 Reassessment

The earlier template-diverse 50-sample `warmup_mild` batch remains a pipeline validation pass, but camera motion was too weak by manual review. It should not be used as final camera-conditioned warmup main data.

## Profile

`warmup_visible_motion` uses stronger but non-stress camera variants:

- `orbit_left_24`
- `orbit_right_24`
- `orbit_left_28`
- `orbit_right_28`
- `strafe_left_050`
- `strafe_right_050`
- `dolly_in_025`
- `dolly_out_025`

Thresholds:

- `target_visible_ratio >= 0.75`
- `max_invisible_frames <= 8`
- `camera_path_length >= 0.45`
- `camera_path_length <= 1.50`
- `background_motion_proxy >= 0.012`
- `video_motion_proxy >= 0.015`

## 1-Sample Actual

| Item | Value |
|---|---|
| Status | passed |
| HDF5 | `local_assets/data/physion/generated_v2/raw_hdf5/warmup_visible_motion_plan_1samples/00000_drop_orbit_left_24_seed22000/0000.hdf5` |
| Camera variant | `orbit_left_24` |
| Camera path length | 1.1854358679765697 |
| Background motion proxy | 0.02952023684470491 |
| Target visible ratio | 1.0 |
| Max invisible frames | 0 |
| Too static | false |
| Too extreme | false |
| Suitable | true |

## 10-Sample Actual

| Item | Value |
|---|---:|
| HDF5 generated | 10 |
| Validation OK | 10 |
| Suitable for warmup | 10 |
| Suitable for visible motion | 5 |
| Rejected as too static | 2 |
| Rejected as too extreme | 3 |
| Converted | 5 |
| Conversion errors | 0 |

Template distribution:

- `drop:3`
- `collision:3`
- `roll:2`
- `containment:2`

Camera distribution:

- `orbit_left_24:2`
- `orbit_right_24:2`
- `orbit_left_28:1`
- `orbit_right_28:1`
- `strafe_left_050:1`
- `strafe_right_050:1`
- `dolly_in_025:1`
- `dolly_out_025:1`

## Motion Quality

Accepted samples show clear motion:

- drop orbit 24 / 28 degree samples show visible viewpoint and background changes;
- collision strafe 0.50 samples show visible lateral/parallax motion.

Rejected samples:

- `dolly_in_025` and `dolly_out_025` are still too static;
- containment orbit samples exceed the current `camera_path_length <= 1.50` threshold;
- one collision `orbit_right_28` also exceeded the path threshold.

## Conversion

Converted only the 5 samples with `suitable_for_visible_motion=true`.

Output:

```text
local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_10_gpu0
```

All converted samples have:

- `target.mp4` probe passed;
- `poses.npy` `(81, 4, 4)`;
- `intrinsics.npy` `(81, 4, 4)`;
- dummy `action.npy` `(81, 4)` with zero norm;
- `metadata.json` with `use_action=false`.

## Safety

- No training.
- No DPO training.
- No VideoGPA `03_train`.
- No Stage1.
- No LingBot rollout.
- No reward calibration.
- No 50 / 200 / 1k TDW generation.
- No LoRA or checkpoint saved.
- No `local_assets` committed.

## Next Action

Do not run visible-motion 50 yet without a new decision.

Recommended next step:

1. Adjust profile before 50:
   - keep orbit 24 / drop;
   - keep strafe 0.50 where target framing remains acceptable;
   - remove or strengthen dolly 0.25 because it is still too static;
   - tune containment separately, likely lower orbit degrees or loosen the path threshold only after visual review.
2. Rerun a 10-sample visible-motion smoke after tuning.
3. Ask user approval before any 50-sample run.
