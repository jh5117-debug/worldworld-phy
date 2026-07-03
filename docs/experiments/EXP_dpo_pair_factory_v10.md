# EXP DPO Pair Factory v10

Current Status:
DPO_PAIR_FACTORY_V10_PRD_READY

## Current Status

This experiment intentionally stops focusing on DPO objective training. The current project need is a clean, reviewed, human-visible preference-pair pool.

Starting facts:

- v6b is the strongest current route: 32 recovered prefix5 conditions, B/C rollout PASS, 16 C medium-hard candidates, and 15 DPO-ready GT>C pairs.
- Protocol v1 has 66 historical pairs, but the acceptance gate was broad and cannot be trusted without re-audit.
- Protocol v4 has 42 reward-selected pairs, but v5 visual alignment found only 3 true human-visible ready pairs and 39 too subtle pairs.
- The target is at least 50 reviewed DPO-ready pairs, preferably 100.

No DPO training is run in v10.

## Problem

The project does not yet have enough reviewed DPO preference pairs. Reward-selected pairs can be too subtle, old TypeB rollout pairs can be too blurry or too bad, and training/objective diagnostics are premature without a larger clean pair pool.

Specific risks:

- Data volume is below the minimum needed for a small DPO run.
- Reward and PSNR/SSIM alone do not guarantee human-visible medium-hard losers.
- Existing manifests mix local corruption, rollout, diagnostic, and metric-only candidates.
- Unreviewed or visually unclear losers would create false training signal.

## Hypothesis

Recovering more prefix5 conditions, reusing B/C small-LoRA rollouts, adding strict controlled corruption, and applying reward + quality + Codex visual gates can produce a 50+ reviewed DPO-ready preference-pair set.

Preferred pair sources:

- GT_C: clean GT future wins over C camera+self-temporal-r4 medium-hard rollout.
- GT_Corruption: clean GT future wins over controlled, visible, non-collapsed corruption.
- B_C: B camera-r8 high-quality rollout wins over C medium-hard rollout when B is absolutely clean enough.
- Teacher_Failure: stronger local teacher rollout wins over bad Fast/C rollout only if teacher exists and passes quality.
- SelfRollout: diagnostic-only unless the top rollout has absolute quality and reviewed superiority.

## Inputs

Use these inputs if present:

- `manifests/targeted_BC_loser_mining_v6b_conditions.jsonl`
- `manifests/dpo_typeB_C_loser_pairs_v6b.jsonl`
- `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`
- `manifests/dpo_preference_protocol_v1_pairs.jsonl`
- `manifests/dpo_preference_protocol_v2_pairs.jsonl`
- `manifests/dpo_preference_protocol_v3_pairs.jsonl`
- `manifests/dpo_preference_protocol_v4_pairs.jsonl`
- `manifests/screen16_v2v5.jsonl`
- `manifests/quant_benchmark_v1_all.jsonl`
- `manifests/quant_benchmark_v1_core.jsonl`
- `manifests/quant_benchmark_v1_stress.jsonl`
- Existing `local_assets` rollouts and full GT videos.
- B camera-r8 and C camera+self-temporal-r4 adapters from the small-LoRA sweep.

## Outputs

Primary outputs:

- `manifests/dpo_pair_factory_v10_conditions.jsonl`
- `manifests/dpo_pair_factory_v10_rollout_candidates.jsonl`
- `manifests/dpo_pair_factory_v10_candidate_pairs.jsonl`
- `manifests/dpo_pair_factory_v10_ready_pairs.jsonl`
- `manifests/dpo_pair_factory_v10_top50_pairs.jsonl`
- `manifests/dpo_pair_factory_v10_top100_pairs.jsonl` if enough pairs exist.

Report root:

- `reports/dpo_pair_factory_v10/`

PPT outputs:

