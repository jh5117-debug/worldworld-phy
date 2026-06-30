# LingBot-Fast Camera Condition Audit

Current Status: CAMERA_CONDITION_PATH_CONFIRMED_BUT_SENSITIVITY_PARTIAL

Updated: 2026-06-30 14:21:36

This file corrects the previous `UNKNOWN` wording. No new camera-variant rollout was launched in the v5 reward-visual-alignment round, but earlier camera ablation has already shown:

- repeat A vs B = 0.0
- correct vs frozen = 0.0
- correct vs reversed = 0.02218
- correct vs exaggerated_yaw = 0.03502
- correct vs exaggerated_translation = 0.03765

Interpretation: the camera condition path is confirmed, strong perturbations affect output, and ordinary camera motion sensitivity is weak. Future camera work should calibrate sensitivity and pair mining, not re-prove that the path exists.
