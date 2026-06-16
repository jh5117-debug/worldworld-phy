# StageA 1000 PromptV2 Visual Metrics Report

Metrics file: `local_assets/experiments/exp_stageA_1000_combined_prompt_v2_rollout_compare/metrics/stageA1000_promptv2_visual_metrics.csv`

These are lightweight proxy metrics, not reward v5 scoring and not official FVD/LPIPS. They are intended for a quick visual regression check before deciding whether to run reward scoring.

| variant | PMF_proxy ↑ | FVD_proxy ↓ | PSNR ↑ | SSIM ↑ | LPIPS_proxy ↓ |
| --- | ---: | ---: | ---: | ---: | ---: |
| base | 0.5969 | 0.0178 | 16.9804 | 0.7275 | 0.0874 |
| stageA_step200 | 0.6056 | 0.0278 | 17.0371 | 0.7246 | 0.0887 |
| stageA_final | 0.6177 | 0.0220 | 17.2750 | 0.7312 | 0.0870 |

## Directional Winners
- PMF_proxy: stageA_final
- FVD_proxy: base
- PSNR: stageA_final
- SSIM: stageA_final
- LPIPS_proxy: stageA_final

## Interpretation
- StageA final is slightly better than Base on PMF_proxy, PSNR, SSIM, and LPIPS_proxy, but Base has the best FVD_proxy.
- StageA step200 improves PMF_proxy over Base but is weaker than final on PSNR/SSIM/LPIPS_proxy and has the worst FVD_proxy.
- This is not enough to approve DPO. A human review plus optional reward v5 scoring should decide whether StageA final or step200 is worth using downstream.
