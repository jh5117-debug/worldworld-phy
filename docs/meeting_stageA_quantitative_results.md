# Meeting StageA Quantitative Results

Generated from real formal StageA logs, not hand-copied.

## Source

- Training metrics: `reports/meeting_eval_20260623_stageA_fast/metrics/training_metrics.csv`
- Fixed-val metrics: `reports/meeting_eval_20260623_stageA_fast/metrics/fixed_val_metrics.csv`
- Meeting copy: `reports/meeting_eval_20260624_011137/metrics/`

## Summary

- Optimizer steps parsed: 883
- First step: 1.0
- Last step: 883.0
- Final train loss: 0.06046363711357117
- Final EMA20: 0.055253950623304945
- Final EMA100: 0.058223667161750335
- Non-finite loss count: 0
- Fixed-val step100 loss: None
- Fixed-val step800 loss: None
- Fixed-val relative drop from step100 to step800: 35.42%

## Fixed Validation Curve

| Step | Fixed-val loss |
|---:|---:|
| 100.0 | 0.1039545273940478 |
| 200.0 | 0.09887321256101131 |
| 300.0 | 0.09018118751368352 |
| 400.0 | 0.08251665293106011 |
| 500.0 | 0.07615100187914713 |
| 600.0 | 0.07210309098341636 |
| 700.0 | 0.06916036810725927 |
| 800.0 | 0.06713063893839717 |

## Target Overshoot Note

The formal run reached step 883 because the old outer loop only checked the target gate at epoch boundaries. Commit `7631276` fixed this by stopping inside the epoch once the target optimizer-step gate is reached.
