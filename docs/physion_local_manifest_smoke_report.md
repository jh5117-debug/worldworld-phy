# Physion Local Manifest Smoke Report

Manifest command used project-local paths:

```bash
python -m cam_physgeo.data.build_manifest \
  --physion_movingcam_root local_assets/data/physion/movingcam_raw \
  --physion_movingcam_outputs local_assets/data/physion/movingcam_outputs \
  --out local_assets/data/physion/manifests/physion_cam_physgeo_smoke.jsonl \
  --limit 50
```

## Result

- Total samples: 50.
- Source: `physion_movingcam` only.
- Validation errors: 0.
- Templates: drop 36, collision 3, roll 4, containment 6, unknown 1.
- Camera motions: `relative_yaw_180_reobserve` 26, `offscreen_z_reobserve` 7, `occluder_lookaway_reobserve` 7, `lookaway_up_reobserve` 7, unknown 3.
- `has_camera_pose`: 42.
- `has_intrinsics`: 42.
- `has_depth`: 42.
- `has_id_mask`: 42.
- `has_object_state`: 42.
- `has_reobserve`: 47.

## Split Smoke

The split command wrote smoke splits under `local_assets/data/physion/splits/smoke`:

- train: 43.
- val: 1.
- test: 6.
- moving_camera_physics: 47.
- reobserve: 47.
- static_camera_physics: 2.
- stress: 48.

The HDF5 reader now maps intrinsics to camera projection matrices, not object keys.

