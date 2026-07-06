# EXP DPO Objective Search v13b

Updated: 2026-07-06 12:34 CST

## Current Status

- Canonical repaired ready500 exists: `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`.
- Repaired train/val/test splits exist and the old unrepaired ready500 must not be used.
- v12 32-pair DPO failed with winner-worse / no-signal behavior.
- v12b S_pass4 winner-only passed.
- v12c/v12d winner-detached mean signal was positive, but final winner improvement flipped negative.
- Gap diagnosis indicates win-gap / lose-gap and normalized gap scale must be monitored explicitly.
- This run only uses physical GPU4 and GPU5.
- This run searches 6-10 small DPO variants.
- No scale is allowed until a variant is healthy within <=200 steps and video/metrics also pass.

## Problem

- DPO may obtain margin by degrading the loser rather than improving the winner.
- Winner may still get worse even when mean signal looks positive.
- Loss can stick near 0.693 with no utility movement.
- Raw energy gap scale may be unstable, making normalized/clipped gaps necessary.
- Camera-only LoRA may be too narrow, but broad-LoRA is not allowed.
- Local masks may not be sufficiently used for controlled synthetic pairs.
- Previous final-step behavior can flip negative, so early stopping and best-step tracking are required.

## Hypothesis

A stable <=200-step DPO recipe may be found by combining lower preference strength, lower learning rate, best-step early stop, winner-only or no-lose-gap variants, normalized/clipped loser gap, linear utility, delayed tiny loser gradients, local time/spatial masks, and a limited camera-temporal LoRA variant.

## Data Inputs

- Canonical repaired manifest: `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`
- Train split: `manifests/dpo_pair_factory_v11_train400_repaired.jsonl`
- Val split: `manifests/dpo_pair_factory_v11_val50_repaired.jsonl`
- Test split: `manifests/dpo_pair_factory_v11_test50_repaired.jsonl`
- v12b S_pass/S_fail subsets and `val_video_4`.
- Warm-start LoRA: `local_assets/dpo_objective_repair_v12b/winner_curriculum/checkpoints/winner_anchor_repeat_L0_camera_r4_step020_lora_state.pt`

## Candidate Schemes

1. `S01_winner_detached_pref_low`: L0 camera r4, beta 0.05, lambda_pref 0.005, loser detached.
2. `S02_winner_detached_pref_lower_lr`: same as S01 with half LR.
3. `S03_winner_detached_pref_earlystop_best`: same as S01 with rolling best-step and negative-window stop.
4. `S04_no_lose_gap_normalized_win_only`: no loser energy/logit, winner-preserving backbone.
5. `S05_normalized_clipped_loser_alpha005`: normalized clipped loser gap, alpha_l 0.05.
6. `S06_normalized_clipped_loser_alpha010`: normalized clipped loser gap, alpha_l 0.10.
7. `S07_linear_winner_detached`: linear utility with detached loser.
8. `S08_delayed_loser_gradient_tiny`: winner first, tiny loser gradient only after stable winner signal.
9. `S09_local_time_mask_winner_detached`: local time/spatial mask where metadata exists.
10. `S10_lora_camera_temporal_winner_detached`: limited camera-temporal r4, only if params/memory safe.

## Metrics Logged Every Step

- `m_w`, `m_l`, `m_w_ref`, `m_l_ref`
- `win_gap = m_w - m_w_ref`
- `lose_gap = m_l - m_l_ref`
- `winner_improvement = -win_gap`
- `loser_degradation = lose_gap`
- `g_w = log((m_w + eps)/(m_w_ref + eps))`
- `g_l = log((m_l + eps)/(m_l_ref + eps))`
- clipped loser gap, winner contribution ratio, loser dominance
- DPO/objective loss, utility, implicit accuracy, grad/update norms, sigma/timestep, memory, finite status

## Success Gate

A scheme can pass training signal only if within <=200 steps: mean and latest/final `winner_improvement_post > 0`, mean/latest win-gap < 0, winner contribution ratio >= 0.30, loser dominance <= 0.70, utility moves, loss is not pure 0.693 no-signal, grad/update norms are nonzero, no OOM/NaN/Inf/SIGFPE, and only GPU4/5 were used. A recipe is valid only after checkpoint V2V-5 videos, metrics, and Codex visual audit also pass.

## Failure Gate

Stop a scheme if winner improvement is negative for repeated eval windows, final/latest winner flips negative repeatedly, winner contribution ratio <0.30, loser dominance >0.70, pure no-signal persists, grad/update zero, runtime fails, video worsens, metrics degrade, or any forbidden GPU is used.

## Outputs

- `manifests/dpo_v13b_subsets/`
- `reports/dpo_objective_search_v13b/`
- `local_assets/dpo_objective_search_v13b/` for checkpoints/videos only; not pushed.
- `docs/dpo_objective_search_v13b_report.md`

## What Is Not Run

- No large DPO.
- No train400.
- No S32/S64.
- No StageA.
- No StageB.
- No GRPO.
- No broad-LoRA.
- No checkpoint/data/weight deletion.
- No videos/images/checkpoints/weights pushed.

## Post-Implementation Update (2026-07-06T13:08:17+08:00)

- v13b subset builder, gap logger, objective runner, GPU4/5 scheduler, and gate checks were implemented.
- Validation: compileall PASS; direct smokes PASS; pytest unavailable in system Python.
- Scheduler dry-run decision: `GPU4_5_BLOCKED`; no training launched because GPU4/5 were not available / GPU query timed out conservatively.
- No large DPO, train400, StageA, StageB, GRPO, broad-LoRA, checkpoint deletion, or video/weight push occurred.

## Interim Execution Note - 2026-07-06T15:32:53

S01/S02 have training-signal-only evidence on GPU4/5. The run is intentionally paused before further schemes while checkpoint video/metrics/audit gates are attempted. Safe WanModelFast eval loading was patched in the project wrapper because eval stalled at CPU-side `WanModelFast.from_pretrained` before any V2V-5 video was generated. No recipe is marked PASS until real checkpoint videos, metrics, and Codex visual audit pass.
## Final Update

v13b completed with DPO_RECIPE_NOT_FOUND. S01/S05/S07 reached video/metric evaluation but failed gates. S03/S06/S09 showed winner-positive, non-loser-dominant training-only signals with DPO loss still near 0.693. S10 runtime-blocked before first row. No large DPO, train400, S32, or S64 is allowed from this result.

