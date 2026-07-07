# DPO Utility Calibration v14 Status

Updated: 2026-07-08 01:50 CST

Decision: `DPO_RECIPE_NOT_FOUND_V14`

## Current State

- Canonical repaired ready500 remains the required data entry.
- Offline beta calibration found the prior DPO utility was under-scaled: `u_log` around 1e-4 requires beta around 1000, not beta=0.1.
- Calibrated objectives now produce real training-gap movement; the blocker has shifted from no-signal to visual degradation in true V2V-5 checkpoint rollouts.
- Only physical GPU4/GPU5 were used for v14 E09/E10 training/eval in this update. GPU0-3/6/7 were not used by these v14 jobs.

## Latest Objective Search Evidence

| Scheme | Training Signal | Video Gate | Decision |
|---|---:|---:|---|
| E07 linear winner detached | PASS at 200 steps | FAIL step200 worse 4/4 | not valid |
| E08 calibrated local/full log | PASS at 200 steps | NOT_RUN | training-signal only |
| E09 source weighted rollout priority | PASS early at step50 | FAIL step50 worse/not-better 4/4 | not valid |
| E10 L2 camera-temporal r4 | PASS at 100 steps | FAIL step100 worse 2/4, not clearly better on rest | not valid |

## Exact Current Blocker

The calibrated DPO/winner-anchor objectives can lower winner energy and avoid loser-dominant scalar metrics, but the LoRA updates still degrade generated videos with foreground duplication, object/fragment clutter, white/yellow line or text-like artifacts, and scene contamination.

## Scale Permission

- S16/S32: blocked.
- train400: blocked.
- large DPO: blocked.

Next work should add a rollout-quality/latent visual monitor or stronger visual regularization before further DPO scaling.


## v14 Final Test Status

- `python3 -m compileall cam_physgeo src tests`: PASS.
- Targeted pytest suite: NOT RUN because `pytest` is unavailable in the active H20 shell. No pytest PASS is claimed.
- Test status path: `reports/dpo_utility_calibration_v14/test_status.md`.

## v14 Requirement Audit (2026-07-07T18:10:35Z)

- Requirement audit path: `reports/dpo_utility_calibration_v14/requirement_audit.md`.
- Final decision remains `DPO_RECIPE_NOT_FOUND_V14`.
- All500 energy CSVs are coverage/blocker files with `MISSING_REAL_ENERGY`, not real energy calibration evidence.
- Latent monitor is `LATENT_MONITOR_BLOCKED` because no TRD/VJEPA margins were produced.
- Best scalar candidates E09/E10 failed true V2V-5 visual gates, so S16/S32/train400 remain blocked.

## v14 Scheduler Artifact Update (2026-07-07T18:24:43Z)

- Added `cam_physgeo/orchestration/gpu_scheduler_v14.py`.
- Added `scripts/launch_dpo_v14_scheduler.sh`.
- Added `tests/test_gpu_scheduler_v14.py`.
- Smoke output path: `reports/dpo_utility_calibration_v14/scheduler_state.json` and `scheduler_state_summary.md`.
- Scheduler decision: `NO_TRAINING_NO_SCALE`; it records GPU/state evidence and does not launch training after `DPO_RECIPE_NOT_FOUND_V14`.
