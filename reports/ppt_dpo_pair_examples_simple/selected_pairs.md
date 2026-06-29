# Selected Simple PPT Pairs

Showcase contains 5 pairs/candidates after blur audit.

Strict quality note: all current Type B rollout losers fail the proposed loser_sharpness_ratio >= 0.55 gate, so Type B rows are included as diagnostic examples, not as clean recommended PPT positives. The Type A local corruption row is the cleanest strict-pass example.

## Pair 1: `protocol_v1_B_008_prefix5_anchored_95981b8f74bed0_background_drift_stageA_final`

- Type: `gt_vs_medium_hard_rollout`
- Failure: background drift + hallucinated fragments
- Winner / loser reward: 1.000000 / 0.663222 (margin 0.336778)
- Delta_ref: 0.117087
- Sharpness ratio: 0.191837
- Strict quality status: diagnostic_blur_failed
- Why: Type B containment case with the clearest reward/energy support and visible extra fragments/camera-background degradation.

## Pair 2: `protocol_v1_B_001_prefix5_anchored_1128e39109fc83_object_deformation_stageA_final`

- Type: `gt_vs_medium_hard_rollout`
- Failure: extra object / identity instability
- Winner / loser reward: 1.000000 / 0.694814 (margin 0.305186)
- Delta_ref: 0.100097
- Sharpness ratio: 0.048811
- Strict quality status: diagnostic_blur_failed
- Why: Type B collision case where the rollout remains readable but adds extra foreground/object identity artifacts.

## Pair 3: `protocol_v1_B_012_prefix5_anchored_dc458b2cf487d8_wrong_camera_motion_stageA_final`

- Type: `gt_vs_medium_hard_rollout`
- Failure: wrong camera following + weak event
- Winner / loser reward: 1.000000 / 0.663222 (margin 0.336778)
- Delta_ref: 0.034382
- Sharpness ratio: 0.191837
- Strict quality status: diagnostic_blur_failed
- Why: Type B containment case for explaining wrong camera following and weak physical relation, without a collapsed loser.

## Pair 4: `protocol_v1_B_007_prefix5_anchored_7f708dfe212ad6_freeze_foreground_stageA_final`

- Type: `gt_vs_medium_hard_rollout`
- Failure: partial freeze / weak physical event
- Winner / loser reward: 1.000000 / 0.694814 (margin 0.305186)
- Delta_ref: 0.076811
- Sharpness ratio: 0.048811
- Strict quality status: diagnostic_blur_failed
- Why: Type B collision case for partial freeze / weak event dynamics; useful as a medium-hard rollout loser.

## Pair 5: `protocol_v1_A_030_02222_collision_orbit_right_64_seed41222_wrong_camera_motion_local`

- Type: `local_corruption`
- Failure: controlled local wrong-camera motion
- Winner / loser reward: 1.000000 / 0.740000 (margin 0.260000)
- Delta_ref: 0.028059
- Sharpness ratio: 0.727608
- Strict quality status: recommended
- Why: Type A controlled local corruption example for LocalDPO-style future-only negative construction.
