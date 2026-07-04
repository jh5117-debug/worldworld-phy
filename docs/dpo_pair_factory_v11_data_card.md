Current Status: PASS_WITH_SCOPE_CAVEATS

## 2026-07-04 Repaired Ready500 Canonical + Metrics Update

- Canonical repaired manifest: `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`.
- Old ready500 had 3 too-subtle TypeA_plus pairs removed and replaced.
- Repaired splits: train400 / val50 / test50 / top50 generated with no condition leakage.
- LPIPS real smoke: PASS on 10 representative canonical pairs.
- VBench real smoke: PASS for `temporal_flickering` on 3 videos; full suite still requires dimension-by-dimension verification.
- FVD real backend smoke: PASS using local TorchScript I3D with corrected `[B,3,T,H,W]` layout on 4 pairs; full benchmark still requires a larger fixed eval set.
- Environment caveat: user-site `transformers==4.33.2` conflicts with fastwam expected `4.49.0`; metric environment should be isolated from training.
- No training was run.

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
