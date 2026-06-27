# StageA V2V-5 Warmup Report

Updated: 2026-06-27T15:42:37

## Scope

This run used true prefix-aware V2V-5 conditioning: frames 0-4 are the clean prefix condition and frames 5-80 are generated/evaluated. It did not run StageB, GRPO, or large-scale DPO.

## Training

- Model: LingBot-World-Fast
- Scope: camera-conditioning LoRA only
- Rank/alpha/dropout: 4 / 4 / 0.05
- Steps: 100 high-noise-only optimizer steps
- Loss: future-only latent loss; prefix-touched latent slots are excluded from the training loss.
- Checkpoints evaluated: Original Fast, step25, step50, step75, final.

## Future-only Metrics

| Model | PSNR up | SSIM up | Freeze down | LPIPS | FVD | VBench |
|---|---:|---:|---:|---|---|---|
| original_fast_baseline | 15.844571561861791 | 0.8378291634810275 | 0.0 | BLOCKED_BY_ENV_or_not_requested | BLOCKED_BY_ENV_or_not_requested | BLOCKED_BY_ENV_or_not_requested |
| step025 | 15.752167754592033 | 0.834249667924749 | 0.0 | BLOCKED_BY_ENV_or_not_requested | BLOCKED_BY_ENV_or_not_requested | BLOCKED_BY_ENV_or_not_requested |
| step050 | 15.779865629550223 | 0.8365190548189585 | 0.0 | BLOCKED_BY_ENV_or_not_requested | BLOCKED_BY_ENV_or_not_requested | BLOCKED_BY_ENV_or_not_requested |
| step075 | 15.915238162455646 | 0.8375297596733986 | 0.0 | BLOCKED_BY_ENV_or_not_requested | BLOCKED_BY_ENV_or_not_requested | BLOCKED_BY_ENV_or_not_requested |
| final | 16.01235260629847 | 0.8410866316146557 | 0.0 | BLOCKED_BY_ENV_or_not_requested | BLOCKED_BY_ENV_or_not_requested | BLOCKED_BY_ENV_or_not_requested |

## Visual Review

Codex reviewed the generated comparison contact sheets in `reports/stageA_v2v5_20260627/model_comparison_contact_sheets/`. The final checkpoint is not visually collapsed and is slightly better on PSNR/SSIM, but it still hallucinates extra small objects, does not preserve foreground identity reliably, and does not solve the physical event. The result is therefore MIXED, not PASS.

## Decision

`STAGEA_V2V5_MIXED_USE_WITH_CAUTION`. Use the final checkpoint only as a cautious candidate/diagnostic model. Do not use StageA-generated rollouts as DPO winners yet; use clean GT winners against controlled corrupted GT or quality-qualified rollout losers.
