# EXP fulldata-lingbotfast-warmup-weights Loser Source Evaluation

## Current Status

- Full-data V2V-5 prefix-aware warmup completed with all available 3299 rows, 2 epochs, bf16, C-scope LoRA (`camera_conditioning + self_attention`, last 4 blocks, rank 4 / alpha 4).
- Final adapter path: `local_assets/stageA_v2v5_all_available_c_r4_2epoch_retry1/train/checkpoints/fast_stageA_v2v5_C_camera_self_last4_r4_all_available_2epoch_retry1/high_only_phase/branches/final/fast_stageA_high_noise_adapter`.
- This experiment evaluates whether that adapter, labeled `fulldata-lingbotfast-warmup-weights`, is a better DPO loser source than the previous small-step C adapter.

## Problem

The user wants to generate 500 DPO loser videos only if Codex visually verifies that the new full-data warmup weights produce better/useful medium-hard loser behavior. The old default `WanI2VFast` load path can stall in `WanModelFast.from_pretrained`, so rollout must use the safe loader path proven during v8g.

## Hypothesis

The full-data warmup C adapter may improve stability while preserving medium-hard physical/geometric failures. If the videos are clearer and less collapsed than old C while still visibly wrong versus GT, it may be a better loser source.

## Smoke Design

- Input: first two v6b prefix5 conditions from `manifests/targeted_BC_loser_mining_v6b_conditions.jsonl`.
- New model: `M_C_all_available_warmup_final_safe`.
- Baseline: previous `M_C_camera_self_temporal_r4` small-step C rollout.
- Outputs: generated future videos, contact sheets, visual audit, sampled PSNR/SSIM/sharpness.

## Gate

Scale to 500 only if:

- V2V-5 rollout completes without fallback.
- Contact sheets exist and are reviewed by Codex.
- New C is visually better than old C or clearly provides more useful medium-hard loser behavior.
- It is not more collapsed, not blurrier, not more artifact-prone, and not too similar to GT.

## What Is Not Run

- No DPO training.
- No StageA/StageB/GRPO/broad-LoRA.
- No 500 generation unless smoke visual gate passes.
- No deletion of data/weights/checkpoints without explicit cleanup approval.


## Checkpoint Selection Addendum - 2026-07-06 10:26 CST

The planned checkpoint comparison was partially executed. Intermediate checkpoints `step_000103`, `step_000206`, `step_000309`, and `step_000412` each generated one reviewed contact sheet on `01002`.

Gate result: `FAIL_NO_CLEAR_IMPROVEMENT`.

The scale-to-500 condition remains unmet. The full-data warmup checkpoints should not be used for a 500-video loser generation run until an 8/16-condition smoke shows clear visual advantage and reliable multi-condition rollout completion.
