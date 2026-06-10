# GPU Usage Approval Request: Next Step After 4-Condition Rollout

Date: 2026-06-10

The 4-condition base vs Stage A adapter rollout smoke passed:

- Base videos: 4/4.
- Adapter videos: 4/4.
- Adapter checkpoint loaded: yes.
- Video probe: 12/12 including GT/base/adapter.
- Reward scoring: not run.
- Pair construction: not run.
- DPO: not run.

## Options

Option A: human inspect the 4-condition videos first. No further compute.

Option B: run reward scoring on the 4-condition base/adapter rollout.

Option C: expand rollout to 12 conditions, 3 per template, base plus adapter for 24 videos. Estimated runtime is roughly 4.5 to 5 hours on GPU7 based on the 4-condition run.

Option D: if the adapter is clearly worse in human review, stop and revise warmup / adapter scope.

Option E: if adapter looks good, approve reward scoring plus reward-pair construction as the next gate.

Recommended next step: inspect the 4-condition gallery first, then approve either reward scoring on these 4 conditions or a 12-condition rollout.

DPO remains disallowed until rollout, reward, and pair diagnostics pass.

