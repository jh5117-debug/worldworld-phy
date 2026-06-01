# LingBot DPO Backward Scope Sweep Report

## Status

- Mode: `dpo_backward_scope_sweep`
- Result: partial.
- Training: no.
- Optimizer: no.
- Optimizer step: no.
- LoRA save: no.
- Checkpoint save: no.
- Reference model: frozen same LingBot-Fast checkpoint.
- Reference grads: `0` for all scopes.
- Raw log:
  `local_assets/outputs/smoke/lingbot_dpo_backward_scope_sweep/stdout_stderr_single_load.log`
- Matrix summary:
  `local_assets/outputs/smoke/lingbot_dpo_backward_scope_sweep/scope_sweep_summary.json`

An earlier sweep attempt was stopped before per-scope results because it
reloaded the policy model for every scope. The successful rerun used a single
policy load and preserved the old raw log without deleting it.

## Scope Matrix

| Scope | Status | Trainable params | Params with grad | Loss | Grad mean | Grad max | Peak memory |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `tiny_subset` | passed | 327,744 | 2 | 0.6931471824645996 | 0.02462015111814253 | 0.04843546822667122 | 54,447,887,872 |
| `head_only` | passed | 337,984 | 3 | 0.6931471824645996 | 0.01708240743028 | 0.04843546822667122 | 54,481,141,760 |
| `plucker_projection_only` | OOM | n/a | n/a | n/a | n/a | n/a | 100,444,744,704 |
| `action_scale_shift_tiny` | OOM | n/a | n/a | n/a | n/a | n/a | 100,477,145,088 |
| `camera_lora_tiny` | skipped | 0 | n/a | n/a | n/a | n/a | 48,238,553,088 |

## Gradient Checks

- `tiny_subset`: finite gradients, no NaN/Inf, no parameter update.
- `head_only`: finite gradients, no NaN/Inf, no parameter update.
- Reference params with grad: `0`.
- `camera_lora_tiny`: skipped because no existing LoRA/PEFT params were present
  and this dry-run does not inject or save LoRA.

## OOM Results

Both camera-aware non-LoRA scopes OOMed despite small trainable parameter
counts:

- `plucker_projection_only` selected only camera projection biases, but those
  are early in the camera/control path and still force a large backward graph.
- `action_scale_shift_tiny` selected late camera scale/shift/injector biases,
  but the full DiT backward graph still exceeded H20 memory at the current
  8-frame 480x832 latent size.

This means parameter count alone is not enough. The next scope needs actual
LoRA/adapter injection or memory reduction, not just selecting existing camera
biases.

## Recommendation

No meaningful camera-aware scope passed. The only passing scopes are output-head
plumbing scopes:

- `tiny_subset`
- `head_only`

Recommended next work:

1. Implement a real LoRA injection path for a tiny camera/control or QKV scope,
   rank 2 or 4.
2. Run the same 1-pair backward-only check with no optimizer and no save.
3. Only after a meaningful camera/LoRA scope passes should the user be asked
   whether to attempt a 1-pair optimizer-step dry-run.

Real DPO training remains disallowed.
