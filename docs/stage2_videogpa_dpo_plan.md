# Stage 2 VideoGPA DPO Plan

Stage 2 is not trained during this smoke pass. The main route is VideoGPA-compatible DPO, not a new standalone trainer.

## Training Gate

Do not train until reward calibration on clean Physion GT vs corrupted GT reaches about `0.85` clean-win rate and the per-corruption drops match their intended reward components.

## Current Smoke Scope

- Build clean Physion GT > corrupted GT pairs.
- Score both videos with the PhysGeo reward.
- Filter by reward margin.
- Export VideoGPA-compatible JSON with prompt, chosen video, rejected video, and camera metadata.
- Inspect VideoGPA repository structure.

## Adapter Gap

VideoGPA's original scripts are prompt/video-pair oriented. LingBot-Fast needs image or prefix video, camera poses, and intrinsics. The adapter must extend the dataset batch with:

- `image` or `prefix`
- `poses.npy`
- `intrinsics.npy`
- `metadata.json`
- dummy zero `action.npy` only if the legacy runtime requires it

The LingBot/Wan policy and reference model loader must then map these tensors into the same denoising/noise-timestep path used by DPO.

## Why No Training Now

Reward calibration is the first gate. Training on weak or mis-ranked clean/corrupt pairs would turn DPO into reward noise amplification. Full `03_train.py` launch remains blocked until reward, LingBot-Fast loading, and camera-condition adapters are all verified.
