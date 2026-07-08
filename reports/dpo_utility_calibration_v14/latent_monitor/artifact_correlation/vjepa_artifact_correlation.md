# v14 V-JEPA2 Artifact Correlation

Decision: `VJEPA_ARTIFACT_CORRELATION_WEAK_MONITOR_ONLY`

This analysis reuses existing V-JEPA2 checkpoint-regression scores and Codex visual labels. It does not run training, decode videos, or generate new rollouts.

- Source CSV: `reports/dpo_utility_calibration_v14/latent_monitor/checkpoint_regression_all_available/vjepa2_checkpoint_regression_all_with_visual.csv`
- Rows: `24`

| Group | Label | Metric | Pos/Neg | AUC positive-higher | Mean pos | Mean neg | Interpretation |
|---|---|---|---:|---:|---:|---:|---|
| `all_available` | `worse_than_step0` | `vjepa_margin` | 19/5 | 0.484 | 0.00284069 | 0.00237569 | `NO_RELIABLE_DISCRIMINATION` |
| `all_available` | `worse_than_step0` | `token_relation_margin` | 19/5 | 0.463 | 0.0635638 | 0.0613157 | `NO_RELIABLE_DISCRIMINATION` |
| `all_available` | `identity_worse` | `vjepa_margin` | 10/14 | 0.779 | 0.00405868 | 0.00180462 | `PROMISING_DISCRIMINATION_SMALL_N` |
| `all_available` | `identity_worse` | `token_relation_margin` | 10/14 | 0.736 | 0.0710836 | 0.0573896 | `WEAK_DISCRIMINATION_SMALL_N` |
| `all_available` | `artifact_worse` | `vjepa_margin` | 10/14 | 0.779 | 0.00405868 | 0.00180462 | `PROMISING_DISCRIMINATION_SMALL_N` |
| `all_available` | `artifact_worse` | `token_relation_margin` | 10/14 | 0.736 | 0.0710836 | 0.0573896 | `WEAK_DISCRIMINATION_SMALL_N` |
| `scalar_positive_e07_e09_e10` | `worse_than_step0` | `vjepa_margin` | 10/2 | 0.650 | 0.00405868 | 0.00235477 | `WEAK_DISCRIMINATION_SMALL_N` |
| `scalar_positive_e07_e09_e10` | `worse_than_step0` | `token_relation_margin` | 10/2 | 0.650 | 0.0710836 | 0.0573091 | `WEAK_DISCRIMINATION_SMALL_N` |
| `scalar_positive_e07_e09_e10` | `identity_worse` | `vjepa_margin` | 10/2 | 0.650 | 0.00405868 | 0.00235477 | `WEAK_DISCRIMINATION_SMALL_N` |
| `scalar_positive_e07_e09_e10` | `identity_worse` | `token_relation_margin` | 10/2 | 0.650 | 0.0710836 | 0.0573091 | `WEAK_DISCRIMINATION_SMALL_N` |
| `scalar_positive_e07_e09_e10` | `artifact_worse` | `vjepa_margin` | 10/2 | 0.650 | 0.00405868 | 0.00235477 | `WEAK_DISCRIMINATION_SMALL_N` |
| `scalar_positive_e07_e09_e10` | `artifact_worse` | `token_relation_margin` | 10/2 | 0.650 | 0.0710836 | 0.0573091 | `WEAK_DISCRIMINATION_SMALL_N` |
| `pre_v14_screen_e02_e04_e05` | `worse_than_step0` | `vjepa_margin` | 9/3 | 0.296 | 0.00148737 | 0.00238963 | `INVERSE_OR_NOISY_RELATION` |
| `pre_v14_screen_e02_e04_e05` | `worse_than_step0` | `token_relation_margin` | 9/3 | 0.333 | 0.0552084 | 0.0639868 | `INVERSE_OR_NOISY_RELATION` |
| `pre_v14_screen_e02_e04_e05` | `identity_worse` | `vjepa_margin` | 0/12 |  |  | 0.00171293 | `UNDEFINED_SINGLE_CLASS_OR_TOO_FEW_ROWS` |
| `pre_v14_screen_e02_e04_e05` | `identity_worse` | `token_relation_margin` | 0/12 |  |  | 0.057403 | `UNDEFINED_SINGLE_CLASS_OR_TOO_FEW_ROWS` |
| `pre_v14_screen_e02_e04_e05` | `artifact_worse` | `vjepa_margin` | 0/12 |  |  | 0.00171293 | `UNDEFINED_SINGLE_CLASS_OR_TOO_FEW_ROWS` |
| `pre_v14_screen_e02_e04_e05` | `artifact_worse` | `token_relation_margin` | 0/12 |  |  | 0.057403 | `UNDEFINED_SINGLE_CLASS_OR_TOO_FEW_ROWS` |

## Interpretation

- V-JEPA2 margins are useful as a high-recall drift/inspection signal because margins are positive for checkpoint changes and WIN/LOSE differences where videos are available.
- Artifact-specific discrimination has a promising small-N signal for identity/artifact labels in the full 24-row set, but it weakens on the scalar-positive E07/E09/E10 subset where most samples are already visually bad.
- Therefore V-JEPA2 should not be used as a standalone approval metric or direct reward yet. It should be paired with artifact-specific visual labels and explicit rejection gates in v15.

## Outputs

- CSV: `reports/dpo_utility_calibration_v14/latent_monitor/artifact_correlation/vjepa_artifact_correlation.csv`
- JSON: `reports/dpo_utility_calibration_v14/latent_monitor/artifact_correlation/vjepa_artifact_correlation.json`
