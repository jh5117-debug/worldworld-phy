# v14 Real-Energy Diverse12 Summary

Decision: `REAL_ENERGY_DIVERSE12_PASS`

- Rows: `12`
- OK rows: `12`
- Unique failure types: `12`
- GPU: `physical GPU5 via CUDA_VISIBLE_DEVICES=5`
- CSV: `reports/dpo_utility_calibration_v14/blocker_retry/real_energy_diverse12_cuda_runtime/shard_00_of_01.csv`
- Standard CSV: `reports/dpo_utility_calibration_v14/energy_utility_diverse12_real.csv`
- Source manifest: `manifests/dpo_v14_subsets/asset_complete_prefix5_diverse12.jsonl`
- Delta_ref min / median / mean / max: `-0.017491504549980164` / `0.008648000657558441` / `0.010474516699711481` / `0.03765569627285004`
- Delta_ref positive / negative rows: `10` / `2`
- Energy seconds min / mean / max: `171.09925389289856` / `193.42098329464594` / `227.95005226135254`

## Failure Types

- `collision_response_failure_synthetic`
- `containment_failure_synthetic`
- `drop_motion_failure_synthetic`
- `roll_event_fragment_synthetic`
- `wrong_camera_motion_visible`
- `reobserve_mismatch_visible`
- `object_identity_color_shift`
- `object_duplicate_or_fragment`
- `object_deformation_visible`
- `partial_freeze_foreground`
- `local_scene_patch_drift`
- `background_drift_visible`

## Negative Delta_ref Rows

- `v11_SYN_0428_01039_drop_orbit_left_72_seed40039_object_duplicate_or_fragment` `object_duplicate_or_fragment` Delta_ref `-0.017491504549980164`
- `v11_SYN_0053_02262_collision_orbit_right_64_seed41262_background_drift_visible` `background_drift_visible` Delta_ref `-1.4696270227432251e-05`

This extends v14 real-energy calibration from a background-drift-heavy subset to a 12-failure-type asset-complete subset. It still does not change the DPO recipe decision unless a future scheme also passes true-video and metric gates.
