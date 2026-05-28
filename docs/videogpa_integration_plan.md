# VideoGPA Integration Plan

- repo path: `local_assets/third_party/VideoGPA/official_repo`
- exists: True
- commit: `551e63a5c2c493962f1e1d090bfa8324bf18b694`

## Answers
1. Preference data is a `groups` JSON. Each group has `group_id`, `prompt`/`text_prompt`, optional `input_image_path`, `original_video_path`, `extra_condition`, and `videos`.
2. Our `videogpa_pairs.json` is format-compatible for metadata reading; actual encode/train compatibility still needs a LingBot-specific latent/condition adapter.
3. Encode input is a preference JSON plus video paths, prompts, model/VAE config, and output latent root.
4. Encode output is metadata with `latent_path`/`condition_path` per video in VideoGPA's native backends.
5. VideoGPA has image/video model paths for its supported backends, but not this LingBot-Fast camera-condition path out of the box.
6. VideoGPA does not natively consume camera poses/intrinsics; we preserve them in `extra_condition`.
7. The minimum adapter keeps VideoGPA pair ranking/loss semantics and adds LingBot condition collation outside the official repo.
8. VideoGPA Wan/CogVideoX loaders cannot be assumed to load LingBot-Fast; LingBot-Fast uses project-local WanI2VFast and camera Plucker conditioning.
9. A LingBotFastAdapter needs `load_model`, `encode_video_to_latent`, `encode_condition`, `prepare_winner_loser_batch`, and real `compute_dpo_energy_or_logprob`.
10. Encode smoke currently validates pair JSON and video readability; it stops before native latent encoding because the LingBot VAE/condition adapter is missing.
11. Do not modify official VideoGPA training scripts yet; use wrapper/adapter files under `cam_physgeo/dpo`.
12. Formal training still needs Fast inference, rollout reward validation, encode smoke with real LingBot latents, and a non-fake energy/logprob adapter.

## Discovered Scripts
- encode scripts: ['train/CogVideoX-5B/02_encode.py', 'train/CogVideoX-I2V-5B/02_encode.py', 'train/CogVideoX1.5-5B/02_encode.py', 'train/Wan2.2-TI2V-5B/02_encode.py', 'train/CogVideoX-5B/02_encode.py', 'train/CogVideoX-I2V-5B/02_encode.py', 'train/CogVideoX1.5-5B/02_encode.py', 'train/Wan2.2-TI2V-5B/02_encode.py']
- train scripts: ['train/CogVideoX-5B/03_train.py', 'train/CogVideoX-I2V-5B/03_train.py', 'train/CogVideoX1.5-5B/03_train.py', 'train/Wan2.2-TI2V-5B/03_train.py', 'train/CogVideoX-5B/03_train.py', 'train/CogVideoX-I2V-5B/03_train.py', 'train/CogVideoX1.5-5B/03_train.py', 'train/Wan2.2-TI2V-5B/03_train.py']

## Inspected Files
- `README.md`: {'line_count': 254, 'mentions': {'prompt': True, 'chosen': False, 'rejected': False, 'latent': True, 'wan': True, 'cogvideox': True, 'camera': True}}
- `train/01_preference_pair.py`: {'line_count': 296, 'mentions': {'prompt': False, 'chosen': False, 'rejected': False, 'latent': False, 'wan': False, 'cogvideox': False, 'camera': False}}
- `train/CogVideoX-5B/02_encode.py`: {'line_count': 272, 'mentions': {'prompt': True, 'chosen': False, 'rejected': False, 'latent': True, 'wan': False, 'cogvideox': True, 'camera': False}}
- `train/CogVideoX-5B/03_train.py`: {'line_count': 307, 'mentions': {'prompt': True, 'chosen': False, 'rejected': False, 'latent': True, 'wan': True, 'cogvideox': True, 'camera': False}}
- `train/CogVideoX-I2V-5B/02_encode.py`: {'line_count': 229, 'mentions': {'prompt': True, 'chosen': False, 'rejected': False, 'latent': True, 'wan': False, 'cogvideox': True, 'camera': False}}
- `train/CogVideoX-I2V-5B/03_train.py`: {'line_count': 300, 'mentions': {'prompt': True, 'chosen': False, 'rejected': False, 'latent': True, 'wan': True, 'cogvideox': True, 'camera': False}}
- `train/CogVideoX1.5-5B/02_encode.py`: {'line_count': 236, 'mentions': {'prompt': True, 'chosen': False, 'rejected': False, 'latent': True, 'wan': False, 'cogvideox': True, 'camera': False}}
- `train/CogVideoX1.5-5B/03_train.py`: {'line_count': 298, 'mentions': {'prompt': True, 'chosen': False, 'rejected': False, 'latent': True, 'wan': True, 'cogvideox': True, 'camera': False}}
- `train/Wan2.2-TI2V-5B/02_encode.py`: {'line_count': 240, 'mentions': {'prompt': True, 'chosen': False, 'rejected': False, 'latent': True, 'wan': True, 'cogvideox': False, 'camera': False}}
- `train/Wan2.2-TI2V-5B/03_train.py`: {'line_count': 417, 'mentions': {'prompt': True, 'chosen': False, 'rejected': False, 'latent': True, 'wan': True, 'cogvideox': False, 'camera': False}}
- `train/dataset.py`: {'line_count': 284, 'mentions': {'prompt': True, 'chosen': True, 'rejected': True, 'latent': True, 'wan': True, 'cogvideox': False, 'camera': False}}
