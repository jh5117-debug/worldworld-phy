Current Status: V12D_JOB1_FAILED_TRAINING_SIGNAL_NO_SCALE

# DPO GPU Scheduler v12d Status

Updated: 2026-07-05 11:21:55

## Scheduler

- Tmux session: `dpo_gpu_scheduler_v12d`
- State path: `reports/dpo_gpu_scheduler_v12d/scheduler_state.json`
- Heartbeat path: `reports/dpo_gpu_scheduler_v12d/heartbeat.jsonl`
- Log path: `reports/dpo_gpu_scheduler_v12d/scheduler.log`
- Scheduler launched: yes

## GPU Policy

- Allowed physical GPUs: GPU4, GPU5, GPU6, GPU7.
- Forbidden physical GPUs: GPU0, GPU1, GPU2, GPU3.
- Job1 assigned physical GPU: `[4]`.
- Scheduler did not assign GPU0-3.
- Unknown/pre-existing tasks on GPU0-3 were observed but not killed.

## Job1 Result

- Job: `v12c_winner_detached_preference_s_pass4`
- Status: `FAIL`
- Decision: `TRAINING_SIGNAL_FAIL`
- Exit code: `0`
- Steps completed: `10` / `10`
- Runtime seconds: `934.1450774669647`
- Mean winner_improvement_post: `0.00011658668518066406`
- Final winner_improvement_post: `-8.320808410644531e-05`
- Mean loser_degradation_post: `-5.3834915161132815e-05`
- Mean winner_contribution_ratio_post: `0.8491498668883544`
- Runner status: `WINNER_DETACHED_PREFERENCE_SIGNAL_FAIL`

## Interpretation

Runtime completed, but the gate failed because final winner improvement was not positive. This is an objective-signal failure, not a runtime PASS. The scheduler correctly did not run `tiny_loser_gradient_preference`, S16/S32/S64, or train400 pilot.

Checkpoint LoRA states were saved locally under `local_assets/` at step0/5/10 and were not pushed. Checkpoint video eval remains pending and no video/metric/visual PASS is claimed.

## Gate Status

- Preflight: PASS.
- Job1 training signal: FAIL.
- Checkpoint video eval: NOT_RUN because training signal failed.
- Metrics: NOT_RUN for checkpoints.
- Codex visual audit: NOT_RUN for checkpoints.
- Scale permission: DENIED.

## Safety

- No unconditional large DPO.
- No StageA / StageB / GRPO / full-data StageA / broad-LoRA.
- No checkpoint deletion.
- No data/weights/video pushed.
- No GPU0-3 assigned by scheduler.
