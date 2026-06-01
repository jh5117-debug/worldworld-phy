# Current State Before LoRA / Camera Scope Debug

## Previous Result

- Branch: `physion-dpo-backward-only-dryrun`
- Commit: `0354cac`
- DPO scalar loss passed.
- `L_DPO = 0.6931471824645996`
- `beta = 0.1`
- Policy and reference used the same LingBot-Fast base checkpoint.
- `E_policy_winner = 0.8652140498161316`
- `E_policy_loser = 0.8322668075561523`
- `E_ref_winner = 0.8652140498161316`
- `E_ref_loser = 0.8322668075561523`

## Backward Status

- Backward-only has been tested.
- The semantic `camera_adapter` scope failed with CUDA OOM.
- Peak memory was about 95-100 GB during the failed camera scope attempt.
- The fallback `tiny_subset` passed.

## Tiny Subset

Trainable params:

- `head.head.bias`
- `head.head.weight`

Trainable count: `327,744`.

This subset has limited training meaning. It proves the 1-pair DPO scalar can
backpropagate through the real LingBot forward path while the reference remains
frozen, but it is not the right scope for camera-conditioned adaptation.

## Gate

- Optimizer step: not allowed.
- Real training: not allowed.
- This round is limited to a more meaningful trainable-scope inventory and
  1-pair backward-only sweep.

## Next Action

Test bounded camera-aware scopes such as `action_scale_shift_tiny` and
`plucker_projection_only`, skipping LoRA scopes unless LoRA parameters are
already present.
