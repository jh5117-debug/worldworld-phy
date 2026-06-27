# Anchored DPO Probe Final Report

Updated: 2026-06-27T17:40:45

## Final Status

**DPO_PROBE_FAILED** for scale-up.

The true LingBot-Fast prefix-aware V2V-5 DPO path is now runnable, but the tiny probe did not produce a useful preference-learning signal and the post-probe video evaluation is worse than the best StageA V2V-5 checkpoint. Do not scale DPO from this checkpoint.

## What Was Actually Run

- Pair manifest: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`
- Pair count used in probe: 5 prefix5 pairs
- Condition: clean prefix frames 0-4, prompt, poses, intrinsics
- Target: winner/loser future frames 5-80
- Loss/reward mask: future only, raw frame indices 5..80
- Policy/reference: LingBot-World-Fast flow-matching energy backend
- LoRA: camera-conditioning only, rank 4, 160 modules, 6,553,600 trainable parameters
- Probe: 20 optimizer steps on GPU7, BF16 mixed-safe path
- Large-scale DPO: not run

## DPO Runtime Checks

- no SIGFPE / no OOM / no NaN or Inf
- same noise and same timestep verified
- reference frozen verified
- prefix excluded from loss
- future-only energy verified
- adapter save/load passed

## DPO Learning Signal

| Metric | Value |
|---|---:|
| dpo_loss mean | 0.693144497 |
| dpo_loss last | 0.693165958 |
| implicit accuracy mean | 0.600 |
| implicit accuracy last | 0.000 |
| winner improvement mean | 0.000084573 |
| winner improvement last | -0.000231806 |
| loser degradation mean | -0.000030977 |
| loser degradation last | -0.000143982 |
| reference-relative margin mean | 0.000053596 |
| grad norm mean | 0.001245106 |
| mean step time sec | 192.222 |

Interpretation: the DPO loss stays essentially at random-preference scale (`~0.693`), winner improvement is tiny and turns negative at the last step, and the margin is too small to treat as a useful preference signal.

## Video Evaluation

All reported metrics are future-only on frames 5-80.

| Model | PSNR up | SSIM up | Freeze down | Decision |
|---|---:|---:|---:|---|
| Original Fast | 15.844572 | 0.837829 | 0.000 | baseline |
| StageA V2V-5 final | 16.012353 | 0.841087 | 0.000 | mixed, best available checkpoint |
| DPO step20 | 15.819494 | 0.836042 | 0.000 | failed for scale-up |

Codex visual review of the DPO comparison sheets found that DPO step20 tends to add extra small objects/fragments and does not improve foreground identity or physical events. It is not a good DPO policy checkpoint.

LPIPS / FVD / VBench remain `BLOCKED_BY_ENV_or_not_requested` in this environment. They were not fabricated.

## Decision

- DPO backend: **real and runnable**.
- DPO BF16 runtime: **ready**.
- Tiny DPO learning/video outcome: **failed for scale-up**.
- Recommended next action: keep using prefix5 GT-clean > controlled-corruption pairs for diagnostics, but rebuild pair scoring/quality floors before another DPO probe. Do not use current StageA or current DPO outputs as winners.

## Artifacts

- Prefix5 pairs: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`
- StageA metrics: `reports/stageA_v2v5_20260627/metrics_summary.csv`
- StageA decision: `reports/stageA_v2v5_20260627/best_stageA_checkpoint_decision.json`
- DPO training metrics: `reports/dpo_probe_v2v5_20260627/tiny5_step20/training_metrics.jsonl`
- DPO signal summary: `reports/dpo_probe_v2v5_20260627/tiny5_step20/probe_signal_summary.json`
- DPO checkpoint video eval: `reports/dpo_probe_v2v5_20260627/step020_eval/metrics/checkpoint_summary.json`
- DPO video audit: `reports/dpo_probe_v2v5_20260627/step020_eval/video_audit/all_video_audit.csv`
- DPO comparison sheets: `reports/dpo_probe_v2v5_20260627/step020_eval/model_comparison_contact_sheets/`


## Safety

No StageB, GRPO, full-data long StageA, or large-scale DPO was run. No historical checkpoint was deleted or modified. Large videos/checkpoints remain outside Git.
