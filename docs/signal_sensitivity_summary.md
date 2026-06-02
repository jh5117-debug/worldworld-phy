# DPO Signal Sensitivity Summary

## Inputs Checked

Available reports:

- `docs/lora_functional_influence_probe_report.md`
- `docs/dpo_lr_sensitivity_sweep_report.md`
- `docs/dpo_scope_sensitivity_sweep_report.md`
- `docs/prior_art_dpo_signal_sensitivity_review.md`
- `docs/dpo_sign_beta_diagnostic_report.md`

Missing before this summary:

- `docs/final_report_dpo_signal_sensitivity.md`
- `docs/github_push_report_dpo_signal_sensitivity.md`

## Results

1. LoRA functional influence: passed.
2. `no_lora` and `lora_zero` matched exactly, confirming zero LoRA contribution
   does not perturb the frozen base path.
3. `default_lora` changed predictions but changed the energy delta by only
   about `5.960e-08`.
4. Scaled LoRA changed energy:
   - `lora_scaled_10x` delta change: `2.906e-06`;
   - `lora_scaled_100x` delta change: `-1.922e-06`.
5. Current target modules affect the real forward path:
   - `blocks.39.cam_shift_layer`;
   - `blocks.39.cam_scale_layer`.
6. LR sweep did not establish a stronger signal. The full sweep was
   runtime-blocked after about `36m57s` with about `54 GiB` allocated on GPU 6.
7. Fallback `lr=1e-4`, one fixed-noise/fixed-timestep step passed safely, but
   the preference logit remained tiny at about `2.831e-08`.
8. NaN / Inf: none observed in the completed signal diagnostics.
9. OOM: none in the completed signal diagnostics; full LR sweep was terminated
   for runtime, not OOM.
10. Scope sweep: skipped because the LR sweep was runtime-blocked and a broader
    scope would have increased memory/runtime risk without a proven current
    scope signal.
11. Recommended scope remains provisional:
    - current safe scope: `blocks.39.cam_shift_layer`,
      `blocks.39.cam_scale_layer`;
    - next diagnostic scope: last two camera shift/scale blocks, only with an
      optimized runner.
12. Recommended LR remains provisional:
    - `1e-4` is safe for one step;
    - no multi-step LR sweep completed, so it is not a strong recommendation
      for 5-pair expansion.

## Gate Decision

Do not enter 5-pair tiny overfit in this round.

The gate requires a stable LR, no NaN/Inf/OOM, a clear nonzero signal, and a
recommended scope. While LoRA is connected to the forward path and scaled LoRA
changes energy, the default rank-2 camera-control signal is extremely weak, the
full LR sweep did not complete, and no broader scope was tested.

## Blocker

The blocker is not DPO plumbing. The blocker is weak, insufficiently
characterized learning signal:

- default LoRA energy movement is near numerical noise;
- fallback higher-LR run was only one step;
- scope sensitivity was skipped;
- expanding pair count would mostly test dataloader stability, not whether the
  DPO signal is learnable.

## Next Minimal Fix

Before 5-pair / 10-pair tiny overfit:

1. Optimize the sensitivity runner so it reuses loaded policy/reference models.
2. Run a bounded fixed-noise LR sweep for `current` scope, e.g. `1e-5`,
   `5e-5`, `1e-4`, `5e-4`, each for 1-3 steps.
3. If still weak, test `last2_blocks_camera` with rank-2 LoRA and the same
   fixed-noise diagnostic.
4. Keep no-save/no-checkpoint/no-real-training constraints.

Real DPO training remains disallowed.
