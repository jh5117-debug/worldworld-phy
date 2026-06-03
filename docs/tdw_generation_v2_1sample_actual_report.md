# TDW Generation v2 1-Sample Actual Report

## Status

Failed before TDW/Unity sample generation. No HDF5, MP4, or contact sheet was produced.

## Reason

The user explicitly approved `DISPLAY=:8` / GPU0 for exactly one `warmup_mild` sample smoke. The display guard accepted the run with `allow_unapproved_gpu=true` and `gpu_confirmation_token_ok=true`.

The command then failed before TDW/Unity scene generation due wrapper startup issues:

1. relative wrapper path was invalid after subprocess cwd changed to the upstream TDW workspace;
2. generated wrapper source embedded JSON `false` instead of Python `False`.

Both were code-side wrapper blockers, not data validation failures.

## Planned 1-Sample Settings

- profile: `warmup_mild`
- camera set: `warmup_mild`
- allowed variants: `orbit_left_12`, `orbit_right_12`, `strafe_left_025`, `strafe_right_025`, `dolly_in_010`, `dolly_out_010`
- banned variants: lookaway/offscreen/reobserve/extreme
- output root: `local_assets/data/physion/generated_v2`

## Generated Artifacts

None. `find` found no `.hdf5`, `.h5`, `.mp4`, `.jpg`, or `.png` generated under the v2 output root for this sample.

## Validation

Validator was run after the blocked gate and found no generated HDF5 files:

- HDF5 count: 0
- validation ok count: 0
- suitable for warmup: 0

Validation report path on H20:

- `local_assets/data/physion/generated_v2/reports/validation_1sample.md`

## GPU Usage

The first display gate recorded:

- `tdw_display`: `:8`
- `tdw_display_gpu_index`: 0
- allowed GPU indices: `[6, 7]`
- user approval token: later set to `USER_CONFIRMED_UNAPPROVED_GPU`

After approval, the display guard no longer blocked GPU0. The run still failed before scene generation because of the wrapper issues above.

Follow-up display audit found Xvfb displays `:9` to `:13`, but no GPU6/7 Xorg display. `:9` uses Mesa llvmpipe and is not yet a confirmed TDW/Unity CPU/headless generation path.

## Continue To 10-Sample?

No. 10-sample smoke remains skipped until a 1-sample actual generation completes and passes validation, and until the user explicitly confirms the next stage.
