# Final report: TDW v5 aggressive 2x demo

## Scope

User requested five demos with substantially larger camera motion. This run generated only the requested 5-sample review demo. No 50, 200, or 1k generation was run. No training, DPO, VideoGPA training, Stage1, rollout, or reward calibration was run.

## Generation

Profile: `warmup_visible_motion_v5_aggressive_2x_demo`
Generated HDF5: 5/5
Templates: drop 1, collision 2, roll 1, containment 1
Cameras: `orbit_left_72`, `orbit_right_64`, `strafe_left_180`, `orbit_right_60`, `orbit_left_44`
Display/GPU: `DISPLAY=:8` / GPU0-bound TDW run

## Motion quality

- camera_path_length min/avg/max: 1.8034 / 3.1506 / 3.6352
- first-8-frame path min/avg/max: 0.1803 / 0.3151 / 0.3635
- background_motion_proxy min/avg/max: 0.0252 / 0.0390 / 0.0506
- background_motion_proxy_first_8 min/avg/max: 0.0204 / 0.0299 / 0.0383
- delayed_camera_motion: 0/5
- too_extreme: 0/5
- too_static by strict v5 threshold: 3/5

Interpretation: camera geometry is now much more aggressive and starts at frame 0. The strict background-motion threshold still rejects 3/5, so this is a review set rather than a profile ready for 50-sample generation.

## Visibility

Validation OK: 5/5
Target visible ratio: all 1.0
Long foreground disappearance: none reported by validation table

## Conversion

Converted for review: 5/5
`target.mp4`: 5/5
`use_action=false`: enforced
Dummy `action.npy`: generated

## Human review

Review index: `local_assets/reports/human_review/tdw_visible_motion_v5_aggressive_2x_demo_5/review_index.md`
Gallery: `local_assets/reports/human_review/tdw_visible_motion_v5_aggressive_2x_demo_5/video_gallery.html`
Sample table: `local_assets/reports/human_review/tdw_visible_motion_v5_aggressive_2x_demo_5/sample_table.csv`

## Safety

No training. No DPO. No VideoGPA 03_train. No Stage1. No reward calibration. No 50/200/1k. No LoRA/checkpoint saved. Generated assets remain under `local_assets` and must not be committed.

## Recommendation

Use this 5-sample demo for visual judgment. If this is too fast or too much orbit, the next sensible profile is a v5-lite midpoint between v4 and this v5 demo. If this is the first set that visibly expresses camera conditioning, tune thresholds and run a 10-sample v5-lite/v5 follow-up before any 50-sample request.
