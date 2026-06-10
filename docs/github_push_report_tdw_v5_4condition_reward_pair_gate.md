# GitHub Push Report: TDW v5 4-Condition Reward Pair Gate

Date: 2026-06-10

Branch:

`physion-tdw-v5-4condition-reward-pair-gate`

Base branch:

`physion-tdw-v5-4condition-rollout-smoke`

Commit message:

`Score 4-condition rollout and build reward pair gate`

Scope staged for Git:

- `cam_physgeo/rewards/score_rollouts.py`
- `cam_physgeo/dpo/build_reward_pairs.py`
- `docs/*.md`

Excluded from Git:

- `local_assets/`
- rollout videos
- reward output JSON/CSV files
- pair output files
- logs
- checkpoints / LoRA weights
- HDF5 / MP4 / NPY / NPZ / PT / PTH / safetensors / latents

Validation:

- `python -m py_compile cam_physgeo/rewards/score_rollouts.py cam_physgeo/dpo/build_reward_pairs.py`
- `git diff --check`

Result:

The 4-condition reward scoring gate was documented. Reward pair construction is blocked because backend confidence is below threshold, so no DPO-ready pairs were built.

Safety:

- no training;
- no DPO;
- no VideoGPA `03_train`;
- no Stage1;
- no new TDW generation;
- no new LingBot rollout;
- no reward calibration;
- no `local_assets` committed.
