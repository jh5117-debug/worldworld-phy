# Final Report: Xorg Multidisplay And StageA1000 Visual Eval

## Xorg
- GPU6 :25 setup: blocked because root SSH/sudo was unavailable non-interactively.
- DISPLAY map: :8 is NVIDIA/GPU0; :9-:13 are llvmpipe; :14/:15 and :20-:26 are unavailable.
- :8 preserved: yes.
- Root password recorded: no.

## TDW Smoke
- 16-sample TDW multi-display smoke: skipped.
- Reason: fewer than two verified NVIDIA displays were available.
- No large TDW generation was run.

## StageA Rollout
- Conditions: 12, balanced as drop/collision/roll/containment = {'drop': 3, 'collision': 3, 'roll': 3, 'containment': 3}
- Base videos: 12/12
- StageA step200 videos: 12/12
- StageA final videos: 12/12
- GT videos linked: 12/12
- Four-column comparison videos: 12/12
- Comparison probe: 12/12 via imageio first-frame read
- Gallery: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work/local_assets/reports/human_review/stageA_1000_promptv2_12condition_base_step200_final/video_gallery.html`

## Metrics
| variant | PMF_proxy ↑ | FVD_proxy ↓ | PSNR ↑ | SSIM ↑ | LPIPS_proxy ↓ |
| --- | ---: | ---: | ---: | ---: | ---: |
| base | 0.5969 | 0.0178 | 16.9804 | 0.7275 | 0.0874 |
| stageA_step200 | 0.6056 | 0.0278 | 17.0371 | 0.7246 | 0.0887 |
| stageA_final | 0.6177 | 0.0220 | 17.2750 | 0.7312 | 0.0870 |

Proxy caveat: PMF/FVD/LPIPS are lightweight proxies, not reward v5 or official dataset-level metrics.

## Safety
No training, no reward scoring, no reward calibration, no DPO, no Stage1, no large TDW generation, no full checkpoint, and no local_assets commit/push.

## Next
- If Xorg root access is provided: configure GPU6 :25 first, then GPU1-7 :20-:26, then rerun 16-sample TDW multi-display smoke.
- If human review likes StageA final/step200: approve reward v5 scoring on this 12-condition rollout.
- If rollout quality is poor: consider Stage B mixed/low-noise or a broader LoRA scope before DPO.
- DPO remains later.
