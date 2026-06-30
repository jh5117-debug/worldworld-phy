
# Reward Pair Failure and LingBot-Fast Support Status

Current Status: PLANNED_AUDIT_BEFORE_ANY_TRAINING

Updated: 2026-06-30 13:11:54

## Current Pair Concern

Protocol v4 produced 42 reward-guided pairs: 34 TypeA+ and 8 TypeM. However preview-frame inspection already showed a key risk: several TypeA+/TypeM losers still look very similar to WIN at normal viewing scale. The heatmap can show a local difference, but the human-visible video difference may be too subtle for a reliable DPO preference pair.

## Why TypeA+ / TypeM May Still Look Too Similar

- The current reward backend for v4 synthetic pairs is mostly proxy/diagnostic, not a fully real perceptual/physics backend.
- Reward margins were generated from corruption metadata and proxy subreward drops; they may overstate human-visible change.
- The local corruption may live in a small affected region, so full-frame WIN/LOSE can look almost identical.
- Some accepted severities were selected to pass reward margin while preserving sharpness, but not necessarily to pass a human-visible local-difference threshold.
- The current gate did not require local_absdiff_p95 / local LPIPS / Codex can-see-difference to be strong enough.

## Why TypeB Is Still Not Usable

TypeB rollout losers remain blocked by blur and low quality. Previous TypeB candidates were diagnostic, not training-ready: they were more visibly different than TypeA, but too blurry/degraded to serve as clean medium-hard negatives.

## Reward Backend Provenance

- Clean GT winner reward: `clean_gt` / diagnostic high-confidence.
- v4 TypeA+/TypeM reward: `proxy_reward_guided_v4`.
- PSNR/sharpness: computed from generated videos.
- SSIM in v4 tables: global proxy, not full SSIM backend.
- LPIPS for full v4 sweep: not run / blocked for the sweep.
- FVD/VBench: `BLOCKED_BY_ENV`.

## Why We Cannot Directly Enter DPO

DPO objective smoke v3 was engineering-positive but signal-negative: winner improvement remained weak/negative and loser degradation dominated. If v4 pairs are also visually too subtle, DPO would be optimizing proxy labels rather than human-visible preferences. This round must first validate visual alignment and reject pairs that humans cannot explain.

## Hypotheses To Verify

1. Reward-selected TypeA+/TypeM pairs may fail human-visible medium-hard criteria.
2. Reward margin may not correlate with local visual difference.
3. Some subrewards may not contribute useful visible errors yet because the backend is proxy/diagnostic.
4. LingBot-Fast may weakly use camera poses/intrinsics.
5. Small camera LoRA may be under-capacity, but simply adding parameters or steps may not fix support/domain mismatch.
6. High-noise-only warmup may fail to repair low-level detail and sharpness.

## Explicitly Not Run

No DPO training, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, checkpoint modification, or large-file Git push will be done in this round.
