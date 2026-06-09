# Final Report: TDW v5 200 Stage A Warmup Pilot

Date: 2026-06-09

## Setup

Dataset: TDW v5 aggressive 2x 200 human-approved camera-visible set.

Split: train 160 / val 20 / test 20.

Model stack: `WanI2VFast`, `WanModelFast`, `Wan2_1_VAE`, `FlowUniPCMultistepScheduler`.

GPU: GPU7 only. GPU0 was not used.

Timestep mode: diagnostic high-noise band, timestep 799, sigma 0.799.

Trainable scope: runtime `camera_control_lora_tiny` on:

- `blocks.39.cam_shift_layer`
- `blocks.39.cam_scale_layer`

## Training Safety

This was a tiny Stage A warmup pilot, not formal training.

- no DPO
- no VideoGPA `03_train`
- no Stage1
- no rollout
- no reward calibration
- no checkpoint saved
- no LoRA saved
- no optimizer state saved
- base weights frozen

## Metrics

The complete gate run used 20 steps. A first 100-step launch was stopped after 3 steps because observed runtime would likely exceed the timeout before writing a final summary.

| Metric | Value |
|---|---:|
| Steps completed | 20 |
| Train loss first / last | 0.052260 / 0.056665 |
| Train loss min / max | 0.030702 / 0.062314 |
| Val losses | 0.033537, 0.034270 |
| Grad norm first / last / max | 0.004051 / 0.007884 / 0.007884 |
| Trainable params | 40,960 |
| LoRA tensors changed | 4 |
| Base sampled tensors changed | 0 |
| Runtime | 3456.8 sec |
| NaN / Inf | none |
| OOM | none |

Tensor checks:

- latent: `[16, 2, 60, 104]`
- camera/control: `[1, 384, 2, 60, 104]`
- dummy action norm: `0.0`
- `use_action=false`

## MoE / Timestep

LingBot-Fast does not expose explicit high-noise / low-noise expert routing in this runtime. The high-noise label is therefore a scheduler-quantile diagnostic band, not an exact expert-route claim.

Expert route: `unavailable_in_fast_or_not_exposed`.

## Gate Result

Stage A stability gate: passed.

The real model loaded, forward/backward/optimizer step ran, LoRA received nonzero gradients, validation forward loss was finite, and sampled frozen base parameters were unchanged.

## Limitation

The first 20 rows in the train split were all `collision + orbit_right_64`, so this is a stability gate rather than a template-balanced behavior conclusion. The next pilot should shuffle or balance samples.

## Next

Do not run Stage B, rollout, checkpoint saving, reward calibration, or DPO automatically.

Next decision options:

- approve Stage B mixed/low-noise detail pilot with shuffled/balanced sampler;
- approve rerunning Stage A with adapter checkpoint save enabled for later rollout;
- pause and inspect metrics.
