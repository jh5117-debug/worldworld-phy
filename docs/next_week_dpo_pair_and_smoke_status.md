# Next Week DPO Pair and Smoke Status

Current Status: READY_FOR_TINY_SDPO_SMOKE_AND_PAIR_FACTORY_EXPANSION

Updated: 2026-07-01 15:55:00 CST

## Current GT>C Pair State

- Current DPO-ready GT>C pairs: 15.
- Pair manifest: `manifests/dpo_typeB_C_loser_pairs_v6b.jsonl`.
- DPO-ready subset: `reports/targeted_BC_loser_mining_v6b/dpo_ready_pairs_v6b.jsonl`.
- Winner: clean GT future.
- Loser: C camera+self/temporal-r4 rollout.
- Loser reward mean: about 0.7541.
- Loser reward range: about 0.7144 to 0.8073.
- Mean reward margin: about 0.2459.

## B and C Roles

- B camera-only rank8: stable candidate generator / control baseline; trainable params 13,107,200.
- C camera+self/temporal rank4: current medium-hard loser source; trainable params 1,310,720.

C is not a collapsed or too-bad loser. C's average proxy reward is slightly higher than Original Fast/base while still below clean GT winner reward 1.0. This is desirable for medium-hard DPO data: the loser should be readable and plausible, but visibly wrong on foreground, physical event, reobserve, or object state.

## Why Tiny DPO Smoke Is Allowed

The v6b pair factory produced 15 reviewed GT>C DPO-ready pairs, exceeding the >=8 subset requirement and the >=10 tiny-smoke gate. Tiny SDPO-anchor smoke is allowed only as an engineering/objective sanity test.

## Why Large DPO Is Still Not Allowed

Previous DPO smoke runs were engineering-positive but objective-signal weak/unstable. Winner preservation was not strong enough to justify scaling. This round may run at most 20 optimizer steps and must not proceed to large-scale DPO.

## GPU Policy

Use only physical GPU4, GPU5, GPU6, and GPU7. GPU0-3 are not authorized. Current status check showed GPU6 had nontrivial memory occupancy, so all launch scripts must check GPU4-7 with `scripts/safe_gpu_status.sh` and downgrade/wait rather than taking unknown jobs.

## Explicit Non-Runs

This round does not run StageB, GRPO, full-data long StageA, broad-LoRA, or large-scale DPO. It does not delete or modify checkpoints, data, or weights.
