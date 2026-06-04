# GPU Usage Approval Request: TDW Template-Diverse 200-Sample Pilot

Date: 2026-06-05

## Current Status

Template-diverse 50-sample `warmup_mild` validation passed:

- generated HDF5: 50/50
- validation OK: 50/50
- suitable for warmup: 50/50
- LingBot cam-only conversion: 50/50
- target.mp4 probe: 50/50
- `use_action=false`: 50/50
- dummy action zero norm: 50/50

Template distribution:

| Template | Count |
|---|---:|
| `drop` | 15 |
| `collision` | 15 |
| `roll` | 10 |
| `containment` | 10 |

Camera variants:

- `orbit_left_12`: 9
- `orbit_right_12`: 9
- `strafe_left_025`: 8
- `strafe_right_025`: 8
- `dolly_in_010`: 8
- `dolly_out_010`: 8

Storage used:

- raw HDF5: about 4.0 GiB
- LingBot conversion: about 9.1 GiB

## Requested Next Stage

Run a 200-sample TDW template-diverse warmup_mild pilot.

This requires explicit user approval because TDW currently uses GPU0-bound `DISPLAY=:8`.

## Proposed Command

```bash
python -m cam_physgeo.data.tdw_generation_v2.plan_trials \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_mild \
  --templates drop collision roll containment \
  --template_counts drop:60,collision:60,roll:40,containment:40 \
  --num_trials 200 \
  --out local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_template_diverse_200.jsonl \
  --dry-run

bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_mild \
  --plan local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_template_diverse_200.jsonl \
  --out_root local_assets/data/physion/generated_v2 \
  --display :8 \
  --allow_unapproved_gpu \
  --gpu_confirmation_token USER_CONFIRMED_UNAPPROVED_GPU \
  --no_overwrite
```

## Estimate / Risk

Extrapolating from the 50-sample run:

- raw HDF5: about 16 GiB
- LingBot conversion: about 36 GiB
- generation time: about 7-8 hours
- conversion/validation time: additional time after generation

Risks:

- long GPU0-bound TDW/Unity occupancy;
- more storage use;
- no automatic expansion to 1k+ should happen after 200.

Alternative:

Configure a GPU6/7 TDW display before a longer 200-sample pilot.

## Recommendation

200-sample pilot is technically ready after the 50-sample pass, but should only run with explicit user approval.

