# LingBot-Fast Noise Schedule Audit

Status: provisional_from_local_code

Date: 2026-06-22

## Corrected Stage Definition

StageA is now defined as:

- model family: LingBot-World-Fast
- policy: `lingbot_world_fast`
- objective focus: high-noise/global structure
- sampling policy: `high_only`
- high-noise probability: 1.0
- low-noise probability: 0.0
- branch mode: `high_only`
- control type: `cam`
- use action: false

StageB is future work and is not run in this task. StageB is reserved for low-noise or mixed-noise detail/foreground refinement after StageA is validated.

## Evidence From Local Runtime

Local LingBot code exposes a Fast checkpoint under:

`/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam/lingbot_world_fast`

The official Fast runtime loads `WanI2VFast` / `WanModelFast` from `lingbot_world_fast`. The Fast runtime does not expose the legacy Base `low_noise_model` / `high_noise_model` policy folders as the training policy.

The scheduler constants observed in local Wan config are:

- `num_train_timesteps = 1000`
- `sample_shift = 10.0`
- legacy Base boundary observed as `0.947`

For Fast StageA, the current implementation treats high-noise as a diagnostic high band from the existing scheduler and samples only from that high band. This is a high-noise training policy, not a claim that Fast has a separate exposed high expert.

## Code Guardrails Added

- Fast config requires `model_family=lingbot_world_fast`.
- Fast config requires `noise_policy=high_only`.
- Fast config requires `high_noise_probability=1.0` and `low_noise_probability=0.0`.
- Fast runner refuses `branch_mode=low` and `branch_mode=sequence`.
- Fast helper refuses policy paths containing `low_noise_model` or `high_noise_model`.
- Fixed validation now treats `high_only` as high band.
- Fixed validation noise seed no longer depends on global step.

## Remaining Required Evidence

Before final PASS:

- 10,000 timestep sampling histogram with zero low-noise samples.
- Single-GPU 20-step Fast high-only preflight.
- 2-GPU and 7-GPU Fast high-only preflights.
- Fixed-val reproducibility check across checkpoints.
