# StageA 1000 PromptV2 Rollout Output Verification Report

Date: 2026-06-17T06:21:34

## Counts
- Conditions: 12
- GT videos linked: 12/12
- Base rollout: 12/12 ok, 0 failed
- StageA step200 rollout: 12/12 ok, 0 failed
- StageA final rollout: 12/12 ok, 0 failed
- Four-column comparison videos: 12/12
- Comparison video probe: 12/12 via imageio first-frame read

## Paths
- Combined rollout root: `local_assets/experiments/exp_stageA_1000_combined_prompt_v2_rollout_compare/rollout/gt_base_step200_final`
- Comparison videos: `local_assets/experiments/exp_stageA_1000_combined_prompt_v2_rollout_compare/rollout/gt_base_step200_final/comparison_videos_gt_base_step200_final`
- Human review gallery: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work/local_assets/reports/human_review/stageA_1000_promptv2_12condition_base_step200_final/video_gallery.html`

## Notes
The initial base/session was stopped after Base reached 12/12 to avoid duplicate adapter rollout. Step200 and final adapter rollouts ran in separate tmux sessions on GPU6 and GPU5. No reward scoring, pair construction, DPO, or training was run.
