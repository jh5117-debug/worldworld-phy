# EXP Prefix-Aware Anchored DPO Probe

Status: blocked_until_real_trainer

## Question

Can a tiny anchored DPO probe improve future-segment generation without degrading foreground identity, quality, or camera adherence?

## Current Blocker

`cam_physgeo/training/train_stage2_anchored_dpo.py` is still guarded and does not run a real LingBot-Fast policy/reference DPO optimization step.

## Required Real Path

The trainer must:

- load LingBot-Fast policy
- load frozen LingBot-Fast reference
- initialize policy from selected checkpoint or Original Fast
- encode condition, winner future, and loser future
- use the same timestep and same noise for winner and loser
- compute policy and reference energies on the future segment only
- compute anchored DPO loss
- backpropagate only through the expected LoRA parameters
- save adapter-only checkpoints
- verify save/load and resume

## Default Pair Type

Start with anchored pairs:

- clean GT future > corrupted GT future
- clean GT future > quality-qualified bad rollout future

Avoid using bad top rollout > worse bottom rollout as the main pair source.

## Prefix

Default probe prefix length: `prefix_len=5`.

## Gate

Do not scale DPO unless:

- DPO loss has non-saturated signal
- winner improvement is positive
- the policy does not merely degrade the loser
- FG-ID and quality do not regress
- checkpoint rollout videos pass Codex visual audit

