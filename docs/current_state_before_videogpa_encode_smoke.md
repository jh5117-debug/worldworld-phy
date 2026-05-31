# Current State Before VideoGPA Encode Smoke

## Execution Context

- Intended remote worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_videogpa_encode_work`
- Base branch: `physion-dino-reward-v5-camera-stress`
- New branch: `physion-videogpa-encode-smoke`
- `local_assets` on the remote worktree is a symlink to `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets`.
- No assets were moved or deleted.

## Gate State

- Gate A: passed. LingBot-Fast 1-sample actual inference is working.
- Gate B: passed. Three Fast rollout smoke videos exist.
- Gate C: partial/pass. Camera embedding and DiT modulation path are confirmed, and stress camera variants change video output; ordinary frozen/correct remains weak.
- Gate D: partial/pass for smoke. Reward v5 uses clean GT metadata, RAFT flow, and DINOv2-small features; clean > Fast is `3/3`, but generated depth/mask/physics terms still have proxy/fallback parts.
- Gate E: VideoGPA encode smoke is now allowed.
- Gate F: DPO remains blocked.

## Why Encode Smoke Is Allowed

VideoGPA encode smoke is limited to pair format, video readability, prompt/image/camera sidecar preservation, and native encode compatibility inspection. This does not train, does not run `03_train.py`, and does not compute DPO loss.

## Why DPO Is Still Blocked

DPO still lacks a real LingBot-Fast latent encode path, same-noise/same-timestep batch path, and true `compute_dpo_energy_or_logprob`. Any DPO train command remains disallowed.

## Pair Sources

- Existing gt_vs_corrupt smoke pairs: `local_assets/data/physion/processed/dpo_pairs/smoke/dpo_pairs_physion_gt_vs_corrupt.jsonl`
- New gt_vs_corrupt tiny build target: `local_assets/data/physion/processed/dpo_pairs/videogpa_encode_smoke/gt_vs_corrupt_pairs.jsonl`
- New clean_gt_vs_fast target: `local_assets/data/physion/processed/dpo_pairs/videogpa_encode_smoke/gt_vs_fast_pairs.jsonl`

The requested gt_vs_corrupt tiny build with `min_margin=0.15` produced zero kept pairs on this run, so the only fully valid fresh tiny pair set was clean_gt_vs_fast with reward v5 margins.

## VideoGPA State

- Repo path: `local_assets/third_party/VideoGPA/official_repo`
- Commit: `551e63a5c2c493962f1e1d090bfa8324bf18b694`
- Native encode scripts exist for CogVideoX and Wan2.2 backends.
- Native scripts do not consume LingBot-Fast camera poses/intrinsics directly.
- Camera condition is preserved through `extra_condition` and sidecar JSON.
- Maximum encode scope this round: 1-2 pairs.
