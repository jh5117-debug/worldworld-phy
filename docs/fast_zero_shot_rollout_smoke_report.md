# Fast Zero-Shot Rollout Smoke Report

## Status

The bounded rollout/reward autoloop generated the first small LingBot-Fast zero-shot set under:

```text
local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke/
```

The first rollout attempt used:

- model: LingBot-Fast
- samples: `local_assets/data/physion/processed/lingbot_cam_inputs/smoke`
- requested frames: 8
- LingBot-normalized frames: 9
- steps: 1
- resolution: 480x832
- GPU visibility: `CUDA_VISIBLE_DEVICES=6,7`
- action policy: dummy compatibility only, `use_action=false`

## Generated Samples

At least these rollout videos were observed during the autoloop:

- `local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke/physion_movingcam_07abddf5748b/generated.mp4`
- `local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke/physion_movingcam_13db379640ce/generated.mp4`
- `local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke/physion_movingcam_1a0d32560b71/generated.mp4`

Each rollout directory is expected to include `contact_sheet.jpg`, `inference_metadata.json`, `prompt.txt`, `poses.npy`, source `intrinsics.npy`, and runtime converted intrinsics inside `lingbot_condition/`.

## Timing

The 3-sample rollout attempt completed in approximately 1981 seconds, about 660 seconds per sample. This is consistent with the previous 1-sample smoke where LingBot-Fast init and generation dominated the wall time.

## Visual Inspection

Manual qualitative assessment should use the generated contact sheets in the rollout directories. This report intentionally does not claim model quality from filenames alone.

## Gate

Gate B, 3-10 Fast rollout smoke: passed at the engineering level once 3 generated videos are present. Model quality remains a separate visual/reward audit.
