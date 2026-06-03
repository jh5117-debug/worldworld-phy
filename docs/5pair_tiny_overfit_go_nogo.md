# 5-Pair Tiny Overfit Go / No-Go

## Decision

No-go.

## Reason

The 5-pair tiny overfit gate requires:

- LoRA functional influence confirmed;
- at least two LR settings completed in a fixed-noise signal sweep;
- nonzero and interpretable `Delta_policy` movement;
- finite loss and finite gradients;
- no OOM;
- base/reference unchanged;
- no LoRA/checkpoint save.

The first condition was already true from prior work, but the optimized
`dpo_signal_sensitivity_fast` sweep did not complete on GPU in this run because
remote SSH access became unstable after the TDW smoke. Therefore the signal gate
is still incomplete.

## Allowed Next Step

Run only the 1-pair fast signal sweep on GPU6/7 when access is stable.

## Not Allowed

- No 5-pair overfit yet.
- No 10-pair or multi-pair DPO.
- No real DPO training.
- No LoRA save.
- No checkpoint save.
