# LingBot DPO Scalar Loss Dry-Run Report

## Status

- Result: passed.
- Mode: `dpo_scalar_loss_dryrun`
- Pair count: 1
- Training: no.
- Backward: no.
- Optimizer: no.
- Parameter update: no.
- LoRA save: no.

## Inputs

- Policy energy source: `local_assets/outputs/smoke/lingbot_energy_logprob_dryrun_v2`
- Reference energy source: `local_assets/outputs/smoke/lingbot_reference_energy_dryrun`
- Beta: `0.1`

## Energies

- `E_policy_winner`: `0.8652140498161316`
- `E_policy_loser`: `0.8322668075561523`
- `E_ref_winner`: `0.8652140498161316`
- `E_ref_loser`: `0.8322668075561523`
- `Delta_policy`: `-0.03294724225997925`
- `Delta_ref`: `-0.03294724225997925`
- `dpo_argument`: `0.0`
- `L_DPO`: `0.6931471824645996`
- Loss finite: yes.

## Sign Convention

Energy is MSE against the LingBot/Wan flow target, so lower energy means higher
model likelihood under this denoising-error proxy.

- `Delta = E_loser - E_winner`
- Positive delta means winner has lower energy than loser.
- Formula used:
  `L_DPO = -log sigmoid(beta * (Delta_policy - Delta_ref))`

Because policy and reference are the same frozen checkpoint in this smoke,
`Delta_policy == Delta_ref`, so the argument is zero and the loss is
approximately `log(2)`. This is meaningful as a plumbing/sign check, not as a
preference-improvement result.

## Next Gate

Next round may do a 1-pair backward-only dry-run only if the user explicitly
approves it. Constraints should remain:

- max 1 pair;
- real policy/reference energies;
- no optimizer;
- no training loop;
- no checkpoint or LoRA save.

Real DPO training remains disallowed.
