# V2V-5 Rollout Scoring Report

Updated: 2026-06-27T17:40:45

## Scope

All primary metrics are future-only on frames 5-80. Prefix frames 0-4 are condition and are not counted in the main scores.

## StageA Screen16 Scoring

| Model | PSNR up | SSIM up | Freeze down |
|---|---:|---:|---:|
| Original Fast | 15.844572 | 0.837829 | 0.000 |
| StageA V2V-5 final | 16.012353 | 0.841087 | 0.000 |

StageA final is the best metric checkpoint, but visual review is still mixed because of extra-object hallucination and weak physical-event preservation.

## DPO Step20 Scoring

| Model | PSNR up | SSIM up | Freeze down |
|---|---:|---:|---:|
| DPO step20 | 15.819494 | 0.836042 | 0.000 |

DPO step20 is below StageA final and slightly below Original Fast on PSNR/SSIM. Visual review found more extra-object fragments in several samples. This is not a good checkpoint for rollout candidate generation.

## Artifacts

- Prefix5 pairs: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`
- StageA metrics: `reports/stageA_v2v5_20260627/metrics_summary.csv`
- StageA decision: `reports/stageA_v2v5_20260627/best_stageA_checkpoint_decision.json`
- DPO training metrics: `reports/dpo_probe_v2v5_20260627/tiny5_step20/training_metrics.jsonl`
- DPO signal summary: `reports/dpo_probe_v2v5_20260627/tiny5_step20/probe_signal_summary.json`
- DPO checkpoint video eval: `reports/dpo_probe_v2v5_20260627/step020_eval/metrics/checkpoint_summary.json`
- DPO video audit: `reports/dpo_probe_v2v5_20260627/step020_eval/video_audit/all_video_audit.csv`
- DPO comparison sheets: `reports/dpo_probe_v2v5_20260627/step020_eval/model_comparison_contact_sheets/`
