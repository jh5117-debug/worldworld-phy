# TDW v2 Warmup Visible-Motion 10-Sample Plan Report

Date: 2026-06-05

## Command

```bash
python3 -m cam_physgeo.data.tdw_generation_v2.plan_trials \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_visible_motion \
  --templates drop collision roll containment \
  --template_counts drop:3,collision:3,roll:2,containment:2 \
  --num_trials 10 \
  --out local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_10.jsonl \
  --dry-run
```

## Result

Plan dry-run passed.

Template distribution:

| Template | Count |
|---|---:|
| `drop` | 3 |
| `collision` | 3 |
| `roll` | 2 |
| `containment` | 2 |

Camera variant distribution:

| Camera variant | Count |
|---|---:|
| `orbit_left_24` | 2 |
| `orbit_right_24` | 2 |
| `orbit_left_28` | 1 |
| `orbit_right_28` | 1 |
| `strafe_left_050` | 1 |
| `strafe_right_050` | 1 |
| `dolly_in_025` | 1 |
| `dolly_out_025` | 1 |

Stress/reobserve keyword check:

- `bad_count = 0`

Actual generation was not run because no GPU6/7 TDW display is currently available.

## v2 Recheck

The plan was rechecked for the GPU6/7 display setup turn and still passes:

- rows: 10
- template distribution: `drop:3`, `collision:3`, `roll:2`, `containment:2`
- camera variants: `orbit_left_24`, `orbit_right_24`, `orbit_left_28`, `orbit_right_28`, `strafe_left_050`, `strafe_right_050`, `dolly_in_025`, `dolly_out_025`
- stress/reobserve `bad_count=0`

Actual generation remains blocked until a GPU6/7 TDW display exists.
