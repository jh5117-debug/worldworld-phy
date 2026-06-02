# DPO LR Sensitivity Sweep Report

## Summary

- Requested full sweep: `1e-5`, `5e-5`, `1e-4`, `5e-4`.
- Fixed noise seed: `123`.
- Fixed timestep: `579`.
- Rank/alpha: `2 / 4.0`.
- Target modules:
  - `blocks.39.cam_shift_layer`
  - `blocks.39.cam_scale_layer`
- Full sweep status: runtime-blocked / terminated.
- Fallback status: `lr=1e-4`, `1` step passed.

## Full Sweep Blocker

The full `dpo_lr_sensitivity_sweep` was started on the remote worktree but did
not produce a first per-lr summary after about `36m57s`. It held about `54 GiB`
on GPU 6 and did not OOM. To avoid an unbounded diagnostic run, the process was
terminated and GPU memory was released.

Remote path, not committed:

`local_assets/outputs/smoke/lingbot_dpo_lr_sensitivity_sweep/`

## Fallback 1-Step Result

Because the full sweep was too slow, a bounded fallback ran `lr=1e-4` for one
fixed-noise/fixed-timestep step.

| field | value |
| --- | ---: |
| success | true |
| L_DPO | 0.6931471825 |
| E_policy_winner | 0.1394620091 |
| E_policy_loser | 0.1332646310 |
| E_ref_winner | 0.1394616365 |
| E_ref_loser | 0.1332639754 |
| Delta_policy | -0.0061973780 |
| Delta_ref | -0.0061976612 |
| preference_logit | 2.831e-08 |
| grad_norm_after_clip | 3.057e-05 |
| LoRA max diff | 9.990e-05 |
| base params changed | no |
| reference params changed | no |
| NaN/Inf | no |
| OOM | no |

Remote path, not committed:

`local_assets/outputs/smoke/lingbot_dpo_lr_sensitivity_fallback_1e4_1step/`

## Interpretation

The fallback confirms that a higher lr can step safely, but it still does not
show a strong scalar learning signal in a single step. The logit remains around
`1e-8`, so the observed weakness is not solved simply by trying `lr=1e-4` once.

The full multi-lr sweep remains blocked by runtime cost in this remote session.
Do not proceed to 5-pair/10-pair overfit based on this fallback alone.

## Recommendation

Before expanding pair count, either:

- optimize the LR sweep to reuse a single loaded policy/reference model; or
- run a stronger but still bounded fixed-noise diagnostic with a broader camera
  LoRA scope and fewer settings.
