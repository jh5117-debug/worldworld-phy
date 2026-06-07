# TDW visible-motion v4 stronger start0 profile report

This profile is a small review smoke requested after v3 200 looked usable but still visually slow. It is not a 200/1k run.

Design:
- Keep camera motion start at frame 0.
- Increase orbit for drop to 36/40 degrees.
- Use stronger non-drop orbit: collision 32, roll 30, containment 22.
- Replace weak v3 strafe 0.55/0.65 with strafe 0.90 probes.
- Keep dolly disabled.
- Keep target visibility and non-stress constraints.

Thresholds:
- min camera path total: 0.85
- max camera path total: 2.10
- min first-8-frame path: 0.085
- min first-16-frame path: 0.17
- min background motion: 0.022
- min first-8 background motion: 0.007

- Profile: `warmup_visible_motion_v4_stronger_start0_review`
- Generated HDF5: 16/16
- Validation OK: 16/16
- Suitable for visible motion: 16/16
- Too static: 0/16
- Too extreme: 0/16
- Delayed camera motion: 0/16
- Unique scene hash: 16/16
- Template distribution: `{'drop': 4, 'collision': 4, 'roll': 4, 'containment': 4}`
- Camera distribution: `{'orbit_left_36': 1, 'orbit_right_36': 1, 'orbit_left_40': 1, 'orbit_right_40': 1, 'orbit_left_32': 1, 'orbit_right_32': 1, 'strafe_left_090': 3, 'strafe_right_090': 3, 'orbit_left_30': 1, 'orbit_right_30': 1, 'orbit_left_22': 1, 'orbit_right_22': 1}`
- Camera path min/avg/max: 0.9017 / 1.4567 / 1.9758
- First-8 path min/avg/max: 0.0902 / 0.1457 / 0.1976
- Background motion min/avg/max: 0.0245 / 0.0335 / 0.0432
- First-8 background motion min/avg/max: 0.0187 / 0.0254 / 0.0345
- Target visible ratio min/avg/max: 1.0000 / 1.0000 / 1.0000
- LingBot conversion: 16/16
- target.mp4 exists: 16/16
- metadata use_action=false: 16/16
- action.npy present: 16/16
- Review gallery: `local_assets/reports/human_review/tdw_visible_motion_v4_stronger_start0_review_16/video_gallery.html`
