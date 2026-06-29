# Next Step Protocol v3 Status

Current Status: READY_FOR_PRD_CHECKPOINT / GPU_TRAINING_WAITING_FOR_AVAILABLE_CAPACITY
Updated: 2026-06-29 15:16:36

## Current Protocol v2 Conclusion

- Current branch: `research/quant-small-lora-dpo-probe-20260624`
- Latest pushed baseline before this round: `b9ad809`
- Protocol v2 manifest: `manifests/dpo_preference_protocol_v2_pairs.jsonl`
- Protocol v2 pairs: 34 valid total = 34 Type A local corruption, 0 Type B rollout, 0 Type C.
- Type B rollout losers were rejected because all 16 audited v1 Type B candidates failed `loser_sharpness_ratio >= 0.55`; 10 / 16 also failed the per-condition R_quality p40 gate.
- DPO engineering run-through v2 passed runtime only on 8 Type A pairs, but final winner improvement was negative and winner contribution ratio was 0.0. DPO must not scale yet.

## Why This Round Comes Next

This round targets the blockers that prevent clean DPO data and reliable evaluation:

1. FVD and VBench remain `BLOCKED_BY_ENV`, so the quantitative table is incomplete.
2. Type B rollout losers are too blurry and would teach a blur preference rather than physics/camera preference.
3. Type A local corruption is stable but still needs spatial-token LocalDPO masks rather than affected-time-only masks.
4. DPO objective smoke is allowed only after Protocol v3 and LocalDPO mask gates pass.

## GPU / Process Note

At status read time, all GPUs 0-7 were already occupied by an unrelated `/home/nvme03/SZQ-WAM` LIBERO evaluation. This round will not kill unrelated processes. GPU-heavy candidate-generator training waits until capacity is available; CPU/docs/metric-backend work proceeds first.

## Explicitly Not Run In This Round Unless A Gate Allows The Tiny Smoke

- No StageB.
- No GRPO.
- No full-data long StageA.
- No large-scale DPO.
- No checkpoint deletion.
- No data/weights/video push.
