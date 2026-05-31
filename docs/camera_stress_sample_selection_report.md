# Camera Stress Sample Selection Report

## Command

```bash
python -m cam_physgeo.eval.select_camera_stress_samples \
  --samples local_assets/data/physion/processed/lingbot_cam_inputs/smoke \
  --out local_assets/reports/smoke/camera_stress_sample_selection \
  --top_k 10
```

## Selected Sample

- Top sample: `physion_movingcam_13db379640ce`
- Camera motion: `relative_yaw_180_reobserve`
- Template: `drop`
- Translation magnitude: `0.0`
- Trajectory length: `0.0`
- Rotation magnitude: `2.1636307710103373` rad
- Yaw proxy: `2.1464942232960413` rad
- Stress score: `108.62024998861276`

This sample was selected because it has the largest rotation/yaw stress among the smoke processed samples. The previous ablation sample `physion_movingcam_07abddf5748b` had much lower yaw (`0.17890078376627638`) and rotation (`0.3136431590915344`), so it was plausibly too weak for correct-vs-frozen to separate.

## Top Samples

1. `physion_movingcam_13db379640ce`: `relative_yaw_180_reobserve`, yaw `2.1465`, rotation `2.1636`
2. `physion_movingcam_1bb16ffe6fb6`: `relative_yaw_180_reobserve`, yaw `1.7937`, rotation `1.8896`
3. `physion_movingcam_1a0d32560b71`: `relative_yaw_180_reobserve`, yaw `1.8011`, rotation `1.8351`
4. `physion_movingcam_1f1bb7d06d70`: `occluder_lookaway_reobserve`, translation `1.5143`, trajectory `1.5716`
5. `physion_movingcam_07abddf5748b`: `offscreen_z_reobserve`, translation `1.3363`, trajectory `1.3822`

Outputs:

- `local_assets/reports/smoke/camera_stress_sample_selection/summary.json`
- `local_assets/reports/smoke/camera_stress_sample_selection/top_samples.csv`
- `local_assets/reports/smoke/camera_stress_sample_selection/top_sample.txt`
