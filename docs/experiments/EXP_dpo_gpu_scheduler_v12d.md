# EXP_dpo_gpu_scheduler_v12d

## Current Status

- Canonical repaired ready500 exists at `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`.
- Metric smoke is available: LPIPS real smoke PASS, VBench `temporal_flickering` real smoke PASS, and FVD TorchScript I3D smoke PASS with scope caveats.
- v12 failed on 32-pair mixed guarded DPO: winner became worse and the preference objective stayed near no-signal.
- v12b S_pass4 winner-only curriculum passed with mean `winner_improvement_post = 5.76973e-05`, final `winner_improvement_post = 5.87106e-05`, and mean winner contribution ratio `0.579694`.
- v12c code was prepared but GPU4 was blocked, so tiny preference training did not start.
- Current user authorization allows physical GPU4-7 and forbids GPU0-3.
- Current task is a gated scheduler plus v12c/v12d execution, not unconditional large DPO.

## Problem

- GPU idle time wastes iteration, but direct large DPO is unsafe.
- DPO can become loser-dominant and appear to improve by pushing the loser worse instead of preserving the winner.
- Training must be gated by winner signal, checkpoint videos, metrics, and Codex visual audit.
- The scheduler must automatically switch to data/eval tasks if a training gate fails, instead of forcing more training.

## Hypothesis

A gated GPU scheduler can keep GPU4-7 utilized while preserving safety. `winner_detached_preference` on S_pass4 is the first valid next step. If S_pass4 passes, the system can scale through S_pass8/S16/S32/S64. Only if all tiny/small gates pass may a train400 pilot run, capped at 100 steps. If any signal, video, metric, or visual gate fails, no scaling is allowed.

## GPU Policy

- Allowed physical GPUs: `[4, 5, 6, 7]`.
- Forbidden physical GPUs: `[0, 1, 2, 3]`.
- All train/eval/rollout commands must set `CUDA_VISIBLE_DEVICES` to a subset of physical GPU4-7.
- The process-local device argument must be `--gpu 0` for a single assigned physical GPU.
- If an unknown process occupies a GPU, the scheduler marks that GPU unavailable and does not kill it.
- If a scheduler-started process is detected on GPU0-3, the scheduler must stop only its own process and mark the run failed.

## Success Gate

- Scheduler starts under tmux session `dpo_gpu_scheduler_v12d`.
- Scheduler uses only physical GPU4-7 and never schedules GPU0-3.
- `v12c_winner_detached_preference` starts when an allowed GPU is free.
- Each training checkpoint has real V2V-5 video generation, metrics, contact sheets, and Codex visual audit before any scale-up decision.
- Training gates require positive mean/final winner improvement, nonzero gradients and updates, no OOM/NaN/SIGFPE, no loser-dominant margin, and no no-signal fake pass.
- Video gates require all expected videos/contact sheets, `reviewed=true`, non-empty reasons, no visual degradation, no increased freeze, and no worse identity/background/camera/reobserve behavior.
- Metric gates require PSNR/SSIM/LPIPS/FVD-smoke/VBench temporal flickering/PhysGeo to be non-degrading or to record exact `BLOCKED_BY_ENV` without fabrication.

## Failure Gate

- Any scheduler process uses physical GPU0-3.
- Scheduler starts train400 before all tiny/small gates pass.
- Checkpoint video eval is missing but scale proceeds.
- Winner signal is negative or loser-dominant.
- Visual audit detects degradation.
- Metrics degrade without an explicit stop.
- Unknown GPU process is killed.
- Videos/images/local_assets/checkpoints/weights are staged or pushed.

## Job Queue

1. `preflight_state_check`: no GPU. Verify canonical manifests, S_pass4 manifest, warm-start LoRA, metric backend summaries, GPU4-7 state, and duplicate scheduler status.
2. `v12c_winner_detached_preference_s_pass4`: one allowed GPU, preferred physical GPU4. Run 10 steps from v12b warm start.
3. `v12c_checkpoint_eval_winner_detached`: depends on Job 1 PASS. Generate real checkpoint videos for step0/5/10, metrics, contact sheets, and Codex audit.
4. `v12c_tiny_loser_gradient_preference`: depends on Job 1 and Job 2 PASS. Tiny loser-gradient probe with max loser lambda 0.05.
5. `checkpoint_eval_tiny_loser_gradient`: depends on Job 4 PASS. Same video/metric/audit gates.
6. `build_s_pass8_or_s16`: audit/expand S_pass subset only after earlier gates.
7. `s_pass16_guarded_preference`: max 20 steps, checkpoint eval required.
8. `s32_guarded_preference`: max 20 steps, checkpoint eval required.
9. `s64_small_probe`: max 50 steps, checkpoint eval required.
10. `train400_pilot_100step`: only if all previous gates pass and `safe_to_train400_pilot=true`; capped at 100 steps.

## Fallback Behavior

If a training gate fails, the scheduler must not continue training. It may run non-training fallback tasks only: LocalDPO spatial mask audit, real rollout expansion smoke, expanded LPIPS/FVD/VBench/PhysGeo metric QA, PPT/QA contact sheet packaging, or pair source balance reports.

## Outputs

- `reports/dpo_gpu_scheduler_v12d/scheduler_state.json`
- `reports/dpo_gpu_scheduler_v12d/heartbeat.jsonl`
- `reports/dpo_gpu_scheduler_v12d/job_events.jsonl`
- `reports/dpo_gpu_scheduler_v12d/gpu_usage.csv`
- `reports/dpo_gpu_scheduler_v12d/final_summary.md`
- `reports/dpo_gpu_scheduler_v12d/jobs/*.json`
- `reports/dpo_gpu_scheduler_v12d/jobs/*.md`

## What Is Not Run

- No unconditional large DPO.
- No StageA.
- No StageB.
- No GRPO.
- No full-data StageA.
- No broad-LoRA.
- No checkpoint deletion.
- No video/image/local_assets/weight/checkpoint push.

## Initial Decision

Proceed with implementation and launch of the GPU4-7 gated scheduler. The first executable training step is v12c `winner_detached_preference` on S_pass4. Train400 pilot is not allowed at PRD start.
