# TDW Generation v2 Visible-Motion 1-Sample GPU0 Plan Report

Date: 2026-06-05

## Command

```bash
python3 -m cam_physgeo.data.tdw_generation_v2.plan_trials \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_visible_motion \
  --templates drop collision roll containment \
  --template_counts drop:1 \
  --num_trials 1 \
  --out local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_1_gpu0.jsonl \
  --dry-run
```

## Result

| Item | Value |
|---|---|
| Planned samples | 1 |
| Template distribution | `drop:1` |
| Camera variants | `orbit_left_24:1` |
| Stress / reobserve variants | 0 |
| Plan path | `local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_1_gpu0.jsonl` |

The plan was clean and safe to run under the explicit GPU0 smoke approval.
