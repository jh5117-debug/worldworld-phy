# TDW visible-motion v2 Human Review Failure Analysis

## Status

`warmup_visible_motion_v2` 50-sample validation passed the pipeline checks:

- HDF5 generation: 50/50
- HDF5/key validation: 50/50
- LingBot cam-only conversion: 50/50
- target.mp4 probe: 50/50
- `use_action=false`: 50/50

Human review failed the data-quality gate.

## Failure Points

1. Scene diversity was too low.
   The review set looked like the same scene or a small number of scene configurations with different camera views.

2. Visible camera motion was still weak.
   The validator accepted total camera/background motion, but the videos did not strongly communicate camera-conditioned generation to a human reviewer.

3. Camera motion was delayed.
   v2 commands used `--camera_motion_start 24` and `--camera_motion_end 57`, so motion was not clearly present from frame 0.

## Interpretation

The v2 batch remains useful as a pipeline validation set, but it should not be used as the final LingBot-Fast camera-conditioned warmup main dataset.

## Required v3 Fix

`warmup_visible_motion_v3_start0_scene_diverse` must address:

- scene diversity, not just camera diversity;
- camera motion starting at frame 0;
- stronger visible motion while avoiding offscreen/reobserve/stress behavior;
- early-frame background/parallax motion;
- a human review pack with per-template examples, contact sheets, and metrics.
