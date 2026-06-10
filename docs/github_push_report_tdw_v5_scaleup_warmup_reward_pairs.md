# GitHub Push Report: TDW v5 Scale-Up / Warmup / Reward Pair Gates

Date: 2026-06-10

Branch:

`physion-tdw-v5-scaleup-warmup-reward-pairs`

Commit message:

`Run TDW v5 warmup rollout reward pair pipeline gates`

Scope:

- added adapter checkpoint loading for LingBot-Fast inference;
- added base-vs-adapter rollout wrapper;
- added rollout reward scoring wrapper;
- added reward-based pair construction wrapper;
- added gate reports and approval requests.

Excluded:

- `local_assets/`;
- HDF5/MP4/NPY;
- rollouts;
- reward outputs;
- pair outputs under `local_assets`;
- checkpoints/LoRA weights;
- optimizer state;
- large logs.
