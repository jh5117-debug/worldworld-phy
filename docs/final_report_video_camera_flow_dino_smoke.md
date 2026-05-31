# Final Report: Video Camera Flow DINO Smoke

## Gates

- Gate A: passed. LingBot-Fast 1-sample inference works.
- Gate B: passed. Three Fast rollout smoke videos exist.
- Gate C: partial/pass. Camera embedding and DiT camera path are confirmed; 8-frame video ablation shows exaggerated camera affects output beyond same-seed repeat baseline, but frozen camera matched correct in this one sample.
- Gate D: partial. Clean real backend works, RAFT-small real flow now forwards and enters Fast bg/cam scoring, but DINOv2-small is still missing so feature/reobserve identity terms are not DPO-ready.
- Gate E: not allowed. VideoGPA encode should wait for DINO feature backend and a clearer camera-effect conclusion.
- Gate F: not allowed. DPO remains blocked.

## Execution Context

- Remote worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_min_adapter_work`
- Remote branch during execution: `physion-fast-rollout-reward-autoloop`
- Local commit branch: `physion-video-camera-flow-dino-smoke`
- `local_assets` in the helper worktree points to the project-local asset tree.
- No data, weights, checkpoints, or generated assets were moved or deleted.
- Generated videos, contact sheets, logs, and backend summaries stayed under `local_assets/` and are not committed.

## 8-Frame Video-Level Camera Ablation

- 480x832 attempt: OOM because GPU memory was occupied by another process.
- 256x448 fallback: completed all 4 variants.
- Variants: `repeat_correct_A`, `repeat_correct_B`, `frozen`, `exaggerated_yaw`
- Repeat baseline pixel L1: `0.0`
- Correct vs frozen pixel L1: `0.0`
- Correct vs exaggerated-yaw pixel L1: `0.02547357603907585`
- Comparison contact sheet: `local_assets/data/physion/processed/rollouts/camera_ablation_effect_8f_256/physion_movingcam_07abddf5748b/comparison_contact_sheet.jpg`

Conclusion: video-level camera effect is likely present for the deliberately exaggerated yaw variant because it exceeds same-seed stochastic baseline. Normal camera/frozen sensitivity is still not proven by this one sample.

## Optical Flow Backend

- RAFT assets found under `local_assets/weights/optical_flow/RAFT`.
- Checkpoint used: `local_assets/weights/optical_flow/RAFT/models/raft-small.pth`
- Real forward: yes
- Flow shape: `[1, 256, 448, 2]`
- Mean/std/max magnitude: `7.4475 / 4.0387 / 27.3030`
- Elapsed: `11.37s`
- CUDA allocated: about `82 MB`

This can now support minimal real-flow R_bg/R_cam/P_freeze proxies. It is not yet a full rigid-flow metric because generated depth is still missing.

## DINOv2 Backend

- Local checkpoint: missing.
- Forward: not run.
- Recommended model: `dinov2_vits14`
- Target path: `local_assets/weights/dinov2/dinov2_vits14`
- User approval required before download.

DINO absence still blocks DPO-ready R_fg and R_reobs.

## Reward V4

- Clean GT avg: `0.9996457055610642`
- Fast avg: `0.7617640182184134`
- Clean > Fast: `3/3`
- Clean confidence-weighted avg: `0.982798850450035`
- Fast confidence-weighted avg: `0.28148399796357515`
- Clean real-backend-only avg: `1.0`
- Fast real-backend-only avg: `0.47644271948215194`
- Fast real components: `bg`, `cam`
- Fast feature available only: `0.0`

Reward ordering is now sane for the 3-sample smoke, and real RAFT flow participates in generated-rollout bg/cam scoring. It is still not DPO-ready because DINO/V-JEPA feature terms are not real and generated depth is absent.

## Allow Next Steps?

- VideoGPA encode next round: no by default. Camera effect is only partial and DINO features are missing.
- DPO: no.

## Next Minimal Actions

1. If camera proof needs to be stronger, run a longer fixed-noise camera ablation with correct/frozen/exaggerated after GPU memory is clean.
2. Add DINOv2-small checkpoint only after user approval, then wire forward for R_fg and R_reobs.
3. Re-run reward-on-rollout with real flow plus DINO before considering VideoGPA encode smoke.

## Follow-Up: DINO Reward V5 / Camera Stress

- Stress sample selected: `physion_movingcam_13db379640ce`, `relative_yaw_180_reobserve`, yaw proxy `2.1465`.
- 8-frame 480x832 stress ablation generated all six variants.
- Repeat baseline stayed `0.0`; reversed pixel L1 `0.02218`, exaggerated-yaw `0.03502`, exaggerated-translation `0.03765`.
- DINOv2-small `dinov2_vits14` downloaded to `local_assets/weights/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth`, size `88283115` bytes.
- DINO forward succeeded; reward component feature shape reached `[4, 384]`.
- Reward v5 clean > Fast remained `3/3`; Fast real components now include `bg`, `cam`, `fg`, and `reobs`.
- Next round may consider VideoGPA encode smoke only. DPO remains blocked.
