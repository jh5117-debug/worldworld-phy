# TDW Generation v2 Visible-Motion 10-Sample GPU0 Plan Report

Date: 2026-06-05

## Command

```bash
python3 -m cam_physgeo.data.tdw_generation_v2.plan_trials \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_visible_motion \
  --templates drop collision roll containment \
  --template_counts drop:3,collision:3,roll:2,containment:2 \
  --num_trials 10 \
  --out local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_10_gpu0.jsonl \
  --dry-run
```

## Result

| Item | Value |
|---|---|
| Planned samples | 10 |
| Template distribution | `drop:3, collision:3, roll:2, containment:2` |
| Camera variants | `orbit_left_24:2, orbit_right_24:2, orbit_left_28:1, orbit_right_28:1, strafe_left_050:1, strafe_right_050:1, dolly_in_025:1, dolly_out_025:1` |
| Stress / reobserve variants | 0 |
| Plan path | `local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_10_gpu0.jsonl` |

The plan preserved template diversity and kept stress / reobserve camera variants out of the warmup-visible-motion profile.
