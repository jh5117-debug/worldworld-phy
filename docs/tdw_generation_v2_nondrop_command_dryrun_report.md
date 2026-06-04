# TDW Generation v2 Non-Drop Command Dry-Run Report

Date: 2026-06-04

## Goal

Verify that non-drop templates no longer receive drop-only upstream arguments before starting TDW/Unity generation.

## Plan Command

```bash
python -m cam_physgeo.data.tdw_generation_v2.plan_trials \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_mild \
  --templates collision roll containment \
  --template_counts collision:1,roll:1,containment:1 \
  --num_trials 3 \
  --out local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_nondrop_smoke_3.jsonl \
  --dry-run
```

## Dry-Run Command Check

```bash
python -m cam_physgeo.data.tdw_generation_v2.run_tdw_trial \
  --plan local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_nondrop_smoke_3.jsonl \
  --out_root local_assets/data/physion/generated_v2 \
  --display :8 \
  --dry-run
```

## Result

| Template | Output directory contains template | `--drop` | `--ymin` | `--ymax` | `--dscale` | `--run 1` |
|---|---|---|---|---|---|---|
| collision | yes | no | no | no | no | added after actual failure diagnosis |
| roll | yes | no | no | no | no | added after actual failure diagnosis |
| containment | yes | no | no | no | no | added after actual failure diagnosis |

The first dry-run check confirmed that `collision`, `roll`, and `containment` no longer receive drop-only arguments. After the actual smoke produced no HDF5 files, the wrapper was further fixed to include the required upstream execution flag `--run 1`.

## Gate Decision

Command dry-run for template-specific drop args: **passed**.

Execution-flag check: **fixed after actual smoke diagnosis**. The next actual TDW non-drop run should be rerun with `--run 1` present.

