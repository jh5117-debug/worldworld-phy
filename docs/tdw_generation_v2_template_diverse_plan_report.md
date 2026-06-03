# TDW Generation v2 Template-Diverse Plan Report

Date: 2026-06-03

## Command

```bash
python -m cam_physgeo.data.tdw_generation_v2.plan_trials \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_mild \
  --templates drop collision roll containment \
  --template_counts drop:3,collision:3,roll:2,containment:2 \
  --num_trials 10 \
  --out local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_template_diverse_10.jsonl \
  --dry-run
```

Local verification used `/tmp/plan_warmup_mild_template_diverse_10.jsonl` to avoid writing generated assets during code validation.

## Plan Summary

| Item | Value |
|---|---|
| Planned trials | 10 |
| Profile | `warmup_mild` |
| Camera set | `warmup_mild` |
| Template distribution | `drop:3`, `collision:3`, `roll:2`, `containment:2` |
| Camera variants | `orbit_left_12`, `orbit_right_12`, `strafe_left_025`, `strafe_right_025`, `dolly_in_010`, `dolly_out_010` |
| Stress/reobserve bad count | 0 |
| Template diversity check | passed |

## Template Sequence

| Index | Template |
|---:|---|
| 0 | drop |
| 1 | drop |
| 2 | drop |
| 3 | collision |
| 4 | collision |
| 5 | collision |
| 6 | roll |
| 7 | roll |
| 8 | containment |
| 9 | containment |

## Dry-Run Runner Check

`run_tdw_trial --plan ... --dry-run` produced 10 explicit upstream commands and preserved the exact template sequence above.

The obsolete batch-runner import blocker is now recorded as ignored only for plan mode. GPU/display blockers still block actual execution.

## Actual Generation Decision

Actual template-diverse 10-sample generation was not run in this turn. The only known TDW display is GPU0-bound `DISPLAY=:8`; this prompt did not explicitly approve GPU0 for the new template-diverse 10-sample run.

Next action: approve the command in `docs/gpu_usage_approval_request_tdw_template_diverse_10.md`, or configure a GPU6/7 TDW display.

