# v14 Asset Recovery Smoke Limit1

Decision: `PASS`

- This smoke used `CUDA_VISIBLE_DEVICES=` and did not use GPU.
- It materialized one local asset-complete prefix5 row from the recoverable all500 manifest.
- Generated MP4 files are under `local_assets/` and must not be pushed.

## Summary

- Input manifest: `manifests/dpo_v14_subsets/asset_complete/all500_recoverable_for_energy.jsonl`
- Output manifest: `manifests/dpo_v14_subsets/asset_complete/all500_recovered_smoke1_prefix5.jsonl`
- Selected count: `1`
- Status counts: `{'ADAPTED': 1}`
- Schema validated: `1`

## Report Rows
- `v11_SYN_0017_02215_collision_strafe_left_180_seed41215_background_drift_visible`: `ADAPTED` 
