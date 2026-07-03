Current Status: PASS

# DPO Pair Factory v10b Data Card

## Dataset Name

DPO Pair Factory v10b

## Purpose

Camera-conditioned V2V-5 / prefix5 DPO preference pairs for LingBot-Fast physical-geometric consistency.

## Input Condition

- Prefix frames: 0-4
- Prompt
- Camera poses
- Intrinsics

## Target Future

- Future frames: 5-80

## Pair Types

- GT>C rollout-derived: 15 pairs. Winner is clean GT future, loser is C camera+self/temporal rank4 rollout.
- Controlled synthetic visible TypeM-v10: 63 pairs. Winner is clean GT future, loser is a controlled synthetic visible medium-hard negative.
- TypeA_plus human-visible controlled: 3 pairs.

## Important Caveat

The 63 synthetic pairs are controlled negatives, not real model rollout losers. They are suitable for anchored / LocalDPO-style controlled objectives and presentation of the protocol, but they do not prove that real rollout loser mining is solved.

## Recommended Use

- Use `manifests/dpo_pair_factory_v10b_top50_balanced.jsonl` for anchored tiny DPO data experiments after objective/winner-signal validation.
- Use `manifests/dpo_pair_factory_v10b_ready_rollout_only.jsonl` for model-distribution pair analysis and rollout-derived examples.
- Use `manifests/dpo_pair_factory_v10b_ready_synthetic_controlled.jsonl` for controlled local corruption / LocalDPO-style learning.
- Use `manifests/dpo_pair_factory_v10b_ppt_subset.jsonl` and the existing showcase MP4 for presentation.

## Not Recommended

- Do not claim all 81 pairs are real rollout pairs.
- Do not train large DPO before winner-side objective validation.
- Do not use diagnostic-only pairs for training.
- Do not claim LocalDPO is fully validated until spatial masks are consumed by the objective.

## Known Limitations

- Real C rollout expansion remains blocked by WanI2VFast initialization / policy runtime loading.
- Synthetic negatives may be easier than real rollout failures.
- Reward and visual audit remain mixed; the final gate relies on schema checks plus existing Codex visual review.
- Real rollout-derived pair count is still only 15.
