# TDW v5 aggressive 2x demo plan

Profile: `warmup_visible_motion_v5_aggressive_2x_demo`

Purpose: answer the human-review request to roughly double visible camera motion and generate five demos. This profile is deliberately less conservative than v4/v3 and is review-only.

Planned samples: 5

Template distribution:
- drop: 1
- collision: 2
- roll: 1
- containment: 1

Camera variants:
- drop: `orbit_left_72`
- collision: `orbit_right_64`, `strafe_left_180`
- roll: `orbit_right_60`
- containment: `orbit_left_44`

Motion start: frame 0.

Scale relative to v4/v3: orbit/strafe magnitudes are intentionally pushed higher. This is not a 50/200 generation request.

Manifest: `local_assets/data/physion/generated_v3/manifests/plan_warmup_visible_motion_v5_aggressive_2x_demo_5.jsonl`
Output root: `local_assets/data/physion/generated_v3`
