# Current State Before Stage A 1000 combined_prompt_v2 Warmup

Date: 2026-06-17 CST

## Data readiness

- Manifest exists: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_lingbot_manifest_combined_prompt_v2.jsonl`
- Split exists: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_splits_combined_prompt_v2`
- Counts: all 1000, train 800, val 100, test 100
- Prompt variant: combined_v2: 1000
- Generic prompt count: 0
- use_action=false count: 1000

## Why warmup can run now

The 1000-sample TDW v5 dataset already has LingBot cam-only converted samples and combined_prompt_v2 entries. The prompt blocker from the generic prompt route is removed for this manifest. LingBot-Fast warmup is a PyTorch/CUDA job and does not depend on TDW DISPLAY/Xorg.

## Why no TDW / DPO / rollout in this task

No TDW generation, no DPO training, no VideoGPA 03_train, no Stage1, no rollout, no reward scoring/calibration, no full model checkpoint, and no optimizer state were run/saved in this task.

## GPU scope

Warmup used GPU7 under CUDA_VISIBLE_DEVICES=7. GPU0 was not used.

## GitHub push status

The H20 GitHub SSH identity is still `itak04`, not the repo writer identity for `jh5117-debug/worldworld-phy.git`; push must be treated as blocked until the SSH key is fixed.
