Current Status: V12D_PRD_READY_SCHEDULER_PENDING

# DPO GPU Scheduler v12d Status

Updated: 2026-07-05 10:30:04

## Current State

- Canonical repaired ready500 exists at `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`.
- Repaired train/val/test/top50 splits exist and the deprecated old ready500 entry must not be used.
- v12 failed on a mixed 32-pair guarded DPO probe because winner improvement became negative and the objective stayed near no-signal.
- v12b filtered the data to S_pass4 and winner-only curriculum passed with mean `winner_improvement_post = 5.76973e-05`, final `winner_improvement_post = 5.87106e-05`, and mean winner contribution ratio `0.579694`.
- v12c code and setup are prepared, but the prior execution did not train because GPU4 was blocked.
- Current user authorization allows H20 physical GPU4, GPU5, GPU6, and GPU7 only. GPU0-3 are forbidden.

## v12d Objective

Implement and launch a gated GPU4-7 scheduler that starts with v12c `winner_detached_preference` on S_pass4, then advances only through explicit gates: training signal, checkpoint video generation, metrics, and Codex visual audit.

## Hard Safety Rules

- Do not use physical GPU0, GPU1, GPU2, or GPU3.
- Do not kill unknown GPU processes.
- Do not run unconditional large DPO.
- Do not run StageA, StageB, GRPO, full-data StageA, or broad-LoRA.
- Do not delete checkpoint, data, or weights.
- Do not push videos/images/local_assets/checkpoints/weights/large logs.

## First Scheduled Training Job

`v12c_winner_detached_preference_s_pass4` should run with `CUDA_VISIBLE_DEVICES=<one of 4,5,6,7>` and process-local `--gpu 0`. It must use the v12b winner-only warm start:

`local_assets/dpo_objective_repair_v12b/winner_curriculum/checkpoints/winner_anchor_repeat_L0_camera_r4_step020_lora_state.pt`

## Scale Gate

Train400 pilot is not allowed unless S_pass4, checkpoint video eval, metrics, S_pass expansion, S16, S32, and S64 gates pass. Even then, train400 pilot is capped at 100 steps.
