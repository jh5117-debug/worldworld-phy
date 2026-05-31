# VideoGPA Encode Dry-Run Report

## Command Scope

Dry-run used the fresh `gt_vs_fast` VideoGPA JSON:

`local_assets/data/physion/processed/dpo_pairs/videogpa_encode_smoke/videogpa_gt_vs_fast_pairs.json`

No training command and no VideoGPA `03_train.py` command was launched.

## Readability Checks

- Pair JSON readable: yes.
- Groups checked: `2`.
- Winner videos readable: yes.
- Loser videos readable: yes.
- Prompt readable: yes.
- Condition image readable: yes.
- Poses metadata readable: yes.
- Intrinsics metadata readable: yes.
- `use_action=false`: preserved.
- Output directory writable: yes.

## Video Metadata

- Clean GT videos: 81 frames, 832x480, 16 fps.
- Fast rollout videos: 9 frames, 832x480, 16 fps.

## VideoGPA Paths

- Native encode scripts found:
  - `train/CogVideoX-5B/02_encode.py`
  - `train/CogVideoX-I2V-5B/02_encode.py`
  - `train/CogVideoX1.5-5B/02_encode.py`
  - `train/Wan2.2-TI2V-5B/02_encode.py`
- Native train scripts found but not run.
- LingBot-Fast VAE/tokenizer/model paths are not part of the native VideoGPA encode configs.

## Result

Dry-run passed metadata and video readability. It intentionally stopped before native latent encode because LingBot-Fast VAE/condition encode is not wired into VideoGPA yet.
