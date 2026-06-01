# LingBot DPO Backward-Only Dry-Run Report

## Status

- Final result: passed with fallback `tiny_subset`.
- Primary `camera_adapter` attempt: failed with CUDA OOM.
- Training: no.
- Optimizer: no.
- Optimizer step: no.
- Parameter update: no.
- LoRA save: no.
- Checkpoint save: no.

## Attempts

### Attempt 1: `camera_adapter`

- Command output: `local_assets/outputs/smoke/lingbot_dpo_backward_only_dryrun/stdout_stderr_retry.log`
- Summary: `local_assets/outputs/smoke/lingbot_dpo_backward_only_dryrun/grad_summary.json`
- Result: failed.
- Error type: `dpo_backward_only_failed`
- Error: CUDA OOM during backward path.
- Peak allocated memory: about `100.55 GB`.
- Cause: even a bounded camera/control subset retains too much of the DiT graph
  for 480x832, 8-frame LingBot latents.

### Attempt 2: `tiny_subset`

- Command output:
  `local_assets/outputs/smoke/lingbot_dpo_backward_only_dryrun_tiny_subset/stdout_stderr_rerun.log`
- Summary:
  `local_assets/outputs/smoke/lingbot_dpo_backward_only_dryrun_tiny_subset/grad_summary.json`
- Result: passed.
- Trainable params:
  - `head.head.bias`
  - `head.head.weight`
- Trainable param count: `327,744`.
- Frozen param count: `23,788,523,520`.
- Reference params with grad: `0`.

## Loss And Energies

- Beta: `0.1`
- `E_policy_winner`: `0.8652140498161316`
- `E_policy_loser`: `0.8322668075561523`
- `E_ref_winner`: `0.8652140498161316`
- `E_ref_loser`: `0.8322668075561523`
- `Delta_policy`: `-0.03294724225997925`
- `Delta_ref`: `-0.03294724225997925`
- `L_DPO`: `0.6931471824645996`
- Loss finite: yes.

The loss is `log(2)` because policy and reference are still the same checkpoint.
This is expected for a plumbing dry-run.

## Gradient Summary

- Params with grad: `2`
- Params without grad: `0`
- Grad norm min: `0.0008048340096138418`
- Grad norm max: `0.04843546822667122`
- Grad norm mean: `0.02462015111814253`
- Any NaN grad: `false`
- Any Inf grad: `false`
- Reference grad check: passed (`0` params with grad).
- Policy parameter changed check: passed.
- Max abs diff before/after backward with no step: `0.0`.

## Memory

- Final fallback peak allocated: `54,360,615,936` bytes.
- Final fallback reserved: `55,071,211,520` bytes.
- GPU 6/7 returned idle after completion.

## Gate

Backward-only plumbing passed for a tiny policy parameter subset. It did not
pass for the semantically preferred camera/control scope because that scope OOMs
at the current latent size.

Next round may ask for a 1-pair optimizer-step dry-run only if the user
explicitly approves it. Real training remains disallowed.
