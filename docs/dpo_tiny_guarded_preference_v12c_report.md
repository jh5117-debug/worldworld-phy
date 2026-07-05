# DPO Tiny Guarded Preference v12c Report

Current Status: V12C_GPU4_BLOCKED

## What Completed

- PRD/status were created and pushed.
- Setup audit verified `manifests/dpo_v12b_subsets/s_pass_winner_anchor.jsonl` has 4 S_pass pairs.
- Warm-start inventory found loadable v12b step20 LoRA:
  `local_assets/dpo_objective_repair_v12b/winner_curriculum/checkpoints/winner_anchor_repeat_L0_camera_r4_step020_lora_state.pt`
- Warm-start LoRA SHA256: `cc0b0833d63b94902cb426b5594dd00dcefc911b59e4e919183398c047b57baf`.
- Warm-start LoRA params: `6553600`.
- Local mask audit found 3/4 pairs are local-mask ready.
- Implemented v12c probe wrapper and runner support for:
  - `winner_detached_preference`
  - `tiny_loser_gradient_preference`
  - `linear_winner_detached`
  - `--init_lora_state` warm-start loading.

## What Did Not Run

- `winner_detached_preference` did not start.
- `tiny_loser_gradient_preference` did not start.
- `linear_winner_detached` did not start.
- No checkpoint video eval was run because no objective ran.
- No metrics were run for v12c checkpoints.

## Blocker

Physical GPU4 was repeatedly occupied by non-project `eval_libero_single.py gpu_id=4` processes during the v12c launch window. The hard GPU policy forbids fallback to GPU0/1/2/3/5/6/7 and forbids killing unknown tasks.

Decision: `V12C_GPU4_BLOCKED`.

## Next Exact Command When GPU4 Is Free

```bash
CUDA_VISIBLE_DEVICES=4 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True python3 -m cam_physgeo.dpo.dpo_v12c_guarded_probe   --train_manifest manifests/dpo_v12b_subsets/s_pass_winner_anchor.jsonl   --val_manifest manifests/dpo_v12b_subsets/s_pass_winner_anchor.jsonl   --scope L0_camera_r4   --objective winner_detached_preference   --steps 10   --beta 0.1   --lambda_winner_anchor 1.0   --lambda_pref 0.02   --lambda_loser 0.0   --gpu 0   --prefix_len 5   --prediction_start_frame 5   --future_only true   --output_root local_assets/dpo_tiny_guarded_preference_v12c/winner_detached_preference   --report_root reports/dpo_tiny_guarded_preference_v12c/winner_detached_preference
```

## Safety Confirmation

- No DPO / SDPO / Linear-DPO objective ran.
- No large DPO, S1/S2/S3, train400, StageA, StageB, GRPO, or broad-LoRA ran.
- No checkpoint/data/weights were deleted.
- No videos, images, checkpoints, tensors, or weights are staged for Git.
