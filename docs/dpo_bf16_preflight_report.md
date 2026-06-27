# DPO BF16 Preflight Report

Updated: 2026-06-27T17:40:45

## Status

**DPO_BF16_READY** for runtime/numerical execution.

This covers the real prefix-aware V2V-5 LingBot-Fast flow-matching energy backend. It is not the old diagnostic-energy skeleton.

## Prefix5 Input

- Pair manifest: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`
- Condition: prefix frames 0-4, `prefix_len=5`, `prediction_start_frame=5`
- Winner/loser target: future frames 5-80
- Loss/reward frame indices: 5..80; latent loss slots conservatively exclude prefix-contaminated slots
- `use_action=false`; no action branch is used

## Matrix

See `reports/dpo_bf16_preflight/matrix.csv`.

| Run | Status | World size | Steps | Pairs | Notes |
|---|---|---:|---:|---:|---|
| single_gpu7 | PASS | 1 | 2 | 5 | no SIGFPE/OOM/NaN; same noise/timestep; finite loss; nonzero grad |
| ddp2_gpu67 | PASS | 2 | 5 | 6 | no SIGFPE/OOM/NaN; same noise/timestep; finite loss; nonzero grad |
| ddp8_gpu01234567 | PASS | 8 | 5 | 5 | no SIGFPE/OOM/NaN; same noise/timestep; finite loss; nonzero grad |

## Tiny Probe Runtime Confirmation

The subsequent 20-step tiny probe also ran without SIGFPE/OOM/NaN and saved an adapter, but it did not pass the learning/video-quality gate.

- Probe output: `reports/dpo_probe_v2v5_20260627/tiny5_step20/`
- Mean step time: 192.222 sec
- Mean DPO loss: 0.693144497
- Final DPO loss: 0.693165958

## Interpretation

BF16 is numerically usable for the DPO backend, but the current preference data / scoring / tiny update does not yield a useful checkpoint. BF16 readiness does not imply DPO quality readiness.
