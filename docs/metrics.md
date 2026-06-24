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
