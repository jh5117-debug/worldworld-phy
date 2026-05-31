# Final Report: Camera Effect And Reward Real Backend

## Execution Context

- Remote execution worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_min_adapter_work`
- Remote execution branch at run time: `physion-fast-rollout-reward-autoloop`
- Remote execution commit at run time: `5a4eefbd6f5a42968c5cc8a4977def99535d27b7`
- Commit/push branch for this code/doc update: `physion-camera-effect-reward-real-backend`
- `local_assets` in the helper worktree is a symlink to `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets`
- No data, generated videos, HDF5, NPY/NPZ, checkpoints, or weights were moved or deleted.
- Generated smoke outputs stayed under `local_assets/` and are not part of git.

## Gates

- Gate A: passed. LingBot-Fast 1-sample inference already works.
- Gate B: passed. Three Fast rollout smoke videos already exist.
- Gate C: partial. Embedding/control tensor and source-level DiT modulation path are confirmed, but video-level camera effect is still not proven.
- Gate D: partial. Clean GT real backend is now active and reward v3 ranks clean above Fast on 3/3, but Fast rollout scoring is still proxy/fallback-heavy.
- Gate E: not allowed. VideoGPA encode should wait.
- Gate F: not allowed. DPO remains blocked.

## DiT Modulation Probe

The probe found the intended camera path in LingBot-Fast:

- `image2video_fast.py` builds `c2ws_plucker_emb`.
- `image2video_fast.py` passes `c2ws_plucker_emb` through `dit_cond_dict`.
- `model_fast.py` defines `cam_injector_layer1/2`, `cam_scale_layer`, and `cam_shift_layer`.
- `model_fast.py` applies camera scale/shift to hidden states.

Runtime action scale/shift tensors were not captured because this probe did not load the full Fast DiT in a no-generation hook. Source-level modulation is confirmed; runtime tensor capture remains a follow-up.

Camera/control tensor variants differ:

- correct vs frozen L2: `12.8458`
- correct vs reversed L2: `25.6122`
- correct vs exaggerated_yaw L2: `83.0763`
- dummy action norm: `0.0`

## Video-Level Camera Effect

The minimal 4-frame video ablation failed before producing videos. LingBot-Fast computed a negative latent temporal dimension for `frame_num=5` in `wan/image2video_fast.py:323`. One retry also hit CUDA OOM during model transfer due another process holding GPU memory.

Therefore video-level effect is still not proven. The next attempt should use a known-valid frame count, likely 8 frames, and a clean GPU allocation.

## Clean GT Real Backend

For the 3 checked clean samples:

- Processed depth: available.
- Processed ID mask: available.
- Camera pose and intrinsics metadata: available.
- Object-state metadata: available.
- HDF5 path: present.

Direct HDF5 traversal from the LingBot env is blocked by missing `h5py`, but the processed Physion-derived assets are sufficient for current clean-side real backend scoring.

## Optical Flow Backend

- RAFT assets exist under `local_assets/weights/optical_flow/RAFT`.
- Real learned flow forward is not wired.
- Low-res OpenCV Farneback fallback runs and returns shape `[1, 256, 448, 2]`.
- R_bg, R_cam, and P_freeze must remain provisional until RAFT/GMFlow/WAFT forward is wired.

## DINOv2 Backend

- `local_assets/weights/dinov2` exists but contains no checkpoint.
- DINOv2 forward is unavailable.
- Recommended small checkpoint: `dinov2_vits14`.
- Download should go to `local_assets/weights/dinov2` only after user approval.

## Reward V3

- Raw clean avg: `0.9996`
- Raw Fast avg: `0.8796`
- Raw clean > Fast win rate: `1.0`
- Confidence-weighted clean avg: `0.9828`
- Confidence-weighted Fast avg: `0.2175`
- Real-backend-only clean avg: `1.0`
- Real-backend-only Fast avg: `0.0`

The reversal is fixed for the 3-sample smoke by clean-side real metadata and confidence-aware aggregation. The reward is still not DPO-ready because Fast rollout side lacks real generated-video feature/flow/depth backends.

## Allow Next Steps?

- VideoGPA encode: no. Camera video-level effect is not proven and reward is still provisional.
- DPO: no.

## Next Minimal Actions

1. Run a clean 8-frame camera ablation with `repeat_correct_A`, `repeat_correct_B`, `frozen`, and `exaggerated_yaw`.
2. Wire real RAFT/GMFlow/WAFT forward using the existing optical-flow assets.
3. Add DINOv2-small checkpoint and forward path after user approval.
4. Re-run reward-on-rollout only after flow and DINO backends are real.

## Follow-Up Update: 8F Camera / Flow / DINO Smoke

- The valid 8-frame camera ablation completed at 256x448 after 480x832 hit GPU-memory pressure.
- Same-seed repeat difference was `0.0`; frozen matched correct; exaggerated-yaw produced nonzero output difference (`pixel_l1=0.02547`).
- RAFT-small real optical-flow forward now succeeds from `local_assets/weights/optical_flow/RAFT/models/raft-small.pth`.
- Flow smoke shape: `[1, 256, 448, 2]`; mean/std/max magnitude: `7.4475 / 4.0387 / 27.3030`.
- Reward v4 ranks clean above Fast on 3/3 with Fast-side bg/cam real flow components active.
- DINOv2 remains missing, so R_fg/R_reobs are not DPO-ready.
