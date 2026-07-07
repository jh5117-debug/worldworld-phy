# TRD / V-JEPA Latent Monitor Coverage Summary

Decision: `LATENT_MONITOR_PASS_VJEPA2_SMOKE_WITH_ASSET_BLOCKERS`

Combined rows: 133; ok rows: 74; error rows: 59
Positive token-relation margin among ok rows: 74/74

## Subset Coverage

| subset | rows | ok | errors | positive_vjepa | positive_relation | decision |
|---|---:|---:|---:|---:|---:|---|
| calibration4 | 4 | 4 | 0 | 4 | 4 | `LATENT_MONITOR_VJEPA2_VIDEO_SMOKE_PASS` |
| synthetic10 | 10 | 6 | 4 | 6 | 6 | `LATENT_MONITOR_VJEPA2_VIDEO_SMOKE_PASS` |
| stratified100 | 100 | 64 | 36 | 64 | 64 | `LATENT_MONITOR_VJEPA2_VIDEO_SMOKE_PASS` |
| s_pass4 | 4 | 0 | 4 | 0 | 0 | `LATENT_MONITOR_VJEPA2_VIDEO_SMOKE_FAIL` |
| rollout15 | 15 | 0 | 15 | 0 | 0 | `LATENT_MONITOR_VJEPA2_VIDEO_SMOKE_FAIL` |

## Interpretation

The local V-JEPA2.1 ViT-B EMA encoder distinguishes every pair for which both WIN and LOSE videos are available: all ok rows have positive V-JEPA embedding margins and positive token-relation margins.

Coverage is currently limited by missing old local_assets videos, especially rollout-derived GT>C losers and some v10 TypeM synthetic loser files. Those rows are recorded as errors rather than silently dropped or faked.

This supports V-JEPA2/DINO as a v15 monitor or regularizer candidate, but it does not permit DPO scale because v14 DPO checkpoint videos still degraded.
