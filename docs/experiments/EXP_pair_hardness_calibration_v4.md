# EXP Pair Hardness Calibration v4

Current Status: PLANNED_PRD_READY

Updated: 2026-06-30 11:17:53

## Problem

Existing pairs do not land in the medium-hard band: TypeA is often too close to the winner and TypeB is often blurry or collapsed.

## Hypothesis

A calibrated hardness gate using reward margin, visible difference, sharpness ratio, quality floor, and visual audit can separate too-subtle, medium-hard, and too-degraded negatives.

## Inputs

Protocol v3 TypeA pairs, v1/v2 TypeB diagnostics, generated TypeA+ candidates, and TypeM synthetic candidates.

## Reward Definition

Use Cam-PhysGeo reward:

`R_total = w_bg*R_bg + w_cam*R_cam + w_fg*R_fg + w_phys*R_phys + w_reobs*R_reobs + w_quality*R_quality - w_freeze*P_freeze - w_blur*P_blur`.

Every subreward backend must be labeled `real`, `proxy`, `diagnostic`, or `blocked`. FVD/VBench remain `BLOCKED_BY_ENV` unless a real backend is available.

## Pair Selection Rule

Classify as TOO_SUBTLE, MEDIUM_HARD, or TOO_DEGRADED. Initial thresholds: visual_quality >= 1, loser_sharpness_ratio >= 0.65, R_quality >= p40, reward_margin in [0.12, 0.40], LPIPS future in [0.04, 0.25] when available, main failure not blur except diagnostic.

## Metrics

PSNR, SSIM, LPIPS if available, FVD if available, VBench if available, sharpness ratio, blur proxy, freeze proxy, Cam-PhysGeo subrewards, reward margin, subreward margins, and LingBot energy margin when already available. Blocked metrics must be reported as blocked, not fabricated.

## Codex Visual Audit Rule

Codex must inspect contact sheets or preview frames for selected pairs. A pair is accepted only if the winner is clean, the loser is readable, the failure is visible in one sentence, the loser is not collapsed or blurry, and the observed failure aligns with the reward/subreward drop.

## Success Gate

Hardness gate config is saved; accepted medium-hard pairs have clear failure text, aligned subreward drop, and pass sharpness/quality gates.

## Failure Gate

Accepted count is inflated by blurry, collapsed, or indistinguishable pairs, or thresholds are not recorded.

## Output Paths

`docs/dpo_pair_hardness_calibration_v4.md`, `reports/dpo_pair_hardness_v4/hardness_gate_config.json`, and pair hardness CSV summaries.

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
