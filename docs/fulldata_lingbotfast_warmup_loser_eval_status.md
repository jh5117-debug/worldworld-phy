# Full-data LingBotFast Warmup Loser Eval Status

Status: `NEW_C_SMOKE_NOT_BETTER_THAN_OLD_C_ON_2COND`

## Summary

The full-data warmup adapter can generate V2V-5 videos after patching `run_v2v5_inference.py` to use the v8g safe `WanModelFast.from_pretrained` args. The default LingBot `WanI2VFast` path stalled before GPU generation.

Smoke output:

- New rollout root: `local_assets/dpo_pair_factory_v11/new_c_warmup_loser_smoke/M_C_all_available_final_safe_2cond`
- Contact sheets: 2/2
- Future videos: 2/2
- Metrics: `reports/dpo_pair_factory_v11/new_c_warmup_loser_smoke/new_vs_old_c_metrics.csv`
- Visual audit: `reports/dpo_pair_factory_v11/new_c_warmup_loser_smoke/new_vs_old_c_visual_audit.md`

## Codex Visual Decision

Do not launch 500-video generation yet.

- Sample `01002`: new C is clear and usable, but visually almost identical to old C. Both miss the physical event.
- Sample `01008`: new C is clear, but shows disappearance/duplicate-fragment artifacts and is not better than old C.

## Runtime Fix

Added `--safe_wan_from_pretrained` and `--safe_wan_from_pretrained_log` to `cam_physgeo/eval/run_v2v5_inference.py`. This forces:

- `local_files_only=True`
- `use_safetensors=True`
- `low_cpu_mem_usage=True`

## Cleanup

No files were deleted. A cleanup inventory was written:

- `reports/cleanup_fulldata_warmup_loser_eval/cleanup_inventory.md`
- `reports/cleanup_fulldata_warmup_loser_eval/cleanup_inventory_top.csv`


## Checkpoint Selection Update - 2026-07-06 10:26 CST

Status: `FULLDATA_WARMUP_CHECKPOINT_SELECT_NO_GO_FOR_500`

Intermediate checkpoints `step_000103`, `step_000206`, `step_000309`, and `step_000412` were smoke-tested on GPU4-7 with the safe V2V-5 loader.

- Each checkpoint produced 1 reviewed `01002` future/contact sheet.
- None was visually better than old C or the final full-data checkpoint.
- Common failure: physical contact event missing, green object mostly static, red object drifts to boundary, late duplicate/color fragments.
- The runner stalled before completing the second selected condition, so the four smoke processes were terminated to free GPU4-7.
- 500-video generation was not launched.

Audit path: `reports/dpo_pair_factory_v11/new_c_warmup_loser_checkpoint_select/checkpoint_selection_visual_audit.md`.
