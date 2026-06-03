# TDW Generation v2 Plan Report

Stage 0 dry-run planning is supported by `cam_physgeo.data.tdw_generation_v2.plan_trials`.

Command:

```bash
python -m cam_physgeo.data.tdw_generation_v2.plan_trials \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_mild \
  --templates drop collision roll containment \
  --num_trials 10 \
  --out local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_10.jsonl \
  --dry-run
```

The plan uses mild variants only in the v2 config: `orbit_left_12` and `strafe_right_025`.
