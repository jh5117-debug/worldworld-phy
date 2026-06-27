# Final Report: V2V-5 StageA and Tiny DPO Probe

Updated: 2026-06-27T17:40:45

## Git / Branch

- Branch: `research/quant-small-lora-dpo-probe-20260624`
- Latest pushed engineering commits before final docs include V2V-5 wrapper, future-only StageA loss, metrics helpers, and StageA pilot configuration.

## V2V-5 Wrapper

Status: real wrapper implemented and used.

- Prefix frames 0-4 are loaded as clean video condition.
- Generated/evaluated future is frames 5-80.
- Manifests record prefix_len=5 and prediction_start_frame=5.
- This is not the old image-only I2V-1 path.

## StageA V2V-5

- Dataset: prefix5 pilot, 1000 samples, train/val/test 800/100/100.
- Training: 100 high-noise steps.
- LoRA: camera-conditioning only, rank 4, alpha 4, dropout 0.05.
- Best checkpoint: final.
- Decision: `STAGEA_V2V5_MIXED_USE_WITH_CAUTION`.

| Model | PSNR up | SSIM up | Freeze down |
|---|---:|---:|---:|
| Original Fast | 15.844572 | 0.837829 | 0.000 |
| StageA V2V-5 final | 16.012353 | 0.841087 | 0.000 |

Visual audit: final is not collapsed and is slightly better by PSNR/SSIM, but it still hallucinates extra objects and does not reliably preserve foreground identity or physical events.

## DPO Probe

- Pair type: prefix-aware V2V-5 anchored pairs.
- Probe size: 5 pairs, 20 optimizer steps.
- Backend: real LingBot-Fast energy, not fake proxy.
- BF16 runtime: passed.
- Decision: `DPO_PROBE_FAILED`.

| Metric | Value |
|---|---:|
| mean DPO loss | 0.693144497 |
| final DPO loss | 0.693165958 |
| mean implicit accuracy | 0.600 |
| mean winner improvement | 0.000084573 |
| final winner improvement | -0.000231806 |
| DPO step20 PSNR | 15.819494 |
| DPO step20 SSIM | 0.836042 |

Reason: the probe runs, but loss stays near 0.693, winner improvement is too small and negative at final, and DPO step20 video quality is worse than StageA final.

## Metric Availability

- PSNR/SSIM/freeze proxy: completed.
- LPIPS/FVD/VBench: blocked or unavailable in this environment; not fabricated.
- PhysGeo metrics: diagnostic only, not sufficient for DPO scale-up decision yet.

## Recommendation

Do not scale DPO. The next useful step is reward/pair-quality repair: improve object identity/event metrics, keep GT-clean winners, reject collapsed losers, and only rerun DPO once winner improvement can be measured before video quality degrades.

## Safety Confirmation

No StageB, GRPO, full-data long StageA, large-scale DPO, checkpoint deletion, or data/weight/video push was performed.
