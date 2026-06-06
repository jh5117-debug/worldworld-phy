# TDW visible-motion v3 human review acceptance update

The user reviewed the `warmup_visible_motion_v3_start0_scene_diverse` 50-sample videos and confirmed that the videos are usable.

This updates the interpretation of the previous validator result:

- HDF5/key validation remains: 50 / 50.
- Scene diversity remains: 50 unique scene hashes / 50.
- Numeric `suitable_for_visible_motion_v3` remains: 28 / 50.
- Human review acceptance is now: 50 / 50.

The 22 strafe samples previously marked `too_static` / `delayed_camera_motion` should be treated as diagnostic warnings, not as hard rejects for this human-reviewed batch.

Full LingBot cam-only conversion was run for all 50 samples:

`local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v3_start0_scene_diverse_50_human_accepted_all/`

Conversion result:

- target.mp4: 50 / 50
- `use_action=false`: 50 / 50
- dummy `action.npy`: 50 / 50
- conversion errors: 0

The previous partial 28-sample conversion directory was deleted after all-50 conversion succeeded.

Do not run 200 automatically. The next step is an explicit user approval request for a v3 200-sample pilot.
