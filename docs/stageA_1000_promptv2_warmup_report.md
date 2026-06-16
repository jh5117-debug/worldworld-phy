# Stage A 1000 combined_prompt_v2 Warmup Report

## Run

- Dataset: TDW v5 1000 combined_prompt_v2
- Split: train 800 / val 100 / test 100
- Model: LingBot-Fast
- Mode: Stage A high-noise / global-camera warmup
- Effective run: fallback max_steps=300 after the initial 1000-step attempt was estimated to exceed the <=24h safety bound.
- GPU: GPU7 only
- Timestep band: diagnostic_high_noise_quantile, timestep 799, sigma 0.7990000248
- Trainable scope: camera_control_lora_tiny
- Trainable LoRA tensors: 4

## Metrics

| metric | value |
| --- | ---: |
| steps completed | 300 |
| train loss first | 0.045310 |
| train loss last | 0.033751 |
| train loss min | 0.025159 |
| train loss max | 0.072702 |
| grad norm first | 0.003626 |
| grad norm last | 0.038558 |
| grad norm min | 0.002390 |
| grad norm max | 0.068376 |

## Validation losses

| step | loss | template | camera_variant |
| ---: | ---: | --- | --- |
| 100 | 0.035215 | drop | orbit_left_72 |
| 200 | 0.031541 | collision | strafe_left_180 |
| 300 | 0.051866 | roll | orbit_right_60 |

## Coverage

- Train templates: drop: 75, collision: 75, roll: 75, containment: 75
- First 20 templates: drop: 5, collision: 5, roll: 5, containment: 5
- Train cameras: orbit_left_72: 75, orbit_right_60: 75, orbit_left_44: 75, orbit_right_64: 38, strafe_left_180: 37
- Unique train sample IDs: 300 / 300

## Checkpoints

| file | bytes |
| --- | ---: |
| local_assets/experiments/exp_stageA_1000_combined_prompt_v2_warmup/checkpoint/stageA_1000_promptv2_high_noise_camera_lora_step_000200/adapter_state.pt | 166809 |
| local_assets/experiments/exp_stageA_1000_combined_prompt_v2_warmup/checkpoint/stageA_1000_promptv2_high_noise_camera_lora_final/adapter_state.pt | 166809 |

Final adapter checkpoint: `local_assets/experiments/exp_stageA_1000_combined_prompt_v2_warmup/checkpoint/stageA_1000_promptv2_high_noise_camera_lora_final/adapter_state.pt`

The summary reports adapter-only checkpoint contents: 4 LoRA tensors, 40,960 parameters, contains_only_lora=true, contains_optimizer_state=false, contains_full_model=false.

## Safety

- NaN / Inf: none observed in train/val metrics
- OOM: none observed
- Full model checkpoint: none
- Optimizer state: none
- Rollout: not run
- Reward scoring: not run
- DPO: not run
