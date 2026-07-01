<!-- targeted_BC_loser_mining_v6b_update -->
# Targeted B/C Loser Mining v6b Update

Current Status: READY_FOR_TINY_DPO_SMOKE

Updated: 2026-07-01 09:20:29 CST

- Runnable prefix5 recovery PASS: 32 / 32 conditions recovered from quant benchmark full videos by materializing prefix frames 0-4 and GT future frames 5-80.
- Previous v6 had only 5 runnable rows because it only used already-materialized DPO prefix5 asset dirs; quant benchmark rows needed prefix/future video recovery.
- Smoke rollout PASS for M0/B/C.
- 16-condition rollout PASS for M0/B/C.
- 32-condition rollout PASS for B camera-r8 and C camera+self-temporal-r4. M0 32cond baseline remains PARTIAL (first16 only) and was not needed for GT>C pair construction.
- B camera-r8 conclusion: stable candidate generator / control baseline.
- C camera+self-temporal-r4 conclusion: usable medium-hard loser source.
- Codex visually reviewed first16 and remaining16 overview sheets.
- Medium-hard C loser candidates selected: 16.
- DPO-ready GT>C pairs: 15, exceeding the >=10 tiny DPO smoke gate.
- Final v6b pair manifest: `manifests/dpo_typeB_C_loser_pairs_v6b.jsonl`.
- PPT showcase generated locally: `reports/ppt_winlose_showcase_latest/BC_medium_hard_loser_v6b_for_ppt.mp4` (not for Git).
- No DPO training, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint edits, or checkpoint deletion were run.

<!-- /targeted_BC_loser_mining_v6b_update -->

# Targeted B/C Small-LoRA Loser Mining v6 Report

Current Status: BLOCKED_INSUFFICIENT_MEDIUM_HARD_ROLLOUTS

Updated: 2026-06-30 20:50:46 CST

## Summary

- GPU discovery blocker: fixed with `scripts/safe_gpu_status.sh`; `query-compute-apps` is timeout-guarded and no longer blocks rollout.
- Runner discovery blocker: fixed by using deterministic module `cam_physgeo.eval.run_v2v5_inference`.
- Environment blocker: resolved for runner by using phys-videophy Python plus `/tmp/h20_v2v5_av_only` for the missing `av` package.
- Smoke rollout: PASS for M0 Original Fast, B camera-only rank8, and C camera+self/temporal rank4.
- Available-condition rollout: PARTIAL_PASS. Only 5 runnable prefix5 conditions exist in the current tree, not the requested 8/32 coverage.
- Generated videos: 3 smoke + 15 available-condition videos.
- C medium-hard loser candidates: 4 / 5 by Codex visual audit.
- DPO-ready GT>C pair count: 4, below the >=10 gate.
- 32-condition rollout: NOT_RUN because only 5 runnable prefix5 conditions were available.
- Recommendation: do not run DPO smoke yet; expand runnable prefix5 conditions or add external rollout source first.

## Checkpoints

- B camera-only rank8 adapter: `local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_B_camera_r8_train200_20260624_141215/checkpoints/small_lora_B_camera_r8_train200_20260624_141215/high_only_phase/branches/step_000200/fast_stageA_high_noise_adapter`
- B trainable params: 13,107,200. Conclusion: stable candidate generator / control baseline.
- C camera+self/temporal rank4 adapter: `local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_C_camera_self_r4_train200_20260624_141215/checkpoints/small_lora_C_camera_self_r4_train200_20260624_141215/high_only_phase/branches/step_000200/fast_stageA_high_noise_adapter`
- C trainable params: 1,310,720. Conclusion: best current scope for medium-hard loser mining, but data yield remains too small.

## Outputs

- Smoke manifest: `reports/targeted_BC_loser_mining_v6/smoke_generated_manifest.csv`
- Smoke metrics: `reports/targeted_BC_loser_mining_v6/smoke_metric_summary.csv`
- Available-condition manifest: `reports/targeted_BC_loser_mining_v6/generated_manifest_available5.csv`
- Available-condition metrics: `reports/targeted_BC_loser_mining_v6/metric_summary_available5.csv`
- Visual audit: `reports/targeted_BC_loser_mining_v6/video_audit_available5.csv`
- Pair audit: `reports/targeted_BC_loser_mining_v6/pair_candidate_audit.csv`
- Final pair manifest: `manifests/dpo_typeB_C_loser_pairs_v6.jsonl`
- PPT showcase: `reports/ppt_winlose_showcase_latest/BC_medium_hard_loser_v6_for_ppt.mp4`

## Metric Caveats

- PSNR and SSIM proxy ran.
- LPIPS is BLOCKED_BY_ENV in the selected runner env because `lpips` is unavailable.
- FVD is BLOCKED_BY_ENV because no local FVD/I3D backend was available.
- VBench is BLOCKED_BY_ENV because no local VBench evaluator/weights were available.
- Reward vectors in this round are diagnostic proxies, not final training rewards.

## Decision

`READY_FOR_TINY_DPO_SMOKE = false`. The v6 targeted B/C route is promising qualitatively, but 4 pairs is below the >=10 tiny-smoke gate.

## Explicit Non-Runs

No DPO training, no StageB, no GRPO, no full-data StageA, no broad-LoRA, no checkpoint deletion or modification.

## Test Status

- `python -m compileall cam_physgeo src tests`: PASS.
- `pytest -q tests/test_pair_schema_v2v5.py tests/test_medium_hard_loser_selection.py tests/test_reward_guided_pair_selector.py`: NOT_RUN because pytest is unavailable in PATH on the remote host; recorded in `reports/targeted_BC_loser_mining_v6/pytest_v6.log`.
