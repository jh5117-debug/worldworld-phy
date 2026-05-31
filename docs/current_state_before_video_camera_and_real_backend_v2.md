# Current State Before Video Camera And Real Backend V2

## Context

- Remote execution worktree used for smoke runs: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_min_adapter_work`.
- Helper `local_assets` points at the project-local asset tree under `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets`.
- No data, weights, checkpoints, HDF5, MP4, NPY/NPZ, or safetensors were moved or deleted.
- Previous branch baseline: `physion-camera-effect-reward-real-backend`.

## Prior Results

- Camera/control tensor changes with camera variant: yes.
- DiT camera scale/shift path: source path confirmed in LingBot-Fast.
- Video-level camera effect: not proven before this round because the previous 4-frame ablation is invalid for the LingBot-Fast temporal latent path and failed with a negative temporal dimension.
- Known legal generation setting: 8 frames, 1 step. This setting already produced 1-sample inference and 3 Fast rollouts.
- Reward v3 fixed the clean/Fast ordering on the 3 rollout smoke samples:
  - clean avg: `0.9996`
  - Fast avg: `0.8796`
  - clean > Fast: `3/3`
  - confidence-weighted clean: `0.9828`
  - confidence-weighted Fast: `0.2175`
- Reward is still not DPO-ready because generated Fast-side feature/flow/depth backends were not all real.
- Optical flow before this round: Farneback fallback only in reward reports, despite local RAFT assets.
- DINOv2 before this round: directory exists but no checkpoint; no forward.

## Gates Before This Round

- Gate A: passed. LingBot-Fast 1-sample inference works.
- Gate B: passed. Three Fast rollout smoke videos exist.
- Gate C: partial. Embedding/control and DiT path pass; video-level effect not proven.
- Gate D: partial. Reward ordering fixed, but Fast-side real backends missing.
- Gate E: VideoGPA encode not allowed.
- Gate F: DPO not allowed.
