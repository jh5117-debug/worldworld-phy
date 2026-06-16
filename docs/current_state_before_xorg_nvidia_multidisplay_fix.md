# Current State Before Xorg NVIDIA Multidisplay Fix

## Data

- Current v5 1000 manifest exists: yes.
- Valid samples: 1000 / 1000.
- target.mp4 probe: 1000 / 1000.
- Split: train 800 / val 100 / test 100.
- Scene hash unique: 1000 / 1000.

## Prompt Blocker and Fix

- Original official manifest unique prompt count: 1.
- Generic prompt ratio: 1.000.
- `combined_prompt_v2` experiment manifest exists: `local_assets/experiments/exp_multidisplay_tdw_scaleup_promptv2_stageA/prompt_v2/manifest_combined_prompt_v2.jsonl`.
- Main prompt-v2 manifest path: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_lingbot_manifest_combined_prompt_v2.jsonl`.

## Display State

- `:8`: NVIDIA OpenGL renderer, GPU0, preserved.
- `:9` to `:13`: `xdpyinfo` OK but renderer is Mesa llvmpipe, not valid for TDW GPU generation.
- `:14`, `:15`, `:20` to `:26`: unavailable before root setup.
- Root batch-mode SSH failed with publickey/password auth, so automatic Xorg setup was not performed.

## GitHub Push

GitHub SSH identity is still `itak04`; push to `jh5117-debug/worldworld-phy.git` is blocked until a key with write access is installed.

## This Round Minimal Goal

Prepare prompt-v2 1000 dataset entry and reports. Multi-display smoke is blocked until real NVIDIA displays exist.
