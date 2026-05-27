# Physion-Cam-PhysGeo-DPO

Camera-conditioned physical-geometric preference alignment for LingBot-Base / LingBot-Fast.

Inputs:

- initial image or prefix video
- generated Physion prompt
- camera poses
- intrinsics/projection-derived calibration

Output:

- future video with persistent background geometry, foreground identity, physical event plausibility, and reobserve consistency

Active data sources:

- `physion_official`
- `physion_movingcam`

Inactive/deprecated:

- CSGO/game action data
- PhyInOne
- real `action.npy` conditioning

Smoke path:

```bash
python -m cam_physgeo.data.physion_hdf5_audit \
  --roots /home/nvme03/workspace/physion_moving_camera_mainline_20260505 \
  --out docs/physion_hdf5_key_audit.md \
  --limit 5

python -m cam_physgeo.data.build_manifest \
  --physion_movingcam_root /home/nvme03/workspace/physion_moving_camera_mainline_20260505/synthetic_data_assets \
  --physion_movingcam_outputs /home/nvme03/workspace/physion_moving_camera_mainline_20260505/outputs \
  --out manifests/physion_cam_physgeo_smoke.jsonl \
  --limit 20
```

All large data, weights, generated videos, manifests, reports, and checkpoints are gitignored.
