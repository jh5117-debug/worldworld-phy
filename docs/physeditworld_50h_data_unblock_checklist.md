# PhysEditWorld 50h Data Unblock Checklist

## Current Blocker

The selected PhysEditWorld 50h root is not visible from the current H20 repo environment. The strict manifests are intentionally empty, so baseline rollout, rank32 warm-up, anchored pair construction, and tiny DPO must not start.

## Required Before Training

The mounted/provided root must contain enough metadata to build non-empty rows with:

- `sample_id`
- `replay_group_id`
- `scene_id`
- `initial_state_id`
- `action_trace_id`
- `camera_policy_id`
- `gravity_value` and `gravity_label`
- target video path
- prefix/image path or recoverable frames
- action trace path
- camera trajectory / poses path
- intrinsics path
- prompt or prompt source

## One-Command Preflight

Run on H20 or PAI after mounting data/NAS:

```bash
bash scripts/migration/check_physeditworld_pai_readiness.sh
```

Outputs:

- `reports/migration/physeditworld_pai_readiness.csv`
- `reports/migration/physeditworld_pai_readiness.json`
- `reports/migration/physeditworld_pai_readiness_summary.md`

Expected decision before Phase 3 rollout:

```text
READY_FOR_BASELINE_ROLLOUT_PREFLIGHT
```

## If Still Blocked

- `PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED`: mount/provide the selected 50h root and rerun Phase 1 audit.
- `PHYS_EDIT_WORLD_CONVERSION_BLOCKED`: rerun prompt-only LingBot conversion.
- `PAI_NAS_MOUNT_BLOCKED`: mount `/mnt/workspace/hj/nas_hj` or set `NAS_PATH` to a writable target.

## Safety

This preflight is CPU/IO only. It does not copy large files, start GPU jobs, delete data, or run training.
