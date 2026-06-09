# Prior-Art LingBot Warmup Dataloader Review

Date: 2026-06-09

## Search Scope

Searched `cam_physgeo`, `scripts`, `configs`, `local_assets/third_party/lingbot_world`, and `/home/nvme03/workspace/lingbot-world` for existing dataset, dataloader, warmup, camera-condition, and LingBot file conventions.

Search log:
`local_assets/experiments/exp_tdw_v5_200_lingbot_warmup_gate/logs/prior_art_lingbot_grep.txt`

## Existing Conventions Found

- Camera-conditioned samples use:
  - `image.jpg`
  - `target.mp4`
  - `poses.npy`
  - `intrinsics.npy`
  - `action.npy`
  - `prompt.txt`
  - `metadata.json`
- Existing DPO and eval paths require `use_action=false`.
- `action.npy` is a dummy compatibility fallback; camera conditioning is carried by poses/intrinsics.
- Existing code paths reference `target.mp4` for clean target video and use the sample directory as the camera-condition bundle.

## Relevant Existing Code

- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`
- `cam_physgeo/dpo/pair_builder.py`
- `cam_physgeo/eval/run_inference.py`
- `cam_physgeo/eval/camera_condition_ablation.py`
- `cam_physgeo/eval/probe_camera_embedding.py`

## Minimal Smoke Plan

Use a manifest-backed dataloader smoke before any model update:

- read train/val/test JSONL manifests;
- decode `target.mp4`;
- load `image.jpg`, `poses.npy`, `intrinsics.npy`, `action.npy`;
- verify `metadata.use_action=false`;
- confirm action norm is zero;
- report batch shapes and decode timing.

This follows the existing cam-only sample contract instead of inventing a new data format.

## Forward-Loss Dry-Run Plan

The next safe stage is a no-backward/no-optimizer/no-checkpoint forward-loss dry-run. Because full LingBot-Fast/VAE/T5 model loading can consume substantial GPU memory and time, it should remain a separately approved pre-training step when GPU6/7 or GPU7 are actually free.
