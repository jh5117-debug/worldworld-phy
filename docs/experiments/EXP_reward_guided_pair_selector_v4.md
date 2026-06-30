# EXP Reward-Guided Pair Selector v4

Current Status: PLANNED_PRD_READY

Updated: 2026-06-30 11:17:53

## Problem

Protocol v3 pairs are either too subtle TypeA or too degraded TypeB. Pair selection needs to be grounded in Cam-PhysGeo reward, quality gates, and visual audit rather than a single score.

## Hypothesis

A selector that combines reward margin, subreward alignment, sharpness/quality gates, and Codex visual audit can produce clearer medium-hard pairs for DPO smoke without accepting blurry false negatives.

## Inputs

`manifests/dpo_preference_protocol_v3_pairs.jsonl`, v1/v2/v3 pair audits, TypeB rejection reports, existing energy audit, and PPT-selected diagnostics.

## Reward Definition

Use Cam-PhysGeo reward:

`R_total = w_bg*R_bg + w_cam*R_cam + w_fg*R_fg + w_phys*R_phys + w_reobs*R_reobs + w_quality*R_quality - w_freeze*P_freeze - w_blur*P_blur`.

Every subreward backend must be labeled `real`, `proxy`, `diagnostic`, or `blocked`. FVD/VBench remain `BLOCKED_BY_ENV` unless a real backend is available.

## Pair Selection Rule

Keep a pair only when reward_margin is positive and medium-sized, the main subreward drop matches the failure type, sharpness and quality pass, and Codex audit marks the preference visible and valid. Do not admit TypeB by default.

## Metrics

PSNR, SSIM, LPIPS if available, FVD if available, VBench if available, sharpness ratio, blur proxy, freeze proxy, Cam-PhysGeo subrewards, reward margin, subreward margins, and LingBot energy margin when already available. Blocked metrics must be reported as blocked, not fabricated.

## Codex Visual Audit Rule

Codex must inspect contact sheets or preview frames for selected pairs. A pair is accepted only if the winner is clean, the loser is readable, the failure is visible in one sentence, the loser is not collapsed or blurry, and the observed failure aligns with the reward/subreward drop.

## Success Gate

Selector writes weights/spec, subreward alignment, and accepted/rejected decisions with clear reasons. Accepted pairs are neither too subtle nor too degraded.

## Failure Gate

Pairs are all too subtle, all degraded, reward/failure alignment fails, videos are missing, or quality metrics are blocked without a fallback audit.

## Output Paths

`reports/dpo_pair_hardness_v4/reward_selector_spec.json`, `reward_selector_weights.json`, `subreward_alignment.csv`, and `subreward_alignment_summary.md`.

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
