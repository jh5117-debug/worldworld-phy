# DPO Protocol v4 Start Status

Current Status: MIXED_PROTOCOL_V3_TYPEA_ONLY_NEEDS_REWARD_GUIDED_MEDIUM_HARD

Updated: 2026-06-30 11:17:53

## Current Protocol v3 State

Preference Protocol v3 is available at `manifests/dpo_preference_protocol_v3_pairs.jsonl`.
It contains 34 valid V2V-5 prefix-aware pairs, all TypeA local-corruption pairs. TypeB rollout losers are currently zero because the v2/v3 quality gate rejected the previous rollout candidates for blur and low quality.

Known state carried into v4:

- V2V-5 wrapper is prefix-aware: prefix frames 0-4 are the condition and future frames 5-80 are the target.
- Protocol v1 had 66 valid pairs, including 16 TypeB rollout losers, but TypeB quality was later judged too weak.
- Protocol v2/v3 retained 34 TypeA local-corruption pairs and blocked TypeB.
- DPO engineering smoke v3 ran through the mechanics, but the objective signal stayed loser-dominant and is not ready to scale.
- PSNR, SSIM, and LPIPS are usable. FVD and VBench remain `BLOCKED_BY_ENV` and must not be fabricated.

## Why TypeA Is Too Subtle

The existing TypeA pairs compare clean GT future against local-corrupted GT future. They are high quality and stable, but many corruptions are visually subtle: the loser can look almost like the winner, reward margins can be weak, and a presentation audience may not immediately see the failure. This makes TypeA useful as a safe LocalDPO-style starting point, but not sufficient as the only medium-hard preference protocol.

## Why TypeB Is Too Degraded / Blur Blocked

The previous TypeB pairs compare clean GT future against rollout losers. The differences are easier to see, but the loser videos often fail the quality floor: many are blurry, degraded, or too far from a readable medium-hard negative. v2 rejected 16/16 TypeB candidates with `sharpness_ratio_lt_0.55`, and 10/16 also failed the condition-level R_quality p40 gate. These are diagnostic examples, not training-ready negatives.

## Why DPO Cannot Be Scaled Directly

DPO objective ablations and smoke runs show weak or loser-dominant signal:

- Standard energy-DPO: weak signal.
- SDPO-style anchor: engineering path runs, but winner preservation is not reliable.
- Linear-DPO and LocalDPO-style probes were loser-only or inconclusive.
- Failure diagnosis reported unstable winner-only improvement, winner/loser gradient conflict, and insufficient spatial-token masking for full LocalDPO.

Scaling DPO now would mainly risk pushing losers worse while failing to improve winners.

## Why This Round Only Builds Reward-Guided Pairs

Protocol v4 focuses on pair construction, reward-guided hardness calibration, synthetic medium-hard negatives, and clear PPT visualization. The goal is to build cleaner DPO-ready data before another objective smoke. This round introduces:

- TypeA+: stronger but still clean local corruptions selected by reward and visual gates.
- TypeM: rollout-inspired synthetic medium-hard negatives that preserve clarity while exposing physical/geometric errors.
- TypeB usable: only if a true rollout loser passes sharpness and quality gates.
- TypeB diagnostic: at most one PPT-only blur-failed example, not training-ready.

## Explicitly Not Run

This round does not train DPO, does not run StageB, does not run GRPO, does not run full-data long StageA, does not alter checkpoints, and does not delete historical outputs.
