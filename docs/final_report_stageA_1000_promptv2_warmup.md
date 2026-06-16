# Final Report: Stage A 1000 combined_prompt_v2 Warmup

## Dataset

- Manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_lingbot_manifest_combined_prompt_v2.jsonl`
- Split: train 800 / val 100 / test 100
- Prompt route: combined_prompt_v2
- Generic prompt count: 0
- Total samples: 1000

## Sampler

Balanced sampler passed and the real run confirmed exact coverage:

- first 20: drop 5 / collision 5 / roll 5 / containment 5
- full 300: drop 75 / collision 75 / roll 75 / containment 75
- unique train sample IDs: 300 / 300

## Warmup

- Status: passed_stageA_warmup_pilot
- Requested 1000-step command was started, but early measured speed exceeded the <=24h safety bound; it was stopped before any checkpoint and restarted with fallback max_steps=300.
- Steps completed: 300
- GPU: GPU7 only
- Timestep: high-noise diagnostic, timestep 799, sigma 0.7990
- Train loss: first 0.045310, last 0.033751, min 0.025159, max 0.072702
- Val losses: step 100: 0.035215, step 200: 0.031541, step 300: 0.051866
- Grad norm: first 0.003626, last 0.038558, max 0.068376
- NaN / Inf: none
- OOM: none

## Checkpoint

- Step checkpoint: `local_assets/experiments/exp_stageA_1000_combined_prompt_v2_warmup/checkpoint/stageA_1000_promptv2_high_noise_camera_lora_step_000200/adapter_state.pt` (166809 bytes)
- Final checkpoint: `local_assets/experiments/exp_stageA_1000_combined_prompt_v2_warmup/checkpoint/stageA_1000_promptv2_high_noise_camera_lora_final/adapter_state.pt` (166809 bytes)
- Adapter-only: yes
- Full model checkpoint: no
- Optimizer state: no

## Safety

No TDW generation, no rollout, no reward scoring/calibration, no DPO training, no VideoGPA 03_train, no Stage1, no full model finetune, and no local_assets push.

## Next

Request user approval for a 12-condition Base vs StageA_1000_prompt_v2 rollout smoke using the final adapter checkpoint. Reward scoring and quality-bounded hard-negative mining should remain after rollout review. DPO remains later.
