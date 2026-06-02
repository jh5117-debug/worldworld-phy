# Current State Before Fixed-Noise DPO Diagnostic

## Previous Branch State

- Previous branch: `physion-dpo-1pair-overfit-miniloop`
- Previous commit: `3d91ba689b257352d1f415ce95830eef9f9994dc`
- No formal training, VideoGPA `03_train.py`, Stage1, rollout generation, reward calibration, LoRA save, checkpoint save, or local asset submission occurred.

## Resampled 5-Step Mini-Loop

- Status: passed.
- Pair count: `1`.
- Steps: `5 / 5`.
- LoRA target modules:
  - `blocks.39.cam_shift_layer`
  - `blocks.39.cam_scale_layer`
- Rank / alpha: `2 / 4.0`
- Trainable LoRA params: `40,960`
- Optimizer: AdamW, lr `1e-5`.
- Loss values: `[0.6931473016738892, 0.6931471228599548, 0.6931470632553101, 0.6931471228599548, 0.6931472420692444]`
- LoRA params changed: yes, max diff `4.924208769807592e-05`.
- Base sample params changed: no, max diff `0.0`.
- Reference sample params changed: no, max diff `0.0`.
- NaN/Inf gradients: no.
- OOM: no.
- Peak allocation: about `50.75 GiB`.
- `restore_after_loop`: passed.

## Interpretation Gap

The 5-step mini-loop resampled both noise and timestep at each step. The loss stayed finite but was not expected to decrease monotonically because each step used a different denoising task. A fixed-noise/fixed-timestep comparison was not run in the previous round.

## Current Permission Boundary

- Real training is not allowed.
- VideoGPA `03_train.py` is not allowed.
- Multi-pair DPO is not allowed.
- Rollout generation, reward calibration, Stage1, and TDW generation are not allowed.
- This round is only allowed to run a 1-pair fixed-noise/fixed-timestep diagnostic.
- Optimizer steps are capped at `10`.
- Optimizer may contain only LoRA params.
- Base/reference must remain unchanged.
- No LoRA/checkpoint save is allowed.
