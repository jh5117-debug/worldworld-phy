# EXP Prefix-Aware Anchored DPO Probe (2026-06-27 04:43:53)

Status: PRE-DPO PREFLIGHT. No DPO probe has been launched yet.

## Hypothesis

A prefix-aware anchored DPO probe can provide a meaningful preference signal only if the energy backend scores future frames 5-80 while conditioning on clean prefix frames 0-4, prompt, poses, and intrinsics.

## Active Pair Manifest

`manifests/anchored_dpo_probe_pairs_prefix5.jsonl`

- pair count: 50
- prefix_len: 5
- prediction_start_frame: 5
- loss_frame_indices: 5..80
- reward_frame_indices: 5..80
- readiness summary: `reports/dpo_prefix5_pair_visual_audit/prefix5_training_readiness_summary.md`

## Backend

- Policy: LingBot-World-Fast high-only camera model with LoRA trainable parameters.
- Reference: same base model with LoRA scaling disabled under no_grad.
- Energy: flow-matching prediction error on strict future latent slots only.
- Same timestep/noise: required for winner and loser.
- use_action: false.

## BF16 Policy

- DiT / LoRA mixed-safe BF16 path.
- VAE FP32 by Stage1 precision environment.
- Camera/projection and loss reduction are kept stable through Stage1 helper policies.

## Gates

1. Single GPU7 2-step preflight must pass.
2. DDP2 GPU6,7 5-step preflight must pass.
3. DDP8 GPU0-7 5-step preflight must pass.
4. Tiny DPO probe may run only after the above gates pass.

## Stop Conditions

- Any nonfinite energy/loss.
- SIGFPE, OOM, or exit code 136.
- Reference has trainable params or receives gradients.
- Winner/loser do not share timestep/noise.
- Prefix frames enter loss mask.

## Current Decision

Do not scale DPO. Real BF16 preflight is the next gate.


---

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
