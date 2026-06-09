# GPU Approval Request: Stage A Balanced Rollout Smoke

Date: 2026-06-09

## Current Gate

The balanced Stage A high-noise warmup pilot passed:

- steps: `60 / 60`;
- train sampler: balanced by `template,camera_variant`;
- first 20 templates: `drop:5`, `collision:5`, `roll:5`, `containment:5`;
- full 60 templates: `drop:15`, `collision:15`, `roll:15`, `containment:15`;
- train loss finite: yes;
- val loss finite: yes;
- LoRA tensors changed: `4`;
- sampled frozen base tensors changed: `0`;
- no NaN / Inf / OOM.

Adapter checkpoint:

`local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/checkpoint/stageA_balanced_camera_lora_final/adapter_state.pt`

Size: `166,809` bytes.

The checkpoint contains adapter-only LoRA weights and no full model or optimizer state.

## Requested Next Action

Run a tiny rollout smoke comparing base LingBot-Fast against the Stage A balanced adapter.

Proposed rollout samples:

- 4 samples total;
- one `drop`;
- one `collision`;
- one `roll`;
- one `containment`.

Purpose:

- inspect whether Stage A improves camera movement adherence;
- check background stability and parallax;
- compare base vs Stage A adapter qualitatively;
- avoid DPO until the warmup behavior is visually useful.

## Proposed GPU

- Preferred: GPU7.
- Fallback: GPU6 or GPU6/7 if needed.
- Do not use GPU0 for LingBot rollout unless explicitly re-approved.

## Restrictions

- No DPO.
- No reward calibration.
- No VideoGPA `03_train`.
- No Stage1.
- No additional training.
- No optimizer state.
- Output videos only.

## Command Draft

This is a request only; do not run without explicit user approval.

```bash
CUDA_VISIBLE_DEVICES=7 TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 \
/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python -m cam_physgeo.training.lingbot_warmup_smoke \
  --mode rollout_smoke \
  --model_type fast \
  --config configs/cam_physgeo/videogpa_adapter.yaml \
  --adapter_checkpoint local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/checkpoint/stageA_balanced_camera_lora_final/adapter_state.pt \
  --test_manifest local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/test.jsonl \
  --out local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/rollout_smoke \
  --num_samples 4 \
  --one_per_template true \
  --num_frames 8 \
  --resolution 480x832 \
  --dtype bf16 \
  --device cuda \
  --use_action false \
  --compare_base true \
  --no_dpo true \
  --no_reward_calibration true \
  --local_files_only true
```

## Approval Needed

Explicit user approval is required before running this rollout smoke.
