# Camera Condition Effect Stress V2 Report

## Command

```bash
CUDA_VISIBLE_DEVICES=6,7 TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 python -m cam_physgeo.eval.camera_condition_ablation \
  --samples local_assets/data/physion/processed/lingbot_cam_inputs/smoke \
  --sample_id_from local_assets/reports/smoke/camera_stress_sample_selection/top_sample.txt \
  --out local_assets/data/physion/processed/rollouts/camera_ablation_stress_v2 \
  --model_type fast \
  --limit 1 \
  --num_frames 8 \
  --num_steps 1 \
  --resolution 480x832 \
  --variants repeat_correct_A repeat_correct_B frozen reversed exaggerated_yaw exaggerated_translation \
  --same_seed true \
  --save_contact_sheet \
  --debug-camera-condition \
  --save-condition-summary \
  --timeout 900 \
  --local-files-only
```

## Result

- Selected sample: `physion_movingcam_13db379640ce`
- Resolution: `480x832`
- Frames/steps: `8 / 1`
- Variants generated: `6/6`
- Output root: `local_assets/data/physion/processed/rollouts/camera_ablation_stress_v2/physion_movingcam_13db379640ce`
- Comparison contact sheet: `local_assets/data/physion/processed/rollouts/camera_ablation_stress_v2/physion_movingcam_13db379640ce/comparison_contact_sheet.jpg`

## Metrics

- Repeat baseline, A vs B pixel L1: `0.0`
- Correct A vs frozen pixel L1: `0.0`
- Correct A vs reversed pixel L1: `0.022175125777721405`
- Correct A vs exaggerated_yaw pixel L1: `0.03501671180129051`
- Correct A vs exaggerated_translation pixel L1: `0.03765185922384262`
- Reversed motion delta: `0.0049514248967170715`
- Exaggerated-yaw motion delta: `0.005172686651349068`
- Exaggerated-translation motion delta: `0.0059309303760528564`
- Metric backend for ablation diffs: frame-diff proxy.

## Conclusion

Camera video-level effect is now stronger than partial. The selected high-yaw stress sample shows reversed and exaggerated camera variants differ from same-seed repeat baseline, while repeat baseline is exactly zero. Frozen still matches correct in this short setting, so the model is clearly sensitive to strong temporal camera changes, but ordinary frozen/correct separation may need longer frames or a camera scale/shift strength check.

VideoGPA encode remains a next-round decision only; it was not run.
