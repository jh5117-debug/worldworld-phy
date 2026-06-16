# Final Report: Multidisplay TDW Scaleup + Prompt-v2 + Stage A Planning

## Current data audit

- 1000 dataset exists: yes.
- Valid samples: 1000 / 1000.
- target.mp4 probe: 1000 / 1000.
- Template distribution: `{'drop': 300, 'collision': 300, 'roll': 200, 'containment': 200}`.
- Camera distribution: `{'orbit_left_72': 300, 'orbit_right_64': 150, 'strafe_left_180': 150, 'orbit_right_60': 200, 'orbit_left_44': 200}`.
- Scene hash unique: 1000 / 1000.
- Duplicate scene hash count: 0.
- Prompt unique count: 1.
- Generic prompt ratio: 1.000.

Conclusion: the 1000 data is real and structurally valid, but the current official prompt is too generic.

## Multi-display

- `:8` is valid NVIDIA display.
- `:9` to `:13` currently report llvmpipe, not NVIDIA.
- `:14` and `:15` are unavailable.
- Root batch-mode access was unavailable; no root setup was performed and no root password was recorded.
- 8-display TDW smoke was not run.

## Data scale-up

No additional TDW data was generated in this phase because the multi-display NVIDIA precondition failed. Next generation should wait until `:9` to `:15` are real NVIDIA Xorg displays, then run a 16-sample smoke before adding another 1000.

## Prompt

`combined_prompt_v2` was generated for all 1000 samples:

- manifest: `local_assets/experiments/exp_multidisplay_tdw_scaleup_promptv2_stageA/prompt_v2/manifest_combined_prompt_v2.jsonl`
- prompt root: `local_assets/experiments/exp_multidisplay_tdw_scaleup_promptv2_stageA/prompt_v2/prompts`

The old object-aware prompt is rejected as a default because it can hallucinate extra objects. The new prompt avoids generic object category lists and uses first-frame visible-object constraints.

## Stage A

Stage A was planned but not run in this phase. The next Stage A should use the valid 1000 split and combined_prompt_v2, with high-noise diagnostic timesteps, balanced sampling, adapter-only training, and no DPO.

## Hard negative

Added quality-bounded hard-negative config: `configs/cam_physgeo/quality_bounded_hard_negative.yaml`.

Low-quality collapsed videos are excluded from the main DPO loser set. DPO training was not run.

## Next action

1. Configure real NVIDIA Xorg displays `:9` to `:15` as root.
2. Run 16-sample multidisplay TDW smoke.
3. If smoke passes, generate the next 1000 samples, validate, convert, and audit.
4. Schedule Stage A on GPU4-7 only when not competing with TDW displays.
5. Keep DPO blocked until quality-bounded hard-negative pairs pass confidence and manual review.
