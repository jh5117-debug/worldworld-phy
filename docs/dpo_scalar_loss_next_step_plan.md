# DPO Scalar Loss Next Step Plan

## Current Status

The 1-pair policy energy dry-run passed with real LingBot-Fast forward and a
code-backed flow target. No DPO scalar loss was computed in this round.

## Formula Only

For the next approved dry-run, use prediction-error energies:

```text
E_policy_w = MSE(policy_pred_w, target_w)
E_policy_l = MSE(policy_pred_l, target_l)
E_ref_w    = MSE(ref_pred_w, target_w)
E_ref_l    = MSE(ref_pred_l, target_l)

delta_policy = E_policy_l - E_policy_w
delta_ref    = E_ref_l - E_ref_w

L_dpo = -log_sigmoid(beta * (delta_policy - delta_ref))
```

Lower energy means better denoising/velocity prediction. The loser-minus-winner
delta should be compared against the frozen reference delta.

## Required Constraints

- User confirmation is required before running this scalar-loss dry-run.
- Still max 1 pair.
- No training loop.
- No optimizer.
- No LoRA save.
- No checkpoint save.
- Prefer no backward first. If backward is desired later, ask explicitly.
- Reference model must be real and frozen, not deferred or faked.

## Current Blocker For Scalar Loss

Reference energies are deferred. The next minimum step is to load or otherwise
evaluate a real frozen reference model under memory constraints, then compute
the formula above without parameter updates.
