# EXP Targeted B/C Loser Mining v6

Current Status: PLANNED / PRD_READY

## Problem

Saved small-LoRA sweep artifacts were recovered and visually audited, but they are not directly usable as DPO-ready TypeB rollout losers. The recovered audit contains 208 rollout video rows and 212 contact-sheet rows, with A/B/C/D each contributing 48 videos. Existing TypeB quality-gate pass count is 0 / 208.

The previous decision is:

- A camera-only rank4 is clear and stable but too conservative, so it is not a primary loser source.
- B camera-only rank8 is the clearest and most stable scope, with the best fixed-val score, so it is the candidate generator / control baseline.
- C camera + limited self/temporal rank4 is the best scope for mining future medium-hard loser rollouts because it remains readable while showing more foreground identity, object deformation, and physical-event failures.
- D camera + limited cross-attention rank4 is a diagnostic runner-up but has higher cross-attention artifact risk.

## Hypothesis

A targeted rerollout using B and C on a locked benchmark can produce clearer, human-visible medium-hard TypeB-style losers than the saved screen16 sweep artifacts. B should provide stable high-quality candidate/reference rollouts, while C may provide readable negatives with foreground / physical / reobserve failures.

## Inputs

Primary readbacks:

- `docs/current_unified_eval_dpo_status.md`
- `docs/small_lora_sweep_loser_source_audit.md`
- `docs/small_lora_scope_sweep_final_report.md`
- `reports/small_lora_sweep_visual_audit/best_loser_source_decision.md`
- `reports/small_lora_sweep_visual_audit/model_summary.csv`
- `reports/small_lora_sweep_visual_audit/all_video_audit.csv`

Candidate benchmark manifests, in priority order:

- `manifests/quant_benchmark_v1_all.jsonl`
- `manifests/quant_benchmark_v1_core.jsonl`
- `manifests/quant_benchmark_v1_stress.jsonl`
- fallback: `manifests/screen16_v2v5.jsonl`
- fallback: `manifests/dpo_preference_protocol_v3_pairs.jsonl`

## Model / Checkpoint Search

Inventory to produce:

- `reports/targeted_BC_loser_mining_v6/checkpoint_inventory.csv`

Required checkpoint metadata:

- B camera-only rank8 adapter path, config, checkpoint step, trainable params, model fingerprint.
- C camera+self/temporal rank4 adapter path, config, checkpoint step, trainable params, matched modules, model fingerprint.

If B/C adapter checkpoints cannot be found, this experiment must stop rollout work and write `BLOCKED_CHECKPOINT_NOT_FOUND`. Saved videos may remain diagnostic only; no checkpoint path may be fabricated.

## Rollout Plan

Candidate models:

- M0 Original Fast baseline
- M_B B camera-only rank8
- M_C C camera + limited self/temporal rank4
- Optional diagnostic only: M_A A camera-only rank4
- Optional diagnostic only: M_D D camera + limited cross-attention rank4

Benchmark plan:

- Start with 32 conditions.
- Cover drop / collision / roll / containment.
- Include at least 8 reobserve / stress conditions if available.
- Use identical prefix/image, prompt, poses, intrinsics, seed, scheduler, inference steps, resolution, and future-frame evaluation window.
- Use seeds=2 per condition per candidate model.
- Expand to 80 only after the 32-condition run is stable.

Output roots:

- `local_assets/targeted_BC_loser_mining_v6/rollouts/`
- `reports/targeted_BC_loser_mining_v6/generated_manifest.csv`
- `reports/targeted_BC_loser_mining_v6/generated_manifest.jsonl`

## Metrics

For each rollout:

- PSNR
- SSIM
- LPIPS if available
- FVD if available
- VBench if available
- R_bg
- R_cam
- R_fg
- R_phys
- R_reobs
- R_quality
- P_freeze
- P_blur
- R_total
- sharpness
- blur
- flicker
- freeze_rate

FVD / VBench must be marked `BLOCKED_BY_ENV` if unavailable. They must not be faked or replaced with unrelated metrics.

Metric outputs:

- `reports/targeted_BC_loser_mining_v6/rollout_scores.csv`
- `reports/targeted_BC_loser_mining_v6/reward_vectors.jsonl`
- `reports/targeted_BC_loser_mining_v6/metric_summary.csv`

## Codex Visual Audit Rule

