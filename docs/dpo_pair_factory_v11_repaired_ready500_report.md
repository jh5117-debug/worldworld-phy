Current Status: PASS_WITH_SCOPE_CAVEATS

# DPO Pair Factory v11 Repaired Ready500 Report

Updated: 2026-07-04 12:35:32

## Canonical Manifest

The repaired manifest is now frozen as canonical:

- Canonical: `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`
- Train: `manifests/dpo_pair_factory_v11_train400_repaired.jsonl`
- Val: `manifests/dpo_pair_factory_v11_val50_repaired.jsonl`
- Test: `manifests/dpo_pair_factory_v11_test50_repaired.jsonl`
- Top50 demo: `manifests/dpo_pair_factory_v11_top50_demo_repaired.jsonl`

Freeze checks:

- Canonical count: 500
- Train/val/test/top50: 400 / 50 / 50 / 50
- Removed too-subtle IDs absent: yes
- Replacement IDs present: yes
- Duplicate pair IDs: no
- Condition-level train/val/test leakage: no

## Removed IDs

- `protocol_v4_TypeAplus_022_s4_strong_pass_object_identity_change_local`
- `protocol_v4_TypeAplus_024_s4_strong_pass_partial_freeze`
- `protocol_v4_TypeAplus_028_s4_strong_pass_partial_freeze`

## Replacement Count

- Replacement pairs: 3
- Source: already reviewed v11 synthetic controlled candidate pool

## Metric Verification

### LPIPS

- Status: PASS
- Output: `reports/dpo_pair_factory_v11/metrics_backend_repair/lpips_real_smoke.csv`
- Summary: `reports/dpo_pair_factory_v11/metrics_backend_repair/lpips_real_smoke_summary.md`
- Mean winner-vs-loser LPIPS over 10 pairs: 0.18500665950996337

### VBench

- Status: PASS_WITH_SCOPE_CAVEAT
- Real smoke dimension: `temporal_flickering`
- Input videos: 3 repaired pair loser videos
- Output: `reports/dpo_pair_factory_v11/metrics_backend_repair/vbench_real_smoke.csv`
- Caveat: full VBench suite is not yet verified dimension-by-dimension.

### FVD

- Status: PASS_WITH_SCOPE_CAVEAT
- Backend: local TorchScript I3D weight `/home/nvme03/workspace/world_model_phys/code/finetune_v3/lingbot-csgo-finetune/i3d_torchscript.pt`
- Tiny smoke: 4 winner videos vs 4 loser videos
- FVD smoke score: 0.6614066493904447
- Caveat: this validates backend availability, not a stable benchmark FVD.

## Environment Warning

VBench installation added user-site `transformers==4.33.2`, while fastwam expects `transformers==4.49.0`. This metric environment should be treated as evaluation-only unless training commands explicitly isolate dependencies.

## Decision

The repaired canonical 500-pair dataset is ready as the data entry for a future tiny DPO smoke. This round did not run any training.
