# v14 Artifact Regression Summary

Decision: `ARTIFACT_REGRESSION_CONFIRMS_SCALAR_VISUAL_MISMATCH`
Scale permission: `NO_SCALE`

This summary aggregates existing Codex visual audits for scalar-positive v14 DPO candidates. It does not run new training or generate new videos.

| Scheme | Training Signal | Video Worse | Identity Worse | Artifact Worse | Background Worse | Camera Worse | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| `E07_screen200` | mean WI=+0.00580584, mean WCR=0.985 | 4/4 | 4/4 | 4/4 | 0/4 | 0/4 | `NOT_VALID_DPO_RECIPE_VISUAL_GATE_FAIL` |
| `E09_screen200` | mean WI=+0.000524421, mean WCR=0.923 | 4/4 | 4/4 | 4/4 | 2/4 | 1/4 | `NOT_VALID_DPO_RECIPE_VISUAL_GATE_FAIL` |
| `E10_screen100` | mean WI=+0.000185096, mean WCR=0.824 | 2/4 | 2/4 | 2/4 | 0/4 | 0/4 | `NOT_VALID_DPO_RECIPE_VISUAL_GATE_FAIL` |

## Interpretation

- E07/E09/E10 all have positive scalar winner movement, but every promising candidate fails the true V2V-5 visual gate.
- The dominant visual failure is not freeze; it is artifact amplification: foreground duplication, identity clutter, object fragments, line/text-like marks, background/camera contamination in some samples, and scene pollution.
- This supports the v14 root blocker: current scalar energy/gap objectives do not protect rollout visual quality.
- The safe next action is to build v15 artifact-aware monitor/gate/regularizer from existing checkpoint videos before any further DPO scale.

## Paths

- Summary CSV: `reports/dpo_utility_calibration_v14/artifact_regression/artifact_regression_summary.csv`
- Row CSV: `reports/dpo_utility_calibration_v14/artifact_regression/artifact_regression_rows.csv`
- Summary JSON: `reports/dpo_utility_calibration_v14/artifact_regression/artifact_regression_summary.json`
