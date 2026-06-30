# EXP PPT Win-Lose Medium-Hard Showcase v4

Current Status: PLANNED_PRD_READY

Updated: 2026-06-30 11:17:53

## Problem

The previous showcase was useful but TypeA was subtle and TypeB was blur-failed. The teacher-facing pre needs clear WIN/LOSE, reward labels, and medium-hard explanation.

## Hypothesis

A 4-5 segment all-in-one video using TypeA+ and TypeM pairs will communicate the protocol better than raw TypeA or blurry TypeB diagnostics.

## Inputs

Protocol v4 accepted pairs, selected TypeA+/TypeM rows, optional TypeB diagnostic row, and generated preview/contact sheets.

## Reward Definition

Use Cam-PhysGeo reward:

`R_total = w_bg*R_bg + w_cam*R_cam + w_fg*R_fg + w_phys*R_phys + w_reobs*R_reobs + w_quality*R_quality - w_freeze*P_freeze - w_blur*P_blur`.

Every subreward backend must be labeled `real`, `proxy`, `diagnostic`, or `blocked`. FVD/VBench remain `BLOCKED_BY_ENV` unless a real backend is available.

## Pair Selection Rule

Select 4-5 representative pairs, prioritize TypeA+ and TypeM, include TypeB only as large-label diagnostic if needed. Each segment must show prefix, WIN clean GT, LOSE medium-hard negative, reward_winner, reward_loser, reward_margin, failure type, severity, affected region/heatmap when available.

## Metrics

PSNR, SSIM, LPIPS if available, FVD if available, VBench if available, sharpness ratio, blur proxy, freeze proxy, Cam-PhysGeo subrewards, reward margin, subreward margins, and LingBot energy margin when already available. Blocked metrics must be reported as blocked, not fabricated.

## Codex Visual Audit Rule

Codex must inspect contact sheets or preview frames for selected pairs. A pair is accepted only if the winner is clean, the loser is readable, the failure is visible in one sentence, the loser is not collapsed or blurry, and the observed failure aligns with the reward/subreward drop.

## Success Gate

MP4 is readable at PPT scale, WIN/LOSE labels are obvious, rewards are legible, and Codex visual review says the failure is visible and medium-hard.

## Failure Gate

Text is too small, loser is too blurry, difference is invisible, TypeB diagnostic is misrepresented as trainable, or videos are missing.

## Output Paths

`reports/ppt_winlose_showcase_latest/winlose_showcase_reward_guided_v4_for_ppt.mp4`, `reward_guided_v4_selected_pairs.csv`, and `reward_guided_v4_notes.md`.

## What Is Explicitly Not Run

- No DPO training.
- No StageB.
- No GRPO.
- No full-data long StageA.
- No checkpoint rewrite or deletion.
- No large media/checkpoint files committed to Git.

## Git Checkpoints

- Before execution: commit PRD files with `Prepare reward-guided DPO protocol v4 PRDs`.
- After execution: commit only source, tests, docs, manifests, and small CSV/JSON summaries.
