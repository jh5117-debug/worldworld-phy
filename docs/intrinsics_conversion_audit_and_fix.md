# Intrinsics Conversion Audit And Fix

## Problem

Physion moving-camera samples store `intrinsics.npy` as per-frame 4x4 projection matrices, for example `(81, 4, 4)`. LingBot-Fast camera utilities expect per-frame pixel-space intrinsics shaped `(F, 4)` as:

```text
[fx, fy, cx, cy]
```

Passing the raw Physion projection matrices directly caused LingBot camera utility shape errors during actual inference.

## Fix

The conversion now lives in:

```text
cam_physgeo/utils/camera.py
```

Function:

```python
convert_projection_to_lingbot_intrinsics(projection_matrices, width, height, convention="auto")
```

Supported inputs:

- `(F, 4)` and `(4,)`: already LingBot-style vectors.
- `(F, 3, 3)` and `(3, 3)`: pixel-space camera matrices.
- `(F, 4, 4)` and `(4, 4)`: TDW/Unity/OpenGL-style projection matrices.

For projection matrices, the current convention is:

```text
fx = P[0, 0] * width / 2
fy = P[1, 1] * height / 2
cx = (1 - P[0, 2]) * width / 2
cy = (1 - P[1, 2]) * height / 2
```

When `convention="auto"`, the function emits a warning because the TDW/OpenGL convention is inferred from the Physion export layout rather than proven by calibration.

## Runtime Policy

- Original Physion `intrinsics.npy` is not modified.
- `run_inference.py` writes a per-attempt runtime copy under `lingbot_condition/intrinsics.npy`.
- Metadata records source shape, runtime shape, adapter format, and conversion warning.
- `convert_to_lingbot_cam_inputs.py` now records how runtime LingBot intrinsics will be adapted, while preserving source intrinsics.

## Validation

Local smoke checks passed:

```text
python -m compileall -q cam_physgeo
python tests/test_intrinsics_conversion.py
```

Remote smoke checks passed in the LingBot environment before the rollout/reward autoloop started.

## Remaining Risk

The conversion is format-correct and enabled 1-sample LingBot-Fast inference, but exact camera-following interpretation still depends on the TDW/OpenGL projection convention. Camera ablation is required before claiming the model truly follows camera condition.
