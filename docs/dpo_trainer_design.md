# Anchored DPO Trainer Design

Updated: 2026-06-27 01:28:06

## Implemented In This Pass

- `cam_physgeo.dpo.dpo_loss` now uses energy-form anchored DPO:
  - lower energy is better;
  - `Delta_policy = E_policy(loser) - E_policy(winner)`;
  - `Delta_ref = E_ref(loser) - E_ref(winner)`;
  - `L = -logsigmoid(beta * (Delta_policy - Delta_ref))`.
- `cam_physgeo.training.train_stage2_anchored_dpo` is no longer a guarded placeholder.
- The trainer can load anchored pairs, verify pair assets, enforce same noise/timestep, run a diagnostic DPO optimizer step, and save/load a tiny adapter state.

## Real LingBot-Fast Backend Status

Status: `BLOCKED_FAST_ENERGY_BACKEND`

Reason: LingBot-Fast rollout initialization is available in prior artifacts, but the anchored DPO energy path has not yet exposed a callable winner/loser flow-matching energy function with frozen reference.

The diagnostic backend is intentionally not presented as real LingBot-Fast DPO. It validates plumbing and loss direction only.

## Pair Source

- Pair manifest: `local_assets/overnight_quant_lora_dpo_20260624_overnight_test/anchored_pairs/anchored_dpo_probe_pairs.jsonl`
- Pair count: `50`
- Default DPO prefix target: prefix-aware V2V-5 in the next real backend pass.

## Remaining Required Work

1. Expose a callable LingBot-Fast flow-matching energy function for arbitrary winner/loser videos.
2. Instantiate policy and frozen reference with identical initialization.
3. Encode condition, winner latent, and loser latent with shared timestep and shared noise.
4. Backpropagate only into the selected small LoRA policy scope.
5. Run BF16 single/DDP preflight after the real energy backend is callable.


## Prefix-5 Pair Rebuild Status (2026-06-27 03:24:08)

- Old anchored pairs were I2V-1 / first-image conditioned, not V2V-5.
- New manifest: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`.
- Pair count: `50`.
- Valid prefix5 pair count: `50`.
- Prefix clips use frames 0-4; winner/loser futures use frames 5-80.
- DPO loss/reward masks are `5..80`.
- Real DPO remains blocked until LingBot-Fast winner/loser energy backend and BF16 DDP preflight are available.
