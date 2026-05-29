# Camera Condition Ablation Report

## Status

The camera condition ablation smoke completed for one sample:

```text
physion_movingcam_07abddf5748b
```

Variants generated:

- correct camera
- frozen camera
- reversed camera

Output root:

```text
local_assets/data/physion/processed/rollouts/camera_ablation_smoke/
```

Comparison contact sheet:

```text
local_assets/data/physion/processed/rollouts/camera_ablation_smoke/physion_movingcam_07abddf5748b/comparison_contact_sheet.jpg
```

## Generated Videos

- `local_assets/data/physion/processed/rollouts/camera_ablation_smoke/physion_movingcam_07abddf5748b/correct/physion_movingcam_07abddf5748b/generated.mp4`
- `local_assets/data/physion/processed/rollouts/camera_ablation_smoke/physion_movingcam_07abddf5748b/frozen/physion_movingcam_07abddf5748b/generated.mp4`
- `local_assets/data/physion/processed/rollouts/camera_ablation_smoke/physion_movingcam_07abddf5748b/reversed/physion_movingcam_07abddf5748b/generated.mp4`

## Timing

- correct: about 618.7 seconds
- frozen: about 682.5 seconds
- reversed: about 671.6 seconds
- total ablation attempt: about 1975.9 seconds

## Camera Condition Handling

- `poses.npy` was modified only in temporary ablation input directories.
- Original Physion samples were not modified.
- `intrinsics.npy` was preserved and converted at runtime to LingBot `(F,4)` format.
- `action.npy` remained dummy compatibility data.
- `metadata.json` preserved `use_action=false`.

## Qualitative Result

The comparison contact sheet shows the three variants are visually very similar at this short 8-frame, 1-step smoke scale. This means the smoke proves that correct/frozen/reversed camera inputs can be passed through the pipeline, but it does not prove that LingBot-Fast is materially using the camera condition.

Gate C should be marked partial or not proven until a stronger camera-only audit is run with longer motion, fixed seed controls, and a metric that compares background motion across camera variants.
