# V-JEPA2 Expanded Checkpoint Gate Design

Decision: `VJEPA2_DRIFT_GATE_EXPANDED_MONITOR_ONLY`

- Manifest: `manifests/dpo_v14_subsets/checkpoint_regression_all_available_vjepa_pairs.jsonl`
- V-JEPA2 CSV: `reports/dpo_utility_calibration_v14/latent_monitor/checkpoint_regression_all_available/vjepa2_checkpoint_regression_all.csv`
- Joined CSV: `reports/dpo_utility_calibration_v14/latent_monitor/checkpoint_regression_all_available/vjepa2_checkpoint_regression_all_with_visual.csv`
- Threshold CSV: `reports/dpo_utility_calibration_v14/latent_monitor/checkpoint_regression_all_available/vjepa2_checkpoint_gate_thresholds_all.csv`
- Stats JSON: `reports/dpo_utility_calibration_v14/latent_monitor/checkpoint_regression_all_available/vjepa2_checkpoint_gate_stats_all.json`
- Rows: `24`
- Codex worse/not-worse rows: `19` / `5`

## Scheme Counts

- `E02_best7`: rows `4`, worse `4`
- `E04_screen5`: rows `4`, worse `3`
- `E05_screen5`: rows `4`, worse `2`
- `E07_screen200`: rows `4`, worse `4`
- `E09_screen200`: rows `4`, worse `4`
- `E10_screen100`: rows `4`, worse `2`

## Metric Statistics

### token_relation_margin

- AUC vs Codex worse label: `0.4631578947368421`
- min / median / mean / max: `0.03626668453216553` / `0.057847822085022926` / `0.0630954415537417` / `0.10660583525896072`
- Conservative no-FN threshold: `0.039196910336613655` (TP `19`, FP `4`, TN `1`, FN `0`, balanced `0.6`)
- Best balanced threshold: `0.039196910336613655` (TP `19`, FP `4`, TN `1`, FN `0`, balanced `0.6`)

### vjepa_margin

- AUC vs Codex worse label: `0.4842105263157895`
- min / median / mean / max: `0.0006732344627380371` / `0.0018117725849151611` / `0.0027438153823216758` / `0.010382771492004395`
- Conservative no-FN threshold: `0.0006732344627380371` (TP `19`, FP `5`, TN `0`, FN `0`, balanced `0.5`)
- Best balanced threshold: `0.00417289137840271` (TP `4`, FP `0`, TN `5`, FN `15`, balanced `0.6052631578947368`)

## Interpretation

The expanded 24-row regression set confirms V-JEPA2 detects checkpoint drift in every available updated checkpoint pair, but the margins are not precise enough to approve a checkpoint without visual/metric review. This is useful as a high-recall monitor or stop/inspect trigger for v15. It does not change v14 scale permission.

Current decision remains `DPO_RECIPE_NOT_FOUND_V14` / `NO_SCALE`.
