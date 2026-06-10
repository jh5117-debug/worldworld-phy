# TDW v5 4-Condition Base vs Stage A Adapter Rollout Report

Date: 2026-06-10

## Result

Status: passed after a small adapter-load fix.

Final rollout result:

- Conditions: 4.
- Base videos: 4/4.
- Stage A adapter videos: 4/4.
- Failed videos after fix: 0.
- Probe: 12/12 videos passed, including GT, base, and adapter columns.
- Probe backend: OpenCV.
- Video format: 81 frames, 16 fps, 832x480.

## Adapter Load Fix

The first base pass succeeded for all 4 conditions. The first adapter attempt correctly stopped on adapter-load failure instead of faking an adapter result.

Root cause:

The generated LingBot runtime script only inserted the LingBot code path into `sys.path`, so it could not import `cam_physgeo.dpo.lora_utils` for runtime LoRA injection.

Fix:

`cam_physgeo/eval/run_inference.py` now passes `WORLD_MODEL_PHYS_ROOT` to the runtime subprocess and inserts the project root into `sys.path` before adapter import. The adapter-only rerun then loaded the checkpoint and generated all 4 adapter videos.

The failed pre-fix summary is preserved at:

`local_assets/experiments/exp_tdw_v5_scaleup_warmup_reward_pairs/rollout/4condition_base_vs_stageA_adapter/rollout_summary_adapter_import_failure_before_fix.json`

## Conditions

| Template | Camera | Base Runtime (s) | Adapter Runtime (s) |
|---|---|---:|---:|
| drop | `orbit_left_72` | 787.0 | 706.1 |
| collision | `strafe_left_180` | 668.0 | 696.0 |
| roll | `orbit_right_60` | 692.1 | 685.4 |
| containment | `orbit_left_44` | 684.3 | 707.0 |

## Output Paths

Combined summary:

`local_assets/experiments/exp_tdw_v5_scaleup_warmup_reward_pairs/rollout/4condition_base_vs_stageA_adapter/rollout_summary_combined_base_adapter.json`

Human review gallery:

`local_assets/reports/human_review/tdw_v5_stageA_4condition_base_vs_adapter/video_gallery.html`

Review videos:

`local_assets/reports/human_review/tdw_v5_stageA_4condition_base_vs_adapter/videos/`

Raw logs:

- Initial base + failed adapter attempt: `local_assets/experiments/exp_tdw_v5_scaleup_warmup_reward_pairs/logs/4condition_rollout_stdout_stderr.log`
- Adapter-only rerun: `local_assets/experiments/exp_tdw_v5_scaleup_warmup_reward_pairs/logs/4condition_adapter_rerun_stdout_stderr.log`

The raw logs include verbose model-loader warnings and should be inspected by path rather than copied into summaries.

## Safety

No training, DPO, reward scoring, reward calibration, pair construction, VideoGPA `03_train`, Stage1, new TDW generation, or checkpoint save was run.

