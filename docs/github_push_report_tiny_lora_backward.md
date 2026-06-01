# GitHub Push Report: Tiny LoRA Backward

## Branch

- Branch: `physion-dpo-tiny-lora-backward`
- Commit message: `Add tiny camera-control LoRA backward-only dry-run`
- Remote URL:
  `ssh://ssh.github.com:443/jh5117-debug/worldworld-phy.git`

## Push Status

- Initial branch push: success.
- Final push after adding this report: success expected from the final
  force-with-lease push.
- Pull request URL suggested by remote:
  `https://github.com/jh5117-debug/worldworld-phy/pull/new/physion-dpo-tiny-lora-backward`

## Submitted Files

- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`
- `cam_physgeo/dpo/lora_utils.py`
- `tests/test_lora_utils.py`
- `docs/current_state_before_tiny_lora_camera_adapter.md`
- `docs/prior_art_tiny_lora_camera_adapter_review.md`
- `docs/lora_utils_implementation_report.md`
- `docs/lingbot_lora_target_inspection_report.md`
- `docs/lingbot_lora_injection_dryrun_report.md`
- `docs/lingbot_dpo_lora_backward_only_report.md`
- `docs/lingbot_dpo_backward_scope_sweep_report.md`
- `docs/stage2_videogpa_dpo_plan.md`
- `docs/final_report_tiny_lora_backward.md`
- `docs/github_push_report_tiny_lora_backward.md`

## Exclusions Confirmed

No `local_assets/`, generated videos, encoded latents, gradient tensors, HDF5,
NPY, NPZ, PT, PTH, safetensors, outputs, logs, third-party raw repositories,
LoRA weights, or checkpoints were staged or committed.

## Verification

- Local `python -m compileall -q cam_physgeo`: passed.
- Local `PYTHONPATH=. pytest -q tests/test_lora_utils.py tests/test_reward_confidence.py`:
  passed, `7 passed`.
- Remote rank-2 camera-control LoRA backward-only: passed.
- Remote trainable LoRA params: `40,960`.
- Remote params with grad: `4`.
- Remote base params with grad: `0`.
- Remote reference params with grad: `0`.
- Optimizer / step / save: none.

## Notes

Remote SSH was unstable during this round. A combined inspect/injection/backward
script was interrupted and left a fallback process; that process was stopped.
The successful result is from the explicit rank-2 target run:

`local_assets/outputs/smoke/lingbot_dpo_lora_backward_only_dryrun/rank2_explicit_late_shift_scale/grad_summary.json`
