# TDW v5 1000 Dataset Audit Report

## Integrity

- Manifest exists: yes.
- Count: 1000.
- Valid samples: 1000.
- Invalid samples: 0.
- target.mp4 probe pass: 1000.
- Ready for dataloader: True.

## Tensor Shapes

- poses: `{'[81, 4, 4]': 1000}`
- intrinsics: `{'[81, 4, 4]': 1000}`
- action: `{'[81, 4]': 1000}`

## Distribution

- Template distribution: `{'drop': 300, 'collision': 300, 'roll': 200, 'containment': 200}`.
- Camera distribution: `{'orbit_left_72': 300, 'orbit_right_64': 150, 'strafe_left_180': 150, 'orbit_right_60': 200, 'orbit_left_44': 200}`.

## Scene Diversity

- Scene hash unique: 1000 / 1000.
- Duplicate scene hash count: 0.
- First-frame phash unique: 969 / 1000.
- First-frame phash duplicate count: 31.

## Prompt Audit

- Unique prompt count: 1.
- Generic prompt ratio: 1.000.
- Top prompt: `A synthetic indoor physical scene. The static background should remain geometrically stable. Foreground objects move under physical dynamics such as gravity, collision, rolling, containment, or support. The camera follows the provided camera trajectory.`

## Decision

The 1000-sample dataset is real and structurally valid. The main blocker is prompt quality, not sample count or file integrity. For new rollouts/warmup prompts, use `combined_prompt_v2` instead of the old generic prompt.
