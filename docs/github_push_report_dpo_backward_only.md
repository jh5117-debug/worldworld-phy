# GitHub Push Report: DPO Backward-Only

## Branch

- Branch: `physion-dpo-backward-only-dryrun`
- Commit: branch HEAD after the final push.
- Commit message: `Add 1-pair DPO backward-only dry-run`

## Push

- Push status: success. The first push created the branch, then the commit was
  amended to include this push report and force-pushed to the same branch.
- Remote branch: `origin/physion-dpo-backward-only-dryrun`
- Remote URL used by local repo: `ssh://ssh.github.com:443/jh5117-debug/worldworld-phy.git`
- Pull request URL suggested by remote:
  `https://github.com/jh5117-debug/worldworld-phy/pull/new/physion-dpo-backward-only-dryrun`

## Submitted Files

- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`
- `docs/current_state_before_dpo_backward_only.md`
- `docs/prior_art_dpo_backward_lora_review.md`
- `docs/lingbot_trainable_scope_report.md`
- `docs/lingbot_dpo_backward_only_dryrun_report.md`
- `docs/final_report_dpo_backward_only.md`
- `docs/stage2_videogpa_dpo_plan.md`
- `docs/physion_tdw_large_scale_generation_plan.md`

## Exclusions Confirmed

No `local_assets/`, generated videos, encoded latents, HDF5, NPY, NPZ, PT, PTH,
safetensors, DINO weights, large logs, outputs, or third-party raw repositories
were staged or committed.

## Verification

- `python -m compileall -q cam_physgeo`: passed.
- `PYTHONPATH=. pytest -q tests/test_reward_confidence.py`: passed, `4 passed`.
