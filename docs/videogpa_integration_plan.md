# VideoGPA Integration Plan

- repo path: `local_assets/third_party/VideoGPA/official_repo`
- exists: True
- commit: `551e63a5c2c493962f1e1d090bfa8324bf18b694`
- note: the parent `local_assets/third_party/VideoGPA` directory was preserved because it already existed; the official clone used by this project is the `official_repo` subdirectory.

## Answers
1. Preference data is a `groups` JSON. Each group has `group_id`, `prompt`/`text_prompt`, optional `input_image_path`, `original_video_path`, and `videos`; each video stores `video_path`, `generation_id`, `consistency_score`, `motion_norm`, and later `latent_path`/`condition_path`.
2. The encode stage needs video paths, prompts, image prompts for I2V/TI2V, model path, output JSON, latent root, GPU list, and frame count.
3. The DPO train stage needs encoded latents and conditions, `metric_name`, `metric_mode`, `min_gap`, beta, LoRA config, and a compatible model backend.
4. VideoGPA includes backend-specific train scripts; the inspected files indicate whether Wan/CogVideoX strings are present.
5. LingBot-Fast is not assumed binary-compatible with VideoGPA Wan entrypoints until a LingBot camera-condition batch adapter is written.
6. Required adapters: Physion pair exporter, LingBot cam-condition dataset adapter, latent encoder adapter, and frozen reference/policy loader adapter.
7. Clean/corrupt Physion pairs export into one VideoGPA group per pair: clean GT has lower `consistency_score = 1 - R_total`, corrupted has higher score.
8. Camera poses/intrinsics are preserved in group-level `extra_condition` and `metadata`; training support is a separate adapter step.
9. If VideoGPA only supports text conditioning, extend the dataset batch with image/prefix/camera tensors while keeping the DPO loss path intact.
10. Current dry-run checks repository shape and exported JSON readability; no `03_train.py` long training is launched.

## Inspected Files
- `README.md`: {'line_count': 254, 'mentions': {'prompt': True, 'chosen': False, 'rejected': False, 'latent': True, 'wan': True, 'cogvideox': True}}
- `train/01_preference_pair.py`: {'line_count': 296, 'mentions': {'prompt': False, 'chosen': False, 'rejected': False, 'latent': False, 'wan': False, 'cogvideox': False}}
- `train/dataset.py`: {'line_count': 284, 'mentions': {'prompt': True, 'chosen': True, 'rejected': True, 'latent': True, 'wan': True, 'cogvideox': False}}
