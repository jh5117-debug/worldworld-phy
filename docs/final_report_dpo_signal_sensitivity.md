# Final Report: DPO Signal Sensitivity

## Status

Partial / blocked for pair-count expansion.

The diagnostic confirms that the tiny camera-control LoRA is connected to the
LingBot-Fast forward path, but the default rank-2 signal is too weak and too
under-characterized to justify a 5-pair tiny overfit run.

## Git / Remote

- Worktree used for consolidation: `/tmp/local_assets_work`
- Branch: `physion-dpo-signal-sensitivity`
- Correct repo: `jh5117-debug/worldworld-phy`
- Remote: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`
- `local_assets`: untracked local asset root; no asset files committed.
- Moved/deleted assets: no.

## Functional Influence

- Status: passed.
- Target modules:
  - `blocks.39.cam_shift_layer`
  - `blocks.39.cam_scale_layer`
- Rank/alpha: `2 / 4.0`
- `no_lora` and `lora_zero`: identical energies and predictions.
- `default_lora`: changes predictions, but energy delta movement is only
  `5.960e-08`.
- `lora_scaled_10x`: energy delta movement increases to `2.906e-06`.
- `lora_scaled_100x`: energy delta movement is `-1.922e-06`.

Interpretation: the LoRA path is active, but normal-scale contribution is very
small.

## LR Sensitivity

- Full sweep requested: `1e-5`, `5e-5`, `1e-4`, `5e-4`.
- Full sweep status: runtime-blocked / terminated.
- Blocker: no first LR summary after about `36m57s`; GPU allocation held around
  `54 GiB`; not an OOM.
- Fallback: `lr=1e-4`, one fixed-noise/fixed-timestep step passed.
- Fallback preference logit: `2.831e-08`.
- NaN/Inf: no.
- OOM: no in completed fallback.

Interpretation: `1e-4` is safe for one step, but it does not prove a stronger
multi-step signal.

## Scope Sensitivity

- Scope sweep: skipped.
- Reason: the LR sweep was runtime-blocked; broader camera scopes would have
  added memory/runtime risk before the current scope signal was understood.
- Current safe scope remains:
  - `blocks.39.cam_shift_layer`
  - `blocks.39.cam_scale_layer`
- Next candidate only after optimized runner:
  - last two camera shift/scale blocks.

## Sign / Beta

The sign convention remains consistent:

```text
Delta = E_loser - E_winner
L_DPO = -log sigmoid(beta * (Delta_policy - Delta_ref))
```

Increasing beta alone does not solve the issue because the underlying
`Delta_policy - Delta_ref` gap is around `1e-7` to `1e-8` in the completed
diagnostics.

## Gate Decision

5-pair tiny overfit is not allowed in this branch state.

Reasons:

- LoRA functional influence passed.
- Energy effect is real under scaling, but default signal is very weak.
- Stable multi-step LR was not established.
- Scope recommendation is provisional, not validated.
- Pair-count expansion would risk confusing dataloader stability with learning
  signal quality.

Real DPO training remains disallowed.

## Next Minimal Action

Optimize and rerun signal sensitivity before expanding pairs:

1. Reuse loaded policy/reference models in the LR/scope sweep runner.
2. Run short fixed-noise LR sweeps.
3. Test `last2_blocks_camera` only if the current scope remains weak.
4. Keep LoRA/checkpoint saving disabled.
