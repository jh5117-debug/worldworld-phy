# v14 GPU4/5 Scheduler Summary

- Timestamp: `2026-07-08T02:24:04+0800`
- Allowed physical GPUs: `[4, 5]`
- Forbidden physical GPUs: `[0, 1, 2, 3, 6, 7]`
- Idle allowed GPUs: `[4, 5]`
- Objective decision: `DPO_RECIPE_NOT_FOUND_V14`
- Scheduler decision: `NO_TRAINING_NO_SCALE`
- Next action: `NO_TRAINING_RECIPE_NOT_FOUND`

This v14 scheduler is intentionally conservative after the objective search decision. If the current decision is `DPO_RECIPE_NOT_FOUND_V14`, it does not launch additional training and only records GPU/state evidence. This preserves the v14 `NO_SCALE` gate.
