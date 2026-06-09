# Prior Art: LingBot / Wan MoE and Timestep-Stage Audit

Date: 2026-06-09

## Evidence Read

Local code and checkpoint evidence:

- LingBot Base checkpoint inspection reports `high_noise_model` and `low_noise_model` branches.
- LingBot Fast checkpoint inspection reports a sharded Fast checkpoint, not explicit high/low branch directories.
- `local_assets/third_party/lingbot_world/generate.py` exposes camera-guidance mode help for all denoising steps, high-noise early steps, or low-noise late steps.
- `local_assets/third_party/lingbot_world/generate_fast.py` creates `WanI2VFast`.
- `local_assets/third_party/lingbot_world/wan/image2video_fast.py` defines `WanI2VFast`, uses `FlowUniPCMultistepScheduler`, and has `num_train_timesteps`.

## Findings

| Question | Answer |
|---|---|
| Does LingBot Base expose MoE high/low branches? | Yes, checkpoint layout has `high_noise_model` and `low_noise_model`. |
| Does LingBot-Fast runtime expose explicit expert routing? | Not in this smoke. `WanI2VFast/WanModelFast` loaded, but expert route was `unavailable_in_fast_or_not_exposed`. |
| Is Fast likely a separate/distilled/sharded runtime? | Yes, local checkpoint inspection reports Fast-style shards and no explicit high/low branch dirs. |
| Scheduler/timestep convention | `FlowUniPCMultistepScheduler`, `num_train_timesteps=1000`. |
| Exact high/low split threshold | Unknown from the exposed Fast runtime. Do not claim a precise expert split. |

## Smoke Policy

Because Fast does not expose a reliable expert route, this round reports high/low as scheduler-quantile diagnostics:

- diagnostic high-noise quantile: timestep 799, sigma approximately 0.799;
- diagnostic low-noise quantile: timestep 200, sigma approximately 0.200;
- random: timestep 412, sigma approximately 0.412.

These are not claimed to be the exact LingBot paper expert boundary. They are a safe diagnostic until the Fast expert routing or checkpoint boundary is exposed.

## Warmup Recommendation

Use staged warmup rather than immediate full warmup:

1. Stage A: high-noise/global-camera diagnostic band first, because camera motion and background parallax are global-layout phenomena.
2. Stage B: mixed or lower-noise detail refinement only after Stage A is finite/stable.

DPO remains later, after warmup and reward-based winner/loser pair selection.
