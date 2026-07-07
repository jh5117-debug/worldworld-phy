# v14 Requirement Audit

Generated: `2026-07-07T18:10:35Z`

This audit checks the active v14 objective against current H20-2 artifacts. It does not redefine success: the requested final state was either a valid 200-step recipe with video/metrics passing, or an exact blocker if no recipe is found.

## Decision

- Final decision: `DPO_RECIPE_NOT_FOUND_V14`
- Scale permission: `NO_SCALE`
- S16/S32 permission: `NO`
- Train400 permission: `NO`
- Main blocker: scalar energy/gap objectives can be improved, but true V2V-5 rollouts degrade visually after LoRA updates.

## Requirement Table

| Requirement | Status | Evidence |
|---|---:|---|
| SSH/repo/GPU rule | `PASS` | Committed v14 runs/reports document H20 repo branch and GPU4/5-only execution; final GPU query shows GPU4/5 idle and no v14 jobs on forbidden GPUs. |
| PRD written before experiment | `PASS` | docs/experiments/EXP_dpo_utility_calibration_and_latent_monitor_v14.md exists with post-run updates. |
| Pair inventory/subsets | `PASS` | reports/dpo_utility_calibration_v14/pair_inventory_summary.md and manifests/dpo_v14_subsets/* exist. |
| Offline all500 real energy calibration | `BLOCKED` | Coverage CSVs exist but every row is MISSING_REAL_ENERGY; one-pair LingBot energy smoke timed out before first row. |
| Beta/loss response | `PASS` | beta_loss_response_summary.md recommends u_log and beta around 1000 from real v13b training CSVs. |
| Gap scale root cause | `PASS` | gap_scale_root_cause.md documents u≈1e-4/2e-4 and near-zero beta*u at beta=0.1. |
| Latent VJEPA/VideoREPA/TRD monitor | `BLOCKED` | Backend audit found local candidates but produced no TRD/VJEPA margins; no latent auxiliary enabled. |
| Normalization/regularization design | `PASS` | normalization_regularization_design.md and dpo_objective_v14_normalized.yaml document calibrated components. |
| 10-scheme objective search | `PARTIAL_PASS_NO_RECIPE` | E01-E10 were attempted as screens/full runs; several reached scalar training signal, but none passed required video/metric gate. |
| Checkpoint video and Codex audit for promising schemes | `PASS_FOR_PROMISING_SCHEMES` | E02/E04/E05/E07/E09/E10 produced true V2V-5 checkpoint evaluations or audits where promoted; E09/E10 latest audits failed visual gate. |
| Metrics gate | `PARTIAL` | Metric gates existed for selected schemes; E09/E10 latest decision relies on visual gate failure. VBench/FVD full integration remains incomplete for this wrapper. |
| Decision labels and scale permission | `PASS` | best_scheme_decision.json says DPO_RECIPE_NOT_FOUND_V14, NO_SCALE, no train400. |
| Tests | `PARTIAL` | compileall PASS; pytest NOT RUN because pytest is unavailable in active H20 shell. No pytest PASS claimed. |
| Git / forbidden artifacts | `PASS` | Only docs/CSV/JSON/MD were pushed. No local_assets, videos, images, checkpoints, weights, logs, NPY/NPZ/HDF5 pushed. |

## Offline Energy Coverage

| File | Rows | Status Counts |
|---|---:|---|
| `energy_utility_all500.csv` | 500 | `{'MISSING_REAL_ENERGY': 500}` |
| `energy_utility_local_mask.csv` | 485 | `{'MISSING_REAL_ENERGY': 485}` |
| `energy_utility_rollout_only.csv` | 15 | `{'MISSING_REAL_ENERGY': 15}` |
| `energy_utility_s_fail.csv` | 0 | `{}` |
| `energy_utility_s_pass.csv` | 4 | `{'MISSING_REAL_ENERGY': 4}` |
| `energy_utility_stratified100.csv` | 100 | `{'MISSING_REAL_ENERGY': 100}` |
| `energy_utility_synthetic.csv` | 485 | `{'MISSING_REAL_ENERGY': 485}` |

Interpretation: these files prove subset coverage and the real-energy blocker, not all500 real LingBot energy calibration.

## Objective Schemes

| Scheme | Training Status | Final Winner Improvement | Mean WCR | Video Audit | Audit Path |
|---|---|---:|---:|---|---|
| `E01_screen20` | `CALIBRATED_WINNER_DETACHED_RAW_SIGNAL_HEALTHY` | `0.0002976655960083008` | `0.903795999637663` | `NOT_EVALUATED` | `` |
| `E02_best7` | `CALIBRATED_WINNER_DETACHED_LOG_SIGNAL_HEALTHY` | `0.00033855438232421875` | `0.6667287038434788` | `FAIL` | `reports/dpo_utility_calibration_v14/objective_search/E02_best7/checkpoint_eval/video_audit_summary.md` |
| `E02_smoke10` | `CALIBRATED_WINNER_DETACHED_LOG_SIGNAL_FAIL` | `-4.172325134277344e-05` | `0.6669103726560174` | `NOT_EVALUATED` | `` |
| `E03_smoke10` | `EARLY_STOP_WINNER_WORSE` | `-8.20159912109375e-05` | `0.5` | `NOT_EVALUATED` | `` |
| `E04_screen5` | `NO_LOSE_GAP_NORMALIZED_WIN_ONLY_SIGNAL_HEALTHY` | `0.00013786554336547852` | `0.7916118421052631` | `FAIL` | `reports/dpo_utility_calibration_v14/objective_search/E04_screen5/checkpoint_eval/video_audit_summary.md` |
| `E05_screen5` | `NORMALIZED_CLIPPED_LOSER_SIGNAL_HEALTHY` | `0.00012230873107910156` | `0.8219769835932469` | `FAIL` | `reports/dpo_utility_calibration_v14/objective_search/E05_screen5/checkpoint_eval/video_audit_summary.md` |
| `E06_screen20` | `NORMALIZED_CLIPPED_LOSER_SIGNAL_HEALTHY` | `0.00028055906295776367` | `0.8173402562032311` | `NOT_EVALUATED` | `` |
| `E07_screen200` | `LINEAR_WINNER_DETACHED_PASS` | `0.016121745109558105` | `0.985` | `FAIL` | `reports/dpo_utility_calibration_v14/objective_search/E07_screen200/checkpoint_eval/video_audit_summary.md` |
| `E08_screen200` | `CALIBRATED_WINNER_DETACHED_LOG_SIGNAL_HEALTHY` | `0.01444697380065918` | `0.9794931332986636` | `NOT_EVALUATED` | `` |
| `E09_screen200` | `TRAINING_SIGNAL_PASS_EARLY_STOPPED_FOR_VIDEO_EVAL` | `0.0012439489364624023` | `None` | `FAIL` | `reports/dpo_utility_calibration_v14/objective_search/E09_screen200/checkpoint_eval/video_audit_summary.md` |
| `E10_screen100` | `CALIBRATED_WINNER_DETACHED_LOG_SIGNAL_HEALTHY` | `0.00040417909622192383` | `0.8241835090048764` | `FAIL` | `reports/dpo_utility_calibration_v14/objective_search/E10_screen100/checkpoint_eval/video_audit_summary.md` |

## Answers Required By v14

1. Why was `u` around `1e-4`? Existing v13b real training CSVs show full-future/reduced energy gaps yield median `|u_log|≈2.05e-4` and `|u_raw|≈1.51e-4`; beta=0.1 therefore produced logits around `1e-5`.
2. Which reduction/normalization is best? Real all500 energy is blocked, but v13b-derived beta response favors log-normalized utility `u_log` over raw for the next guarded probe. This is a partial answer, not final all500 calibration.
3. What beta should be used? For observed v13b utility scale, beta around `1000` puts median `|beta*u_log|≈0.205`; beta=0.1 is under-scaled.
4. Are synthetic pairs too mild / rollout pairs stronger / local mask stronger? Not proven by all500 real energy because LingBot energy calibration timed out. Existing inventory distinguishes the groups; final quantitative comparison remains blocked.
5. Does TRD/VJEPA distinguish winner/loser? Not answered: no valid TRD/VJEPA scores were produced, so latent monitor is `LATENT_MONITOR_BLOCKED`.
6. Which scheme is best? E09 step50 and E10 step100 are best scalar-signal candidates; both fail true-video visual gates, so neither is a valid DPO recipe.
7. Can DPO proceed to S16/S32/train400? No. `NO_SCALE`, `NO_S16_S32`, `NO_TRAIN400`.

## Next Safe Action

Do not continue ordinary DPO scaling. Add a rollout-quality or latent visual monitor/regularizer that catches foreground duplication, object fragments, and scene contamination before checkpoint rollout, then rerun a tiny gated search.

## v14 Scheduler Artifact Update (2026-07-07T18:24:43Z)

- Added `cam_physgeo/orchestration/gpu_scheduler_v14.py`.
- Added `scripts/launch_dpo_v14_scheduler.sh`.
- Added `tests/test_gpu_scheduler_v14.py`.
- Smoke output path: `reports/dpo_utility_calibration_v14/scheduler_state.json` and `scheduler_state_summary.md`.
- Scheduler decision: `NO_TRAINING_NO_SCALE`; it records GPU/state evidence and does not launch training after `DPO_RECIPE_NOT_FOUND_V14`.

## v14 Blocker Retry Plan Update

- Added blocker resolution plan: `reports/dpo_utility_calibration_v14/blocker_resolution_plan.md`.
- Added conservative dry-run command generator: `scripts/plan_v14_blocker_retry.sh`.
- Added config: `configs/cam_physgeo/dpo_v14_blocker_retry.yaml`.
- Added direct import smoke log: `reports/dpo_utility_calibration_v14/test_logs/direct_import_smoke_v14.log`.
- These artifacts do not launch training and do not change `NO_SCALE`.
