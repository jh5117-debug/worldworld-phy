# TDW Generation v2 Non-Drop `--run 1` Command Dry-Run Report

Date: 2026-06-04

## Plan

```bash
python3 -m cam_physgeo.data.tdw_generation_v2.plan_trials \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_mild \
  --templates collision roll containment \
  --template_counts collision:1,roll:1,containment:1 \
  --num_trials 3 \
  --out local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_nondrop_smoke_3_run1.jsonl \
  --dry-run
```

Plan output:

| Item | Value |
|---|---|
| manifest | `local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_nondrop_smoke_3_run1.jsonl` |
| rows | 3 |
| templates | `collision:1`, `roll:1`, `containment:1` |
| camera variants | `orbit_left_12`, `orbit_right_12`, `strafe_left_025` |
| stress/reobserve variants | none |

## Command Dry-Run

```bash
python3 -m cam_physgeo.data.tdw_generation_v2.run_tdw_trial \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_mild \
  --num_trials 3 \
  --plan local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_nondrop_smoke_3_run1.jsonl \
  --out_root local_assets/data/physion/generated_v2 \
  --display :8 \
  --dry-run
```

Dry-run report:

`local_assets/data/physion/generated_v2/reports/run_warmup_mild_plan_3.json`

## Checks

| Template | `--run 1` | `--drop` | `--ymin` | `--ymax` | `--dscale` | output dir includes template | warmup_mild camera |
|---|---|---|---|---|---|---|---|
| collision | yes | no | no | no | no | yes | yes |
| roll | yes | no | no | no | no | yes | yes |
| containment | yes | no | no | no | no | yes | yes |

## Gate Decision

Non-drop `--run 1` command dry-run: **passed**.

