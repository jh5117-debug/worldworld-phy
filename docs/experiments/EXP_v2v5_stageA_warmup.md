# EXP: V2V-5 StageA Warmup

## Current Fact

This experiment is a quick prefix-aware V2V-5 support warmup, not full-data StageA and not StageB/DPO.

## Hypothesis

A very small camera-conditioning-only LoRA can help LingBot-Fast consume five clean prefix frames plus camera poses/intrinsics without damaging foreground identity as broad LoRA did.

## Dataset

- Dataset dir: `local_assets/stageA_v2v5_pilot_20260627/dataset/`
- Source converted root: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets/data/physion/generated_v5/converted_stage1_v1/`
- Split: train 800 / val 100 / test 100
- Template distribution: drop 300, collision 300, roll 200, containment 200
- Prefix length: 5
- Prediction start frame: 5
- Future target frames: 5-80
- `control_type=cam`, `use_action=false`

## Model And Tuning

- Base model: LingBot-World-Fast camera model
- Config: `configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml`
- Launcher: `scripts/launch_fast_stageA_v2v5_camera_r4.sh`
- Scope: `camera_conditioning` only
- LoRA rank/alpha/dropout: 4 / 4 / 0.05
- LR: 1e-6
- Precision: mixed-safe BF16, VAE FP32 path preserved by existing Fast StageA code
- Max optimizer steps: 100
- Save/eval every: 25 steps

## Gates

The experiment can only be considered usable if:

- training loss and fixed-val are finite;
- LoRA gradients are non-zero;
- prefix_len is logged as 5;
- future_latent_start is logged as 2 for 81-frame clips;
- generated V2V-5 videos are reviewed for every saved checkpoint;
- video quality is not worse than Original Fast baseline;
- no prefix ignored, scene replacement, global freeze, or broad foreground collapse.

## Out Of Scope

- No StageB.
- No GRPO.
- No large-scale DPO.
- No full-data long StageA.
- No broad-LoRA restart.

## Status

Prepared; launch only after Original Fast V2V-5 baseline smoke/screen16 confirms the wrapper is usable.
