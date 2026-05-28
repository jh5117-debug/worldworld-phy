# VideoGPA Encode Smoke Report

Command inspected `local_assets/third_party/VideoGPA/official_repo` and read `local_assets/data/physion/processed/dpo_pairs/smoke/videogpa_pairs.json`.

## Result

- Pair JSON readable: yes.
- Groups: 51.
- Checked groups: 2.
- Winner/loser videos readable: yes, 4 videos inspected.
- Prompt preserved: yes.
- Camera condition preserved in `extra_condition`: yes.
- Actual native VideoGPA encode attempted: no.
- Latent output: none.
- Training launched: no.

## Why Encode Did Not Run

VideoGPA native encode scripts are backend-specific (`CogVideoX-*`, `Wan2.2-TI2V-5B`). They expect their own VAE/model condition format. LingBot-Fast uses project-local `WanI2VFast`, a Fast checkpoint shard layout, and camera Plucker conditioning from poses/intrinsics. A LingBot-specific latent and condition adapter is required before native VideoGPA encode can be called honestly.

Next required adapter functions:

- `LingBotFastVideoGPAAdapter.encode_video_to_latent` using LingBot VAE.
- `LingBotFastVideoGPAAdapter.encode_condition` with image, prompt, poses, intrinsics, and camera Plucker embeddings.
- VideoGPA metadata update with `latent_path` and `condition_path`.

