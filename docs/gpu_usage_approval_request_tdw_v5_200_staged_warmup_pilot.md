# GPU Approval Request: TDW v5 200 Staged LingBot-Fast Warmup Pilot

Date: 2026-06-09

## Request

Approve Stage A only: a small LingBot-Fast camera-conditioned warmup pilot on the human-approved TDW v5 200 dataset.

Do not approve DPO, VideoGPA `03_train`, Stage1 large training, rollout, reward calibration, full finetuning, or large checkpoint save.

## Why Staged

The true forward-loss smoke passed across diagnostic timestep bands. LingBot Base exposes high-noise / low-noise checkpoint branches, while LingBot-Fast does not expose explicit expert routing in this runtime. Therefore the safest first warmup is a high-noise/global-camera diagnostic band, with timestep/sigma logging kept on every step.

## Dataset

- Dataset: TDW v5 aggressive 2x 200 human-approved camera-visible set.
- Split: train 160, val 20, test 20.
- `use_action=false`.
- Dummy `action.npy` only.

## Proposed Stage A

Purpose: align camera-conditioned global layout, background parallax, and visible camera motion.

Suggested settings:

- GPU: GPU7 first, then GPU6/7 if memory needs it.
- Steps: max 100.
- Batch size: 1.
- Frames: 8 or 16.
- Timestep mode: diagnostic high-noise band or logged scheduler high-noise quantile.
- Trainable params: camera adapter / LoRA only.
- Checkpoint: disabled by default; one small checkpoint only if explicitly approved.
- Validation: val subset forward loss.
- Outputs: loss curve and camera-condition metrics only; no rollout unless separately approved.

Command draft (do not run without approval):

```bash
CUDA_VISIBLE_DEVICES=7 TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 \
/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python -m cam_physgeo.training.lingbot_warmup_smoke \
  --mode staged_warmup_pilot \
  --model_type fast \
  --config configs/cam_physgeo/videogpa_adapter.yaml \
  --train_manifest local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/train.jsonl \
  --val_manifest local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/val.jsonl \
  --out local_assets/experiments/exp_tdw_v5_200_stageA_warmup_pilot \
  --batch_size 1 \
  --max_steps 100 \
  --num_frames 8 \
  --resolution 480x832 \
  --dtype bf16 \
  --device cuda \
  --use_action false \
  --timestep_mode high_noise \
  --trainable_scope camera_adapter_lora \
  --no_dpo true \
  --no_rollout true \
  --no_reward_calibration true \
  --no_checkpoint true
```

## Proposed Stage B

Only if Stage A is stable.

- Timestep mode: mixed or low-noise diagnostic band.
- Steps: max 100.
- Purpose: preserve visual quality and object detail while retaining camera response.

## Stop Conditions

- OOM.
- NaN/Inf loss.
- Loss instability.
- Evidence of camera-condition collapse.
- Any path requiring checkpoint/LoRA save without approval.

Explicit user approval is required before Stage A starts.
