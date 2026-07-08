# Metrics Status

Current Status: Protocol v3 metric backend readiness updated

## Protocol v3 Backend Matrix

- PSNR: PASS
- SSIM: PASS
- LPIPS: PASS
- FVD: BLOCKED_BY_ENV after pytorchvideo/torchmetrics audit; no real video FVD backend or local temporal weights.
- VBench: BLOCKED_BY_ENV; no local VBench package/assets.

Report: reports/metrics_backend_readiness_v2/metrics_backend_report.md
Matrix: reports/metrics_backend_readiness_v2/metrics_backend_matrix.csv

LPIPS/FVD/VBench are never fabricated. Image FID is not reported as FVD.

---


Current Status: Protocol v2 metric backend readiness updated
Updated: 2026-06-29 11:58:36

## Protocol v2 Backend Matrix

- PSNR: PASS
- SSIM: PASS
- LPIPS: PASS
- FVD: BLOCKED_BY_ENV
- VBench: BLOCKED_BY_ENV

Report: `reports/metrics_backend_readiness/metrics_backend_report.md`
Matrix: `reports/metrics_backend_readiness/metrics_backend_matrix.csv`

LPIPS/FVD/VBench are never fabricated. FVD remains blocked unless a real video FVD backend is configured. VBench remains blocked unless local VBench package/assets/config are available.

---

# Metrics Status

Updated: 2026-06-27T17:40:45

## V2V-5 StageA / DPO Metrics

All current primary numbers below are computed on future frames 5-80 only.

| Model | PSNR up | SSIM up | Freeze down |
|---|---:|---:|---:|
| Original Fast | 15.844572 | 0.837829 | 0.000 |
| StageA V2V-5 final | 16.012353 | 0.841087 | 0.000 |
| DPO step20 | 15.819494 | 0.836042 | 0.000 |

LPIPS, FVD, and VBench are still blocked/not available in the active environment and were not fabricated. PhysGeo components remain diagnostic; PSNR/SSIM are not sufficient evidence of physical consistency.

DPO signal summary: mean loss 0.693144497, final loss 0.693165958, mean implicit accuracy 0.600, mean winner improvement 0.000084573.

---

# Metrics Status (2026-06-27 04:43:25)

DPO-specific metric state:
- DPO energy diagnostics now record policy/ref winner and loser energies, delta_policy, delta_ref, DPO loss, implicit accuracy, winner_improvement, loser_degradation, same_noise, same_timestep, and future-only latent loss indices.
- Prefix frames are excluded from the DPO energy target at latent level.
- Video metrics for tiny probe checkpoints remain pending until BF16 preflight passes and probe checkpoints exist.


---

# Current Metrics Status

Updated: 2026-06-27 01:28:38

- Available now: PSNR, SSIM, freeze proxy, quality proxy, Epipolar diagnostic, C-SGC diagnostic.
- Blocked by environment: LPIPS, FVD, VBench.
- Incomplete real backends: ADE/DTW trajectory, object mask IoU, FG-ID, PES, RCS.
- Interpretation rule: PSNR/SSIM are reconstruction indicators only; they cannot prove camera-conditioned physical consistency.

# Current Status Update - 2026-06-24

- New active branch: `research/quant-small-lora-dpo-probe-20260624` from `63d1b93`.
- Broad-LoRA is no longer the main route for candidate generation because generation quality was FAILED_OR_MIXED despite fixed-val loss improvement.
- Current focus: Quantitative Benchmark v1, small/low-rank LoRA scope sweep, Reward Calibration v2, and anchored DPO probe.
- GPU0-7 are authorized for this round; no full-data long StageA, no StageB, no GRPO, and no large-scale DPO.
- DPO data strategy: GT winners plus quality-bounded hard-negative losers selected from Original Fast, last-week camera-only tiny LoRA, small-LoRA sweep candidates, controlled corruptions, and broad-LoRA only if it passes loser quality floor.

---

# Metrics

- BRC: Background Rigid Consistency.
- CAF: Camera Adherence / Following.
- FG-ID: Foreground identity consistency.
- ODS: Object deformation score.
- PES: Physics event score.
- RCS: Reobserve consistency score.
- Freeze Rate: camera/foreground/global freeze detection.
- Quality: blur, brightness, saturation, flicker.

Primary benchmark splits: camera-only static, static-camera physics, moving-camera physics, reobserve split, and PhyInOne OOD.

## Video Audit Workflow Update - 2026-06-24

`cam_physgeo.eval.video_audit` now creates per-video contact sheets plus `all_video_audit.csv` / `all_video_audit.jsonl` templates. The script performs only decode/freeze/blur/flicker prechecks and marks rows as `codex_precheck_needs_visual_review`; final PASS/FAIL still requires Codex visual review of every generated video.

