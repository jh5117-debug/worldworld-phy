# Epipolar + C-SGC Reward Calibration

This is a preliminary calibration using clean GT and synthetic corruptions. It does not run DPO and does not build pairs.

- Input root: `local_assets/meeting_eval_20260624_011137`
- Epipolar rows: 40
- C-SGC rows: 40
- Calibration CSV: `reports/meeting_eval_20260624_011137/reward_calibration.csv`
- Overall clean > candidate rate for combined R_geo: 0.500

## Per Corruption / Model Ordering

| Candidate | N | R_epi clean>candidate | R_csgc clean>candidate | R_geo clean>candidate | Mean delta R_geo |
|---|---:|---:|---:|---:|---:|
| background_drift | 8 | 0.625 | 0.625 | 0.875 | -0.0025 |
| camera_freeze | 8 | 0.250 | 0.375 | 0.250 | -0.0057 |
| nonrigid_warp | 8 | 0.375 | 0.500 | 0.625 | -0.0023 |
| wrong_camera | 8 | 0.250 | 0.375 | 0.250 | 0.0019 |

## Status

The combined geometry reward does not yet meet the requested 0.85 clean-over-corruption target. Treat Epipolar/C-SGC as diagnostic metrics, not DPO-ready reward terms.

Calibration status: `BLOCKED_OR_PRELIMINARY`
