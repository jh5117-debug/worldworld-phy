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



## Current Status Update (2026-06-27 01:28:06)

- screen16 artifacts are available.
- full80 all-checkpoint rollout is incomplete; current full80 covers `GT, original_fast, D_step050` only.
- prefix-aware conditioning code and tests are implemented.
- diagnostic DPO preflight status: `PASS`.
- LingBot-Fast DPO backend status: `BLOCKED_FAST_ENERGY_BACKEND`.
- DPO probe remains blocked until real winner/loser energy is callable.


## Prefix-5 Pair Rebuild Status (2026-06-27 03:24:08)

- Old anchored pairs were I2V-1 / first-image conditioned, not V2V-5.
- New manifest: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`.
- Pair count: `50`.
- Valid prefix5 pair count: `50`.
- Prefix clips use frames 0-4; winner/loser futures use frames 5-80.
- DPO loss/reward masks are `5..80`.
- Real DPO remains blocked until LingBot-Fast winner/loser energy backend and BF16 DDP preflight are available.
