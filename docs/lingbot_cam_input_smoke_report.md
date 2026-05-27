# LingBot Cam-Only Input Smoke Report

Conversion command:

```bash
python -m cam_physgeo.data.convert_to_lingbot_cam_inputs \
  --manifest local_assets/data/physion/manifests/physion_cam_physgeo_smoke.jsonl \
  --out local_assets/data/physion/processed/lingbot_cam_inputs/smoke \
  --source physion_movingcam \
  --num_frames 81 \
  --fps 16 \
  --size 480x832 \
  --use_action false \
  --make_dummy_action true \
  --limit 5
```

Result: 5 sample directories were generated under `local_assets/data/physion/processed/lingbot_cam_inputs/smoke`.

Each sample contains:

- `image.jpg`
- `target.mp4`
- `poses.npy`
- `intrinsics.npy`
- `prompt.txt`
- `metadata.json`
- optional `depth.npy`
- optional `id_mask.npy`
- dummy `action.npy` only for legacy compatibility

`metadata.json` records `use_action=false`. The generated `action.npy` is a zero dummy fallback and is not used as a modeling condition.

The HDF5 key mapping was fixed so `intrinsics_source=hdf5` and intrinsics come from camera projection matrices such as `frames/0000/camera_matrices/projection_matrix`.

