# Reward Input Audit V2 Report

## Scope

Input:

- Clean samples: `local_assets/data/physion/processed/lingbot_cam_inputs/smoke`
- Fast rollouts: `local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke`
- Limit: `3`
- Output: `local_assets/reports/smoke/reward_input_audit_v2`

## Clean GT Metadata

For all 3 checked samples:

- `target.mp4`: present.
- `depth.npy`: present.
- `id_mask.npy`: present.
- `poses.npy`: present.
- `intrinsics.npy`: present.
- `hdf5_path`: present in `metadata.json`.
- Clean reward backend coverage: depth, ID mask, camera, intrinsics, and object state all marked available.

The HDF5 path exists, but the LingBot env used for this smoke does not have `h5py`, so direct HDF5 key traversal could not be used from that environment. The scorer therefore uses the processed Physion-derived depth/id/camera/object-state metadata already produced by the converter.

## Fast Rollout Metadata

For the generated Fast rollouts:

- `generated.mp4`: present for the 3 rollout smoke samples.
- Generated depth/id are absent.
- Generated feature and learned flow backends are still absent.
- Fast reward remains provisional and fallback/proxy-heavy.

## Conclusion

Clean GT real metadata is now usable through processed Physion-derived sample assets and metadata. Direct HDF5 fallback should be improved by adding `h5py` to the runtime env or by running HDF5 reads in an env where `h5py` is available.
