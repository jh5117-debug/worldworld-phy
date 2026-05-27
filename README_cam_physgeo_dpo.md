# Physion-Cam-PhysGeo-DPO

Camera-conditioned physical-geometric preference alignment for **LingBot-Fast**.

The active project root is:

```bash
/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys
```

All active local data, weights, third-party repos, manifests, processed samples, reports, outputs, and caches live under:

```bash
local_assets/
```

## Scope

- Main model: LingBot-Fast.
- Baseline only: LingBot-Base.
- Data: Physion/TDW moving-camera synthetic data, plus optional official Physion copied under `local_assets`.
- Conditions: initial image or prefix video, prompt, camera poses, intrinsics.
- No action core condition: dummy zero `action.npy` is emitted only for legacy compatibility and always paired with `use_action=false`.
- DPO route: VideoGPA-compatible clean/corrupt preference pairs first; no long DPO training in smoke.

## First Smoke

```bash
python -m cam_physgeo.data.build_manifest \
  --physion_movingcam_root local_assets/data/physion/movingcam_raw \
  --physion_movingcam_outputs local_assets/data/physion/movingcam_outputs \
  --out local_assets/data/physion/manifests/physion_cam_physgeo_smoke.jsonl \
  --limit 50

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

`local_assets/` is gitignored. Push only code, configs, scripts, docs, and small tests.
