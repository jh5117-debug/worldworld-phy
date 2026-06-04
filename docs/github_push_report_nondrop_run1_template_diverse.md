# GitHub Push Report: Non-Drop `--run 1` Template-Diverse Gate

Date: 2026-06-04

## Branch

`physion-nondrop-run1-template-diverse`

## Remote

`ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`

## Commit Message

`Record non-drop TDW run1 template gate result`

## Scope Pushed

Docs only:

- `docs/current_gate_board_before_nondrop_run1_retry.md`
- `docs/tdw_generation_v2_nondrop_run1_command_dryrun_report.md`
- `docs/tdw_generation_v2_nondrop_3sample_run1_report.md`
- `docs/tdw_generation_v2_template_diverse_10_run1_report.md`
- `docs/tdw_generation_v2_template_diverse_10_run1_conversion_report.md`
- `docs/tdw_video_deliverables_template_diverse_run1_update_report.md`
- `docs/final_report_nondrop_run1_template_diverse.md`
- `docs/gpu_usage_approval_request_tdw_template_diverse_50.md`
- `docs/PRD_physion_tdw_camphysgeo_dpo.md`
- `docs/stage2_videogpa_dpo_plan.md`
- `docs/physion_tdw_large_scale_generation_plan.md`
- `docs/tdw_physion_movingcam_v2_generation_spec.md`

## Excluded

Not committed:

- `local_assets/`
- generated HDF5 / h5
- generated MP4
- NPY / NPZ
- contact sheets
- large logs
- weights
- latents
- checkpoints
- LoRA
- third-party raw repositories

## Verification

- No code changes were needed in this commit; the `--run 1` code fix was already present in the base branch.
- Staged files were markdown only.
- The template-diverse 10 and 50-sample generations were not run.

