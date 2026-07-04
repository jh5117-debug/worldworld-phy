Current Status: PRD_READY_PENDING_EXECUTION

# DPO Training Sanity v12 Status

Updated: 2026-07-04 13:28 CST

## Data Entry

Use only the repaired canonical ready500 manifest and repaired splits:

- Canonical: `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`
- Train: `manifests/dpo_pair_factory_v11_train400_repaired.jsonl`
- Val: `manifests/dpo_pair_factory_v11_val50_repaired.jsonl`
- Test: `manifests/dpo_pair_factory_v11_test50_repaired.jsonl`
- Top50 demo: `manifests/dpo_pair_factory_v11_top50_demo_repaired.jsonl`

The old `manifests/dpo_pair_factory_v11_ready_500.jsonl` is deprecated because it contained three too-subtle TypeA_plus pairs.

## Current Evidence

- Repaired canonical count: 500.
- Repaired train/val/test/top50: 400 / 50 / 50 / 50.
- LPIPS real smoke: PASS.
- VBench real scoring smoke: PASS for `temporal_flickering` only.
- FVD real video-FVD smoke: PASS using local TorchScript I3D, with tiny-smoke caveat.
- Metric environment warning: VBench installed user-site `transformers==4.33.2`; fastwam expects `transformers==4.49.0`.

## DPO Risk

Previous DPO diagnosis showed weak/no preference signal and winner preservation failures. The main risk is loser-degradation-dominant optimization. v12 is therefore a tiny sanity experiment, not a scale run.

## v12 Scope

This round may run:

- repaired data subset construction;
- LoRA scope inventory;
- winner-anchor scope sanity;
- guarded tiny DPO only if at least one scope passes winner-anchor sanity;
- checkpoint video + metric evaluation for every tiny DPO checkpoint.

This round must not run large DPO, StageB, GRPO, full-data StageA, broad-LoRA, or any checkpoint/data deletion.
