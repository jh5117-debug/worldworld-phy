# GitHub Push Report

Current Status: PASS_REWARD_VISUAL_ALIGNMENT_V5_PUSHED

Updated: 2026-06-30 13:39:05

## Branch

`research/quant-small-lora-dpo-probe-20260624`

## This Round Commits

- `86e24bd` - Prepare reward visual alignment and Fast support diagnosis PRDs
- `6c9d73c` - Audit reward-selected pair visibility and Fast support blockers

## Key Result

Reward visual alignment v5 found Protocol v4 NOT_READY for DPO:

- 42 v4 pairs checked
- 3 strict human-visible / DPO-ready pairs
- 39 too subtle
- TypeM strict medium-hard count: 0

## Not Pushed

Large generated media remains local only:

- `reports/ppt_winlose_showcase_latest/winlose_showcase_visible_mediumhard_v5_for_ppt.mp4`
- preview frames/contact sheets

No MP4, JPG, PNG, HDF5, NPY/NPZ, PT/PTH, safetensors, checkpoint, weight, or large log files were pushed.

## Training Status

No DPO training, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, or checkpoint modification was run.
