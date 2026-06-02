# GitHub Push Report: 1-Pair Overfit Mini-Loop

## Branch

- Branch: `physion-dpo-1pair-overfit-miniloop`
- Commit containing smoke code/results before this push-report file was added:
  `c5fa28d3c4c2b1a89950a2ecc0f62044aa3d69b9`
- Final pushed branch tip is the commit containing this report; verify with
  `git log -1 --oneline physion-dpo-1pair-overfit-miniloop`.
- Remote: `origin`
- Remote URL: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`

Remote integrity correction: this branch was missing from the correct
user-visible repository until the remote was checked against
`jh5117-debug/worldworld-phy` and pushed explicitly. Future push checks must run:

```bash
git remote -v
git ls-remote --heads origin
```

Do not push this branch to `world_model_phys.git`.

## Scope Committed

Committed code/docs only:

- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`
- `docs/current_state_before_dpo_1pair_overfit_miniloop.md`
- `docs/prior_art_dpo_overfit_miniloop_review.md`
- `docs/final_report_1pair_overfit_miniloop.md`
- `docs/stage2_videogpa_dpo_plan.md`
- `docs/github_push_report_1pair_overfit_miniloop.md`

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
- Remote `compileall` with LingBot conda Python: passed.
- Remote pytest was not available in the LingBot conda environment (`No module named pytest`), so local pytest result is the recorded test validation.
- Remote 1-pair / 5-step mini-loop: passed.

## Remote Smoke Output

Remote worktree:

`/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_1pair_overfit_miniloop_work`

Remote output path, not committed:

`local_assets/outputs/smoke/lingbot_dpo_1pair_overfit_miniloop/`

Summary:

- `success=true`
- `steps_completed=5`
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

Initial branch push succeeded. This report was then included in an amended
branch-tip commit and pushed with `--force-with-lease`.
