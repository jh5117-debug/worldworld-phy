# Reward Calibration Expanded Report

Expanded calibration used the 50-sample smoke manifest because the manifest contains 50 entries.

Output root: `local_assets/reports/reward_calibration/smoke_50_or_100`.

## Result

- Samples: 50.
- Comparisons: 300.
- Clean average `R_total`: 0.1041.
- Corrupted average `R_total`: 0.0449.
- Clean average without quality: 0.1054.
- Corrupted average without quality: 0.0453.
- Clean > corrupted win rate: 0.6033.
- Reached 0.85 gate: false.

## Per-Corruption Win Rate

- background_drift: 0.040.
- freeze_foreground: 0.880.
- global_freeze: 0.880.
- object_color_identity_change: 0.880.
- object_deformation: 0.880.
- reobserve_mismatch: 0.060.

## Interpretation

The 20-sample result from the previous pass was not stable. Freeze and object corruptions are separated, but background drift and reobserve mismatch are not. This is consistent with the current fallback backend status: `R_bg/R_cam` do not yet use real optical flow/depth rigid residuals, and `R_reobs` does not yet use real DINO/V-JEPA features.

Do not expand DPO pair generation or start DPO until this returns above 0.85 on 50-100 samples.