Required audit fields remain:

- background stability
- camera following
- foreground identity
- object deformation
- physical event
- reobserve
- freeze
- visual quality
- failure tags

This avoids selecting only best-looking examples for PPT or DPO. Every rollout candidate must have a row before pair selection.

## DPO Training Sanity v12

Tiny guarded SDPO on S1 was stopped at step10: mean winner improvement turned negative and DPO loss remained near 0.693. Decision: `DPO_V12_FAILED_WINNER_WORSE_NO_SIGNAL`. Large DPO remains blocked.

<!-- V12C_METRIC_PLAN_STATUS_START -->

## V12C METRIC PLAN STATUS

v12c checkpoint metrics were not run because the preference probe was blocked before training by GPU4 occupancy. Required metrics remain PSNR, SSIM, LPIPS, FVD smoke, VBench temporal flickering, and PhysGeo for any future step0/5/10 checkpoint eval.

<!-- V12C_METRIC_PLAN_STATUS_END -->

## v13b DPO Objective Search Update

- Updated: 2026-07-06T13:08:17+08:00.
- v13b objective search code and GPU4/5-only scheduler are prepared.
- Training did not launch because GPU4/5 were occupied by existing non-v13b jobs / GPU query timed out conservatively.
- Decision: `DPO_RECIPE_GPU_BLOCKED`; no scale, no train400, no large DPO.
## v13b Metric Gate Note

For v13b, S05 and S07 passed enough training signal to run checkpoint evaluation, but both failed the strict metric gate due VBench temporal_flickering worsening from step000 to step050. Visual audit did not show obvious collapse, but the metric gate remains binding. No fake FVD/VBench values were used.

## v14 Latent Monitor Status

V-JEPA/VideoREPA/TRD are monitor-first only. v14 found local backend candidates but did not produce valid TRD/VJEPA scores, so no latent auxiliary loss is enabled.


## E02_best7 Checkpoint Video Audit Update (2026-07-07T02:37:56.080956Z)

- Candidate: `E02_best7` / `calibrated_winner_detached_log` / `beta=1000` / `L0_camera_r4`.
- Training signal: `TRAINING_SIGNAL_PASS`.
- Mean winner improvement post: `0.00010894877570016044`.
- Final winner improvement post: `0.00033855438232421875`.
- Mean winner contribution ratio: `0.6680136300480072`.
- True V2V-5 checkpoint videos generated: `12` (`step000`, `step005`, `step007` on 4 validation samples).
- Codex visual audit: `FAIL`. Final `step007` is worse than `step000` on multiple samples due to duplicate objects, hallucinated blobs/fragments, and foreground object-count/identity drift.
- Metrics: PSNR/SSIM rows `12/12`; LPIPS GPU smoke `PASS`; FVD remains `BLOCKED_BY_ENV`; VBench real checkpoint scoring not configured in this wrapper.
- Decision: `DPO_RECIPE_TRAINING_SIGNAL_ONLY_VIDEO_FAIL_V14`.
- Scale permission: `NO_SCALE`; do not run S16/S32/train400 from this recipe.

Relevant paths:
- `reports/dpo_utility_calibration_v14/objective_search/E02_best7/checkpoint_eval/video_audit.csv`
- `reports/dpo_utility_calibration_v14/objective_search/E02_best7/checkpoint_eval/video_audit_summary.md`
- `reports/dpo_utility_calibration_v14/objective_search/E02_best7/metrics/metrics_summary.md`


## v14 E09/E10 Final Visual Gate Update (2026-07-07T17:56:59Z)

- E09 (, L0 camera r4) reached strong early scalar signal at step50: winner improvement , WCR , loser degradation negative. True V2V-5 audit failed: step50 was worse/not-better on 4/4 fixed validation samples, with foreground duplication, colored blob fragments, and line/text-like artifacts.
- E10 (, L2 camera-temporal r4) completed 100/100 steps with final winner improvement  and mean WCR . True V2V-5 audit failed: step100 was worse on 2/4 samples and not decisively better on the rest, with duplicate green balls, object identity clutter, and foreground fragments.
- Current decision: . The scalar no-signal / beta-scale issue is partially repaired, but energy/gap improvement does not yet predict rollout visual quality.
- Scale permission: ; no S16/S32/train400/large DPO from these recipes. Next direction is a rollout-quality or latent visual monitor/regularizer before further DPO scaling.


## v14 Latent Monitor Metric Note (2026-07-07T22:19:25Z)

- Added a local DINOv2 ViT-S/14 frame fallback monitor smoke.
- Output: `reports/dpo_utility_calibration_v14/latent_monitor/dinov2_frame_smoke.csv`.
- Decision: `LATENT_MONITOR_DINO_FRAME_SMOKE_PASS` on 4/4 calibration pairs.
- This is not a replacement for full V-JEPA/VideoREPA/TRD, but it is a real no-download latent visual score that detects controlled loser differences.