- `reports/ppt_winlose_showcase_latest/dpo_pair_factory_v10_showcase.mp4`
- `reports/ppt_winlose_showcase_latest/dpo_pair_factory_v10_selected.csv`
- `reports/ppt_winlose_showcase_latest/dpo_pair_factory_v10_notes.md`

The MP4 and image/contact-sheet artifacts are not committed.

## Success Gate

Minimum success:

- At least 50 reviewed DPO-ready pairs.
- Every ready pair has prefix_len = 5 and prediction_start_frame = 5.
- Every ready pair uses the same prefix, prompt, poses, and intrinsics for winner and loser.
- Every ready loser has real video/contact-sheet evidence and `codex_visual_audit.reviewed = true`.
- Every ready loser is medium-hard, clear enough, not too blurry, not collapsed, not too similar, and has non-empty `written_reason`.
- Reward/metric/quality gates support the visual decision; no pair is selected by metric alone.

Stretch success:

- At least 100 reviewed DPO-ready pairs.
- Pair types include GT_C, GT_Corruption, and B_C or teacher/failure if available.
- At least four templates are represented when available.

## Failure Gate

- `<10` reviewed pairs: `PAIR_FACTORY_V10_BLOCKED_INSUFFICIENT_PAIR_DATA`.
- `10-49` reviewed pairs: `PAIR_FACTORY_V10_TINY_ONLY`.
- Severe reward/visual mismatch: block training and report needed backend/gate fixes.
- Rollout runner cannot generate more videos after non-destructive repair attempts.
- Clean GT/future videos or required condition metadata are missing and unrecoverable.

## Visual Audit Rule

Every loser entering a ready manifest must have:

- real video or contact sheet reviewed by Codex;
- `reviewed = true`;
- `is_dpo_ready = true`;
- `is_medium_hard = true`;
- `is_too_blurry = false`;
- `is_collapsed = false`;
- `is_too_similar_to_winner = false`;
- `is_too_bad = false`;
- a clear `main_failure_tag`;
- non-empty `written_reason`.

No visual audit means not DPO-ready.

## Metrics

Compute where available:

- PSNR
- SSIM
- LPIPS if local backend exists
- FVD if local backend/assets exist
- VBench if local backend/assets exist
- PhysGeo reward components: R_bg, R_cam, R_fg, R_phys, R_reobs, R_quality, P_freeze, P_blur, R_total
- sharpness, blur, flicker, freeze_rate, brightness, contrast

Unavailable LPIPS/FVD/VBench must be reported as `BLOCKED_BY_ENV`; do not fabricate.

## What Is Explicitly Not Run

- No DPO training.
- No SDPO.
- No Linear-DPO.
- No Safe-linear.
- No winner-anchor objective.
- No large DPO.
- No StageA training.
- No StageB.
- No GRPO.
- No broad-LoRA.
- No checkpoint deletion or modification.
- No data/weights/video push.

## Git Checkpoint

Commit PRD before execution:

`Prepare DPO pair factory v10 PRD`

Follow-up commits should separate condition recovery, existing pair audit, rollout/scoring, pair construction, and final documentation.

## Milestone Readback

### 2026-07-03 Condition Inventory
- Runnable prefix5 conditions recovered: 102.
- Status: CONDITION_INVENTORY_READY_100.
- Output manifest: `manifests/dpo_pair_factory_v10_conditions.jsonl`.
- Recovered videos are stored under `local_assets/dpo_pair_factory_v10/recovered_conditions/` and are not committed.

### 2026-07-03 Existing Pair Audit
- Total existing pairs checked: 195.
- Strict DPO-ready existing pairs: 18.
- Ready types: GT_C 15, TypeA_plus 3.
- Old v1/v2/v3 pairs are marked review-required due subtle-risk, not counted as ready.
- Output manifest: `manifests/dpo_pair_factory_v10_existing_ready_pairs.jsonl`.
- Next step: expanded pair mining from the 102 recovered runnable conditions.

