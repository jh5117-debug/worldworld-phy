# DPO GPU Scheduler v12d Report

Current Status: V12D_JOB1_FAILED_TRAINING_SIGNAL_NO_SCALE

Updated: 2026-07-05 11:21:55

## Implementation

The GPU4-7 gated scheduler was implemented and launched in tmux session `dpo_gpu_scheduler_v12d`. It writes state, heartbeat, job events, GPU usage, per-job summaries, and final scheduler summary under `reports/dpo_gpu_scheduler_v12d/`.

## First Training Job

- Job: `v12c_winner_detached_preference_s_pass4`
- Assigned physical GPU: `[4]`
- Exit code: `0`
- Scheduler decision: `TRAINING_SIGNAL_FAIL`
- Runner status: `WINNER_DETACHED_PREFERENCE_SIGNAL_FAIL`
- Rows written: `10` / `10`
- Mean winner_improvement_post: `0.00011658668518066406`
- Final winner_improvement_post: `-8.320808410644531e-05`
- Mean loser_degradation_post: `-5.3834915161132815e-05`
- Mean winner_contribution_ratio_post: `0.8491498668883544`

## Gate Decision

`TRAINING_SIGNAL_FAIL`. The final winner improvement is negative, so v12d does not permit further DPO training. This blocks checkpoint-eval-dependent continuation, tiny loser-gradient preference, S16/S32/S64, and train400 pilot.

## Why This Is Not PASS

The run completed 10 optimizer rows and had a positive mean winner improvement, but the final winner improvement was negative. The user explicitly required stop/report behavior when winner worsens. Therefore the correct decision is failure/no scale.

## Artifacts

- Training CSV: `reports/dpo_tiny_guarded_preference_v12c/winner_detached_preference/winner_detached_preference_10step.csv`
- Training summary: `reports/dpo_tiny_guarded_preference_v12c/winner_detached_preference/training_summary.md`
- Scheduler state: `reports/dpo_gpu_scheduler_v12d/scheduler_state.json`
- Scheduler summary: `reports/dpo_gpu_scheduler_v12d/final_summary.md`
- Local checkpoints: `local_assets/dpo_tiny_guarded_preference_v12c/winner_detached_preference/checkpoints/` (not committed)

## Verification

- `python3 -m compileall cam_physgeo src tests`: PASS before launch.
- Pytest unavailable in `/usr/bin/python3`; no pytest PASS is claimed.

## Scale Decision

Train400 pilot is NOT allowed. Large DPO remains blocked.
