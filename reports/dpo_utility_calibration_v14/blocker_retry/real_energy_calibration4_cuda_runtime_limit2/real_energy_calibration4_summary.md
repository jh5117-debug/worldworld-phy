# v14 Bounded Real-Energy Calibration4 Summary

Generated: `2026-07-07T21:52:32Z`

Decision: `REAL_ENERGY_CALIBRATION4_CUDA_RUNTIME_PASS`

## Result

- Manifest: `manifests/dpo_v14_subsets/asset_complete_prefix5_calibration4.jsonl`
- Energy CSV: `reports/dpo_utility_calibration_v14/blocker_retry/real_energy_calibration4_cuda_runtime_limit2/shard_00_of_01.csv`
- Rows: `4`; OK rows: `4`
- Runtime/device: `--runtime_device cuda`; physical GPU4 generated rows 0-1, physical GPU5 generated rows 2-3.
- Energy seconds per pair: `[228.92305850982666, 225.6800239086151, 246.5310070514679, 175.17605328559875]`
- Max CUDA peak memory GB: `50.43468189239502`

## Interpretation

The repaired asset-complete Prefix5 adapter plus CUDA runtime produced 4/4 real LingBot energy rows. This is still a bounded calibration proof, not an all500 calibration.

## Remaining Decision

`DPO_RECIPE_NOT_FOUND_V14` remains because previous scalar-positive schemes failed true V2V-5 visual gates. S16/S32/train400/large DPO remain blocked.
