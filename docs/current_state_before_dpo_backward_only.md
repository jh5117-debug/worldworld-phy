# Current State Before DPO Backward-Only

## Previous Gate

- DPO scalar loss dry-run: passed.
- Backward: not tested yet.
- Optimizer: not allowed.
- Training: not allowed.
- Current run limit: 1 pair only.

## Scalar Loss Inputs

- Beta: `0.1`
- Policy/reference checkpoint relation: same LingBot-Fast checkpoint.
- Reference role: frozen same-checkpoint reference, not Base, not reward, not
  VideoGPA native model.

Policy energy:

- `E_policy_winner`: `0.8652140498161316`
- `E_policy_loser`: `0.8322668075561523`
- `Delta_policy`: `-0.03294724225997925`

Reference energy:

- `E_ref_winner`: `0.8652140498161316`
- `E_ref_loser`: `0.8322668075561523`
- `Delta_ref`: `-0.03294724225997925`

DPO scalar:

- `L_DPO`: `0.6931471824645996`
- `dpo_argument`: `0.0`
- Expected because policy and reference are the same frozen checkpoint.

## Batch and Condition

- Batch path: `local_assets/outputs/smoke/lingbot_dpo_batch_dryrun`
- Winner/loser latent shape: `[16, 2, 60, 104]`
- Temporal compression: `4x`
- Spatial compression: `8x`
- Same noise: confirmed.
- Same timestep: confirmed.
- Example timestep: `579`
- Reward margin: `0.5240882262358174`
- Condition includes image, prompt, poses, converted intrinsics, dummy action
  compatibility path, and LingBot Plucker/control tensor.
- Plucker/control tensor shape: `[1, 448, 2, 60, 104]`
- Dummy action norm: `0.0`
- `use_action=false` remains mandatory.

## This Round

Allowed:

- select a tiny policy trainable scope;
- compute real reference energy under `no_grad`;
- compute differentiable policy energy;
- compute scalar DPO loss;
- call `loss.backward()`;
- inspect and clear gradients.

Not allowed:

- optimizer;
- optimizer step;
- parameter update;
- LoRA save;
- checkpoint save;
- VideoGPA `03_train.py`;
- real DPO training.
