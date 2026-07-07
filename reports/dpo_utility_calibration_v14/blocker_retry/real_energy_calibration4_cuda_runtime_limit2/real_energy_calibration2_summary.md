# v14 Bounded Real-Energy Calibration2 Summary

Generated: `2026-07-07T21:19:30Z`

Decision: `REAL_ENERGY_CALIBRATION2_CUDA_RUNTIME_PASS`

## Result

- Manifest: `manifests/dpo_v14_subsets/asset_complete_prefix5_calibration4.jsonl`
- Energy CSV: `reports/dpo_utility_calibration_v14/blocker_retry/real_energy_calibration4_cuda_runtime_limit2/shard_00_of_01.csv`
- Rows: `2`; OK rows: `2`
- Runtime/device: `--runtime_device cuda`, physical GPU4 only; GPU5 was not used.
- Energy seconds per pair: `[228.92305850982666, 225.6800239086151]`
- Max CUDA peak memory GB: `50.43468189239502`

## Interpretation

The repaired asset-complete Prefix5 adapter plus CUDA runtime can now produce more than one real LingBot energy row. This moves v14 calibration from one-pair proof to a bounded multi-pair proof.

## Remaining Decision

This is calibration evidence only. `DPO_RECIPE_NOT_FOUND_V14` remains because previous scalar-positive schemes failed true V2V-5 visual gates. S16/S32/train400/large DPO remain blocked.
