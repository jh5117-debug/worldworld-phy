# TDW v5 200 LingBot Dataloader Smoke Report

Date: 2026-06-09

## Inputs

- Train manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/train.jsonl`
- Val manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/val.jsonl`
- Test manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/test.jsonl`
- Output: `local_assets/experiments/exp_tdw_v5_200_lingbot_warmup_gate/dataloader_smoke/`

## Result

- Passed: yes
- Train rows: 160
- Val rows: 20
- Test rows: 20
- Batches probed: 9
- Batch size: 2
- Video decode: passed

## Batch Shapes

Representative batch shapes:

- image tensor: `[2, 480, 832, 3]`
- video tensor: `[2, 81, 480, 832, 3]`
- poses: `[2, 81, 4, 4]`
- intrinsics: `[2, 81, 4, 4]`
- action: `[2, 81, 4]`

## Safety Checks

- `metadata.use_action=false`: passed
- action norms: 0.0
- prompt examples: non-empty synthetic physical-scene prompts
- no optimizer, no backward, no model weight mutation

## Decode Timing

Representative `target.mp4` decode time was about 1.4 to 1.8 seconds per sample for 81 frames at 480x832 in this smoke.

The v5 200 split is ready for a model-load forward-loss dry-run once the GPU/model-load step is explicitly approved and scheduled.
