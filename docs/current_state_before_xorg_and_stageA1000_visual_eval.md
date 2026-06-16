# Current State Before Xorg And StageA1000 Visual Eval

Date: 2026-06-17T02:50:44

## Dataset
- 1000 combined_prompt_v2 manifest exists: True `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_lingbot_manifest_combined_prompt_v2.jsonl`
- Train split exists: True `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_splits_combined_prompt_v2/train.jsonl`
- Val split exists: True `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_splits_combined_prompt_v2/val.jsonl`
- Test split exists: True `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_splits_combined_prompt_v2/test.jsonl`
- generic prompt blocker: fixed for this entry; prompt_variant is expected to be combined_v2.

## StageA 1000 prompt_v2
- Completed previously: 300/300 steps.
- Step200 checkpoint exists: True `local_assets/experiments/exp_stageA_1000_combined_prompt_v2_warmup/checkpoint/stageA_1000_promptv2_high_noise_camera_lora_step_000200/adapter_state.pt`
- Final checkpoint exists: True `local_assets/experiments/exp_stageA_1000_combined_prompt_v2_warmup/checkpoint/stageA_1000_promptv2_high_noise_camera_lora_final/adapter_state.pt`
- We compare step200 and final because validation loss was best at step200 while final is the last training state.

## Display
- `:8`: xdpyinfo=OK, renderer=NVIDIA
- `:9`: xdpyinfo=OK, renderer=llvmpipe
- `:10`: xdpyinfo=OK, renderer=llvmpipe
- `:11`: xdpyinfo=OK, renderer=llvmpipe
- `:12`: xdpyinfo=OK, renderer=llvmpipe
- `:13`: xdpyinfo=OK, renderer=llvmpipe
- `:14`: xdpyinfo=FAIL, renderer=unavailable
- `:15`: xdpyinfo=FAIL, renderer=unavailable
- `:20`: xdpyinfo=FAIL, renderer=unavailable
- `:21`: xdpyinfo=FAIL, renderer=unavailable
- `:22`: xdpyinfo=FAIL, renderer=unavailable
- `:23`: xdpyinfo=FAIL, renderer=unavailable
- `:24`: xdpyinfo=FAIL, renderer=unavailable
- `:25`: xdpyinfo=FAIL, renderer=unavailable
- `:26`: xdpyinfo=FAIL, renderer=unavailable

Only DISPLAY=:8 is NVIDIA. Displays :9-:13 are llvmpipe. Displays :20-:26 are unavailable before root setup.

## Safety
This run does not train, does not run reward scoring, does not build pairs, and does not run DPO. TDW smoke is allowed only if real NVIDIA displays become available.
