
# EXP LingBot-Fast Support / Capacity / Step Diagnosis

Current Status: PLANNED_PRD_READY

Updated: 2026-06-30 13:11:54

## Problem

LingBot-Fast V2V-5 outputs and rollout losers may be poor because of camera-condition weakness, domain support mismatch, insufficient LoRA capacity, insufficient steps, high-noise-only training, or prior broad-LoRA degradation. We need diagnosis before more DPO or large training.

## Hypothesis

If correct vs frozen/reversed/exaggerated camera outputs are nearly identical, Fast is weakly using camera conditions and camera injection must be fixed before DPO. If small LoRA rank/steps improve validation quality, the issue may be capacity/step count. If all small-LoRA variants fail, the bottleneck is likely domain support/objective/data rather than parameter count.

## Inputs

- Fixed V2V-5 screen16 / prefix5 conditions
- Existing StageA warmup reports and checkpoint metadata
- Existing candidate_generator_v2 and DPO smoke reports
- Original Fast baseline and any previous tiny camera-only LoRA if available

## Metrics

Pixel difference, LPIPS if available, PSNR, SSIM, sharpness/blur, background flow proxy, camera-following score, PhysGeo metrics, TypeB usability count, Codex visual difference.

## Visual Audit Rule

Every camera audit or small-LoRA checkpoint requires true V2V-5 rollout/contact sheet inspection. Metrics do not count as positive if videos are visually worse, blurry, frozen, or camera-insensitive.

## Success Gate

- Camera-condition audit determines whether camera changes affect output.
- Small-LoRA scaling plan/results distinguish capacity, steps, camera path, high-noise-only, and domain-support hypotheses.
- No broad-LoRA and no DPO are run.

## Failure Gate

The experiment is blocked if camera variants cannot be generated, if outputs are not visually inspected, or if training/checkpoint files would need to be modified/deleted.

## Output Paths

- `reports/fast_support_diagnosis/camera_condition_audit.csv`
- `reports/fast_support_diagnosis/camera_condition_audit.md`
- `reports/fast_support_diagnosis/contact_sheets/`
- `reports/fast_support_diagnosis/small_lora_scaling/decision.json`
- `docs/fast_support_capacity_step_diagnosis_report.md`

## What Is Explicitly Not Run

- No DPO training.
- No StageB.
- No GRPO.
- No full-data StageA.
- No broad-LoRA.
- No checkpoint deletion or modification.
- No MP4/JPG/PNG/checkpoint/large logs committed to Git.

## Git Checkpoint Before / After

Before execution: commit PRD/status files with `Prepare reward visual alignment and Fast support diagnosis PRDs`.
After execution: commit only code, scripts, docs, and small CSV/JSON summaries.
