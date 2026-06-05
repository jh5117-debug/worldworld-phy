# Final Report: TDW Visible-Motion v2

Date: 2026-06-05

## v1 Summary

`warmup_visible_motion` v1 generated 10 HDF5 samples and passed HDF5/key/visibility validation for all 10, but only 5 / 10 passed visible-motion quality.

Accepted:

- drop + `orbit_left_24`
- drop + `orbit_right_24`
- drop + `orbit_left_28`
- collision + `strafe_left_050`
- collision + `strafe_right_050`

Rejected:

- collision + `orbit_right_28`: too extreme;
- roll + `dolly_in_025`: too static;
- roll + `dolly_out_025`: too static;
- containment + `orbit_left_24`: too extreme;
- containment + `orbit_right_24`: too extreme.

## v2 Profile

Added:

```text
warmup_visible_motion_v2
```

The v2 profile uses per-template camera choices:

| Template | Camera choices |
|---|---|
| drop | `orbit_left_24`, `orbit_right_24`, `orbit_left_28`, `orbit_right_28` |
| collision | `strafe_left_050`, `strafe_right_050`, `orbit_left_24`, `orbit_right_24` |
| roll | `strafe_left_050`, `strafe_right_050`, `orbit_left_24`, `orbit_right_24` |
| containment | `orbit_left_18`, `orbit_right_18`, `orbit_left_20`, `orbit_right_20`, `strafe_left_050`, `strafe_right_050` |

This avoids the known v1 failure modes:

- no dolly for roll;
- no orbit 28 for collision;
- no orbit 24 / 28 for containment.

## v2 Plan

Local dry-run passed:

- `drop:3`
- `collision:3`
- `roll:2`
- `containment:2`
- no stress / reobserve camera variants;
- no roll dolly variants;
- no containment orbit 24 / 28 variants.

Planned rows:

- drop: `orbit_left_24`, `orbit_right_24`, `orbit_left_28`
- collision: `strafe_left_050`, `strafe_right_050`, `orbit_left_24`
- roll: `strafe_left_050`, `strafe_right_050`
- containment: `orbit_left_18`, `orbit_right_18`

## v2 Actual

Not run.

The remote SSH control plane repeatedly timed out or reset while syncing code/config to the TDW helper worktree. No v2 actual TDW command was launched, and no v2 HDF5 / MP4 / NPY was generated.

## 50 Readiness

No.

The v2 10-sample actual smoke must run and achieve:

- acceptance >= 8 / 10;
- at least one accepted sample per template;
- no systematic `too_static` or `too_extreme` failure.

Only then should a 50-sample approval request be written.

## Safety

- No training.
- No DPO.
- No VideoGPA `03_train`.
- No Stage1.
- No reward calibration.
- No 50 / 200 / 1k.
- No generated assets committed.
- No `local_assets` committed.

## Next Action

When SSH is stable, continue from:

1. sync the v2 code/config to the remote helper worktree;
2. run the v2 10-sample plan on the remote;
3. run the approved GPU0 `DISPLAY=:8` v2 10-sample smoke;
4. validate and convert only accepted samples.
