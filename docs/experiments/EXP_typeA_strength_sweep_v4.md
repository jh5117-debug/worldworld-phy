# EXP TypeA Strength Sweep v4

Current Status: PASS_TYPEA_PLUS_34_ACCEPTED

Updated: 2026-06-30 11:17:53

## Problem

TypeA local corruptions are clean but often visually too subtle for presentation and may provide weak DPO signal.

## Hypothesis

Sweeping local corruption severity while preserving clarity can produce TypeA+ pairs that are easier to see and still safe for LocalDPO-style training.

## Inputs

`manifests/dpo_preference_protocol_v3_pairs.jsonl` and `reports/dpo_preference_protocol_v2/typeA_localdpo_pair_audit.csv`.

## Reward Definition

Use Cam-PhysGeo reward:

`R_total = w_bg*R_bg + w_cam*R_cam + w_fg*R_fg + w_phys*R_phys + w_reobs*R_reobs + w_quality*R_quality - w_freeze*P_freeze - w_blur*P_blur`.

Every subreward backend must be labeled `real`, `proxy`, `diagnostic`, or `blocked`. FVD/VBench remain `BLOCKED_BY_ENV` unless a real backend is available.

## Pair Selection Rule

For each TypeA pair, generate s1/s2/s3/s4 local corruption candidates over future frames 5-80 only, keep same prefix/prompt/poses/intrinsics, and choose the best medium-hard severity if one passes.

## Metrics

PSNR, SSIM, LPIPS if available, FVD if available, VBench if available, sharpness ratio, blur proxy, freeze proxy, Cam-PhysGeo subrewards, reward margin, subreward margins, and LingBot energy margin when already available. Blocked metrics must be reported as blocked, not fabricated.

## Codex Visual Audit Rule

Codex must inspect contact sheets or preview frames for selected pairs. A pair is accepted only if the winner is clean, the loser is readable, the failure is visible in one sentence, the loser is not collapsed or blurry, and the observed failure aligns with the reward/subreward drop.

## Success Gate

At least 20 TypeA+ pairs pass medium-hard, sharpness, subreward alignment, and visual gates. Prefix frames are unchanged and affected masks/time spans are preserved.

## Failure Gate

All severities are too subtle, too degraded, blur-inducing, globally destructive, or missing required metadata.

## Output Paths

`local_assets/dpo_pair_hardness_v4/typeA_strength_sweep/`, `reports/dpo_pair_hardness_v4/typeA_strength_sweep.csv`, `typeA_strength_sweep_summary.md`, `typeA_plus_pairs.jsonl`, and `typeA_plus_selection.csv`.

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

## Post-Run Update

Updated: 2026-06-30 12:09:54

- Protocol v4 generated 42 training-ready pairs.
- TypeA_plus: 34.
- TypeM: 8.
- TypeB_usable: 0.
- No DPO training or checkpoint modification was run.
