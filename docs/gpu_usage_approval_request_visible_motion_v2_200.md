# GPU Usage Approval Request: warmup_visible_motion_v2 200 Pilot

## 50-Sample Result

`warmup_visible_motion_v2` 50-sample validation passed:

- Generated HDF5: 50/50
- Validation OK: 50/50
- Suitable for visible motion: 50/50
- Rejected: 0/50
- Per-template accepted: drop 15, collision 15, roll 10, containment 10
- Conversion: 50/50

## 200 Readiness

The 200-readiness condition was met:

- acceptance >= 40/50: yes, 50/50
- every template >= 5 accepted samples: yes

This does not authorize running 200. User approval is required.

## Resource Estimate

Observed 50-sample storage:

- raw HDF5: 4.31 GB
- converted LingBot cam-only: 9.75 GB

Estimated 200-sample storage:

- raw HDF5: about 17.2 GB
- converted LingBot cam-only: about 39.0 GB

Runtime estimate from 50-sample polling:

- 50 samples: about 1h45m
- 200 samples: about 7h, depending on TDW/Unity stability

## GPU Requirement

The current TDW route uses GPU0-bound `DISPLAY=:8`. A 200-sample run would require explicit approval for GPU0 or a configured GPU6/7 TDW display.

## Command Requiring Approval

```bash
python3 -m cam_physgeo.data.tdw_generation_v2.plan_trials \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_visible_motion_v2 \
  --templates drop collision roll containment \
  --template_counts drop:60,collision:60,roll:40,containment:40 \
  --num_trials 200 \
  --out local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_v2_200.jsonl \
  --dry-run

bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_visible_motion_v2 \
  --plan local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_v2_200.jsonl \
  --out_root local_assets/data/physion/generated_v2 \
  --display :8 \
  --allow_unapproved_gpu \
  --gpu_confirmation_token USER_CONFIRMED_UNAPPROVED_GPU \
  --no_overwrite
```

## Recommendation

The data gate supports asking for a 200 pilot. Because the run would occupy GPU0-bound TDW display for hours and create tens of GB of data, do not run it without explicit user approval.

