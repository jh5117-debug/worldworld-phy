# Final Report: DPO Trainable Scope Sweep

## Gates

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: partial/pass. Backward-only plumbing works for output-head scopes,
  but no meaningful camera-aware scope passed.
- Gate F: no. Real DPO training remains disallowed.

## Execution

- Local git worktree: `/tmp/local_assets_work`
- Remote main worktree checked:
  `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys`
- Remote execution directory:
  `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_energy_forward_work`
- Branch: `physion-dpo-trainable-scope-sweep`
- Base commit: `0354cac`
- Remote execution `local_assets` symlinks to the same shared asset tree used by
  the main project.
- No data, weights, videos, latents, HDF5, NPY, PT, PTH, safetensors, or
  checkpoints were moved or deleted.
- No `local_assets` content is staged or committed.
- Final GPU check: GPU 6 and GPU 7 were idle at `1 MiB` used and `0%`
  utilization after the sweep.

## Prior Art

VideoGPA official training scripts use LoRA/PEFT as the intended trainable
mechanism. Wan VideoGPA targets attention projections such as `q`, `k`, `v`,
and `o`; CogVideo targets `to_q`, `to_k`, `to_v`, and `to_out.0`. Reference
models are separately loaded, frozen, and evaluated under `no_grad`.

LingBot has local LoRA utilities in `scripts/train_lingbot_dpo_lora.py`, but
the currently loaded LingBot-Fast model has no existing LoRA params. This round
therefore skipped LoRA scopes rather than injecting or saving adapters.

## Scope Inventory

Camera-related modules found:

- `patch_embedding_wancamctrl`
- `c2ws_hidden_states_layer1`
- `c2ws_hidden_states_layer2`
- `blocks.*.cam_injector_layer1`
- `blocks.*.cam_injector_layer2`
- `blocks.*.cam_scale_layer`
- `blocks.*.cam_shift_layer`

Parameter counts:

- Full `camera_adapter`: `4,255,431,680` params.
- Safe `action_scale_shift_tiny` preview: `819,200` params.
- Safe `plucker_projection_only` preview: `15,360` params.
- `head_only`: `337,984` params.
- `tiny_subset`: `327,744` params.
- Existing LoRA: none.

## Scope Sweep

| Scope | Status | Trainable params | Params with grad | Loss | Peak memory |
| --- | --- | ---: | ---: | ---: | ---: |
| `tiny_subset` | passed | 327,744 | 2 | 0.6931471824645996 | 54,447,887,872 |
| `head_only` | passed | 337,984 | 3 | 0.6931471824645996 | 54,481,141,760 |
| `plucker_projection_only` | OOM | n/a | n/a | n/a | 100,444,744,704 |
| `action_scale_shift_tiny` | OOM | n/a | n/a | n/a | 100,477,145,088 |
| `camera_lora_tiny` | skipped | 0 | n/a | n/a | 48,238,553,088 |

Gradient checks:

- Passing scopes had finite gradients.
- No NaN/Inf gradients were observed.
- Reference params with grad: `0`.
- No optimizer was constructed.
- No optimizer step was run.
- No parameter update was performed.
- No LoRA or checkpoint was saved.

## Recommendation

No meaningful camera-aware existing-parameter scope passed. The best passing
scope remains `head_only`/`tiny_subset`, which is useful only for plumbing.

Recommended next scope: none from existing params. The next minimal action is
to implement a real tiny LoRA/camera adapter injection path, likely rank 2 or 4,
then rerun backward-only with no optimizer and no save.

This is better than `tiny_subset` because it would target camera/control or
attention adaptation rather than the output head. It is safer than full
`camera_adapter` because it avoids opening billions of camera/control params and
should reduce backward memory.

## Next Gate

Next round may not do an optimizer-step dry-run yet. It should first make a
meaningful LoRA/camera scope pass backward-only.

Real DPO training is still no.

## Physion / TDW

No TDW/Physion generation was executed. The staged plan remains:

1 sample dry-run -> 10 sample smoke -> 50 validation -> 200 pilot -> 1k+ only
after explicit storage/runtime approval.
