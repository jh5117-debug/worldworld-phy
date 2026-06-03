# Final Report: TDW Display GPU Routing

## 1. Display Audit

Current TDW display:

- `DISPLAY=:8`
- process: `/usr/lib/xorg/Xorg :8 -config /etc/X11/tdw-xorg-gpu0.conf ...`
- bound GPU: GPU0
- config: `/etc/X11/tdw-xorg-gpu0.conf`

No GPU6/7 Xorg display was found.

Other available displays:

- `:9`
- `:10`
- `:11`
- `:12`
- `:13`

These are Xvfb displays. `DISPLAY=:9 glxinfo -B` reports Mesa llvmpipe, so they are software framebuffer displays and not GPU6/7 displays. They do not yet prove TDW/Unity can run in safe CPU/headless mode.

## 2. Guard Implementation

Updated:

- `configs/cam_physgeo/tdw_generation_v2.yaml`
- `cam_physgeo/data/tdw_generation_v2/run_tdw_trial.py`
- `scripts/31_run_tdw_generation_v2_smoke.sh`

Added parameters:

- `--display`
- `--allowed_gpu_ids`
- `--require_allowed_gpu_display`
- `--dry-run-display-check`
- `--no_run_if_display_gpu_mismatch`
- `--allow_unapproved_gpu`
- `--gpu_confirmation_token`

Mismatch behavior:

- display GPU outside `allowed_gpu_ids` -> block before Unity starts;
- unknown display GPU with `--require_allowed_gpu_display` -> block;
- GPU0 use requires explicit user approval plus confirmation token.

Metadata logged:

- display;
- detected display GPU;
- display detection details;
- allowed GPU IDs;
- blocked reason;
- full command.

## 3. Generation

No 1-sample generation was run.

Reason: no GPU6/7 display exists, and current GPU0-bound display is not approved. Xvfb displays exist but TDW/Unity CPU/headless generation is not confirmed safe.

No HDF5, MP4, or contact sheet was generated.

## 4. GPU Usage

GPU0 would be required for current `DISPLAY=:8`. GPU6/7 are idle, but no GPU6/7 TDW display exists.

User approval is needed before either:

- using GPU0 for exactly one sample; or
- configuring a GPU6/7 display.

## 5. Next Action

Choose one:

1. approve GPU0 for a single `warmup_mild` TDW smoke sample;
2. configure/provide a GPU6/7 TDW display;
3. pause TDW generation and keep only plan/wrapper validation.

Do not run 10/50 samples until one-sample actual generation passes and the user confirms the next stage.

## GPU0 Approval Follow-Up

The user later approved exactly one GPU0-bound 1-sample smoke. The display guard accepted the approval token, but the command failed before TDW/Unity generated a scene due runtime-wrapper startup issues. No data was generated, and no 10/50 stage was started.
