# LingBot-Fast Cam-Only Dry-Run V2 Report

## Code Changes

`cam_physgeo/eval/run_inference.py` now supports:

- direct `LINGBOT_ENV/bin/python -u` launcher when available;
- `--timeout` alias for smoke timeout;
- `--local-files-only`, which sets `TRANSFORMERS_OFFLINE=1`, `HF_HUB_OFFLINE=1`, and `HF_DATASETS_OFFLINE=1` in the child runtime;
- `--probe-only`, which stops the generated runtime script after import/image checks and before `WanI2VFast` initialization;
- `--text-embedding-cache` and `--skip-t5-if-cached` as explicit CLI flags.

Cached text embedding bypass is intentionally not faked. If those flags are used for smoke generation, the script writes a clear error because `WanI2VFast` constructs its T5 encoder in `__init__`.

## Intended Dry-Run

```bash
python -m cam_physgeo.eval.run_inference \
  --config configs/cam_physgeo/eval.yaml \
  --model_type fast \
  --samples local_assets/data/physion/processed/lingbot_cam_inputs/smoke \
  --out local_assets/outputs/smoke/lingbot_fast_inference \
  --dry-run \
  --limit 1 \
  --timeout 120 \
  --local-files-only
```

## Current Run Status

The patched code compiled locally and tests passed. The cam_physgeo dry-run was not re-run after the CPU T5 probe failed, because dry-run does not initialize T5 and would not resolve the current blocker.

Use the LingBot env Python when running it next:

```bash
PY=/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python
$PY -m cam_physgeo.eval.run_inference \
  --config configs/cam_physgeo/eval.yaml \
  --model_type fast \
  --samples local_assets/data/physion/processed/lingbot_cam_inputs/smoke \
  --out local_assets/outputs/smoke/lingbot_fast_inference \
  --dry-run \
  --limit 1 \
  --timeout 120
```

## Condition Handling

The dry-run payload documents:

- image condition: `image.jpg`
- prompt condition: `prompt.txt`
- camera condition: `poses.npy` and `intrinsics.npy`
- dummy action policy: `action.npy` is ignored and retained only for legacy compatibility

If the actual LingBot runtime ignores camera pose internally, that remains a TODO in LingBot code and is not represented as solved here.
