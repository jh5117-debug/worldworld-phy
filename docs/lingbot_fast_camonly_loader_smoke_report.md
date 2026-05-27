# LingBot-Fast Cam-Only Loader Smoke Report

Dry-run command:

```bash
python -m cam_physgeo.eval.run_inference \
  --config configs/cam_physgeo/eval.yaml \
  --model_type fast \
  --samples local_assets/data/physion/processed/lingbot_cam_inputs/smoke \
  --out local_assets/outputs/smoke/lingbot_fast_inference \
  --dry-run \
  --limit 1
```

Result:

- LingBot-Fast path: `local_assets/weights/lingbot_fast`.
- Approximate size: 69.1 GiB.
- Safetensors shards: 16.
- Config present: yes.
- Fast shard layout detected: yes.
- LingBot code import: ok from `local_assets/third_party/lingbot_world`.
- Legacy high/low-noise loader layout: not directly detected in the Fast root.
- Inference smoke-run: not launched; the current adapter is still dry-run only for actual video generation.

Cam-only condition handling:

- Input samples contain `image.jpg`, `target.mp4`, `poses.npy`, `intrinsics.npy`, `prompt.txt`, and `metadata.json`.
- `use_action=false`.
- Dummy zero `action.npy` is present only for legacy compatibility.

Next required file-level work is to connect LingBot-Fast's actual pipeline entrypoint to `image/prefix + prompt + camera pose/intrinsics` without treating action as a modeling condition.

