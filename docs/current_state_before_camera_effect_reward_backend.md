# Current State Before Camera Effect / Reward Backend Work

- Local working branch: `physion-camera-effect-reward-real-backend` from `physion-plucker-reward-backend-debug`.
- Last pushed baseline commit: `3b193cda118445e982264ba8edff1f2b878b8757`.
- Intended H20 worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_min_adapter_work` because the main worktree may remain dirty from prior debug.
- `local_assets` stays project-local and is not moved or deleted.

## Prior Camera Status

- Plucker embedding changes with camera variant: yes.
- `c2ws_plucker_emb` / final control tensor is nonzero.
- Probe sample `physion_movingcam_07abddf5748b` produced control tensor shape `(1, 448, 2, 8, 14)`.
- Dummy action norm: `0.0`.
- `use_action=false` is preserved; dummy action is compatibility-only, not the core condition.
- Video-level camera effect is still not proven because prior strong ablation did not complete repeat/frozen/exaggerated videos with a stochastic baseline.

## Prior Reward Status

- Raw/proxy reward still ranked Fast above clean.
- Real-backend-only reward was `0.0` for both clean and Fast, proving that current scoring was proxy-only.
- DINOv2 checkpoint is missing from `local_assets/weights/dinov2`.
- V-JEPA path exists but does not forward.
- Optical flow has no real forward path wired into reward.

## Gates

- Gate A: LingBot-Fast 1-sample inference passed.
- Gate B: 3 Fast rollout passed.
- Gate C: embedding-level passed; DiT/source modulation and video-level effect pending.
- Gate D: reward-on-rollout not reliable; clean real backend pending.
- Gate E: VideoGPA encode not allowed.
- Gate F: DPO not allowed.
