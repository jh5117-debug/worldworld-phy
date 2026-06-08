# TDW v5 aggressive 2x 200 validation report

Generated HDF5: 200/200
Validation OK: 200/200
Warmup key/visibility gate: 200/200
Strict v5 visible-motion accepted: 44/200
Too static under strict v5 threshold: 156/200
Too extreme: 0/200
Delayed camera motion: 0/200
Unique scene hashes: 200/200

Template distribution: {'drop': 60, 'collision': 60, 'roll': 40, 'containment': 40}
Camera distribution: {'orbit_left_72': 60, 'orbit_right_64': 30, 'strafe_left_180': 30, 'orbit_right_60': 40, 'orbit_left_44': 40}

Motion metrics min / avg / max:
- camera_path_length: 1.8034 / 3.2485 / 3.6956
- camera_path_length_first_8_frames: 0.1803 / 0.3249 / 0.3696
- background_motion_proxy: 0.0217 / 0.0390 / 0.0587
- background_motion_proxy_first_8_frames: 0.0179 / 0.0303 / 0.0531
- target_visible_ratio: 1.0000 / 1.0000 / 1.0000

Interpretation:
- The generation pipeline succeeded for all 200 samples.
- Camera motion starts immediately: delayed count is 0.
- Geometry motion is much stronger than the prior mild/v2/v3/v4 profiles.
- Strict v5 suitable count is low because the background proxy threshold was intentionally aggressive; user visually approved the v5 style, so the conversion set is labeled `human_approved_all`.

Raw validation markdown: `local_assets/data/physion/generated_v3/reports/validation_warmup_visible_motion_v5_aggressive_2x_demo_200.md`
Raw validation JSON: `local_assets/data/physion/generated_v3/reports/validation_warmup_visible_motion_v5_aggressive_2x_demo_200.json`
