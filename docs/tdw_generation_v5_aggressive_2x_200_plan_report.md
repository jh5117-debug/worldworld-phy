# TDW v5 aggressive 2x 200-sample plan

Profile: `warmup_visible_motion_v5_aggressive_2x_demo`

User selected the v5 aggressive demo as visually acceptable and approved GPU0 / DISPLAY=:8 for a temporary 200-sample generation. This is not a 1k run and not training.

Planned samples: 200

Template distribution:
- drop: 60
- collision: 60
- roll: 40
- containment: 40

Camera distribution:
- orbit_left_72: 60
- orbit_right_64: 30
- strafe_left_180: 30
- orbit_right_60: 40
- orbit_left_44: 40

Plan checks:
- scene_seed_unique: 200
- stress/offscreen/reobserve/extreme/occluder/dolly: none
- camera starts at frame 0

Manifest: `local_assets/data/physion/generated_v3/manifests/plan_warmup_visible_motion_v5_aggressive_2x_demo_200.jsonl`
Output root: `local_assets/data/physion/generated_v3`

Safety:
- no training
- no DPO
- no VideoGPA 03_train
- no Stage1
- no 1k generation
- generated assets under `local_assets` must not be committed
