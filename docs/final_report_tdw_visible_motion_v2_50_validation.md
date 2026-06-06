# Final Report: TDW visible-motion v2 50 Validation

## Approval

The user approved GPU0-bound `DISPLAY=:8` for `warmup_visible_motion_v2` 50-sample validation only.

No 200 / 1k generation was run.

## v2 50 Generation

- Generated HDF5: 50/50
- Validation OK: 50/50
- Accepted / suitable for visible motion: 50/50
- Rejected: 0/50
- Per-template accepted: drop 15, collision 15, roll 10, containment 10
- GPU used: GPU0 via `DISPLAY=:8`
- Approximate runtime: about 1h45m
- Raw HDF5 storage: 4.31 GB
- Converted storage: 9.75 GB

Camera distribution:

- `orbit_left_24`: 10
- `orbit_right_24`: 9
- `strafe_left_050`: 8
- `strafe_right_050`: 8
- `orbit_left_28`: 4
- `orbit_right_28`: 3
- `orbit_left_18`: 2
- `orbit_right_18`: 2
- `orbit_left_20`: 2
- `orbit_right_20`: 2

## Motion Quality

- camera_path_length min/avg/max: 0.5016 / 1.0778 / 1.4814
- yaw_change_proxy min/avg/max: 6.7214 / 18.7175 / 28.0000
- background_motion_proxy min/avg/max: 0.0121 / 0.0211 / 0.0332
- parallax_proxy min/avg/max: 0.0121 / 0.0211 / 0.0332
- `too_static`: 0
- `too_extreme`: 0

Compared with old `warmup_mild` 50, this batch has explicit visible-motion acceptance and stronger camera/background movement. Compared with v2 10, it preserves the 100% acceptance rate.

## Visibility

- target_visible_ratio min/avg/max: 1.0 / 1.0 / 1.0
- max invisible frames avg/max: 0 / 0
- target_area_ratio_avg: not emitted by the current validator

## Conversion

- Converted count: 50/50
- `target.mp4` probe: passed
- `use_action=false`: 50/50
- dummy action zero norm: 50/50
- `poses.npy` / `intrinsics.npy` shapes valid: 50/50
- `depth.npy` / `id_mask.npy`: 50/50

## Video Deliverables

Updated shared gallery/index:

- `local_assets/reports/tdw_video_deliverables/video_index.md`
- `local_assets/reports/tdw_video_deliverables/video_gallery.html`

Representative per-template samples:

- drop: `local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_v2_50/tdw_v2_00000_drop_orbit_left_24_seed22000_0000/target.mp4`
- collision: `local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_v2_50/tdw_v2_00015_collision_strafe_left_050_seed22015_0000/target.mp4`
- roll: `local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_v2_50/tdw_v2_00030_roll_strafe_left_050_seed22030_0000/target.mp4`
- containment: `local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_v2_50/tdw_v2_00040_containment_orbit_left_18_seed22040_0000/target.mp4`

## 200 Readiness

Ready to request approval for a 200-sample pilot:

- acceptance >= 40/50: yes, 50/50
- every template >= 5 accepted: yes

Approval is still required before any 200 run. 1k+ remains disallowed.

## Safety

- No training.
- No DPO.
- No VideoGPA `03_train`.
- No Stage1.
- No LingBot rollout.
- No reward calibration.
- No 200 / 1k generation.
- No `local_assets` committed.
- No generated HDF5 / MP4 / NPY committed.

## Next Action

Ask the user whether to approve a 200-sample `warmup_visible_motion_v2` pilot on GPU0-bound `DISPLAY=:8`, or configure a GPU6/7 TDW display first. DPO signal remains a separate gate.

