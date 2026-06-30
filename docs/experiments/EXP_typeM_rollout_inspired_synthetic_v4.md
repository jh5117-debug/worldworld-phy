# EXP TypeM Rollout-Inspired Synthetic Medium-Hard v4

Current Status: PLANNED_PRD_READY

Updated: 2026-06-30 11:17:53

## Problem

True rollout TypeB negatives are too blurry, while TypeA can be too subtle. A middle category is needed for clear but non-trivial failures.

## Hypothesis

Synthetic negatives inspired by real rollout failure tags can preserve GT clarity while introducing visible physical/geometric errors, producing a better medium-hard bridge category.

## Inputs

TypeB failure tags/audits from v1/v2, clean GT futures from v3, and Cam-PhysGeo reward selector outputs.

## Reward Definition

Use Cam-PhysGeo reward:

`R_total = w_bg*R_bg + w_cam*R_cam + w_fg*R_fg + w_phys*R_phys + w_reobs*R_reobs + w_quality*R_quality - w_freeze*P_freeze - w_blur*P_blur`.

Every subreward backend must be labeled `real`, `proxy`, `diagnostic`, or `blocked`. FVD/VBench remain `BLOCKED_BY_ENV` unless a real backend is available.

## Pair Selection Rule

Construct TypeM losers from clean GT future with rollout-inspired local failures: extra fragments, background drift, wrong camera motion, object identity instability, and weak physical event. Accept only if clear, sharp, reward-aligned, and medium-hard.

## Metrics

PSNR, SSIM, LPIPS if available, FVD if available, VBench if available, sharpness ratio, blur proxy, freeze proxy, Cam-PhysGeo subrewards, reward margin, subreward margins, and LingBot energy margin when already available. Blocked metrics must be reported as blocked, not fabricated.

## Codex Visual Audit Rule

Codex must inspect contact sheets or preview frames for selected pairs. A pair is accepted only if the winner is clean, the loser is readable, the failure is visible in one sentence, the loser is not collapsed or blurry, and the observed failure aligns with the reward/subreward drop.

## Success Gate

10-30 TypeM pairs are accepted with clear failure modes, sharpness gate pass, positive reward margin, and aligned subreward drop.

## Failure Gate

Generated negatives are blurry, too artificial, too easy, too close to winner, globally degraded, or reward/failure mismatched.

## Output Paths

`manifests/dpo_preference_protocol_v4_typeM_pairs.jsonl`, `reports/dpo_pair_hardness_v4/typeM_pair_audit.csv`, `typeM_pair_summary.md`, and optional contact sheets.

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
