# TDW Generation v2 Native Non-Drop Probe Report

Date: 2026-06-04

## Scope

Native upstream commands were reconstructed for exactly one sample each:

- `collision`
- `roll`
- `containment`

These commands used `DISPLAY=:8` under the user-approved GPU0-bound TDW display and did not include drop-only args.

## Result

| Template | Native output | HDF5 |
|---|---|---|
| `collision` | `local_assets/data/physion/generated_v2/debug_native_nondrop/collision_probe/` | passed |
| `roll` | `local_assets/data/physion/generated_v2/debug_native_nondrop/roll_probe/` | passed |
| `containment` | `local_assets/data/physion/generated_v2/debug_native_nondrop/containment_probe/` | passed |

The native probe proved upstream TDW can generate non-drop HDF5 when given the correct template-specific args and an output path interpreted from the project working directory.

## Interpretation

The failure was in the v2 wrapper, not a fundamental upstream template limitation.

