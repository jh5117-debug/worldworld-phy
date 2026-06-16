# Current State Before StageA 1000 PromptV2 Rollout Compare

- StageA 1000 prompt_v2 completed: yes, previous run finished 300/300 steps.
- Step200 checkpoint exists: True `local_assets/experiments/exp_stageA_1000_combined_prompt_v2_warmup/checkpoint/stageA_1000_promptv2_high_noise_camera_lora_step_000200/adapter_state.pt`
- Final checkpoint exists: True `local_assets/experiments/exp_stageA_1000_combined_prompt_v2_warmup/checkpoint/stageA_1000_promptv2_high_noise_camera_lora_final/adapter_state.pt`
- Step200 size: 166809 bytes
- Final size: 166809 bytes
- Checkpoint type: adapter-only LoRA state from StageA camera-control tiny scope.
- Compare step200 and final because validation loss was lowest at step200 while final is the last state.
- No reward scoring and no DPO are run in this visual evaluation.