Codex must inspect all generated contact sheets or sampled frames before selecting medium-hard losers. Audit fields must include background stability, camera following, foreground identity, object deformation, physical event quality, reobserve consistency, freeze, visual quality, sharpness, blur, collapse, similarity to GT, medium-hard candidacy, failure tags, and written reason.

Audit outputs:

- `reports/targeted_BC_loser_mining_v6/video_audit.csv`
- `reports/targeted_BC_loser_mining_v6/video_audit.jsonl`

## Pair Selection Rule

TypeB-C pair construction:

- Winner priority 1: clean GT future.
- Winner priority 2: B high-quality rollout, only if B winner absolute quality passes.
- Loser: C medium-hard rollout.

Keep only candidates that are clear, not black, not severely blurred, not scene replacement, not globally collapsed, not too similar to GT, not too degraded, reward-margin positive, subreward drop aligned with the visible failure, and explainable in one sentence.

Pair outputs:

- `manifests/dpo_typeB_C_loser_pairs_v6.jsonl`
- `reports/targeted_BC_loser_mining_v6/pair_candidate_audit.csv`
- `reports/targeted_BC_loser_mining_v6/pair_summary.md`
- `reports/targeted_BC_loser_mining_v6/dpo_ready_pairs_v6.jsonl`

If DPO-ready pairs < 10, mark `BLOCKED_INSUFFICIENT_MEDIUM_HARD_ROLLOUTS` and do not recommend DPO scaling.

## PPT Showcase

Generate diagnostic/presentation video:

- `reports/ppt_winlose_showcase_latest/BC_medium_hard_loser_v6_for_ppt.mp4`
- `reports/ppt_winlose_showcase_latest/BC_medium_hard_loser_v6_selected.csv`
- `reports/ppt_winlose_showcase_latest/BC_medium_hard_loser_v6_notes.md`

The MP4 and any contact sheets/images are not committed or pushed.

## Success Gate

PASS only if:

- B and C checkpoints are found and fingerprinted.
- Rollouts complete without training or checkpoint modification.
- Metrics and reward tables are produced.
- Codex visual audit is completed.
- At least 10 clear medium-hard DPO-ready TypeB-C pairs are found.

MIXED if:

- Rollouts and metrics complete, but DPO-ready pairs < 10.

BLOCKED if:

- B/C checkpoints are missing.
- GPU / environment prevents rollout.
- Required videos cannot be generated.

## Failure Gate

Do not force pair count by including blurry, collapsed, too-similar, too-degraded, or reward-misaligned losers. If C does not produce medium-hard losers, record the failure and keep TypeB-C blocked.

## What Is Explicitly Not Run

- No DPO training.
- No StageB.
- No GRPO.
- No full-data StageA.
- No broad-LoRA.
- No checkpoint deletion or modification.
- No data / weight deletion.
- No MP4 / JPG / PNG / HDF5 / NPY / PT / PTH / checkpoint / large-log commit.

## Git Checkpoint Before / After

Before rollout work, commit and push this PRD. After rollout / score / audit / pair construction, update this PRD and the final report with actual status, blocked reasons, and output paths.

## Experiment Update - 2026-06-30 16:20 CST

Current Status: BLOCKED_BY_GPU_OR_RUNNER_DISCOVERY

Checkpoint inventory completed successfully. B and C step200 adapters were found and fingerprinted in `reports/targeted_BC_loser_mining_v6/checkpoint_inventory.csv`.

New rollout did not start because all GPUs showed high memory occupancy in the initial status check, and follow-up `nvidia-smi --query-compute-apps` calls hung. Repository runner discovery also timed out under current filesystem/I/O conditions. No videos, metrics, rewards, or DPO-ready pairs were fabricated.

Outputs written:

- `reports/targeted_BC_loser_mining_v6/checkpoint_inventory.csv`
- `reports/targeted_BC_loser_mining_v6/generated_manifest.csv`
- `reports/targeted_BC_loser_mining_v6/metric_summary.csv`
- `reports/targeted_BC_loser_mining_v6/pair_summary.md`
- `docs/targeted_BC_loser_mining_v6_report.md`

## Verification

- `python3 -m compileall cam_physgeo src tests`: PASS.
- `pytest -q tests/test_pair_schema_v2v5.py tests/test_medium_hard_loser_selection.py tests/test_reward_guided_pair_selector.py`: BLOCKED_BY_ENV, `pytest` command not found in the active remote shell. No pytest PASS was claimed.
