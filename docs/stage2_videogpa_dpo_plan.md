# Stage2 VideoGPA DPO Plan

Do not train yet.

## Why Training Is Blocked

1. LingBot-Fast cam-only actual inference has not completed; the 1-sample smoke timed out after 180 seconds.
2. Fast zero-shot rollouts do not exist, so reward has not been validated on real Fast failures.
3. Expanded clean-vs-corrupt reward calibration dropped to 0.6033 on 50 samples, below the 0.85 gate.
4. VideoGPA encode smoke can read pair JSON and videos, but it cannot produce LingBot-compatible latents yet.
5. LingBot-Fast and VideoGPA trainer model/latent/scheduler compatibility is not confirmed.
6. `LingBotFastVideoGPAAdapter.compute_dpo_energy_or_logprob` is intentionally `NotImplementedError`.
7. Camera poses/intrinsics are preserved in metadata, but not yet part of a real VideoGPA training batch.

## Gates Before Any DPO Training

- Gate A: LingBot-Fast cam-only 1-sample short inference succeeds.
- Gate B: 10-20 Fast zero-shot rollouts are generated.
- Gate C: reward separates clean GT from real Fast rollout failures and catches visible failure modes.
- Gate D: clean-vs-corrupt calibration on 50/100 samples reaches at least 0.85.
- Gate E: VideoGPA pair export plus LingBot-compatible encode smoke succeeds.
- Gate F: `LingBotFastVideoGPAAdapter` prepares winner/loser batch shape with real latent and condition paths.
- Gate G: real DPO energy/logprob is wired; no fake loss.

Only after all gates pass should a small DPO training dry-run be considered. Do not run `03_train.py` now.

