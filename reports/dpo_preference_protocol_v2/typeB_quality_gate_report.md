# Type B Loser Quality Gate v2 Report

Current Status: BLOCKED_BY_BLUR_QUALITY_GATE

- Rollout candidates audited: 48
- Protocol v1 Type B candidates audited with blur/energy: 16
- Type B selected by v2: 0
- Type B rejected by v2: 16

The v2 gate requires loser_sharpness_ratio >= 0.55, visual_quality >= 1, R_quality >= condition p40, positive reward margin, positive audited Delta_ref, and no collapse/black/global-freeze/scene-replacement tags.

## Rejection Reasons

- sharpness_ratio_lt_0.55: 16
- r_quality_below_condition_p40: 10
