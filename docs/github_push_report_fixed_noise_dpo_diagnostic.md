# GitHub Push Report: Fixed-Noise DPO Diagnostic

## Branch

- Branch: `physion-dpo-fixed-noise-diagnostic`
- Base branch: `physion-dpo-1pair-overfit-miniloop`
- Final pushed commit: this report commit; verify with `git rev-parse HEAD` after checkout.
- Remote: `origin`
- Remote URL: `ssh://git@ssh.github.com:443/jh5117-debug/world_model_phys.git`

## Scope Committed

Committed code/docs only:

- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`
- `docs/current_state_before_fixed_noise_dpo_diagnostic.md`
- `docs/prior_art_fixed_noise_dpo_diagnostic_review.md`
- `docs/final_report_fixed_noise_dpo_diagnostic.md`
- `docs/github_push_report_fixed_noise_dpo_diagnostic.md`
- `docs/stage2_videogpa_dpo_plan.md`

Not committed:

- `local_assets/`
- optimizer outputs
- gradient tensors
- encoded latents
- generated videos
- energy tensors
- HDF5/MP4/NPY/NPZ/PT/PTH/safetensors
- saved LoRA weights
- checkpoints
- third-party raw repos

## Validation

- Local `python -m compileall -q cam_physgeo`: passed.
- Local `PYTHONPATH=. pytest -q tests/test_lora_utils.py tests/test_reward_confidence.py`: `7 passed`.
- Remote 1-pair fixed-noise/fixed-timestep diagnostic: passed.

## Remote Smoke Output

Remote worktree:

`/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_fixed_noise_diagnostic_work`

Remote output path, not committed:

`local_assets/outputs/smoke/lingbot_dpo_1pair_overfit_miniloop_fixed_noise/`

Summary:

- `success=true`
- `steps_completed=10`
- fixed noise seed: `123`
- fixed timestep: `579`
- LoRA target modules: `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`
- LoRA rank/alpha: `2 / 4.0`
- LoRA params changed: yes
- Base params changed: no
- Reference params changed: no
- NaN/Inf: no
- OOM: no
- LoRA/checkpoint saved: no
- GPU 6/7 after run: idle, `1 MiB`, `0%`

## Push Status

Initial branch push succeeded. This report is included in the final amended branch-tip commit and pushed with `--force-with-lease`.
