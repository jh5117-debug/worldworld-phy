Current Status: V12D_SCHEDULER_LAUNCHED_JOB1_RUNNING

# DPO GPU Scheduler v12d Status

Updated: 2026-07-05 10:49:58

## Scheduler

- Tmux session: `dpo_gpu_scheduler_v12d`
- State path: `reports/dpo_gpu_scheduler_v12d/scheduler_state.json`
- Heartbeat path: `reports/dpo_gpu_scheduler_v12d/heartbeat.jsonl`
- Log path: `reports/dpo_gpu_scheduler_v12d/scheduler.log`
- Scheduler launched: yes

## GPU Policy

- Allowed physical GPUs: GPU4, GPU5, GPU6, GPU7.
- Forbidden physical GPUs: GPU0, GPU1, GPU2, GPU3.
- First assigned GPU: `[4]`.
- Current Job1 status: `RUNNING`.
- Current Job1 PID: `1770752`.
- Scheduler command uses `CUDA_VISIBLE_DEVICES=4` and process-local `--gpu 0` for Job1.
- GPU0-3 are not assigned by the scheduler; they are only observed as forbidden/occupied by pre-existing external tasks.

## Job1 Interim Signal

- Training rows written so far: `3` / 10.
- Latest step: `2`.
- Latest winner_improvement_post: `0.00027298927307128906`.
- Latest loser_degradation_post: `-2.9802322387695312e-05`.
- Latest winner_contribution_ratio_post: `1.0`.
- Latest grad_norm: `0.1475002238037069`.
- Latest update_norm: `0.002278683235194764`.

## Gate Status

- Preflight: PASS.
- Job1 `winner_detached_preference`: RUNNING, not yet PASS.
- Checkpoint video eval: PENDING, required before any further training.
- Metrics: PENDING, required before any further training.
- Codex visual audit: PENDING, required before any further training.
- Tiny loser-gradient / S16 / S32 / S64 / train400 pilot: not allowed unless gates pass.

## Safety

- No unconditional large DPO.
- No StageA / StageB / GRPO / broad-LoRA.
- No checkpoint deletion.
- No video/image/local_assets/weights/checkpoints pushed.
