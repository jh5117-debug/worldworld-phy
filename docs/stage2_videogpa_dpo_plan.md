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
