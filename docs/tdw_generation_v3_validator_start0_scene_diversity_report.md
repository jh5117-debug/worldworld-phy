# TDW Generation v3 Validator: Start0 and Scene Diversity

## Metrics Added

Motion magnitude:

- `camera_path_length_total`
- `yaw_change_proxy`
- `translation_magnitude_total`
- `background_motion_proxy`
- `parallax_proxy`

Early motion:

- `camera_path_length_first_8_frames`
- `camera_path_length_first_16_frames`
- `background_motion_proxy_first_8_frames`
- `background_motion_proxy_first_16_frames`
- `first_motion_frame`
- `delayed_camera_motion`

Scene diversity:

- `first_frame_phash`
- `id_mask_hash`
- `id_mask_unique_ids`
- `object_state_summary_hash`
- `prompt_hash`
- `scene_hash`
- `duplicate_scene_hash`

Acceptance flags:

- `too_static`
- `too_extreme`
- `delayed_camera_motion`
- `duplicate_scene_hash`
- `suitable_for_visible_motion_v3`

## V3 Acceptance

For `warmup_visible_motion_v3_start0_scene_diverse`, a sample is accepted only when:

- HDF5 keys and camera/object metadata are complete;
- target visibility is acceptable;
- total camera/background motion is above threshold;
- early camera/background motion is above threshold;
- camera motion is not delayed;
- the sample is not too extreme;
- scene hash is not a duplicate.

## Batch-Level Target

For the 50-sample review set:

- accepted samples >= 40/50;
- unique scene hashes >= 40;
- delayed camera motion <= 5;
- every template has accepted samples.
