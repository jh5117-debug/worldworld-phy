# Experiment Registry: TDW visible-motion v3

| Field | Value |
|---|---|
| Experiment name | `tdw_visible_motion_v3_start0_scene_diverse_50` |
| Date | 2026-06-06 |
| Profile | `warmup_visible_motion_v3_start0_scene_diverse` |
| Output root | `local_assets/data/physion/generated_v3/` |
| Experiment folder | `local_assets/experiments/tdw_visible_motion_v3_start0_scene_diverse_50/` |
| Manifest | `local_assets/data/physion/generated_v3/manifests/plan_warmup_visible_motion_v3_start0_scene_diverse_50.jsonl` |
| Validation report | `local_assets/data/physion/generated_v3/reports/validation_warmup_visible_motion_v3_start0_scene_diverse_50.md` |
| LingBot conversion root | `local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v3_start0_scene_diverse_50_human_accepted_all/` |
| Human review pack | `local_assets/reports/human_review/tdw_visible_motion_v3_start0_scene_diverse_50/` |
| Status | generated 50/50; validation OK 50/50; human review accepted 50/50; converted 50/50 |
| Next action | request explicit approval before any 200-sample v3 pilot |

No generated assets in `local_assets` are committed to Git.
## exp_tdw_v5_200_lingbot_warmup_gate

| Field | Value |
|---|---|
| Experiment name | `exp_tdw_v5_200_lingbot_warmup_gate` |
| Date | 2026-06-09 |
| Dataset | `tdw_v5_aggressive_2x_200` |
| Experiment folder | `local_assets/experiments/exp_tdw_v5_200_lingbot_warmup_gate/` |
| LingBot root | `local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v5_aggressive_2x_200_human_approved_all/` |
| Manifest | `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_lingbot_manifest.jsonl` |
| Split root | `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/` |
| Audit report | `local_assets/experiments/exp_tdw_v5_200_lingbot_warmup_gate/audit/audit_report.json` |
| Status | Manifest/audit/split/dataloader passed; real model-load forward-loss pending |
| DPO diag | `not_applicable_pre_dpo` |
| Next action | Approve real LingBot-Fast model-load forward-loss smoke before warmup pilot |
