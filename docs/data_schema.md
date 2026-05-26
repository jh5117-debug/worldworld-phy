# Data Schema

Manifest JSONL rows contain at least:

```json
{
  "sample_id": "...",
  "source": "phyinone|movingcam_synthetic",
  "template": "drop|collision|roll|containment|support|unknown",
  "camera_motion": "...",
  "video_path": "...",
  "hdf5_path": "...",
  "rgb_frames": "... or null",
  "depth_path": "... or null",
  "id_path": "... or null",
  "poses_path": "... or hdf5://...::camera_pose",
  "intrinsics_path": "... or hdf5://...::intrinsics",
  "prompt_path": "... or generated://...",
  "num_frames": 81,
  "fps": 16,
  "width": 832,
  "height": 480,
  "has_moving_camera": true,
  "has_depth": true,
  "has_id_mask": true,
  "has_object_state": true,
  "quality_flags": []
}
```

Converted LingBot cam-only input directory:

```text
sample_dir/
  image.jpg
  prefix.mp4 optional
  target.mp4
  poses.npy
  intrinsics.npy
  prompt.txt
  metadata.json
  depth/ or depth.npy optional
  id_mask/ or id.npy optional
  action.npy optional dummy zero compatibility only
```

`metadata.json` writes `use_action=false` when dummy action is created. Reward and benchmark code must ignore action.
