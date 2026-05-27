# Corruption Smoke Report

Command:

```bash
python -m cam_physgeo.rewards.corruption \
  --manifest local_assets/data/physion/manifests/physion_cam_physgeo_smoke.jsonl \
  --source physion_movingcam \
  --out local_assets/data/physion/processed/corruptions/smoke \
  --limit 5 \
  --types background_drift object_deformation object_color_identity_change reobserve_mismatch freeze_foreground global_freeze \
  --strength medium \
  --make_contact_sheet \
  --seed 123
```

Result:

- Samples: 5.
- Corrupted videos: 30.
- Output root: `local_assets/data/physion/processed/corruptions/smoke`.
- Contact sheets: inside the same smoke corruption tree.

Implemented corruption types include background drift, nonrigid background warp, object deformation, object color/identity change, foreground freeze, camera freeze, global freeze, wrong camera motion, reobserve mismatch, remove object, and create object.

The implementation preserves the first frame by default and preserves V2V prefix frames when configured. It uses Physion ID mask information when available and falls back to conservative spatial regions when masks are missing or unsuitable.

