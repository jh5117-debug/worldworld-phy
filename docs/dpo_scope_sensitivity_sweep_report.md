# DPO Scope Sensitivity Sweep Report

## Status

- Scope sensitivity sweep: skipped.
- Reason: the preceding LR sweep was runtime-blocked, and even a 1-step fallback
  required a long model-load/forward window.
- No broader LoRA scope was run.
- No optimizer step was run for broader scopes.
- No LoRA/checkpoint was saved.

## Planned Scopes

The planned scopes were:

1. `current`:
   - `blocks.39.cam_shift_layer`
   - `blocks.39.cam_scale_layer`
2. `last2_blocks_camera`:
   - `blocks.38.cam_shift_layer`
   - `blocks.38.cam_scale_layer`
   - `blocks.39.cam_shift_layer`
   - `blocks.39.cam_scale_layer`
3. `last4_blocks_camera`:
   - `blocks.36-39` camera shift/scale layers.

## Why Skipped

Running broader scopes after the LR sweep stalled would have increased memory
and runtime risk without first establishing a clear signal from the current
scope. The safe conclusion is to keep Gate E at diagnostic/partial for learning
signal and avoid expanding to 5-pair/10-pair yet.

## Next Scope Recommendation

If the next round focuses on scope sensitivity, use a shorter optimized runner
that reuses the loaded reference/policy and tries only:

- `current`, lr `1e-4`, 1-3 steps;
- `last2_blocks_camera`, lr `1e-4`, 1-3 steps.

Do not try `last4_blocks_camera` until the last-2-block scope is known to be
stable and useful.
