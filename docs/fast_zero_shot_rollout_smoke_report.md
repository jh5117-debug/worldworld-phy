# Fast Zero-Shot Rollout Smoke Report

Rollout generation was not launched because the prerequisite 1-sample LingBot-Fast actual inference smoke failed by timeout.

- Successful generated rollouts: 0.
- Failed actual inference attempts: 1.
- Rollout output root reserved: `local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke`.
- Existing Fast rollout videos: none from this pass.

Because no real Fast videos exist, visual failure modes such as background drift, object deformation, reobserve inconsistency, camera-following failure, freeze, or blur cannot yet be assessed on Fast outputs.

Next step: make `local_assets/outputs/smoke/lingbot_fast_inference/.../generated.mp4` succeed for one sample before running `scripts/07_generate_rollouts.sh`.

