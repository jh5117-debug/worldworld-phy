# 5-Pair Tiny Overfit Go / No-Go

Date: 2026-06-04

## Decision

No-go.

## Required Conditions

| Condition | Status |
|---|---|
| At least 2 LR settings completed | not met; only `1e-5` partial |
| Finite losses | met for 3 observed `1e-5` steps |
| No NaN/Inf | met for 3 observed `1e-5` steps |
| No OOM | met, but runtime/memory still high |
| Delta_policy movement clearly above `5.960e-08` baseline | weak; about `4.92e-07` over 3 steps, not enough without multi-LR confirmation |
| Recommended LR exists | not met |
| Base/reference unchanged | previously passed, not enough alone |
| LoRA influence valid | previously passed, but signal remains weak |

## Rationale

The DPO engineering chain is already validated up through 1-pair LoRA backward, one optimizer step, and a 5-step mini-loop. The missing gate is not plumbing; it is signal strength.

This run produced only three `1e-5` steps before it became too slow to keep running. Losses and gradients were finite, but the sweep did not reach the required multi-LR evidence.

Running 5-pair now would not be an informative smoke test.

## Next Action

Do not run 5-pair in this turn. First fix one of:

- faster `dpo_signal_sensitivity_fast` execution with clear per-LR summaries;
- stronger camera-control LoRA target/scope;
- fixed-noise diagnostic with larger but still safe LR/scope.

## 2026-06-04 Retry Update

Decision remains **no-go**.

The short retry used GPU6/7, `learning_rates=1e-5 1e-4`, and `steps_per_lr=3`, but it did not write usable per-LR metrics in the safe runtime window. At least two LR settings did not complete, no recommended LR was established, and there is still no clear signal beyond the previous near-zero baseline.

Do not run 5-pair until the signal runner produces a complete summary with at least two finite LR settings and a clear Delta_policy/preference-logit movement.
