Current Status:
BLOCKED

# Scale GT>C Pair Factory v7 Report

Pair factory v7 was not launched in this stage because the tiny SDPO smoke and required checkpoint video evaluation consumed the available safe GPU window.

## Current Condition Recovery
- Existing partial manifest: `manifests/scale_gt_c_pair_factory_v7_conditions_80.jsonl`
- Current recovered runnable rows: 21, not 80
- Distribution remains imbalanced and additional quant-manifest recovery is still required.

## Decision
`PAIR_FACTORY_V7_BLOCKED_CONDITION_RECOVERY_AND_GPU_WINDOW`. Do not claim 50+ pairs yet. Existing GT>C DPO-ready v6b pool remains the current usable source; v7 expansion still needs a dedicated rollout window on GPU4-7.

## Not Run
No pair-factory rollout, no large-scale DPO, no StageB, no GRPO, no full-data StageA, no broad-LoRA.
