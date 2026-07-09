# PhysEditWorld Baseline Rollout Summary

Decision: `BASELINE_BLOCKED_EMPTY_MANIFEST`

- Input manifest: `manifests/physeditworld_50h_lingbot_val.jsonl`
- Input rows: 0
- Selected rows: 0
- Manifest validation: `reports/physeditworld_50h/conversion_validation/lingbot_val_manifest_validation.json` decision=`LINGBOT_MANIFEST_BLOCKED_EMPTY`
- Models requested: `original_fast,lingbot_base_if_available`
- Gravity modes requested: `correct,wrong,default`
- Output root: `local_assets/physeditworld_50h_baseline_rollout`
- CUDA_VISIBLE_DEVICES: ``
- GPU policy: `NO_VISIBLE_GPU_SET`
- This wrapper does not perform image-only fallback or prefix_len=1 fallback.
- True rollout remains blocked until valid PhysEditWorld LingBot manifest rows exist and a LingBot backend invocation is wired.

## Source Counts


