# Current State Before Visible-Motion v2 Actual

Worktree used for code/docs: `/tmp/worldworld_phy_push_tdw_prd`

Remote TDW run worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work`

Remote run commit: `c8ac7b2b653b177a942d815148ef663615346d20`

The previous `warmup_visible_motion` v1 smoke generated 10 samples, but only 5/10 passed `suitable_for_visible_motion`. Rejections were caused by template-specific mismatches: roll received dolly variants that were too static, containment received orbit 24 variants that were too extreme, and one collision orbit 28 exceeded the camera-path threshold.

`warmup_visible_motion_v2` already exists and is template-aware. The current goal is to run only the v2 10-sample actual smoke on approved GPU0-bound `DISPLAY=:8`, validate it, convert accepted samples, update deliverables, and stop. No 50 / 200 / 1k generation and no training are permitted.

