# PRD Visual Audit Policy

Current Status: PASS_POLICY_DEFINED

Updated: 2026-07-01 15:55:00 CST

This policy is mandatory for every rollout, pair mining, warm-up, DPO smoke, metric evaluation, and ablation experiment that creates or consumes preference-pair losers.

## 1. PRD Before Experiment

Every experiment must create or update `docs/experiments/EXP_<experiment_name>_<version>.md` before any rollout, pair mining, warm-up, DPO smoke, metric evaluation, or ablation starts.

Each experiment PRD must include:

1. Current Status
2. Goal
3. Hypothesis
4. Input Data
5. Model / Checkpoint
6. Metrics
7. Loser Visual Audit Rule
8. Success Gate
9. Failure Gate
10. Output Paths
11. What is explicitly NOT run
12. Git Checkpoint

Before the experiment starts, the PRD must be committed and pushed. Pushing the PRD is not a stopping point; the experiment continues afterward.

## 2. Same PRD Updated After Experiment

After the experiment finishes, the same PRD must be updated at the top with:

Current Status: PASS / MIXED / FAILED / BLOCKED / DIAGNOSTIC_ONLY

The update must include actual commands run, actual input manifest, actual checkpoint, generated video count, loser candidate count, DPO-ready count, metric summary, Codex visual audit summary, failure cases, best examples, rejected examples, decision, and next action.

## 3. Codex Must Review Every Loser

Every loser used for DPO pair construction must be reviewed from real video/contact-sheet evidence. Reward, PSNR, SSIM, LPIPS, PhysGeo reward, energy margin, and sharpness ratio alone are not sufficient.

For each loser, the experiment must locate or generate:

1. loser_future.mp4 or generated_future.mp4
2. prefix.mp4
3. winner_future.mp4
4. contact sheet
5. sampled frames when needed
6. written_reason

## 4. Required Loser Visual Audit Fields

Every loser visual audit CSV/JSONL must include:

- pair_id
- condition_id
- winner_source
- loser_source
- loser_video_path
- winner_video_path
- pair_type
- failure_type
- loser_visual_quality: 0/1/2
- loser_background_stability: 0/1/2
- loser_camera_following: 0/1/2
- loser_foreground_identity: 0/1/2
- loser_object_deformation: 0/1/2
- loser_physical_event: 0/1/2
- loser_reobserve: 0/1/2
- loser_freeze: 0/1/2
- is_clear_enough: yes/no
- is_too_blurry: yes/no
- is_collapsed: yes/no
- is_black_screen: yes/no
- is_scene_replaced: yes/no
- is_global_freeze: yes/no
- is_too_similar_to_winner: yes/no
- is_too_bad: yes/no
- is_medium_hard: yes/no
- is_dpo_ready: yes/no
- main_failure_tag
- written_reason

## 5. Loser Acceptance Standard

A loser may enter a DPO-ready manifest only if:

1. video is clear;
2. it is not black screen;
3. it is not severely blurry;
4. it is not scene replacement;
5. it is not global freeze;
6. the foreground object has not fully disappeared;
7. it is not collapsed bad video;
8. it is not almost identical to WIN;
9. Codex can explain why it is worse than the winner;
10. reward_winner > reward_loser;
11. reward margin is reasonable;
12. visual_quality_loser >= 1;
13. sharpness_ok = true;
14. medium_hard = true.

Low-score but blurry/collapsed losers must be marked `TOO_BAD_NEGATIVE`, `COLLAPSED_NEGATIVE`, or `BLUR_FAILED` and can only be diagnostic.

## 6. Loser Rejection Standard

Reject any loser with any of:

- too_blurry = yes
- collapsed = yes
- black_screen = yes
- scene_replaced = yes
- global_freeze = yes
- winner_bad = yes
- too_similar_to_winner = yes
- Codex cannot explain failure
- failure tag and reward subscore mismatch
- low-quality-only video without clear physical/geometric/foreground error
- loser much worse than base and therefore too-bad negative

Rejected losers must be written to `reports/<experiment>/rejected_losers.csv` with pair_id, loser_path, reason, reward_loser, reward_margin, visual_quality, sharpness, failure_tag, and written_reason.

## 7. Required Experiment Audit Outputs

Each experiment must output:

- `reports/<experiment>/loser_visual_audit.csv`
- `reports/<experiment>/loser_visual_audit.jsonl`
- `reports/<experiment>/loser_visual_audit_summary.md`

If these files are missing or incomplete, the experiment status must be `BLOCKED_VISUAL_AUDIT_INCOMPLETE` and no pair manifest may be called DPO-ready.

## 8. Pair Manifest Requirement

Every DPO pair JSONL entry must include:

```json
"codex_visual_audit": {
  "reviewed": true,
  "is_clear_enough": true,
  "is_too_blurry": false,
  "is_collapsed": false,
  "is_too_similar_to_winner": false,
  "is_too_bad": false,
  "is_medium_hard": true,
  "is_dpo_ready": true,
  "main_failure_tag": "...",
  "written_reason": "..."
}
```

If `reviewed != true`, the pair must not enter a DPO-ready manifest.

## 9. PPT Requirement

Any PPT win/lose video must use reviewed pairs only. PPT losers must come from `reports/<experiment>/loser_visual_audit.csv` and must be either `is_dpo_ready = yes` or explicitly labeled diagnostic only.

PPT videos must label WIN, LOSE, pair_id, pair_type, winner_reward, loser_reward, reward_margin, main_failure_tag, and DPO_READY or DIAGNOSTIC_ONLY.

## 10. v8 Objective / Pair Factory Addendum

Winner-preserving objective diagnosis v8 may train only on pairs that already passed this loser audit policy. Pair factory recovery v8 may generate additional C rollout losers, but no loser can enter `manifests/dpo_gt_c_pairs_v8.jsonl`, `manifests/dpo_gt_c_pairs_v8_top50.jsonl`, or any DPO-ready subset until its contact sheet/video has been reviewed and the required audit fields are written.

Objective diagnosis v8 must stop if the winner-anchor-only objective cannot improve winner energy. Pair factory v8 must stop or mark partial if review coverage is incomplete; unreviewed losers are not allowed as placeholders.
