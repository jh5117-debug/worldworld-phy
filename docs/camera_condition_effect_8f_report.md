# Camera Condition Effect 8F Report

## Run

- Command target: `cam_physgeo.eval.camera_condition_ablation`
- Sample: `physion_movingcam_07abddf5748b`
- Variants requested: `repeat_correct_A`, `repeat_correct_B`, `frozen`, `exaggerated_yaw`
- Same seed requested: yes
- Initial resolution: `480x832`
- Fallback resolution used: `256x448`
- Frames/steps: `8` frames, `1` step
- GPU: `CUDA_VISIBLE_DEVICES=6,7`
- Output root: `local_assets/data/physion/processed/rollouts/camera_ablation_effect_8f_256/physion_movingcam_07abddf5748b`

The first 480x832 attempt hit CUDA OOM during model transfer because another process occupied most GPU memory. The 8-frame setting itself was valid: it did not reproduce the earlier 4-frame negative-dimension failure. The fallback 256x448 run completed all four variants.

## Outputs

- `repeat_correct_A`: `local_assets/data/physion/processed/rollouts/camera_ablation_effect_8f_256/physion_movingcam_07abddf5748b/repeat_correct_A/physion_movingcam_07abddf5748b/generated.mp4`
- `repeat_correct_B`: `local_assets/data/physion/processed/rollouts/camera_ablation_effect_8f_256/physion_movingcam_07abddf5748b/repeat_correct_B/physion_movingcam_07abddf5748b/generated.mp4`
- `frozen`: `local_assets/data/physion/processed/rollouts/camera_ablation_effect_8f_256/physion_movingcam_07abddf5748b/frozen/physion_movingcam_07abddf5748b/generated.mp4`
- `exaggerated_yaw`: `local_assets/data/physion/processed/rollouts/camera_ablation_effect_8f_256/physion_movingcam_07abddf5748b/exaggerated_yaw/physion_movingcam_07abddf5748b/generated.mp4`
- Comparison contact sheet: `local_assets/data/physion/processed/rollouts/camera_ablation_effect_8f_256/physion_movingcam_07abddf5748b/comparison_contact_sheet.jpg`

## Metrics

- Repeat baseline pixel L1, `repeat_correct_A` vs `repeat_correct_B`: `0.0`
- `repeat_correct_A` vs `frozen` pixel L1: `0.0`
- `repeat_correct_A` vs `exaggerated_yaw` pixel L1: `0.02547357603907585`
- Repeat baseline motion delta: `0.0`
- Frozen motion delta: `0.0`
- Exaggerated-yaw motion delta: `2.0097941160202026e-05`
- Metric backend for this ablation comparison: frame-diff proxy, not learned optical flow.

## Conclusion

Video-level camera effect is partially proven. With same-seed repeats, stochastic baseline was exactly zero, while the exaggerated-yaw camera produced a nonzero video difference. Frozen camera matched correct camera in this sample, so normal-scale camera sensitivity is not yet proven. The next camera-only check should use longer frames or a stronger fixed-noise ablation if we need to quantify ordinary camera motion rather than a deliberately exaggerated perturbation.

VideoGPA encode remains disallowed because reward is still missing a real DINO feature backend.
