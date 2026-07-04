Current Status: PRD_READY

# DPO Objective Repair v12b Status

- Canonical repaired ready500 is the only allowed data entry.
- Previous v12 selected `L0_camera_r4` as the only scope passing winner-anchor sanity.
- Previous v12 guarded SDPO-anchor on S1 stopped at step10 with `DPO_V12_FAILED_WINNER_WORSE_NO_SIGNAL`.
- v12b objective is winner-first repair, not DPO scale.
- This run is constrained to physical GPU4 only with `CUDA_VISIBLE_DEVICES=4`.
- GPU0/1/2/3/5/6/7 are not allowed for v12b execution.
- No large DPO, no StageA/StageB/GRPO, no broad-LoRA, no checkpoint deletion, and no media/weights push.