## v14 V-JEPA2 Latent Monitor Smoke Update (2026-07-07T22:32:50Z)

- V-JEPA2 smoke CSV: `reports/dpo_utility_calibration_v14/latent_monitor/vjepa2_video_smoke.csv`.
- Required summary path: `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_summary.md`.
- Required monitor path: `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_monitor.csv`.
- Backend: local V-JEPA2.1 ViT-B EMA encoder from `vjepa2_1_vitb_dist_vitG_384.pt`; no model download.
- Device: `CUDA_VISIBLE_DEVICES=4`, process `cuda:0` mapping to physical GPU4.
- Result: `LATENT_MONITOR_PASS_VJEPA2_SMOKE` / `LATENT_MONITOR_VJEPA2_VIDEO_SMOKE_PASS` on 4/4 asset-complete calibration pairs.
- Positive V-JEPA embedding margin rows: 4/4.
- Positive token-relation margin rows: 4/4.
- This supports a v15 monitor/regularizer direction for catching artifact amplification, but it is still monitor-only and not an auxiliary-loss training integration.
- DPO recipe decision remains `DPO_RECIPE_NOT_FOUND_V14`; S16/S32/train400/large DPO remain blocked because previous DPO checkpoint videos degraded.


## v14 Broad V-JEPA2 Latent Monitor Coverage Update (2026-07-07T23:06:28Z)

- Coverage summary: `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_summary.md`.
- Combined monitor CSV: `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_monitor.csv`.
- Coverage table: `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_coverage_summary.csv`.
- Ran bounded V-JEPA2 monitor on calibration4, synthetic10, stratified100, S_pass4, and rollout15 subsets.
- Combined rows: 133; ok rows: 74; asset/path error rows: 59.
- For every row where both WIN and LOSE videos were available, V-JEPA2 distinguished the loser: positive V-JEPA margin 74/74 and positive token-relation margin 74/74.
- Stratified100: 64/100 ok, 64/64 positive token-relation margins. The 36 failures are missing old rollout/v10 local_assets videos.
- S_pass4 and rollout15 currently have 0 ok rows because their loser rollout video assets are missing from local_assets; this is recorded as an asset coverage blocker, not a latent-backend failure.
- Decision: `LATENT_MONITOR_PASS_VJEPA2_SMOKE_WITH_ASSET_BLOCKERS`.
- DPO recipe decision remains `DPO_RECIPE_NOT_FOUND_V14`; no S16/S32/train400/large DPO scale is allowed until checkpoint video quality passes.

## v14 Completion Metrics Rule (2026-07-08)

The earlier note that v14 had no valid TRD/V-JEPA scores is superseded. Local V-JEPA2 produced real no-download scores:

- WIN/LOSE coverage: `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_monitor.csv`, 133 attempted rows, 74 available-video ok rows, 74/74 positive token-relation margins.
- Expanded checkpoint regression: `reports/dpo_utility_calibration_v14/latent_monitor/checkpoint_regression_all_available/vjepa2_checkpoint_regression_all.csv`, 24/24 ok rows with positive V-JEPA/token-relation margins.
- Gate statistics show V-JEPA2 is useful as a high-recall drift / inspection trigger, but not a standalone quality approval metric: thresholding catches worse checkpoints but also has false positives and low AUC versus Codex worse/not-worse labels.

Metric policy after v14:
- A promising DPO scheme must pass scalar gaps, true V2V-5 videos, PSNR/SSIM/LPIPS where available, FVD/VBench when the wrapper supports them, PhysGeo checks, and Codex visual audit.
- V-JEPA2 can trigger or prioritize inspection and can be considered for v15 regularization, but it cannot approve a checkpoint by itself.
- If visual audit fails, metric incompleteness cannot authorize scale.

## v14 V-JEPA2 Artifact Correlation Update (2026-07-08T10:31 CST)

- Added correlation report: `reports/dpo_utility_calibration_v14/latent_monitor/artifact_correlation/vjepa_artifact_correlation.md`.
- Source: existing `vjepa2_checkpoint_regression_all_with_visual.csv` plus Codex visual labels; no training or new rollout was run.
- Decision: `VJEPA_ARTIFACT_CORRELATION_WEAK_MONITOR_ONLY`.
- V-JEPA2 remains useful as a high-recall drift/inspection trigger, but artifact-specific discrimination is weak/noisy on the current 24-row checkpoint set and especially limited for scalar-positive E07/E09/E10 rows.
- This supports the v15 plan: V-JEPA2 should be paired with explicit artifact labels/gates, not used as standalone checkpoint approval or a direct DPO reward.
