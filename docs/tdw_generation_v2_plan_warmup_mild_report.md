# TDW Generation v2 Warmup Mild Plan Report

## Command

```bash
python -m cam_physgeo.data.tdw_generation_v2.plan_trials \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_mild \
  --templates drop collision roll containment \
  --num_trials 10 \
  --out local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_10.jsonl \
  --dry-run
```

## Result

Plan dry-run passed locally and on H20.

- planned trials: 10
- camera set: `warmup_mild`
- templates: `drop`, `collision`, `roll`, `containment`
- variants: `orbit_left_12`, `orbit_right_12`, `strafe_left_025`, `strafe_right_025`, `dolly_in_010`, `dolly_out_010`
- stress/reobserve keyword check: passed
- `bad_count`: 0

## Seeds

The plan uses `seed_start=22000`, so the first 10 planned seeds are `22000` through `22009`.

## Confirmation

The JSONL plan exposes:

- `camera_set`
- `camera_variant`
- `camera_motion`
- `camera_args`
- `upstream_camera_variant`

This makes the warmup/stress split auditable before any actual TDW generation starts.

## GPU Usage

Planning uses no GPU. Actual TDW/Unity generation remains gated by display/GPU checks.

## Continue To 1-Sample?

The plan itself is safe to continue. Actual 1-sample generation is blocked unless the H20 TDW display uses only GPU 6/7 or the user approves a different TDW display/GPU configuration.
