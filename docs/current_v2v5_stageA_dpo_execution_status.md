# Current V2V-5 StageA / DPO Execution Status

Updated: 2026-06-27T17:40:45

## Current Branch

`research/quant-small-lora-dpo-probe-20260624`

## Completed

- Prefix-aware V2V-5 pair manifest is ready: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl` with 50 valid pairs.
- True V2V-5 generation wrapper is implemented and used: prefix frames 0-4 are loaded as condition, future frames 5-80 are generated/evaluated.
- Original Fast V2V-5 baseline rollout completed on 16 screen conditions.
- StageA V2V-5 camera-only LoRA warmup completed: 100 high-noise steps, rank 4, future-only loss.
- Every StageA checkpoint was evaluated by real V2V-5 inference and future-only PSNR/SSIM/freeze proxy.
- Tiny prefix5 DPO probe completed: 5 pairs, 20 optimizer steps, true LingBot-Fast energy backend.
- DPO checkpoint step20 was converted to an adapter, run through true V2V-5 inference, audited visually, and scored.

## Decisions

- StageA V2V-5: `STAGEA_V2V5_MIXED_USE_WITH_CAUTION`. It is slightly better than Original Fast on PSNR/SSIM but visually still hallucinates objects and has weak foreground/physics consistency.
- DPO probe: `DPO_PROBE_FAILED`. Runtime path works, but learning signal and post-probe video quality do not pass.

## Key Metrics

| Model | PSNR up | SSIM up | Freeze down |
|---|---:|---:|---:|
| Original Fast | 15.844572 | 0.837829 | 0.000 |
| StageA V2V-5 final | 16.012353 | 0.841087 | 0.000 |
| DPO step20 | 15.819494 | 0.836042 | 0.000 |

## Not Run

- No StageB.
- No GRPO.
- No full-data long StageA.
- No large-scale DPO.
- No data/checkpoint deletion.
