<!-- targeted_BC_loser_mining_v6_update -->
# Git Push Report Update

Current Status: PENDING_PUSH

Updated: 2026-06-30 20:50:46 CST

This update will commit only lightweight docs/scripts/CSV/JSONL summaries for targeted B/C loser mining v6. MP4/JPG/PNG/contact sheets/local_assets/checkpoints/weights remain untracked and must not be pushed.

<!-- /targeted_BC_loser_mining_v6_update -->



## Targeted B/C Loser Mining v6 Update - 2026-06-30

Current Status: BLOCKED_BY_GPU_OR_RUNNER_DISCOVERY

B and C checkpoints were found. B camera-r8 remains the stable candidate generator/control baseline; C camera+self/temporal-r4 remains the intended loser mining scope. New rollout did not start because GPU/process queries were unsafe/hung under high GPU occupancy. No DPO-ready TypeB-C pairs were produced, and no saved sweep video was promoted to DPO-ready.


## Small-LoRA Sweep Loser Source Audit Update - 2026-06-30

Current Status: MIXED / DIAGNOSTIC_ONLY

Recovered saved A/B/C/D sweep video-audit rows from `reports/candidate_generator_v2/video_audit.csv` and inspected A/B/C/D overview contact sheets. Existing TypeB quality-gate pass count is 0 across the recovered rows, so saved sweep outputs are not directly DPO-ready TypeB losers.

Decision: B camera-r8 is the best stable candidate generator/control; C camera+self/temporal-r4 is the best next loser-source mining scope; D is diagnostic runner-up; A is too conservative/too similar. No training or checkpoint modification was performed.

# GitHub Push Report

Current Status: PENDING_CAMERA_CONDITION_STATUS_CORRECTION_PUSH

Updated: 2026-06-30 14:21:36

This round corrects the camera condition status from misleading `UNKNOWN` wording to `CAMERA_CONDITION_PATH_CONFIRMED_BUT_SENSITIVITY_PARTIAL`.

No training, DPO, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint modification, checkpoint deletion, or large-file push was performed.
