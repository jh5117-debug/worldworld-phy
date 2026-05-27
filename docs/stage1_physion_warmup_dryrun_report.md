# Stage1 Physion Warm-Up Dry-Run Report

Command:

```bash
CUDA_VISIBLE_DEVICES=6,7 python -m cam_physgeo.training.train_stage1_physion_warmup \
  --config configs/cam_physgeo/stage1_physion_warmup.yaml \
  --dry-run \
  --limit 2 \
  --max_steps 1
```

Result: dry-run passed.

The entrypoint uses Physion cam-only inputs from `local_assets/data/physion/processed/lingbot_cam_inputs`, targets LingBot-Fast by default, keeps `use_action=false`, and is configured for LoRA/adapter-style support warm-up only.

No real training was launched. Stage1 remains a guarded support warm-up, not the final method. The main DPO route is VideoGPA-compatible anchored preference data once reward calibration is stable.

