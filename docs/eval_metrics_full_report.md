# Eval Metrics Full Report

Updated: 2026-06-27 01:28:06

## Scope

This report summarizes the evaluation artifacts currently available on H20. It is not a claim that every requested model has completed full80 rollout.

## Existing Video Coverage

- screen16 rollouts: `208` videos. This covers Original Fast plus small-LoRA A/B/C/D checkpoints at step050/100/200.
- full80 rollouts: `160` videos. This currently covers `GT, original_fast, D_step050`.
- Missing full80 rollouts: all small-LoRA checkpoints except selected `D_step050`.

## Traditional Metrics Status

| metric | status |
|---|---|
| PSNR | available in current full80 summary |
| SSIM | available in current full80 summary |
| LPIPS | BLOCKED_BY_ENV: `lpips` module unavailable |
| FVD | BLOCKED_BY_ENV: no FVD backend installed |
| VBench | BLOCKED_BY_ENV: `vbench` module unavailable |

## Current Full80 Summary

| model | PSNR mean | SSIM mean | quality proxy mean | freeze rate mean | C-SGC score mean |
|---|---:|---:|---:|---:|---:|
| D_step050 | 13.722508341106195 | 0.6709783111768027 | 0.9085466307352948 | 0.0 | 0.3289897517534479 |
| GT | 99.0 | 1.0 | 0.9970484756494693 | 0.0003125 | 0.32752109125167983 |
| original_fast | 13.837872787021658 | 0.6791498410791107 | 0.9060626438285551 | 0.0 | 0.32888382971773644 |

## Interpretation

- `D_step050` was selected from the screen16 diagnostic pass, not from a completed all-model full80 comparison.
- Existing full80 does not show a decisive win over Original Fast. The selected candidate is only a cautious candidate generator, not a final improved model.
- PSNR/SSIM are reconstruction-style metrics and do not prove physical consistency. PhysGeo metrics remain necessary but current object/event backends are incomplete.

## Next Required Work

1. Fix Fast inference initialization for the missing full80 checkpoints.
2. Install or provide approved backends for LPIPS, FVD, and VBench if those metrics are mandatory.
3. Re-run full80 for all available checkpoints once Fast inference initialization is reliable.
