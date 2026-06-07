# Final report: TDW visible-motion v4 stronger start0 review smoke

## Scope

User requested a stronger visible-motion sample after v3 200 looked usable but still slow. This run generated only a 16-sample v4 smoke. No training, DPO, VideoGPA 03_train, Stage1, reward calibration, 50/200/1k expansion, LoRA, or checkpoint was run.

## Result

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

## Judgment

Compared with v3, the weak strafe issue is directly addressed: v3 strafe was about 0.55/0.65 camera path; v4 strafe_090 validates at about 0.9017 with first-8-frame path about 0.0902. Orbit samples are also stronger, with drop orbit_40 reaching about 1.9758 path while remaining non-extreme in this smoke.

## Next

Human-review the v4 gallery. If the visual motion is acceptable, approve a v4 50-sample review set. Do not jump to 200/1k until v4 50 passes human review.
