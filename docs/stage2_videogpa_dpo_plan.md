# Stage2 VideoGPA DPO Plan

Do not train yet. This project remains Physion-only, Fast-first, camera-conditioned, and no-action except for dummy compatibility files.

## Current Gate State

- Gate A: LingBot-Fast 1-sample actual inference passed.
- Gate B: 3-10 Fast rollout smoke is being validated by the rollout/reward autoloop.
- Gate C: camera condition ablation is being validated with correct/frozen/reversed poses.
- Gate D: reward-on-real-Fast-rollout is being validated after the small rollout set exists.
- Gate E: VideoGPA encode smoke is not allowed in the current phase.
- Gate F: LingBotFastVideoGPAAdapter winner/loser batch shape dry-run is not allowed in the current phase.
- Gate G: real DPO energy/logprob adapter is not wired and remains blocked.

## Why DPO Training Is Still Blocked

1. Small Fast rollout quality and failure modes must be inspected before pair generation grows.
2. Camera ablation must show whether poses/intrinsics materially affect generation. If correct/frozen/reversed look the same, the camera adapter must be fixed first.
3. Reward must separate clean GT from real Fast rollout failures, not only artificial corrupted negatives.
4. Feature backends must be reported honestly: DINO/V-JEPA/VideoMAE/flow may still be proxy or fallback in parts of the current reward path.
5. VideoGPA encode has not been run in this phase and should wait until Gates B-D are understood.
6. `LingBotFastVideoGPAAdapter.compute_dpo_energy_or_logprob` must not be faked.

Only after Gates B, C, and D are reasonably passed should a future round attempt VideoGPA encode smoke. DPO training remains disallowed until all gates A-G pass.

## Camera / Reward Debug Update

- Gate A: passed.
- Gate B: passed at small-smoke level with 3 Fast rollouts.
- Gate C: not proven. Camera tensors reach `WanI2VFast.generate` through `action_path`, and LingBot-Fast source builds `c2ws_plucker_emb`, but strong ablation did not produce enough successful variants to show output differences above stochastic baseline.
- Gate D: failed / not reliable. Raw reward still ranks Fast above clean GT. Confidence-aware aggregation lowers absolute scores and marks rows provisional, but it still wins only 1/3 pairs.
- Gate E: VideoGPA encode remains not allowed.
- Gate F: adapter batch shape work remains deferred.
- Gate G: real DPO energy/logprob remains unimplemented.

Next gate is not VideoGPA. The next minimal work is camera embedding instrumentation plus reward backend repair.

## Plucker / Reward Backend Debug Update

- Gate A: passed.
- Gate B: passed at 3-rollout smoke level.
- Gate C: partial. Direct probe of LingBot's actual `get_plucker_embeddings` path shows correct/frozen/reversed/exaggerated camera variants produce different `c2ws_plucker_emb` control tensors. This proves camera condition reaches the model-side embedding. Video-level effect is still not proven because the same-seed ablation set did not complete.
- Gate D: failed / not reliable. V2 reward aggregation now marks all proxy/missing components as low confidence and adds real-backend-only totals, but no real backend is active for clean or Fast in the rollout scorer. Raw and proxy totals still rank Fast above clean.
- Gate E: VideoGPA encode remains not allowed.
- Gate F: adapter batch-shape work remains deferred.
- Gate G: real DPO energy/logprob remains unimplemented.

Next minimal work before VideoGPA is either: finish a small video-level camera ablation after GPU 6/7 are free, or wire real reward backends for clean GT depth/ID/camera/object-state and generated rollout feature/flow.

## Camera Effect / Reward Real Backend Update

- Gate A: passed.
- Gate B: passed with 3 Fast rollout smoke videos.
- Gate C: partial. Camera/control tensors differ across camera variants and source-level DiT camera scale/shift injection is present. Runtime full-DiT scale/shift tensors were not captured, and video-level effect is still not proven because the 4-frame ablation is invalid for the current LingBot-Fast temporal latent path.
- Gate D: partial. Clean GT real metadata backend is active for depth, ID mask, camera, intrinsics, and object-state metadata. Reward v3 ranks clean above Fast on 3/3 pairs, but Fast rollout scoring remains fallback/proxy because generated-video DINO/flow/depth are not real yet.
- Gate E: VideoGPA encode remains not allowed.
- Gate F: LingBotFastVideoGPAAdapter batch shape work remains deferred.
- Gate G: real DPO energy/logprob remains unimplemented.

Next minimal work remains outside VideoGPA: run a valid 8-frame video-level camera ablation, wire real optical-flow forward from local RAFT assets, and add DINOv2-small only after user approval.

## Video Camera / Flow / DINO Smoke Update

- Gate A: passed.
- Gate B: passed with 3 Fast rollout smoke videos.
- Gate C: partial/pass. Embedding-level and DiT camera path remain confirmed. The valid 8-frame ablation completed at 256x448: same-seed repeat difference was `0.0`, frozen matched correct, and exaggerated-yaw produced nonzero output difference (`pixel_l1=0.02547`). This proves a strong camera perturbation can affect video output, but ordinary camera sensitivity still needs stronger/longer validation.
- Gate D: partial. Clean GT real backend remains active. RAFT-small real optical-flow forward now works and contributes to Fast rollout `bg`/`cam` real components. DINOv2-small is still missing, so `fg`/`reobs` feature terms remain proxy/fallback and reward is not DPO-ready.
- Gate E: VideoGPA encode remains not allowed until camera video effect and reward backends are both reliable.
- Gate F: LingBotFastVideoGPAAdapter batch-shape work remains deferred.
- Gate G: real DPO energy/logprob remains unimplemented.

Next minimal work is still not VideoGPA: add DINOv2-small after approval and re-run reward-on-rollout with both real flow and real feature backends.

## DINO Reward V5 / Camera Stress Update

- Gate A: passed.
- Gate B: passed.
- Gate C: pass/partial. A high-yaw stress sample was selected (`physion_movingcam_13db379640ce`). The 8-frame 480x832 stress ablation generated all six variants. Same-seed repeat stayed `0.0`; reversed, exaggerated-yaw, and exaggerated-translation diverged from repeat baseline. Frozen still matched correct.
- Gate D: partial/pass for smoke. DINOv2-small was downloaded to `local_assets/weights/dinov2/dinov2_vits14/` and forwards successfully. Reward v5 uses clean GT metadata, RAFT real flow, and DINO real features; clean > Fast remains `3/3`.
- Gate E: VideoGPA encode smoke may be considered next, but only encode smoke. Do not train.
- Gate F: DPO remains not allowed.
- Gate G: real DPO energy/logprob remains unimplemented.

Next permitted step is VideoGPA encode smoke only. DPO training is still blocked.

## VideoGPA Encode Smoke Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass. Stress camera perturbations have video-level effect, but ordinary frozen/correct remains weak.
- Gate D: partial/pass for smoke. Reward v5 provides a usable smoke-level clean > Fast signal with RAFT and DINO active, but generated depth/mask/physics are still not complete.
- Gate E: partial. VideoGPA pair export and encode-readiness smoke passed for `gt_vs_fast` metadata/video readability, and camera sidecars were preserved. Native latent encode did not run because LingBot-Fast VAE/condition encoding is not wired into VideoGPA.
- Gate F: still no. DPO remains blocked.
- Gate G: still no. `compute_dpo_energy_or_logprob` is intentionally `NotImplementedError`.

Next minimal step is not training. It is a LingBot-Fast VideoGPA adapter dry-run that implements real LingBot VAE latent encode, same-noise/same-timestep batch collation, and a non-fake energy/logprob path.
