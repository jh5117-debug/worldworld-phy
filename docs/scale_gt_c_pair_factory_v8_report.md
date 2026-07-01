Current Status:
BLOCKED_NOT_RUN_SIGMA_GATE_TIMEOUT

# Scale GT>C Pair Factory v8 Report

## Summary

Pair factory recovery v8 did not launch new rollout or pair construction in this round. The prerequisite objective-diagnosis sigma-bin check did not complete within the safety window, so the workflow stopped before starting additional B/C rollout jobs.

## Inputs Read

- `docs/experiments/EXP_gt_c_pair_factory_recovery_v8.md`
- `docs/scale_gt_c_pair_factory_v7_report.md`
- `manifests/targeted_BC_loser_mining_v6b_conditions.jsonl`
- `reports/targeted_BC_loser_mining_v6b/runnable_condition_check.csv`
- `reports/targeted_BC_loser_mining_v6b/runnable_condition_summary.md`

## Result

- Condition recovery: NOT_RUN
- New runnable prefix5 conditions: 0
- B/C rollout: NOT_RUN
- New generated videos: 0
- Codex visual audit: NOT_RUN
- New v8 GT>C DPO-ready pairs: 0
- New manifests: not produced

## Decision

`PAIR_FACTORY_V8_NOT_RUN_SIGMA_GATE_TIMEOUT`

Do not treat pair factory v8 as a data-expansion result. Existing reviewed v6b/v7 GT>C pairs remain the only usable pool until a separate recovery rollout is safely scheduled.

## Next Action

After the objective sigma/timestep gate is bounded and progress-writing, rerun pair factory recovery as a separate job on GPU4-7 only. Target at least 80 runnable prefix5 conditions and require contact-sheet review before any loser enters the manifest.

## Explicit Non-Runs

No DPO training, no large DPO, no StageB, no GRPO, no full-data StageA, no broad-LoRA, no checkpoint deletion, no checkpoint modification, no unreviewed loser manifest, and no data/weights/video push.
