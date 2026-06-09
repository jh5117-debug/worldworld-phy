# TDW v5 200 LingBot True Forward-Loss Dry-Run

Date: 2026-06-09

Status: passed true forward-loss dry-run.

This was a real no-grad LingBot-Fast forward, not a placeholder tensor path.

## Sample

| Field | Value |
|---|---|
| sample_id | `tdw_v3_00094_collision_orbit_right_64_seed22094_0000` |
| template | `collision` |
| camera_variant | `orbit_right_64` |
| metadata `use_action` | `false` |
| dummy action norm | `0.0` |

## Shapes

| Tensor | Shape |
|---|---|
| target video latent | `[16, 2, 60, 104]` |
| camera Plücker/control | `[1, 384, 2, 60, 104]` |
| prediction | `[16, 2, 60, 104]` |
| target | `[16, 2, 60, 104]` |

## Timestep Bands

Fast expert routing was not exposed, so high/low bands are scheduler-quantile diagnostics.

| Band | Timestep | Sigma | Loss | Finite |
|---|---:|---:|---:|---|
| diagnostic high-noise quantile | 799 | 0.7990 | 0.046257 | yes |
| diagnostic low-noise quantile | 200 | 0.2000 | 0.895799 | yes |
| random | 412 | 0.4120 | 0.437084 | yes |

Target:

`flow_velocity_noise_minus_x0`

Safety:

- real model load confirmed;
- no backward confirmed;
- no optimizer confirmed;
- no checkpoint confirmed;
- no LoRA save;
- no training.

Runtime:

- elapsed: 647.5 seconds;
- GPU7 memory during forward: about 49.4 GiB after final reporting, with a higher observed live forward peak around 54.8 GiB;
- GPU7 memory released after cleanup.

Gate result: passed. This permits writing a staged warmup pilot approval request only; it does not authorize training.
