# VideoGPA Encode Pipeline Inspect

## Repository

- Path: `local_assets/third_party/VideoGPA/official_repo`
- Commit: `551e63a5c2c493962f1e1d090bfa8324bf18b694`
- Remote: `https://github.com/Hongyang-Du/VideoGPA.git`

## Inspected Files

- `README.md`
- `train/01_preference_pair.py`
- `train/dataset.py`
- `train/CogVideoX-5B/02_encode.py`
- `train/CogVideoX-I2V-5B/02_encode.py`
- `train/CogVideoX1.5-5B/02_encode.py`
- `train/Wan2.2-TI2V-5B/02_encode.py`
- matching `03_train.py` files were located but not run.

## Answers

1. VideoGPA pair JSON is a `groups` JSON. Each group contains `group_id`, prompt/text prompt fields, video entries, and score metadata.
2. Encode input is VideoGPA metadata plus winner/loser video paths, prompts, and model-specific VAE/model configuration.
3. Encode output is expected to add latent/condition paths for each video entry in the model-specific backend.
4. Encode uses the VAE attached to the selected VideoGPA backend, e.g. CogVideoX or Wan2.2.
5. VideoGPA has a Wan2.2 TI2V encode path, but not LingBot-Fast's project-local WanI2VFast camera-conditioned path.
6. VideoGPA includes I2V/CogVideoX paths, but they are not the LingBot-Fast runtime.
7. VideoGPA does not natively accept Physion/LingBot poses and intrinsics in the inspected training dataset path.
8. Camera metadata is therefore preserved as `extra_condition` and sidecar JSON for a future LingBot-specific adapter.
9. Native VideoGPA latents cannot be assumed compatible with LingBot-Fast until `LingBotFastVideoGPAAdapter.load_vae` and `encode_video_to_latent` are real.
10. A LingBot-specific VAE adapter is required before real latent encode can be claimed.
11. A wrapper can complete format/readability smoke without modifying the official repo.
12. Do not edit or run `03_train.py` in this phase.

## Encode Scripts Found

- `train/CogVideoX-5B/02_encode.py`
- `train/CogVideoX-I2V-5B/02_encode.py`
- `train/CogVideoX1.5-5B/02_encode.py`
- `train/Wan2.2-TI2V-5B/02_encode.py`

## Compatibility Verdict

VideoGPA native encode is present, but real LingBot-Fast latent encode is blocked on a LingBot-specific VAE/condition adapter. This round therefore performs pair readability, video readability, and camera sidecar preservation only.
