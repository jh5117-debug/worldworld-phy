# V-JEPA2 Checkpoint Gate Design

Decision: `VJEPA2_DRIFT_GATE_CANDIDATE_V15_MONITOR_ONLY`

- Input: `reports/dpo_utility_calibration_v14/latent_monitor/checkpoint_regression_e09_e10/vjepa2_checkpoint_regression_with_visual.csv`
- Threshold sweep: `reports/dpo_utility_calibration_v14/latent_monitor/checkpoint_regression_e09_e10/vjepa2_checkpoint_gate_thresholds.csv`
- Stats JSON: `reports/dpo_utility_calibration_v14/latent_monitor/checkpoint_regression_e09_e10/vjepa2_checkpoint_gate_stats.json`
- Rows: `8`
- Codex worse/not-worse rows: `6` / `2`

## Metric Statistics

### token_relation_margin

- AUC vs Codex worse label: `0.5833333333333334`
- min / median / mean / max: `0.05159546434879303` / `0.059193359687924385` / `0.06632272619754076` / `0.09631488472223282`
- Conservative no-false-negative threshold: `0.05159546434879303` (TP `6`, FP `2`, TN `0`, FN `0`, balanced accuracy `0.5`)

### vjepa_margin

- AUC vs Codex worse label: `0.6666666666666666`
- min / median / mean / max: `0.0014584064483642578` / `0.0026774704456329346` / `0.003367498517036438` / `0.007237434387207031`
- Conservative no-false-negative threshold: `0.0014584064483642578` (TP `6`, FP `2`, TN `0`, FN `0`, balanced accuracy `0.5`)

## Recommended Gate Use

Use V-JEPA2 token-relation margin as a v15 drift monitor, not as a standalone PASS metric. A conservative gate should flag checkpoint pairs whose token-relation margin exceeds the no-false-negative threshold from this tiny E09/E10 set, then require Codex visual audit and conventional metrics before allowing scale.

Because only 8 checkpoint-regression rows are available and two E10 mixed rows still have positive latent drift, this gate is intentionally high-recall and may produce false positives. That is acceptable for safety: it should block or trigger inspection, not approve training.

This report does not authorize v14 scale. Current decision remains `DPO_RECIPE_NOT_FOUND_V14` / `NO_SCALE`.
