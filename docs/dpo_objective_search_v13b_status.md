# DPO Objective Search v13b Status

Updated: 2026-07-06 12:34 CST

## Current State

- Canonical data entry: `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`.
- v12 32-pair guarded DPO failed with winner-worse / no-signal behavior.
- v12b winner-only S_pass4 passed and produced warm-start LoRA state.
- v12c/v12d winner-detached preference had positive mean signal but final winner improvement flipped negative.
- Current task: search 6-10 tiny DPO objective / LoRA / gap-normalization variants, not large DPO.

## GPU Policy

- Allowed physical GPUs: 4 and 5 only.
- Forbidden physical GPUs: 0, 1, 2, 3, 6, 7.
- All training/eval commands must set `CUDA_VISIBLE_DEVICES=4` or `CUDA_VISIBLE_DEVICES=5`.
- Preflight observed GPU4/5 occupied by existing overnight rollout jobs, so training must wait or mark `GPU4_5_BLOCKED`; unknown jobs must not be killed.

## Scope

This round is limited to S4/S8/S16 tiny objective search with max 200 steps per scheme. It must monitor win-gap, lose-gap, normalized gaps, winner improvement, loser degradation, winner contribution ratio, video quality, and metric quality.

## Not Run

- No large DPO.
- No train400.
- No S32/S64.
- No StageA/StageB/GRPO/broad-LoRA.
- No checkpoint/data/weight deletion.
- No videos or `local_assets/` pushed.
