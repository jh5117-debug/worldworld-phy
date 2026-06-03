# TDW Generation v2 Plan Report: Approved 10-Sample Warmup Mild

Generated: 2026-06-04

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

| Item | Value |
|---|---|
| Plan path | `local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_10.jsonl` |
| Planned count | 10 |
| Requested templates | `drop`, `collision`, `roll`, `containment` |
| Planned templates | `drop`, `collision`, `roll`, `containment`, repeated |
| Planned camera variants | `orbit_left_12`, `orbit_right_12`, `strafe_left_025`, `strafe_right_025`, `dolly_in_010`, `dolly_out_010`, repeated |
| Planned seeds | `22000` to `22009` |
| Stress/reobserve bad_count | 0 |

No forbidden camera variants were present:

- no `lookaway`
- no `offscreen`
- no `relative_yaw_180`
- no `reobserve`
- no `extreme`
- no `occluder`

## Note

The dry-run plan is clean. During actual upstream execution, the current batch runner generated all 10 samples with template `drop`; this is recorded as a template coverage limitation in the 10-sample report.
