# v14 Asset Recovery Plan

Decision: `V14_ASSET_RECOVERY_PLAN_READY_NOT_EXECUTED`
Scale permission: `NO_SCALE`

This is a no-video, no-GPU recovery plan. It does not create MP4 files; it only records exactly which clips should be recovered from existing full GT videos before any bounded real-energy retry.

## Counts

- all500 rows: `500`
- recoverable pair rows: `336`
- nonrecoverable pair rows: `164`
- condition-level clip recovery tasks: `74`
- pairs needing prefix clip recovery: `336`
- pairs needing winner future clip recovery: `336`
- pairs needing no clip recovery: `0`

## Blocked Reason Counts

- `missing_loser_video`: `78`
- `prefix_not_recoverable`: `149`
- `winner_not_recoverable`: `149`

## Interpretation

- The plan makes the next bounded real-energy retry actionable for the 336 recoverable all500 rows.
- It does not solve rollout-only or S_pass coverage: those remain blocked by missing loser videos in the current worktree.
- A future recovery command should materialize only a small bounded subset first, then run real energy on that recovered subset.
- No DPO scale is authorized by this plan.

## Outputs

- Pair plan CSV: `reports/dpo_utility_calibration_v14/asset_recovery_plan/recovery_plan_by_pair.csv`
- Pair plan JSONL: `reports/dpo_utility_calibration_v14/asset_recovery_plan/recovery_plan_by_pair.jsonl`
- Condition-level plan CSV: `reports/dpo_utility_calibration_v14/asset_recovery_plan/recovery_plan_by_condition.csv`
- Condition-level plan JSONL: `reports/dpo_utility_calibration_v14/asset_recovery_plan/recovery_plan_by_condition.jsonl`
- Nonrecoverable blockers CSV: `reports/dpo_utility_calibration_v14/asset_recovery_plan/nonrecoverable_blockers.csv`
