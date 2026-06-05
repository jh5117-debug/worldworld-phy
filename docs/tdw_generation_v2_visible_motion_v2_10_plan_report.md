# TDW Generation v2 Visible-Motion v2 10-Sample Plan Report

Date: 2026-06-05

## Command

```bash
python -m cam_physgeo.data.tdw_generation_v2.plan_trials \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_visible_motion_v2 \
  --templates drop collision roll containment \
  --template_counts drop:3,collision:3,roll:2,containment:2 \
  --num_trials 10 \
  --out local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_v2_10.jsonl \
  --dry-run
```

## Local Dry-Run Result

| Item | Value |
|---|---|
| Planned samples | 10 |
| Template distribution | `drop:3, collision:3, roll:2, containment:2` |
| Camera variants | `orbit_left_24:2, strafe_left_050:2, strafe_right_050:2, orbit_right_24:1, orbit_left_28:1, orbit_left_18:1, orbit_right_18:1` |
| Stress / reobserve variants | 0 |
| Roll dolly variants | 0 |
| Containment orbit 24 / 28 variants | 0 |

## Planned Rows

- drop: `orbit_left_24`, `orbit_right_24`, `orbit_left_28`
- collision: `strafe_left_050`, `strafe_right_050`, `orbit_left_24`
- roll: `strafe_left_050`, `strafe_right_050`
- containment: `orbit_left_18`, `orbit_right_18`

## Gate

The local plan dry-run passed all template-aware constraints.

Remote execution remains pending until SSH control-plane stability allows syncing the profile and running the approved GPU0 `DISPLAY=:8` smoke.
