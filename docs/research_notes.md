# Research Notes

Sources actually found/read:

- Local LingBot README: `/home/nvme03/workspace/world_model_phys/code/lingbot-world/README.md`
- Local VideoREPA README: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/third_party/VideoREPA/README.md`
- Local V-JEPA2 README: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/third_party/vjepa2_official/README.md`
- LingBot-World arXiv: https://arxiv.org/abs/2601.20540
- GeoFlow arXiv: https://arxiv.org/abs/2605.18365
- VideoREPA arXiv: https://arxiv.org/abs/2505.23656
- V-JEPA2 arXiv: https://arxiv.org/abs/2506.09985
- VideoGPA arXiv: https://arxiv.org/abs/2601.23286
- Causal Forcing arXiv: https://arxiv.org/abs/2602.02214

## LingBot / LingBot-World

- LingBot-World is an open-source world simulator built on video generation and Wan2.2.
- The local README reports camera-pose control for LingBot-World-Base (Cam), with `intrinsics.npy` shaped `[num_frames, 4]` as `[fx, fy, cx, cy]` and `poses.npy` shaped `[num_frames, 4, 4]` in OpenCV coordinates.
- Inference can run with image, prompt, and optional control signals through `action_path`; for Base-Cam this path contains camera control files, not necessarily semantic actions.
- Base-Cam is the directly relevant model for camera-conditioned I2V/V2V.
- Base-Act/action control is not the main line for this refactor.
- The README states long-horizon memory and consistency as a goal, but the current project failures show that physical event consistency and reobserve stability still need explicit alignment.
- LingBot-Fast is associated with real-time/few-step directions, but the public local README marks Fast as unreleased; we therefore keep Fast interfaces configurable without assuming local weights.
- We can study camera-conditioned physical prediction without real `action.npy`; if legacy code requires it, dummy zero action is compatibility only.

Borrowed: camera-conditioned LingBot interface, image/prompt/poses/intrinsics input contract.

Not copied: action/game conditioning as the core objective.

## GeoFlow

- GeoFlow argues that ordinary video denoising/SFT lacks explicit geometric coherence incentives.
- Its key idea is that background motion should be explainable by rigid camera-induced flow.
- Independently moving foreground objects should preserve appearance identity along motion trajectories.
- It combines optical flow, depth/pose prediction, and feature correspondence.
- `R_geo` targets rigid geometric consistency; `R_dino` targets feature/identity consistency.
- It is model agnostic and can be used as a reward for video generators.
- Pure online RL/GRPO depends heavily on base rollout quality and can be fragile if all rollouts are poor.

Borrowed: explicit geometry and identity rewards.

Not copied: estimating camera from generated video when known camera poses/intrinsics are already provided.

Our change: known-camera, simulator-grounded reward with PhyInOne and moving-camera synthetic extension data depth/ID/event metadata.

## VideoREPA

- VideoREPA identifies a gap between video generation models and self-supervised video encoders on physical understanding.
- It introduces Token Relation Distillation (TRD), aligning pairwise token relations.
- TRD uses spatial and temporal relation alignment rather than hard feature regression.
- The local README says hard REPA-style losses can hurt strong pretrained video diffusion finetuning, while TRD is softer.
- TRD improves physics plausibility but is evaluated largely in T2V physics prompt settings.
- It does not directly solve camera-following, rigid background geometry, or reobserve consistency.

Borrowed: TRD auxiliary loss for spatial/temporal physical relations.

Not copied: making TRD the sole objective.

## V-JEPA / V-JEPA2

- V-JEPA2 is self-supervised video representation learning through masked latent feature prediction.
- Its first stage is action-free observation-video pretraining.
- The local README states V-JEPA2 learns motion understanding and prediction from internet-scale video.
- V-JEPA2-AC adds a small amount of robot trajectory data later, supporting the idea that action is not required for the first representation stage.
- This supports our choice not to force real action labels into a camera-conditioned physical prediction problem.
- V-JEPA features are useful as frozen foreground/background identity and temporal relation teachers.

Borrowed: action-free observation learning argument and frozen video features.

Not copied: replacing LingBot generation with latent-only prediction.

## VideoGPA

- VideoGPA uses geometry-derived preference signals and DPO to improve 3D consistency.
- It frames geometric failures as lack of explicit incentives in standard objectives.
- It supports preference alignment with automatically derived geometric pairs.
- It is closer to our DPO framing than plain SFT.
- It differs because our setting is I2V/V2V with known camera conditions, physical foreground events, and reobserve splits.

Borrowed: DPO/preference framing for geometry.

Not copied: pure geometry-only preference without physical event and known-camera terms.
