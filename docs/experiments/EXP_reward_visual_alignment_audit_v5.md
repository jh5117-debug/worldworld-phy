
# EXP Reward Visual Alignment Audit v5

Current Status: COMPLETED_PROTOCOL_V4_NOT_READY_TOO_SUBTLE

Updated: 2026-06-30 13:11:54

## Problem

Protocol v4 reward-selected TypeA+/TypeM pairs may still look almost identical to WIN. If Codex/human cannot see and explain the failure, the pair must not be DPO-ready, even if reward_margin is positive.

## Hypothesis

Adding local visual-difference measurements and explicit Codex visibility gates will reveal that some v4 reward-selected pairs are too subtle. A corrected gate should keep only pairs where reward/subreward margin aligns with a human-visible local failure.

## Inputs

- `manifests/dpo_preference_protocol_v4_pairs.jsonl`
- `reports/dpo_pair_hardness_v4/protocol_v4_pair_audit.csv`
- `reports/dpo_pair_hardness_v4/typeA_strength_sweep.csv`
- `reports/dpo_pair_hardness_v4/typeM_pair_audit.csv`
- v4 generated WIN/LOSE videos and existing contact sheets

## Metrics

reward_winner, reward_loser, reward_margin, subreward margins, PSNR, SSIM/proxy, LPIPS if available, sharpness_ratio, affected_region_diff, local_absdiff_mean, local_absdiff_p95, diff_bbox_area, visual_difference_score, Codex visibility flags.

## Visual Audit Rule

A pair is DPO-ready only if Codex can see the difference and explain the failure in one sentence without relying only on the heatmap. If WIN/LOSE look the same at presentation scale, mark `VISUAL_TOO_SUBTLE` and remove from v5 ready set.

## Success Gate

- All 42 v4 pairs are audited.
- Human-visible count, too-subtle count, and true medium-hard count are reported.
- v5 ready JSONL contains only visible, explainable, non-blurry, non-collapsed pairs.
- If fewer than 4 are visible, PPT explicitly says current reward-selected pairs are too subtle.

## Failure Gate

Audit is failed if visual visibility is inferred only from proxy reward, if too-subtle pairs remain DPO-ready, or if missing videos are silently ignored.

## Output Paths

- `reports/reward_visual_alignment_v5/pair_visual_alignment.csv`
- `reports/reward_visual_alignment_v5/pair_visual_alignment_summary.md`
- `reports/reward_visual_alignment_v5/dpo_ready_pairs_visual_v5.jsonl`
- `reports/reward_visual_alignment_v5/rejected_too_subtle_pairs.jsonl`
- `reports/ppt_winlose_showcase_latest/winlose_showcase_visible_mediumhard_v5_for_ppt.mp4`
- `reports/ppt_winlose_showcase_latest/visible_mediumhard_v5_selected_pairs.csv`
- `reports/ppt_winlose_showcase_latest/visible_mediumhard_v5_notes.md`

## What Is Explicitly Not Run

- No DPO training.
- No StageB.
- No GRPO.
- No full-data StageA.
- No broad-LoRA.
- No checkpoint deletion or modification.
- No MP4/JPG/PNG/checkpoint/large logs committed to Git.

## Git Checkpoint Before / After

Before execution: commit PRD/status files with `Prepare reward visual alignment and Fast support diagnosis PRDs`.
After execution: commit only code, scripts, docs, and small CSV/JSON summaries.

## Post-Run Update

Updated: 2026-06-30 13:33:20

- Reward visual alignment checked 42 pairs.
- Strict DPO-ready count: 3.
- Protocol v4 is NOT_READY for DPO until visual pair generation is fixed.
- No DPO, StageB, GRPO, full-data StageA, broad-LoRA, or checkpoint modification was run.
