# Current V2V-5 StageA / DPO Execution Status

Updated: 2026-06-27

- Branch: `research/quant-small-lora-dpo-probe-20260624`
- Baseline commit before wrapper work: `53d8882`
- Prefix5 pairs: READY, `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`, 50/50 valid.
- DPO energy backend: READY, real LingBot-Fast energy.
- DPO BF16 preflight: READY for single GPU, DDP2 and DDP8.
- Current focus: replace image-first Fast inference with honest V2V-5 generation.

## Fixed Blocker

The old inference path called `pipe.generate(prompt, image, action_path=...)`, which encoded only frame 0. The new wrapper constructs a prefix-video condition: frames 0-4 are encoded, frames 5-80 are zeroed, and evaluation uses future frames only.

## Not Running

No StageB, no GRPO, no large-scale DPO, no full-data long StageA, no data/checkpoint deletion, and no generated videos/checkpoints are pushed to Git.

## 2026-06-27 V2V-5 StageA Pilot Readiness

- Branch: `research/quant-small-lora-dpo-probe-20260624`
- Latest code checkpoint before pilot launch includes true V2V-5 inference wrapper and future-only StageA loss.
- Prefix5 pair manifest: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl` with 50/50 valid V2V-5 pairs.
- Original Fast V2V-5 screen16 rollout is running under `local_assets/v2v5_rollouts_20260627_082915/original_fast_screen16/`.
- StageA V2V-5 pilot dataset: `local_assets/stageA_v2v5_pilot_20260627/dataset/`.
- Pilot split: train 800 / val 100 / test 100, total 1000.
- Pilot template distribution: drop 300, collision 300, roll 200, containment 200.
- Pilot config: `configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml`.
- Pilot launcher: `scripts/launch_fast_stageA_v2v5_camera_r4.sh`.
- StageA pilot policy: LingBot-Fast, high-noise only, camera-conditioning LoRA only, rank 4, alpha 4, LR 1e-6, max 100 optimizer steps.
- Prefix condition: `PC_PREFIX_LEN=5`; frames 0-4 are visible condition frames.
- Prediction/loss target: future frames 5-80 only; latent loss starts after prefix-touched latent slots.
- Not launched in this checkpoint: StageB, GRPO, large-scale DPO, full-data long StageA.
