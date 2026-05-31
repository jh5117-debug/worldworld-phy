# Current State Before Plucker / Reward Backend Debug

- Execution worktree for H20 probes: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_min_adapter_work`.
- Local branch for this round: `physion-plucker-reward-backend-debug`.
- Remote helper worktree branch before sync: `physion-fast-rollout-reward-autoloop`, commit `5a4eefbd6f5a42968c5cc8a4977def99535d27b7`.
- `local_assets` in the helper worktree points to the same project-local data/weights root; no assets were moved or deleted.

## Prior Results

- 3 Fast rollouts already exist under `local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke`.
- Camera path audit conclusion from the prior round: `poses.npy` and converted `(F,4)` intrinsics are written to `lingbot_condition/`, then passed as `action_path` to `WanI2VFast.generate`.
- LingBot-Fast source constructs `c2ws_plucker_emb` from `poses.npy` and `intrinsics.npy`, and injects it into the Fast DiT.
- Dummy `action.npy` is all zero; `use_action=false` is preserved in metadata.
- Strong video camera ablation did not complete enough variants: only `correct` at low resolution completed, so there is no stochastic baseline and no reliable correct/frozen/reversed/exaggerated video comparison.
- Raw reward-on-rollout remains reversed: clean avg `0.5949`, Fast avg `0.8796`, clean > Fast win rate `0.0`.
- Previous confidence-weighted reward improved reporting but was still not reliable; clean won only `1/3` in the prior report.
- DINOv2 has no local checkpoint, V-JEPA is path-present but not forwarded, and optical flow is not wired into reward scoring.

## Gate State

- Gate A: Fast 1-sample actual inference passed.
- Gate B: 3 Fast rollout smoke passed.
- Gate C: camera condition effect not proven.
- Gate D: reward-on-rollout not reliable.
- Gate E: VideoGPA encode not allowed.
- Gate F: DPO not allowed.

This round should only probe camera embeddings and repair reward confidence aggregation. It should not run training, DPO, VideoGPA encode, Stage1, or large rollout/reward jobs.
