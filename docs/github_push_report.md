Current Status:
PUSHED

## 2026-07-01 v7 Smoke Result Push
- Commit pushed: `cf05ebe Run tiny SDPO anchor smoke v7`.
- Remote branch verified: `research/quant-small-lora-dpo-probe-20260624`.
- Big artifacts were not committed: no MP4/JPG/contact sheets/local_assets/checkpoints/PT files.

Current Status:
READY_TO_PUSH

## 2026-07-01 v7 Smoke Result Commit
- Includes schema-fixed smoke subset manifest, tiny SDPO-anchor v7 result docs, checkpoint video eval summaries, Codex visual audit CSV/JSONL, and strict reward-alignment threshold fix.
- Excludes MP4/JPG/contact sheets/local_assets/checkpoints/PT files and large logs.
- Tests: compileall PASS; pair schema PASS; medium-hard selection PASS; reward selector PASS; same-noise/timestep PASS; reference frozen PASS.

Current Status:
PENDING_PUSH

## 2026-07-01 v7 Pending Commit
Prepared lightweight v7 smoke result docs/CSVs and schema-fixed the v7 smoke subset manifest. Big artifacts remain untracked in local_assets/reports and must not be pushed.


<!-- dpo_smoke_pair_factory_v7_update -->
## DPO Smoke and GT>C Pair Factory v7 Update

Current Status: BLOCKED_GPU_BUSY_SUBSET_READY / PAIR_FACTORY_CONDITION_EXPANSION_PARTIAL

Updated: 2026-07-01 16:05:00 CST

- Visual audit policy and v7 PRDs were committed and pushed before experiment work.
- Tiny smoke subset is ready: 10 reviewed GT>C pairs, loser reward mean 0.759517, reward margin mean 0.240483.
- Loser visual audit is complete for the smoke subset: 10 / 10 reviewed and DPO-ready.
- DPO smoke training did not start because authorized GPU4-7 were occupied at launch time; GPU0-3 were not used.
- Pair factory condition expansion from existing v6b candidate rows produced 21 unique runnable conditions, below the 80 target.
- Pair factory rollout did not start because GPU4-7 were occupied and more condition recovery is still needed.
- No large-scale DPO, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, or checkpoint modification was run.
<!-- /dpo_smoke_pair_factory_v7_update -->
<!-- targeted_BC_loser_mining_v6b_push_update -->
# Git Push Report Update

Current Status: PASS

Updated: 2026-07-01 09:32:00 CST

- Branch: research/quant-small-lora-dpo-probe-20260624
- Result commit pushed: 69c084c Recover prefix5 conditions for targeted B C loser mining
- Remote HEAD matched local HEAD after push for the result commit.
- This round committed only lightweight docs, manifests, CSV, and JSONL summaries.
- MP4/JPG/PNG/contact sheets/local_assets/checkpoints/weights/large logs remained untracked and unpushed.

<!-- /targeted_BC_loser_mining_v6b_push_update -->

<!-- targeted_BC_loser_mining_v6_push_update -->
# Git Push Report Update

Current Status: PASS

Updated: 2026-06-30 20:55:57 CST

- Branch: `research/quant-small-lora-dpo-probe-20260624`
- Latest pushed commit: `0d184cd Resume targeted B C small-LoRA loser mining`
- Remote HEAD matched local HEAD after push.
- No MP4/JPG/PNG/contact sheets/local_assets/checkpoints/weights were staged in the pushed commit.

<!-- /targeted_BC_loser_mining_v6_push_update -->

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

## 2026-07-02 v8 Objective Diagnosis Update

Current Status: PASS

- Branch: `research/quant-small-lora-dpo-probe-20260624`
- PRD commit pushed: `89fb3e9 Prepare winner-preserving DPO diagnosis v8 PRDs`
- Result commit pushed and verified: `d584b12 Diagnose winner-anchor and safe DPO objectives`
- Sigma energy check attempted on physical GPU4 and blocked by timeout.
- Objective training was not started.
- Pair factory v8 was not launched; no new unreviewed loser entered any manifest.
- Pushed artifacts were lightweight source, docs, tests, CSV/JSON/Markdown summaries only.
- No MP4/JPG/PNG/contact sheets/local_assets/checkpoints/weights/large logs were staged or pushed.
