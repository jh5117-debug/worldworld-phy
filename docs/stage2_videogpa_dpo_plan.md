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
