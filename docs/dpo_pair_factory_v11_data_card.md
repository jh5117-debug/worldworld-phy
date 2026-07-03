Current Status: PASS

# DPO Pair Factory v11 Scale-500 Data Card

## Dataset

DPO Pair Factory v11 Scale-500

## Purpose

500 reviewed preference pairs for camera-conditioned V2V-5 LingBot physical-geometric DPO.

## Input Condition

- Prefix frames 0-4
- Prompt
- Poses
- Intrinsics

## Target Future

- Frames 5-80

## Composition

- Ready pairs: 500
- Train/val/test: 400 / 50 / 50
- Real rollout-derived: 15
- Controlled synthetic: 482
- TypeA_plus: 3

## Important Caveat

Controlled synthetic negatives dominate unless real rollout expansion succeeds. These are appropriate for anchored / controlled DPO and LocalDPO-style controlled failures. They must not be described as real rollout losers.

## Recommended Use

- `manifests/dpo_pair_factory_v11_train400.jsonl` for anchored tiny DPO.
- `manifests/dpo_pair_factory_v11_val50.jsonl` for checkpoint selection.
- `manifests/dpo_pair_factory_v11_test50.jsonl` for pair-overfit / sanity.
- `manifests/dpo_pair_factory_v11_rollout_only.jsonl` for real model-distribution analysis.
- `manifests/dpo_pair_factory_v11_synthetic_controlled.jsonl` for LocalDPO-style controlled failures.

## Not Recommended

- Do not claim all 500 are real rollout losers.
- Do not train large DPO without first tiny sanity.
- Do not use rejected pairs.
- Do not include any pair without contact sheet and Codex visual audit.
