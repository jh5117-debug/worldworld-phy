# Metrics Status

Updated: 2026-06-28T00:20:04

## Preference Protocol v1 Metrics

- Rollout pool scored: 48.
- Quality-floor pass rollout count: 48.
- Medium-hard rollout losers selected: 16.
- Valid final pairs: 66.
- Real energy sampled pairs: 5.
- Proxy energy triage pairs: 61.

LPIPS/FVD/VBench remain blocked by environment for protocol scoring and were not fabricated.

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
