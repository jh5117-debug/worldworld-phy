Current Status: MIXED

# DPO Pair Factory v11 Loser Quality and Metrics Backend Status

Updated: 2026-07-04 04:10:15

## User Priority

1. Inspect all 500 ready pairs one by one, focusing on whether each LOSE is usable for training.
2. Repair LPIPS / FVD / VBench metric backends as far as possible without sudo, large model downloads, or fake metrics.

## Loser Quality Audit Result

- Ready500 input: `manifests/dpo_pair_factory_v11_ready_500.jsonl`
- Audited rows: 500
- Training-usable after loser audit: 497
- Rejected / needs review: 3
- Reject reason: `too_subtle_metric` for 3 TypeA_plus pairs
- Source breakdown in audited set: rollout-derived 15, TypeA_plus 3, synthetic controlled 482
- Revised trainable manifest: `manifests/dpo_pair_factory_v11_ready500_trainable_after_loser_audit.jsonl`

Decision: do not train on the original 500 blindly. Use the 497-row trainable manifest unless the 3 TypeA_plus pairs are manually repaired or replaced.

## Metrics Backend Repair Result

- LPIPS: AVAILABLE. `lpips` installed and real `alex` smoke passed.
- FVD: still BLOCKED_BY_ENV_TEMPORAL_BACKBONE. `torchmetrics.video.FrechetVideoDistance` is not available, and no local I3D/FVD temporal feature weights were found. Image FID is installed but must not be reported as FVD.
- VBench: PACKAGE_CLI_AVAILABLE_CONFIG_BLOCKED. `vbench` imports and CLI help works; real scoring still needs explicit dimensions, videos path, and approved local checkpoint/cache policy.

Environment caveat: VBench installation added user-site `transformers==4.33.2`, which pip reports as incompatible with an existing fastwam expectation of `transformers==4.49.0`. Future rollout/training commands should isolate or pin their environment.

## Constraints Confirmed

- No DPO / SDPO / Linear-DPO / winner-anchor training run.
- No StageA / StageB / GRPO / broad-LoRA run.
- No checkpoint deletion.
- No videos or weights pushed.
