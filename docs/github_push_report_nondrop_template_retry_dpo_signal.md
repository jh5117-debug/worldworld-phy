# GitHub Push Report: Non-Drop Template Retry and DPO Signal

Date: 2026-06-04

## Branch

`physion-nondrop-template-retry-dpo-signal`

## Remote

`ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`

## Commit Message

`Retry non-drop TDW templates and DPO signal gate`

## Scope Pushed

Code:

- `cam_physgeo/data/tdw_generation_v2/run_tdw_trial.py`

Docs:

- `docs/current_gate_board_before_nondrop_template_retry.md`
- `docs/tdw_generation_v2_nondrop_command_dryrun_report.md`
- `docs/tdw_generation_v2_nondrop_3sample_actual_report.md`
- `docs/tdw_generation_v2_template_diverse_10_retry_report.md`
- `docs/tdw_generation_v2_template_diverse_10_retry_conversion_report.md`
- `docs/tdw_video_deliverables_template_diverse_retry_update_report.md`
- `docs/dpo_signal_sensitivity_fast_retry_report.md`
- `docs/final_report_nondrop_template_retry_dpo_signal.md`
- `docs/5pair_tiny_overfit_go_nogo.md`
- `docs/gpu_usage_approval_request_tdw_template_diverse_50.md`
- `docs/PRD_physion_tdw_camphysgeo_dpo.md`
- `docs/stage2_videogpa_dpo_plan.md`
- `docs/physion_tdw_large_scale_generation_plan.md`
- `docs/tdw_physion_movingcam_v2_generation_spec.md`

## Excluded

The following were not staged or pushed:

- `local_assets/`
- generated TDW HDF5 / h5
- generated MP4
- NPY / NPZ
- contact sheets
- large logs
- model weights
- latents
- checkpoints
- LoRA files
- third-party raw repositories

## Verification

- `python -m compileall -q cam_physgeo/data/tdw_generation_v2` passed.
- Cached diff consisted only of code/docs.
- `git diff --cached --name-only | xargs -r du -h | sort -h | tail -50` showed only small source and markdown files.

## Notes

The TDW actual retry did not pass validation. The wrapper fix adds upstream `--run 1`, but the fixed command has not been rerun because the approved actual TDW smoke was already consumed.

