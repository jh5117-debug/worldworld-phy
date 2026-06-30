<!-- targeted_BC_loser_mining_v6_update -->
# Targeted B/C Loser Mining v6 Update

Current Status: BLOCKED_INSUFFICIENT_MEDIUM_HARD_ROLLOUTS

Updated: 2026-06-30 20:50:46 CST

- Safe GPU status and deterministic V2V-5 runner discovery are fixed.
- 1-condition smoke PASS for M0/B/C.
- Available-condition rollout PARTIAL_PASS: 15 videos from 5 runnable prefix5 conditions.
- C produced 4 visually meaningful medium-hard loser candidates.
- Final DPO-ready pair count is 4, below the >=10 DPO-smoke gate.
- 8/32-condition rollout could not be faithfully executed because only 5 runnable prefix5 conditions are present in this tree.
- Do not start DPO smoke until more runnable conditions or an external rollout source raises the pair count.

<!-- /targeted_BC_loser_mining_v6_update -->



## Targeted B/C Loser Mining v6 Update - 2026-06-30

Current Status: BLOCKED_BY_GPU_OR_RUNNER_DISCOVERY

B and C checkpoints were found. B camera-r8 remains the stable candidate generator/control baseline; C camera+self/temporal-r4 remains the intended loser mining scope. New rollout did not start because GPU/process queries were unsafe/hung under high GPU occupancy. No DPO-ready TypeB-C pairs were produced, and no saved sweep video was promoted to DPO-ready.


## Small-LoRA Sweep Loser Source Audit Update - 2026-06-30

Current Status: MIXED / DIAGNOSTIC_ONLY

Recovered saved A/B/C/D sweep video-audit rows from `reports/candidate_generator_v2/video_audit.csv` and inspected A/B/C/D overview contact sheets. Existing TypeB quality-gate pass count is 0 across the recovered rows, so saved sweep outputs are not directly DPO-ready TypeB losers.

Decision: B camera-r8 is the best stable candidate generator/control; C camera+self/temporal-r4 is the best next loser-source mining scope; D is diagnostic runner-up; A is too conservative/too similar. No training or checkpoint modification was performed.
