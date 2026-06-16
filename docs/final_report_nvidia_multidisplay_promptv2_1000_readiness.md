# Final Report: NVIDIA Multidisplay + Prompt-v2 1000 Readiness

## 1000 data audit

- Count: 1000.
- Valid: 1000 / 1000.
- target.mp4 probe: 1000 / 1000.
- Scene uniqueness: 1000 / 1000 scene hashes unique.
- Original prompt blocker: unique prompt count 1; generic prompt ratio 1.000.

## Prompt

- Main combined_prompt_v2 manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_lingbot_manifest_combined_prompt_v2.jsonl`.
- Prompt-v2 split dir: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_splits_combined_prompt_v2`.
- Split: train 800 / val 100 / test 100.
- Prompt variant count: `Counter({'combined_v2': 1000})`.

## Display

- `:8`: NVIDIA and preserved.
- `:9` to `:13`: llvmpipe, rejected.
- `:14/:15`: unavailable.
- `:20` to `:26`: not configured; root batch-mode access failed.
- No root password was recorded, echoed, scripted, or committed.

## Multi-display smoke

- Status: not run.
- Generated count: 0.
- Reason: fewer than two valid NVIDIA displays are available.
- Blocker: root-side Xorg setup is still needed for `:20` to `:26`.

## Scale-up decision

- Do not generate additional data yet.
- Not ready for 5000.
- After NVIDIA display smoke passes, recommend +1000 first, then audit before larger expansion.

## Stage A

- Prompt-v2 dataset is ready as an entrypoint.
- Approval request: `docs/gpu_usage_approval_request_stageA_1000_combined_prompt_v2.md`.
- Stage A was not run in this task.

## Hard negative

- Config: `configs/cam_physgeo/quality_bounded_hard_negative.yaml`.
- Policy: quality-bounded hard negatives only; low-quality collapsed videos are excluded from main DPO losers.
- DPO not run.

## Safety

- No DPO training.
- No VideoGPA 03_train.
- No Stage1.
- No full model finetune.
- No local_assets committed or pushed.
- No credentials logged.
