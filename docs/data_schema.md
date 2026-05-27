# Physion Cam-Only Data Schema

Manifest sources are restricted to:

- `physion_official`
- `physion_movingcam`

Each manifest row contains:

```json
{
  "sample_id": "...",
  "source": "physion_official",
  "template": "drop|collision|roll|containment|support|dominoes|drape|link|unknown",
  "camera_motion": "static|orbit|strafe|lookaway|offscreen|relative_yaw_180_reobserve|unknown",
  "video_path": "... or null",
  "hdf5_path": "... or null",
  "rgb_key": "... or null",
  "depth_key": "... or null",
  "id_key": "... or null",
  "flow_key": "... or null",
  "normal_key": "... or null",
  "poses_key": "... or null",
  "intrinsics_key": "... or null",
  "camera_position_key": "... or null",
  "camera_aim_key": "... or null",
  "prompt_path": "... or generated://physion",
  "num_frames": 81,
  "fps": 16,
  "width": 832,
  "height": 480,
  "has_moving_camera": true,
  "has_depth": true,
  "has_id_mask": true,
  "has_flow": false,
  "has_normals": false,
  "has_object_state": true,
  "has_camera_pose": true,
  "has_intrinsics": true,
  "has_reobserve": true,
  "quality_flags": []
}
```

Converted LingBot cam-only sample:

```text
sample_dir/
  image.jpg
  prefix.mp4        optional
  target.mp4
  poses.npy
  intrinsics.npy
  prompt.txt
  metadata.json
  depth.npy         optional
  id_mask.npy       optional
  flow.npy          optional
  normals.npy       optional
  action.npy        optional dummy zero only
```

`metadata.json` always sets `use_action=false`.
