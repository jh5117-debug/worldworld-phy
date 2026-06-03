# DPO Signal Sensitivity Fast Report

## Status

Implemented, not completed on GPU in this run.

The adapter now has a bounded `dpo_signal_sensitivity_fast` mode that reuses
policy/reference model loads for a short fixed-noise LR sweep. The GPU6/7 sweep
did not complete in this run:

1. The first remote launch exited before model load because the non-login shell
   did not have a `python` executable.
2. The corrected launch using the LingBot env Python was blocked by repeated SSH
   reset/timeouts before the process could be safely started and monitored.

## Implemented Mode

```bash
CUDA_VISIBLE_DEVICES=6,7 TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 \
python -m cam_physgeo.dpo.lingbot_fast_videogpa_adapter \
  --mode dpo_signal_sensitivity_fast \
  --config configs/cam_physgeo/videogpa_adapter.yaml \
  --batch local_assets/outputs/smoke/lingbot_dpo_batch_dryrun \
  --out local_assets/outputs/smoke/lingbot_dpo_signal_sensitivity_fast \
  --limit_pairs 1 \
  --beta 0.1 \
  --device cuda \
  --dtype bf16 \
  --trainable_scope camera_control_lora_tiny \
  --lora_rank 2 \
  --lora_alpha 4 \
  --target_modules blocks.39.cam_shift_layer,blocks.39.cam_scale_layer \
  --learning_rates 1e-5 5e-5 1e-4 \
  --steps_per_lr 5 \
  --fixed_noise_seed 123 \
  --fixed_timestep 579 \
  --resample_noise_each_step false \
  --resample_timestep_each_step false \
  --max_grad_norm 1.0 \
  --no_save_lora true \
  --no_checkpoint true \
  --reuse_model_load true \
  --restore_after_each_lr true
```

## Reuse Behavior

- Reference model is loaded once.
- Policy model is loaded once.
- Batch tensors are loaded once.
- Reference energy is cached for fixed-noise/fixed-timestep steps.
- LoRA params are restored to their initial runtime state before each LR.
- No LoRA is saved.
- No checkpoint is saved.
- No real training loop is entered.

Forward conditions are rebuilt per step to avoid reusing mutable LingBot KV
cache state. This is intentionally conservative; it still removes the largest
previous overhead, repeated model loading.

## Previous Signal Context

Previous reports showed:

- LoRA functional influence passed.
- Scaled LoRA changes energy, so the target modules are active.
- Default rank-2 energy movement was around `5.960e-08`.
- A full LR sweep was runtime-blocked.
- `lr=1e-4` one-step fallback passed, but preference logit stayed around
  `2.831e-08`.

## Gate Decision

Signal gate remains weak / incomplete.

5-pair tiny overfit is not allowed from this report state because the fast
multi-LR sweep did not complete on GPU.

## Next Minimal Action

When SSH/GPU access is stable, run the command above on GPU6/7 only. If at least
two LR settings complete with finite gradients and a nonzero `Delta_policy`
movement above the configured threshold, then write a new go/no-go report for
5-pair tiny overfit.
