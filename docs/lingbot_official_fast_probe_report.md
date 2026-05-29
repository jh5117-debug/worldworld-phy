# LingBot Official Fast Probe Report

## Search Result

The local LingBot checkout under `local_assets/third_party/lingbot_world` contains official/minimal-looking Fast entry points:

- `generate_fast.py`
- `run_fast.sh`
- `wan/image2video_fast.py`
- `scripts/generate_lingbot_fast_bo16.py`
- `scripts/generate_lingbot_fast_physics_idea.py`

## Intended Probe

The official probe should use:

- image: one `image.jpg` from `local_assets/data/physion/processed/lingbot_cam_inputs/smoke`
- prompt: `A synthetic physical scene.`
- output: `local_assets/outputs/smoke/lingbot_official_fast_probe`
- GPU: `CUDA_VISIBLE_DEVICES=6,7`
- minimal frame/step settings available in the official script

## Current Run Status

The official probe was not run in this pass because the H20 SSH connection repeatedly reset or timed out before the required script inspection and command construction could complete. No success is claimed.

## Interpretation

This remains an important isolation test:

- If official LingBot-Fast minimal image/prompt inference also stalls, the issue is in the LingBot runtime/T5/model initialization path.
- If official LingBot-Fast minimal inference succeeds, the issue is likely in the `cam_physgeo` adapter or the way the runtime bundle is invoked.

No official Fast output video exists yet for this branch.
