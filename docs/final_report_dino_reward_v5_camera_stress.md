# Final Report: DINO Reward V5 Camera Stress

## Gates

- Gate A: passed. LingBot-Fast 1-sample inference works.
- Gate B: passed. Three Fast rollout smoke videos exist.
- Gate C: pass/partial. Embedding-level and DiT path are confirmed, and high-yaw 8-frame stress ablation shows video-level differences for reversed and exaggerated camera variants. Frozen still matches correct in this short sample.
- Gate D: partial/pass for smoke. Clean real backend, RAFT real flow, and DINOv2 real feature backend are active; generated depth/mask physics remains fallback.
- Gate E: next-round VideoGPA encode smoke can be considered, but was not run.
- Gate F: DPO remains not allowed.

## Execution Context

- Remote worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_min_adapter_work`
- Local branch for commit: `physion-dino-reward-v5-camera-stress`
- `local_assets` in helper worktree points to the project-local asset tree.
- No original data, LingBot weights, Physion assets, HDF5, MP4, or NPY files were moved or deleted.
- DINOv2-small checkpoint was downloaded into `local_assets/weights/dinov2/dinov2_vits14/` and is not committed.
- Generated ablation videos and contact sheets stayed under `local_assets/` and are not committed.

## Camera Stress Sample Selection

- Selected sample: `physion_movingcam_13db379640ce`
- Camera motion: `relative_yaw_180_reobserve`
- Template: `drop`
- Translation magnitude: `0.0`
- Trajectory length: `0.0`
- Rotation magnitude: `2.1636307710103373` rad
- Yaw proxy: `2.1464942232960413` rad

This was chosen because it has the largest yaw/rotation stress among the processed smoke samples.

## Camera Stress Ablation

- Variants: repeat A, repeat B, frozen, reversed, exaggerated yaw, exaggerated translation.
- Generated videos: `6/6`
- Resolution: `480x832`
- Frames/steps: `8 / 1`
- Contact sheet: `local_assets/data/physion/processed/rollouts/camera_ablation_stress_v2/physion_movingcam_13db379640ce/comparison_contact_sheet.jpg`
- Repeat baseline: `0.0`
- Correct vs frozen pixel L1: `0.0`
- Correct vs reversed pixel L1: `0.022175125777721405`
- Correct vs exaggerated yaw pixel L1: `0.03501671180129051`
- Correct vs exaggerated translation pixel L1: `0.03765185922384262`

Camera video-level effect is demonstrated for reversed/exaggerated stress variants beyond the repeat baseline. Frozen/correct remains identical in this short setting, so normal camera-effect strength still needs longer-frame validation before DPO.

## DINOv2 Backend

- Checkpoint found before run: no.
- Downloaded: yes, only DINOv2-small `dinov2_vits14`.
- Checkpoint path: `local_assets/weights/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth`
- Size: `88283115` bytes.
- Forward: success.
- Feature shape: `[1, 384]` in backend smoke; `[4, 384]` in reward component smoke.
- CUDA memory for backend smoke: `127773696` bytes.

## DINO Reward Component

- R_fg uses `real_dino_id_mask` when clean ID mask is present.
- R_reobs uses `real_dino_reobserve_proxy_segments`.
- Generated-video mask/segment localization is still proxy, so confidence is intentionally below perfect.
- This is enough to stop treating R_fg/R_reobs as missing, but not enough to call the full reward DPO-ready.

## Reward V5

- Clean avg: `0.9996457055610642`
- Fast avg: `0.7489099937650526`
- Clean > Fast: `3/3`
- Confidence-weighted clean avg: `0.982798850450035`
- Confidence-weighted Fast avg: `0.4563076715854179`
- Real-backend-only clean avg: `1.0`
- Real-backend-only Fast avg: `0.7112765284109178`
- Flow+DINO-only clean avg: `1.0`
- Flow+DINO-only Fast avg: `0.7112765284109178`
- Fast real components: `bg`, `cam`, `fg`, `reobs`
- Fast fallback components: `phys`, `quality`, `freeze`

Reward v5 no longer has the earlier reverse-ranking failure and now uses both real RAFT flow and real DINOv2 features. Pair selection is still provisional because generated depth/object-mask physics remains fallback.

## Allow Next Steps?

- VideoGPA encode: yes for a small smoke in the next round, if it remains encode-only and no DPO training is started.
- DPO: no.

## Next Minimal Actions

1. Run VideoGPA encode smoke only, not training.
2. Keep DPO blocked until generated depth/mask or physics-event reliability improves.
3. If camera confidence needs strengthening, run a longer fixed-noise ablation focused on frozen vs correct.
4. Improve generated object mask/track propagation so R_fg/R_reobs can use real DINO with better masks.
