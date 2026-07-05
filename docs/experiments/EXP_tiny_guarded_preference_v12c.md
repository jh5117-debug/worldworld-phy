# EXP_tiny_guarded_preference_v12c

## Current Status

- Canonical repaired ready500 exists at `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl` and old `manifests/dpo_pair_factory_v11_ready_500.jsonl` is deprecated.
- v12 failed on 32-pair guarded DPO because winner worsened and the preference signal stayed weak/no-signal.
- v12b per-pair winner-anchor diagnosis found 4 S_PASS and 4 S_FAIL.
- v12b S_pass4 winner-only curriculum passed: mean `winner_improvement_post = 5.76973e-05`, final `winner_improvement_post = 5.87106e-05`, mean winner contribution ratio `0.579694`.
- Current run uses only physical GPU4 with `CUDA_VISIBLE_DEVICES=4`; no GPU0/1/2/3/5/6/7 fallback is allowed.
- Current task is a tiny guarded preference probe, not scale.

## Problem

- Winner-only signal exists only on the filtered S_pass4 subset.
- Opening the preference branch may again cause loser-dominance.
- DPO loss may return to the 0.693 no-signal regime.
- Synthetic controlled pairs dominate ready500, and S_fail pairs show pair conflict.
- Large DPO is not justified until a tiny preference probe preserves winner improvement and passes video/metric audit.

## Hypothesis

- If we warm-start from the winner-only positive S_pass4 state and keep loser gradients disabled or near zero, a tiny preference branch may preserve winner improvement.
- A winner-detached preference loss is safer than full winner+loser DPO because it does not push the loser branch at first.
- Full loser gradients should only be tested after the winner-detached probe passes, with `max_lambda_loser <= 0.05`.
- If sigmoid preference is no-signal but winner is not worse, a linear winner-detached utility can be tested separately.

## Inputs

- `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`
- `manifests/dpo_pair_factory_v11_train400_repaired.jsonl`
- `manifests/dpo_pair_factory_v11_val50_repaired.jsonl`
- `manifests/dpo_v12b_subsets/s_pass_winner_anchor.jsonl` if present, otherwise the committed/report S_pass manifest from `reports/dpo_objective_repair_v12b/winner_anchor_diag/s_pass_winner_anchor.jsonl` must be copied or referenced explicitly.
- `manifests/dpo_v12b_subsets/val_video_4.jsonl`
- v12b winner-only checkpoint if available under `local_assets/dpo_objective_repair_v12b/`.

## GPU Policy

- Physical GPU4 only.
- All execution commands must set `CUDA_VISIBLE_DEVICES=4` and use process-local `--gpu 0`.
- If GPU4 is occupied by an unknown task, report `GPU4_BLOCKED`; do not switch to GPU5/6/7 or GPU0-3.
- If a v12c process is accidentally launched on another GPU, stop only that v12c process, fix visibility, and rerun.

## Objectives

### winner_only_warmstart

Run only if no valid v12b winner-only checkpoint can be loaded. Objective is `loss = E_policy_winner`, max 5 steps on S_pass4. Preference branches remain disabled.

### winner_detached_preference

Main probe. The loser energy is evaluated but detached from gradient:

`u = (stop_gradient(E_policy_loser) - E_policy_winner) - Delta_ref`

`loss = lambda_winner_anchor * E_policy_winner + lambda_pref * -logsigmoid(beta * u)`

Defaults: `beta=0.1`, `lambda_winner_anchor=1.0`, `lambda_pref=0.02`, `lambda_loser=0.0`, max 10 steps.

### tiny_loser_gradient_preference

Only if winner-detached preference passes. Introduces loser gradient with `lambda_loser=0` initially and at most `0.05`, gated by positive winner improvement and winner contribution ratio >= 0.30.

### linear_winner_detached

Only if winner-detached preference runtime passes but sigmoid utility is no-signal while winner does not worsen.

## Success Gate

- Runtime has no OOM / NaN / SIGFPE.
- Grad norm is nonzero and update norm is > 0.
- Mean and final `winner_improvement_post` are positive.
- If loser branch is enabled, `winner_contribution_ratio >= 0.30`.
- Loser degradation is not the only source of margin.
- DPO loss is not a fake 0.693 no-signal result.
- Checkpoint videos at step0/5/10 are not worse after Codex visual audit.
- PSNR/SSIM/LPIPS/FVD-smoke/VBench temporal flickering/PhysGeo do not degrade beyond threshold.

## Failure Gate

- `winner_improvement_post` becomes negative.
- Winner contribution ratio drops below 0.30 when loser branch is enabled.
- Loser-only signal appears.
- DPO loss stays near 0.693 with no utility movement.
- Videos or metrics degrade.
- GPU4 is unavailable or runtime OOM occurs on GPU4.

## Outputs

- `reports/dpo_tiny_guarded_preference_v12c/setup/`
- `reports/dpo_tiny_guarded_preference_v12c/<objective>/`
- `reports/dpo_tiny_guarded_preference_v12c/objective_comparison.csv`
- `docs/dpo_tiny_guarded_preference_v12c_report.md`
- `reports/dpo_tiny_guarded_preference_v12c/self_review.md`
- local checkpoint/video/cache outputs under `local_assets/dpo_tiny_guarded_preference_v12c/` only; do not commit them.

## What Is Not Run

- No large DPO.
- No S1 32 / S2 64 / S3 128 / train400 scale.
- No StageA / StageB / GRPO.
- No broad-LoRA.
- No GPU5/6/7 or GPU0-3 fallback.
- No checkpoint deletion.
- No media, checkpoint, tensor, or weight push.


<!-- V12C_EXECUTION_STATUS_START -->

## Execution Status

- Setup: `S_PASS4_READY`.
- Warm start: loadable v12b step20 LoRA found.
- Local mask audit: 3/4 pairs local-mask ready.
- Code/test preparation: compileall PASS; pytest unavailable; direct smoke PASS.
- Training status: `V12C_GPU4_BLOCKED`.
- Blocker: physical GPU4 occupied by non-project `eval_libero_single.py gpu_id=4`; fallback GPUs are forbidden.
- No v12c preference objective ran.

<!-- V12C_EXECUTION_STATUS_END -->
