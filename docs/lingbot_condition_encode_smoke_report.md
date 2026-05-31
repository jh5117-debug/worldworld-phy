# LingBot Condition Encode Smoke Report

## Result

- Status: passed.
- Condition image exists: yes.
- Prompt exists: yes.
- Text embedding: deferred; no T5 encode was run in this dry-run.
- Poses path exists: yes.
- Poses shape: `[81, 4, 4]`
- Raw intrinsics path exists: yes.
- Raw intrinsics shape: `[81, 4, 4]`
- Converted intrinsics shape: `[81, 4]`
- Conversion convention: TDW/Unity/OpenGL-style projection to pixel `[fx, fy, cx, cy]`, with warning recorded.
- Dummy action path exists: yes.
- Dummy action shape: `[81, 4]`
- Dummy action norm: `0.0`
- `use_action`: `false`

## Camera / Plucker Control

- Plucker/control dry-run status: passed.
- Probe device: CPU for this dry-run.
- Control tensor shape: `[1, 448, 2, 60, 104]`
- Control dtype: `float32`
- Control mean/std: `0.1352 / 0.3529`
- Control min/max: `-0.4613 / 1.0000`
- NaN/Inf: none.
- `can_use_for_training_forward`: true at the shape/condition-pack level.

## Pipeline Keys

The dry-run condition pack preserves the following forward-facing keys:

- `image`
- `prompt`
- `action_path`
- `poses`
- `intrinsics`

## Notes

- The first condition attempt failed because the sidecar intrinsics were still raw `(F,4,4)` projection matrices. The adapter now calls the shared `convert_projection_to_lingbot_intrinsics` helper before building the Plucker/control tensor.
- The reusable probe helper has a CPU/CUDA concatenation mismatch for `control_type=act`; this condition dry-run keeps the Plucker/control probe on CPU. The actual LingBot runtime still owns its camera tensor construction during generation/forward.

